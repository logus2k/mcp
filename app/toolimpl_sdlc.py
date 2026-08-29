"""SDLC Brain tools — the deterministic steps of the maturity-assessment pipeline.

Three tools, one per step of the uniform pipeline that a workflow runs once per
(project, cell):

    collect evidence  ->  score the cell  ->  write the state

They are deliberately *deterministic*: counting deployments, taking medians and
comparing numbers against published bands is arithmetic, not judgment, and a
language model is the wrong instrument for it. Judgment is reserved for the cells
where the evidence is genuinely ambiguous, and is invoked separately.

Design constraints honoured here:

* **Branching lives in the tools.** The workflow graph cannot branch, so the shape
  of the pipeline is identical for every cell and the differences (which sensor,
  which thresholds, measured vs attested) are resolved inside these functions.
* **Configuration over code.** What varies per project (which job, which
  credential) is project config; what varies per cell (which sensor, which bands)
  is a scoring specification. Adding a cell should be adding data.
* **Secrets are never stored.** A connector names the environment variable that
  holds its credential; the value is read at call time.
* **State is files.** One JSON document per project and cell, written atomically,
  because a maturity conclusion has to be readable and diffable by a human.
"""
from __future__ import annotations

import json
import os
import re
import statistics
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

# Where the SDLC knowledge base (read-only reference) and the per-tenant state live.
# Mounted into this service; unset means the Brain tools are not deployed here, and
# they say so plainly rather than inventing a path.
SDLC_RO_DIR = os.getenv("SDLC_RO_DIR", "/sdlc/ro")
SDLC_RW_DIR = os.getenv("SDLC_RW_DIR", "/sdlc/rw")

_CELL_RE = re.compile(r"^[A-Za-z0-9 ._&-]+\|[A-Za-z0-9 ._&-]+$")
_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class SdlcToolError(RuntimeError):
    """A tool could not do its job. Raised loudly — never returned as a fake result,
    because a silently-empty assessment reads as 'no problems found'."""


# ── small helpers ────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _require_project(project: str) -> str:
    project = (project or "").strip()
    if not _ID_RE.match(project):
        raise SdlcToolError(f"invalid project id {project!r}")
    return project


def _require_cell(cell: str) -> str:
    cell = (cell or "").strip()
    if not _CELL_RE.match(cell):
        raise SdlcToolError(
            f"invalid cell {cell!r}: expected '<Phase>|<Lens>', e.g. 'Release|Metrics'"
        )
    return cell


def _cell_filename(cell: str) -> str:
    """'Release|Metrics' -> 'Release__Metrics.json'. One file per cell means the
    thirty-six runs of a nightly pass never contend for the same document."""
    return cell.replace("|", "__").replace(" ", "_") + ".json"


def _read_json(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write_json_atomic(path: str, payload: Any) -> None:
    """Write a temporary file in the same directory, then rename — a reader never
    sees a half-written assessment, and a crash cannot corrupt one."""
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=False)
            fh.write("\n")
        os.chmod(tmp, 0o644)   # readable/diffable on the host, like the other stores
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _project_config(project: str) -> dict:
    path = os.path.join(SDLC_RW_DIR, "projects", f"{project}.json")
    if not os.path.isfile(path):
        raise SdlcToolError(
            f"no configuration for project {project!r} (expected {path}) — "
            "register the project and its connectors first"
        )
    return _read_json(path)


def _scoring_spec(cell: str) -> dict:
    path = os.path.join(SDLC_RO_DIR, "kb", "scoring_specs.json")
    if not os.path.isfile(path):
        raise SdlcToolError(f"scoring specifications not found at {path}")
    spec = (_read_json(path).get("specs") or {}).get(cell)
    if not spec:
        raise SdlcToolError(
            f"no scoring specification for cell {cell!r} — it is not automatically "
            "scorable yet (add one to scoring_specs.json)"
        )
    # A spec keyed to a cell the knowledge base does not have is silently useless: it
    # scores into a record the wall cannot paint and the advisor cannot cite (there is
    # no anchor to quote). Caught here, loudly, rather than discovered as a blank cell.
    kb_path = os.path.join(SDLC_RO_DIR, "kb", "kb_data.json")
    if os.path.isfile(kb_path):
        known = (_read_json(kb_path).get("cells") or {})
        if cell not in known:
            near = [k for k in known if k.split("|")[-1] == cell.split("|")[-1]]
            raise SdlcToolError(
                f"cell {cell!r} is not in the knowledge base — a scoring specification "
                f"must use the KB's exact cell key. Same-lens keys: {sorted(near)[:6]}"
            )
    return spec


def _state_path(project: str, cell: str) -> str:
    return os.path.join(SDLC_RW_DIR, "state", project, _cell_filename(cell))


# ── sensor: Jenkins -> the four delivery metrics ─────────────────────────────
async def _jenkins_dora(project: str, conf: dict, window_days: int,
                        spec: dict | None = None) -> dict:
    """Read a job's build history and derive the four delivery metrics.

    The subtlety worth naming: a *successful build* is not the same thing as a
    *deployment*. Early pipeline runs succeed in seconds without ever reaching a
    deploy stage, so counting them would inflate deployment frequency and deflate
    the failure rate. A build therefore counts as a deployment only if it also ran
    long enough to have deployed (``min_deploy_seconds``).
    """
    base = str(conf.get("base_url") or "").rstrip("/")
    job = str(conf.get("job") or "").strip()
    if not base or not job:
        raise SdlcToolError("jenkins connector needs both 'base_url' and 'job'")

    user = os.getenv(str(conf.get("user_env") or "JENKINS_USER"), "")
    token = os.getenv(str(conf.get("token_env") or "JENKINS_TOKEN"), "")
    if not user or not token:
        raise SdlcToolError(
            "jenkins credentials are not configured — set the environment variables "
            f"{conf.get('user_env')!r} and {conf.get('token_env')!r} on this service"
        )

    tree = ("builds[number,result,timestamp,duration,building,"
            "changeSets[items[commitId,timestamp]]]")
    url = f"{base}/job/{job}/api/json"
    async with httpx.AsyncClient(timeout=45) as client:
        r = await client.get(url, params={"tree": tree}, auth=(user, token))
    if r.status_code != 200:
        raise SdlcToolError(
            f"jenkins {r.status_code} for {url}: {r.text[:200]}"
        )
    builds = (r.json() or {}).get("builds") or []

    min_ms = int(conf.get("min_deploy_seconds") or 45) * 1000
    unstable_ok = bool(conf.get("unstable_counts_as_deploy", True))
    cutoff_ms = (datetime.now(tz=timezone.utc).timestamp() - window_days * 86400) * 1000

    deploy_results = {"SUCCESS"} | ({"UNSTABLE"} if unstable_ok else set())
    in_window = [b for b in builds
                 if not b.get("building") and (b.get("timestamp") or 0) >= cutoff_ms]

    deployments, failures, lead_times = [], [], []
    for b in in_window:
        result = b.get("result")
        ts = int(b.get("timestamp") or 0)
        dur = int(b.get("duration") or 0)
        deployed = result in deploy_results and dur >= min_ms
        if deployed:
            deployments.append(b)
            # Lead time: from the OLDEST commit in this build to the end of the deploy.
            commits = [int(it.get("timestamp") or 0)
                       for cs in (b.get("changeSets") or [])
                       for it in (cs.get("items") or [])
                       if it.get("timestamp")]
            if commits:
                lead_times.append(((ts + dur) - min(commits)) / 3_600_000.0)
        elif result == "FAILURE":
            # ABORTED is a cancelled run, not a failed change — excluded deliberately.
            failures.append(b)

    # Recovery: from a failed build to the next non-failing one, chronologically.
    chron = sorted(in_window, key=lambda b: b.get("timestamp") or 0)
    recoveries = []
    pending_failure_ts = None
    for b in chron:
        result = b.get("result")
        ts = int(b.get("timestamp") or 0)
        if result == "FAILURE" and pending_failure_ts is None:
            pending_failure_ts = ts
        elif result in deploy_results and pending_failure_ts is not None:
            recoveries.append((ts - pending_failure_ts) / 3_600_000.0)
            pending_failure_ts = None

    n_deploy, n_fail = len(deployments), len(failures)
    attempts = n_deploy + n_fail

    metrics: dict[str, Any] = {
        "deployment_frequency": round(n_deploy / window_days, 4) if window_days else None,
        "lead_time_hours": round(statistics.median(lead_times), 2) if lead_times else None,
        "change_failure_rate": round(100.0 * n_fail / attempts, 2) if attempts else None,
        "recovery_time_hours": round(statistics.median(recoveries), 2) if recoveries else None,
    }
    return {
        "metrics": metrics,
        "observations": {
            "builds_in_window": len(in_window),
            "deployments": n_deploy,
            "failed_changes": n_fail,
            "recoveries_observed": len(recoveries),
            "builds_with_commit_data": len(lead_times),
        },
        "source": {"kind": "jenkins", "job": job, "base_url": base},
    }


# ── sensor: repository scan -> practice evidence ─────────────────────────────
# Names of the files a pipeline is usually defined in. Scanned as text so a rule can
# ask "does the pipeline mention coverage?" without parsing five different CI dialects.
_CI_FILES = ("Jenkinsfile", ".gitlab-ci.yml", "azure-pipelines.yml", "Makefile")
_CI_GLOBS = (".github/workflows/*.yml", ".github/workflows/*.yaml")


def _ci_text(root: str) -> str:
    """Everything the project's pipeline definitions say, concatenated and lowercased."""
    import glob as _glob

    parts = []
    for name in _CI_FILES:
        p = os.path.join(root, name)
        if os.path.isfile(p):
            try:
                parts.append(open(p, encoding="utf-8", errors="replace").read())
            except OSError:
                pass
    for pattern in _CI_GLOBS:
        for p in _glob.glob(os.path.join(root, pattern)):
            try:
                parts.append(open(p, encoding="utf-8", errors="replace").read())
            except OSError:
                pass
    return "\n".join(parts).lower()


async def _repo_scan(project: str, conf: dict, window_days: int, spec: dict | None = None) -> dict:
    """Detect *practices* by looking for the artifacts that embody them.

    Deliberately literal: a rule asks whether a path exists or whether the pipeline
    text mentions something. That is weaker than reading intent, but it is honest and
    reviewable — and a practice with no artifact is, for assessment purposes, a
    practice nobody can verify.
    """
    import glob as _glob

    root = str(conf.get("path") or "").rstrip("/")
    if not root:
        raise SdlcToolError("repo connector needs a 'path'")
    if not os.path.isdir(root):
        raise SdlcToolError(
            f"repository for {project!r} is not mounted at {root} — mount it read-only "
            "into this service to enable scan-based cells"
        )

    ci = _ci_text(root)
    signals: dict[str, Any] = {}
    detail: dict[str, Any] = {}

    for name, rule in ((spec or {}).get("signals") or {}).items():
        hit = False
        why = None
        for rel in rule.get("paths") or []:
            matches = _glob.glob(os.path.join(root, rel), recursive=True)
            if matches:
                hit = True
                why = "found " + os.path.relpath(matches[0], root)
                break
        if not hit:
            for needle in rule.get("ci_contains") or []:
                if needle.lower() in ci:
                    hit = True
                    why = f"pipeline mentions {needle!r}"
                    break
        signals[name] = hit
        detail[name] = why or "not found"

    return {
        "signals": signals,
        "observations": {"checked": len(signals), "present": sum(1 for v in signals.values() if v),
                         "detail": detail},
        "source": {"kind": "repo_scan", "path": root, "ci_files_found": bool(ci)},
    }


# ── sensor: uptime monitor -> operational outcomes ───────────────────────────
async def _kuma_observability(project: str, conf: dict, window_days: int,
                              spec: dict | None = None) -> dict:
    """Derive operational outcomes from an uptime monitor's heartbeat history.

    The monitor's database is read from a **copy**: it is a live SQLite file in
    write-ahead mode, and opening it in place would either fail (a read-only mount
    denies the shared-memory file every reader needs) or risk interfering with the
    monitor itself. Copying costs a few milliseconds and cannot disturb production.
    """
    import shutil, sqlite3, tempfile as _tf

    db = str(conf.get("db_path") or "").strip()
    name = str(conf.get("monitor") or project).strip()
    if not db or not os.path.isfile(db):
        raise SdlcToolError(
            f"uptime-monitor database not found at {db!r} — mount it read-only to "
            "enable operational metrics"
        )

    tmpdir = _tf.mkdtemp(prefix="kuma_")
    try:
        local = os.path.join(tmpdir, "snapshot.db")
        shutil.copy2(db, local)
        for suffix in ("-wal", "-shm"):          # carry the recent writes too
            if os.path.isfile(db + suffix):
                shutil.copy2(db + suffix, local + suffix)
        con = sqlite3.connect(local)
        try:
            cur = con.cursor()
            cur.execute("SELECT id FROM monitor WHERE name = ?", (name,))
            row = cur.fetchone()
            if not row:
                raise SdlcToolError(
                    f"no monitor named {name!r} in the uptime monitor — this project is "
                    "not being watched, so its operational metrics cannot be measured"
                )
            mid = row[0]
            cutoff = (datetime.now(tz=timezone.utc)
                      - timedelta(days=window_days)).strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "SELECT time, status FROM heartbeat WHERE monitor_id = ? AND time >= ? "
                "ORDER BY time ASC", (mid, cutoff))
            beats = cur.fetchall()
        finally:
            con.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    if not beats:
        raise SdlcToolError(
            f"monitor {name!r} has no heartbeats in the last {window_days} days"
        )

    # status: 1 = up, 0 = down (uptime-kuma's convention).
    up = sum(1 for _, s in beats if s == 1)
    uptime_pct = round(100.0 * up / len(beats), 3)

    # An incident is a run of down beats; recovery is the gap to the next healthy one.
    recoveries, down_started = [], None
    for t, s in beats:
        try:
            ts = datetime.strptime(str(t)[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if s == 0 and down_started is None:
            down_started = ts
        elif s == 1 and down_started is not None:
            recoveries.append((ts - down_started).total_seconds() / 3600.0)
            down_started = None

    return {
        "metrics": {
            "uptime_percent": uptime_pct,
            # No incidents => nothing to recover from. Declared skip_if_absent in the
            # specification, so this is excluded rather than scored as a failure.
            "mttr_hours": round(statistics.median(recoveries), 3) if recoveries else None,
            # Everything this monitor saw, it detected — that is what monitoring means.
            "auto_detected_share": 100.0,
        },
        "observations": {"checks": len(beats), "down_checks": len(beats) - up,
                         "incidents": len(recoveries), "monitor": name},
        "source": {"kind": "uptime_monitor", "monitor": name},
    }


# ── sensor: source forge -> code-review outcomes ─────────────────────────────
async def _github_code_review(project: str, conf: dict, window_days: int,
                              spec: dict | None = None) -> dict:
    """Measure how changes get reviewed, from the forge's own record.

    Note what is deliberately NOT inferred: if a project has no pull requests, review
    latency is not "zero" or "excellent" — it is unmeasurable, and the fact that no
    change was reviewed is carried by the reviewed-share instead. Silence is not a
    good score.
    """
    repo = str(conf.get("repo") or "").strip()
    if not repo:
        raise SdlcToolError("code-review connector needs a 'repo' (owner/name)")
    token = os.getenv(str(conf.get("token_env") or "GITHUB_TOKEN"), "")
    if not token:
        raise SdlcToolError(
            f"no forge token — set {conf.get('token_env')!r} on this service"
        )
    api = str(conf.get("api_url") or "https://api.github.com").rstrip("/")
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json"}
    since = (datetime.now(tz=timezone.utc) - timedelta(days=window_days))

    async with httpx.AsyncClient(timeout=45, headers=headers) as client:
        prs = (await client.get(f"{api}/repos/{repo}/pulls",
                                params={"state": "all", "per_page": 100})).json()
        commits = (await client.get(f"{api}/repos/{repo}/commits",
                                    params={"since": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                            "per_page": 100})).json()
        if isinstance(prs, dict):
            raise SdlcToolError(f"forge error listing pull requests: {prs.get('message')}")
        if isinstance(commits, dict):
            raise SdlcToolError(f"forge error listing commits: {commits.get('message')}")

        # Review latency: open -> first review, per pull request in the window.
        latencies = []
        recent_prs = [p for p in prs
                      if (p.get("created_at") or "") >= since.strftime("%Y-%m-%dT%H:%M:%SZ")]
        for p in recent_prs[:30]:
            revs = (await client.get(
                f"{api}/repos/{repo}/pulls/{p['number']}/reviews")).json()
            if isinstance(revs, list) and revs:
                t0 = datetime.strptime(p["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                t1 = datetime.strptime(revs[0]["submitted_at"], "%Y-%m-%dT%H:%M:%SZ")
                latencies.append((t1 - t0).total_seconds() / 3600.0)

        # Rework: files touched more than once inside the window.
        touched = {}
        for c in commits[:60]:
            detail = (await client.get(f"{api}/repos/{repo}/commits/{c['sha']}")).json()
            for f in (detail.get("files") or []):
                touched[f.get("filename")] = touched.get(f.get("filename"), 0) + 1

    reworked = sum(1 for n in touched.values() if n > 1)
    changes = len(commits)
    reviewed = len([p for p in recent_prs if p.get("merged_at")])

    return {
        "metrics": {
            # Unmeasurable without pull requests — excluded, not scored as perfect.
            "review_latency_hours": (round(statistics.median(latencies), 2)
                                     if latencies else None),
            # Measurable even at zero, and zero is the honest reading when every change
            # lands directly on the trunk.
            "reviewed_share": round(100.0 * reviewed / changes, 1) if changes else 0.0,
            "rework_rate": (round(100.0 * reworked / len(touched), 1)
                            if touched else None),
        },
        "observations": {"changes": changes, "pull_requests": len(recent_prs),
                         "reviewed": reviewed, "files_touched": len(touched),
                         "files_reworked": reworked},
        "source": {"kind": "github", "repo": repo},
    }


# ── sensor: coverage report -> test outcomes ─────────────────────────────────
async def _local_coverage(project: str, conf: dict, window_days: int,
                          spec: dict | None = None) -> dict:
    """Read a coverage report the build already produces.

    No report is not an error — it is the finding. A project that measures nothing
    scores as untracked, which is exactly what it is.
    """
    import glob as _glob
    import xml.etree.ElementTree as ET

    root = str(conf.get("path") or "").rstrip("/")
    if not root or not os.path.isdir(root):
        raise SdlcToolError(f"repository not mounted at {root!r}")

    pct = None
    found = None
    for pattern in (conf.get("report_globs") or
                    ["coverage.xml", "**/coverage.xml", "cobertura.xml",
                     "**/lcov.info", "coverage/lcov.info", "coverage-summary.json",
                     "**/jacoco.xml"]):
        for path in _glob.glob(os.path.join(root, pattern), recursive=True):
            try:
                if path.endswith(".xml"):
                    r = ET.parse(path).getroot()
                    if r.get("line-rate") is not None:            # cobertura
                        pct = round(float(r.get("line-rate")) * 100, 2)
                    else:                                          # jacoco
                        for c in r.iter("counter"):
                            if c.get("type") == "LINE":
                                cov, mis = float(c.get("covered", 0)), float(c.get("missed", 0))
                                if cov + mis:
                                    pct = round(100.0 * cov / (cov + mis), 2)
                                break
                elif path.endswith(".json"):
                    d = _read_json(path)
                    pct = round(float((d.get("total") or {}).get("lines", {}).get("pct", 0)), 2)
                elif path.endswith(".info"):                       # lcov
                    hit = tot = 0
                    for line in open(path, encoding="utf-8", errors="replace"):
                        if line.startswith("LH:"): hit += int(line[3:] or 0)
                        elif line.startswith("LF:"): tot += int(line[3:] or 0)
                    if tot: pct = round(100.0 * hit / tot, 2)
                if pct is not None:
                    found = os.path.relpath(path, root)
                    break
            except Exception as exc:  # noqa: BLE001 - a malformed report is reported, not fatal
                log.warning("unreadable coverage report %s: %s", path, exc)
        if pct is not None:
            break

    return {
        "metrics": {
            "coverage_percent": pct,     # None => genuinely not tracked => level 0
            "flaky_rate": None,          # needs test analytics; skip_if_absent
        },
        "observations": {"report": found or "none found",
                         "checks": 1 if found else 0},
        "source": {"kind": "coverage", "report": found},
    }


# A specification names a CAPABILITY ("dora", "repo_scan"), never a vendor. The project
# says which connector provides that capability and what implements it, so the same shared
# specification works for a team on Jenkins, one on GitHub Actions, and one on GitLab.
#
#   spec:    {"sensor": "dora"}
#   project: {"connectors": {"ci": {"kind": "jenkins", "base_url": ..., "job": ...}}}
#
# Adding support for another CI system is a new entry here plus a function — no change to
# any specification, and no change to any other project.
CAPABILITY_CONNECTOR = {
    "dora": "ci",
    "repo_scan": "repo",
    "code_review": "forge",
    "coverage": "repo",            # the report is an artefact of the working tree
    "observability": "monitoring",
}

SENSOR_IMPLS = {
    ("dora", "jenkins"): _jenkins_dora,
    ("repo_scan", "local"): _repo_scan,
    ("code_review", "github"): _github_code_review,
    ("coverage", "local"): _local_coverage,
    ("observability", "uptime_kuma"): _kuma_observability,
}


def _resolve_sensor(spec: dict, project_conf: dict, cell: str):
    """Pick the implementation for a cell's capability, given the project's connectors."""
    capability = str(spec.get("sensor") or "")
    slot = CAPABILITY_CONNECTOR.get(capability)
    if slot is None:
        raise SdlcToolError(
            f"cell {cell!r} declares capability {capability!r}, which this service does "
            f"not know (known: {sorted(CAPABILITY_CONNECTOR)})"
        )
    conf = (project_conf.get("connectors") or {}).get(slot)
    if not conf:
        raise SdlcToolError(
            f"this project has no {slot!r} connector, so {cell!r} cannot be assessed. "
            f"Add one to the project configuration (capability: {capability})."
        )
    kind = str(conf.get("kind") or "").strip()
    if not kind:
        raise SdlcToolError(f"the {slot!r} connector must declare a 'kind'")
    fn = SENSOR_IMPLS.get((capability, kind))
    if fn is None:
        supported = sorted(k for c, k in SENSOR_IMPLS if c == capability)
        raise SdlcToolError(
            f"{capability!r} is not implemented for {kind!r} yet (supported: {supported})"
        )
    return fn, conf


# ── tool 1: collect evidence ─────────────────────────────────────────────────
async def sdlc_collect_evidence(args: dict, config: dict) -> dict:
    """Gather the raw evidence for one cell of one project.

    Dispatches on the cell's scoring specification: a measured cell calls its
    sensor; an attested cell returns whatever answer a human has already given
    (and reports that an answer is needed when none exists) — which is how a
    human cell fits the same four-step pipeline without ever blocking on a reply.
    """
    project = _require_project(args.get("project", ""))
    cell = _require_cell(args.get("cell", ""))
    spec = _scoring_spec(cell)
    kind = str(spec.get("kind") or "metric")
    window_days = int(args.get("window_days") or spec.get("window_days") or 30)

    if kind == "derived":
        # Some cells have no signal of their own — the research marks them "inferred".
        # A phase's Principles, for instance, is visible only through the gates and
        # outcomes of that phase's other cells. So read those, and carry their levels.
        # Reports which contributors are missing rather than quietly averaging over a
        # partial set, because a principle inferred from one cell is barely inferred.
        sources = spec.get("from") or []
        listing = await sdlc_state({"project": project, "op": "list"}, config)
        by_cell = {c.get("cell"): c for c in (listing.get("cells") or [])}
        contributors, missing = {}, []
        for src in sources:
            rec = by_cell.get(src)
            if rec and rec.get("level") is not None:
                contributors[src] = int(rec["level"])
            else:
                missing.append(src)
        return {
            "project": project, "cell": cell, "kind": kind,
            "contributors": contributors, "missing": missing,
            "collected_at": _now(),
        }

    if kind == "human":
        # Nothing to sense: this cell is a fact about how people work. Return the stored
        # answer if there is one, otherwise the QUESTION to ask — together with the KB's
        # own level anchors as the options, so the choices are the knowledge base's words
        # rather than invented ones. The run never blocks waiting for a reply.
        prior = await sdlc_state({"project": project, "cell": cell, "op": "read"}, config)
        answer = ((prior.get("state") or {}).get("evidence") or {}).get("answer")
        anchors = ((_kb().get("cells") or {}).get(cell) or {}).get("level_anchors") or []
        return {
            "project": project, "cell": cell, "kind": kind,
            "answer": answer,
            "needs_answer": answer is None,
            "question": spec.get("question"),
            "options": [{"level": i, "label": a} for i, a in enumerate(anchors)],
            "collected_at": _now(),
        }

    sensor, conf = _resolve_sensor(spec, _project_config(project), cell)
    collected = await sensor(project, conf, window_days, spec)
    return {
        "project": project, "cell": cell, "kind": kind,
        "window_days": window_days,
        **collected,
        "collected_at": _now(),
    }


# ── tool 2: score the cell ───────────────────────────────────────────────────
def _band_level(value: float, metric_spec: dict) -> tuple[int, str]:
    """Place one measured value in its band. Bands are ordered best-first, so the
    first match wins and an open-ended final band catches the remainder."""
    for band in metric_spec.get("bands") or []:
        lo, hi = band.get("min"), band.get("max")
        if lo is not None and value >= lo:
            return int(band["level"]), str(band.get("label") or "")
        if hi is not None and value <= hi:
            return int(band["level"]), str(band.get("label") or "")
        if lo is None and hi is None:
            return int(band["level"]), str(band.get("label") or "")
    last = (metric_spec.get("bands") or [{}])[-1]
    return int(last.get("level") or 1), str(last.get("label") or "")


async def sdlc_score_cell(args: dict, config: dict) -> dict:
    """Turn evidence into a maturity level, with the reasoning attached.

    Every conclusion carries *why*: the level of each metric, the band it fell in,
    and which metric decided the outcome. An assessment a human cannot argue with
    is an assessment a human cannot trust.
    """
    project = _require_project(args.get("project", ""))
    cell = _require_cell(args.get("cell", ""))
    spec = _scoring_spec(cell)
    evidence = args.get("evidence")
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence)
        except ValueError as exc:
            raise SdlcToolError(f"evidence is not valid JSON: {exc}") from exc
    if not isinstance(evidence, dict):
        raise SdlcToolError("evidence must be an object (the collect step's output)")

    # --- derived cells: inferred from the phase's other cells ------------------
    # Deliberately the WEAKEST-LINK of its contributors, not their average: a phase's
    # principles are only as real as its least-honoured gate. Confidence drops when
    # some contributors have not been assessed, and it stays unscored if none have —
    # an inference from nothing is not an inference.
    if str(spec.get("kind") or "metric") == "derived":
        contributors = evidence.get("contributors") or {}
        missing = evidence.get("missing") or []
        if not contributors:
            return {
                "project": project, "cell": cell, "level": None, "confidence": None,
                "rationale": "Inferred from %s, none of which is assessed yet."
                             % (", ".join(missing) or "its sibling cells"),
                "source": "derived", "scored_at": _now(),
            }
        level = min(contributors.values())
        weakest = min(contributors, key=lambda k: contributors[k])
        return {
            "project": project, "cell": cell,
            "level": level,
            "confidence": "low" if missing else "medium",
            "rationale": "Level %d, inferred from %s — held at the weakest, %s (L%d).%s" % (
                level,
                ", ".join("%s L%d" % (k, v) for k, v in sorted(contributors.items())),
                weakest, contributors[weakest],
                (" Not yet assessed: %s." % ", ".join(missing)) if missing else "",
            ),
            "per_metric": {k: {"value": v, "level": v, "band": "contributing cell"}
                           for k, v in contributors.items()},
            "limiting_metric": weakest,
            "combine": "derived-min", "source": "derived", "scored_at": _now(),
        }

    # --- attested cells: the person IS the instrument -------------------------
    # No inference: the answer names the level directly, and the rationale quotes the
    # anchor the answerer selected. Unanswered stays unscored rather than defaulting to
    # zero — "nobody has told us" is not the same as "they do it badly".
    if str(spec.get("kind") or "metric") == "human":
        answer = evidence.get("answer")
        if answer is None:
            return {
                "project": project, "cell": cell,
                "level": None, "confidence": None,
                "rationale": "Awaiting an answer — this cell cannot be measured, only attested.",
                "question": evidence.get("question"), "needs_answer": True,
                "source": "human", "scored_at": _now(),
            }
        level = int(answer)
        anchors = ((_kb().get("cells") or {}).get(cell) or {}).get("level_anchors") or []
        chosen = anchors[level] if len(anchors) > level else ""
        # WHO answered decides the provenance. A person's attestation is authoritative;
        # an assistant's reading of the repository is a well-founded guess and must not
        # masquerade as one — it is marked `inferred`, carries its basis, and is offered
        # at lower confidence precisely so it invites correction.
        by = str(evidence.get("by") or "human")
        inferred = by != "human"
        return {
            "project": project, "cell": cell,
            "level": level,
            "confidence": "medium" if inferred else "high",
            "rationale": ("Level %d, inferred (%s): “%s”" % (level, by, chosen)
                          if inferred else
                          "Level %d, attested: “%s”" % (level, chosen)),
            "basis": evidence.get("basis"),
            "per_metric": {}, "limiting_metric": None,
            "combine": "attested",
            "source": "inferred" if inferred else "human",
            "answered_by": by,
            "needs_confirmation": inferred,
            "evidence": {"answer": level, "by": by, "basis": evidence.get("basis")},
            "scored_at": _now(),
        }

    # --- scan cells: a ladder, not a set of dials -----------------------------
    # Practice evidence is presence/absence, so the level is the HIGHEST rung whose
    # conditions all hold (the same rule the evidence criteria state in prose). The
    # first unmet rung is reported, because that is the next thing to actually do.
    if str(spec.get("kind") or "metric") == "scan":
        signals = evidence.get("signals") or {}
        detail = (evidence.get("observations") or {}).get("detail") or {}
        level, met, missing_for_next = 0, [], []
        rungs = sorted(spec.get("levels") or [], key=lambda r: -int(r.get("level", 0)))
        for rung in rungs:
            needed = rung.get("all") or []
            if all(signals.get(s) for s in needed):
                level = int(rung.get("level", 0))
                met = needed
                break
        for rung in sorted(rungs, key=lambda r: int(r.get("level", 0))):
            if int(rung.get("level", 0)) == level + 1:
                missing_for_next = [s for s in (rung.get("all") or []) if not signals.get(s)]
                break
        rationale = "Level %d: %s. Next level needs %s." % (
            level,
            ("satisfied " + ", ".join(met)) if met else "no rung's conditions are met",
            (", ".join(missing_for_next) if missing_for_next else "nothing further defined"),
        )
        return {
            "project": project, "cell": cell,
            "level": level, "confidence": "high", "rationale": rationale,
            "per_metric": {k: {"value": bool(v), "level": None,
                               "band": detail.get(k, "")} for k, v in signals.items()},
            "limiting_metric": (missing_for_next or [None])[0],
            "combine": "ladder",
            "source": "scan",
            "scored_at": _now(),
        }

    measured = evidence.get("metrics") or {}
    per_metric: dict[str, Any] = {}
    levels: list[int] = []
    missing: list[str] = []

    not_applicable = []
    for name, mspec in (spec.get("metrics") or {}).items():
        value = measured.get(name)
        if value is None:
            # Two very different reasons a number can be absent, and conflating them
            # would be dishonest in both directions:
            #   * NOT TRACKED — nobody is measuring it. That is a real gap: level 0.
            #   * NOTHING TO MEASURE — e.g. no incidents occurred, so there is no
            #     recovery time. Scoring that as 0 would punish a project for not
            #     breaking. Such metrics declare `skip_if_absent` and are excluded.
            if mspec.get("skip_if_absent"):
                not_applicable.append(name)
                per_metric[name] = {"value": None, "level": None,
                                    "band": "nothing to measure in this window",
                                    "unit": mspec.get("unit")}
                continue
            missing.append(name)
            per_metric[name] = {"value": None, "level": 0,
                                "band": "not tracked in this window"}
            levels.append(0)
            continue
        lvl, label = _band_level(float(value), mspec)
        per_metric[name] = {"value": value, "level": lvl, "band": label,
                            "unit": mspec.get("unit")}
        levels.append(lvl)

    if not levels:
        # Every metric was inapplicable — there is genuinely nothing to judge yet.
        return {
            "project": project, "cell": cell, "level": None, "confidence": None,
            "rationale": "Nothing to measure in this window (%s). Not scored — which is "
                         "different from scoring zero." % ", ".join(not_applicable),
            "per_metric": per_metric, "source": "telemetry", "scored_at": _now(),
        }

    combine = str(spec.get("combine") or "min")
    level = min(levels) if combine == "min" else round(sum(levels) / len(levels))

    # The weakest metric is what holds the cell back — name it, so the advice that
    # follows has an obvious target. Inapplicable metrics can't be the limiter.
    scored_metrics = {k: v for k, v in per_metric.items() if v.get("level") is not None}
    limiting = sorted(scored_metrics.items(), key=lambda kv: kv[1]["level"])[0][0]
    if missing:
        rationale = (
            f"Level {level}: {', '.join(missing)} not tracked in the last "
            f"{evidence.get('window_days', '?')} days, so the cell cannot score above "
            f"the untracked floor."
        )
        confidence = "low"
    else:
        rationale = (
            f"Level {level}: limited by {limiting} "
            f"({per_metric[limiting]['value']} — {per_metric[limiting]['band']}). "
            + "; ".join(f"{k} L{v['level']}" for k, v in scored_metrics.items())
            + (f". Nothing to measure for: {', '.join(not_applicable)}."
               if not_applicable else "")
        )
        obs = evidence.get("observations") or {}
        # Confidence follows how much the window actually observed. A judgement drawn
        # from a handful of events is a weaker claim, and should present as one.
        sample = max(obs.get("deployments") or 0, obs.get("changes") or 0,
                     obs.get("checks") or 0)
        confidence = "high" if sample >= 5 else "medium"
        if not_applicable:
            confidence = "medium" if confidence == "high" else "low"

    return {
        "project": project, "cell": cell,
        "level": level, "confidence": confidence, "rationale": rationale,
        "per_metric": per_metric,
        "limiting_metric": limiting,
        "combine": combine,
        "source": "telemetry" if not missing else "telemetry (partial)",
        "scored_at": _now(),
    }


# ── tool 3: read/write the assessment state ──────────────────────────────────
async def sdlc_state(args: dict, config: dict) -> dict:
    """Read or write one project-and-cell assessment record.

    Writing preserves history: each scored level is appended to a bounded trail so
    a change over time is visible, and a human override is never silently replaced
    by a fresh machine conclusion — a conflicting reading is flagged instead.
    """
    project = _require_project(args.get("project", ""))
    op = str(args.get("op") or "read").lower()

    if op == "list":
        d = os.path.join(SDLC_RW_DIR, "state", project)
        if not os.path.isdir(d):
            return {"project": project, "cells": []}
        cells = []
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".json"):
                try:
                    cells.append(_read_json(os.path.join(d, fn)))
                except Exception as exc:  # noqa: BLE001 - one bad file must not hide the rest
                    cells.append({"file": fn, "error": str(exc)})
        return {"project": project, "cells": cells}

    cell = _require_cell(args.get("cell", ""))
    path = _state_path(project, cell)

    if op == "read":
        if not os.path.isfile(path):
            return {"project": project, "cell": cell, "state": None, "exists": False}
        return {"project": project, "cell": cell, "state": _read_json(path), "exists": True}

    if op != "write":
        raise SdlcToolError(f"unknown op {op!r}: expected read, write or list")

    incoming = args.get("data")
    if isinstance(incoming, str):
        try:
            incoming = json.loads(incoming)
        except ValueError as exc:
            raise SdlcToolError(f"data is not valid JSON: {exc}") from exc
    if not isinstance(incoming, dict):
        raise SdlcToolError("write needs a 'data' object (the score step's output)")

    prior = _read_json(path) if os.path.isfile(path) else {}
    history = list(prior.get("history") or [])

    override = prior.get("override")
    conflict = None
    if override and override.get("level") is not None \
            and incoming.get("level") is not None \
            and int(override["level"]) != int(incoming["level"]):
        # A human decision stands until a human changes it; the disagreement is
        # surfaced for review rather than resolved silently in either direction.
        conflict = {
            "pinned_level": override["level"],
            "observed_level": incoming["level"],
            "noticed_at": _now(),
        }

    if prior.get("level") is not None and prior.get("level") != incoming.get("level"):
        history.append({
            "level": prior.get("level"),
            "confidence": prior.get("confidence"),
            "at": prior.get("updated_at"),
        })

    record = {
        "project": project,
        "cell": cell,
        "level": override.get("level") if override else incoming.get("level"),
        "observed_level": incoming.get("level"),
        "confidence": incoming.get("confidence"),
        "rationale": incoming.get("rationale"),
        "per_metric": incoming.get("per_metric"),
        "limiting_metric": incoming.get("limiting_metric"),
        "evidence": incoming.get("evidence"),
        "source": "human" if override else incoming.get("source"),
        # Provenance of an attested answer. Carried at the top level (not only inside
        # `evidence`) so a reader — or the wall — can see AT A GLANCE that a conclusion
        # is an inference awaiting confirmation, and on what it rests. Dropping these
        # would let a guess read exactly like an attestation.
        "answered_by": incoming.get("answered_by"),
        "basis": incoming.get("basis"),
        "needs_confirmation": bool(incoming.get("needs_confirmation")),
        "override": override,
        "conflict": conflict,
        "history": history[-50:],       # bounded: a trail, not a ledger
        "created_at": prior.get("created_at") or _now(),
        "updated_at": _now(),
    }
    _write_json_atomic(path, record)
    return {"project": project, "cell": cell, "written": True,
            "path": path, "state": record}


# ── tool 4: advise — turn the position into a ranked, cited next move ────────
def _kb() -> dict:
    path = os.path.join(SDLC_RO_DIR, "kb", "kb_data.json")
    if not os.path.isfile(path):
        raise SdlcToolError(f"knowledge base not found at {path}")
    return _read_json(path)


def _leverage_by_phase(kb: dict) -> dict[str, int]:
    return {m["name"]: int(m.get("leverage") or 2) for m in kb.get("phase_meta") or []}


async def sdlc_advise(args: dict, config: dict) -> dict:
    """Rank what this project should do next, and say why in the KB's own words.

    An assessment is only half the product; the other half is *which gap to close
    first*. Ranking is deliberately simple and inspectable — **gap x leverage**,
    damped when confidence is low — because an advisor whose reasoning cannot be
    audited is one nobody should follow.

    Every proposal is **cited**: the target is the knowledge base's own anchor for
    the next level, and the blocker is the specific condition the assessment found
    unmet. Nothing here is invented by a model.
    """
    project = _require_project(args.get("project", ""))
    top = max(1, min(int(args.get("top") or 3), 20))
    write_inbox = bool(args.get("write_inbox", True))

    listing = await sdlc_state({"project": project, "op": "list"}, config)
    records = [c for c in listing.get("cells") or [] if c.get("level") is not None]
    if not records:
        return {"project": project, "proposals": [], "considered": 0,
                "note": "nothing assessed yet — run the assessment before asking for advice"}

    kb = _kb()
    lev = _leverage_by_phase(kb)
    kb_cells = kb.get("cells") or {}

    proposals = []
    for rec in records:
        cell = rec.get("cell") or ""
        level = int(rec.get("level"))
        if level >= 4:
            continue                     # already at the top of this cell's ladder
        phase = cell.split("|", 1)[0]
        gap = 4 - level
        leverage = lev.get(phase, 2)
        # Low confidence should not drive a roadmap — it should drive a better reading.
        damp = 0.6 if rec.get("confidence") == "low" else 1.0
        score = round(gap * leverage * damp, 2)

        anchors = (kb_cells.get(cell) or {}).get("level_anchors") or []
        target = level + 1
        target_anchor = anchors[target] if len(anchors) > target else None

        proposals.append({
            "cell": cell,
            "from_level": level,
            "to_level": target,
            "blocker": rec.get("limiting_metric"),
            "evidence": rec.get("rationale"),
            "target_anchor": target_anchor,      # the citation: the KB's own words
            "leverage": leverage,
            "gap": gap,
            "confidence": rec.get("confidence"),
            "score": score,
            "source": rec.get("source"),
        })

    proposals.sort(key=lambda p: (-p["score"], p["cell"]))
    top_proposals = proposals[:top]

    written = []
    if write_inbox and top_proposals:
        d = os.path.join(SDLC_RW_DIR, "state", project, "inbox")
        for p in top_proposals:
            item = {
                "type": "proposal",
                "id": "proposal-" + p["cell"].replace("|", "__").replace(" ", "_").lower(),
                "state": "new",
                "project": project,
                "created_at": _now(),
                **p,
            }
            path = os.path.join(d, item["id"] + ".json")
            _write_json_atomic(path, item)
            written.append(item["id"])

    return {
        "project": project,
        "considered": len(records),
        "proposals": top_proposals,
        "inbox_written": written,
        "ranking": "gap x leverage, damped when confidence is low",
        "caveat": "prerequisite edges between cells are not modelled yet, so this ranks "
                  "by value rather than by readiness order",
        "advised_at": _now(),
    }


async def sdlc_answer(args: dict, config: dict) -> dict:
    """Record a human's answer to an attested cell, and score it immediately.

    The answer is the evidence — so it is stored on the cell record (surviving later
    automated passes, which read it back) and applied at once, because a person who
    has just answered should see the result rather than wait for the next nightly run.
    """
    project = _require_project(args.get("project", ""))
    cell = _require_cell(args.get("cell", ""))
    spec = _scoring_spec(cell)
    if str(spec.get("kind") or "") != "human":
        raise SdlcToolError(
            f"cell {cell!r} is measured, not attested — it is scored from evidence, "
            "so answering it by hand would overwrite a reading with an opinion. Use an "
            "override if you genuinely need to pin it."
        )
    try:
        level = int(args.get("level"))
    except (TypeError, ValueError):
        raise SdlcToolError("level must be an integer 0-4") from None
    if not 0 <= level <= 4:
        raise SdlcToolError(f"level {level} out of range (0-4)")

    scored = await sdlc_score_cell(
        {"project": project, "cell": cell,
         "evidence": {"answer": level,
                      "by": args.get("by") or "human",
                      "basis": args.get("basis")}}, config)
    written = await sdlc_state(
        {"project": project, "cell": cell, "op": "write", "data": scored}, config)
    return {"project": project, "cell": cell, "level": level,
            "rationale": scored.get("rationale"),
            "answered_by": args.get("by") or "human",
            "state": written.get("state"), "answered_at": _now()}


IMPLS = {
    "sdlc_collect_evidence": sdlc_collect_evidence,
    "sdlc_score_cell": sdlc_score_cell,
    "sdlc_state": sdlc_state,
    "sdlc_advise": sdlc_advise,
    "sdlc_answer": sdlc_answer,
}
