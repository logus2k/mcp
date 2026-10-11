"""The Console page (console_specification.md section 5): one self-contained HTML page,
inline CSS and JS, no build step. Served by admin.py at /admin. Every URL in it is
relative, so it works at /admin and behind the domain proxy at /mcp-console/admin.
"""

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>MCP Server</title>
<link rel="icon" href="data:,">
<style>
/* Inter, self-hosted as Cortex does (static/css/fonts.css): the Banco CTT family, Regular and Bold */
@font-face { font-family: 'Inter'; src: url('admin/fonts/InterVariable.ttf') format('truetype'); font-weight: 100 900; font-style: normal; font-display: swap; }
/* Layout: a 56px bar, a 200px side menu (a top strip on phones), a content column, and a 520px detail drawer
   (a full-width sheet on phones). Tokens: the Banco CTT set Cortex and Slides use (tokens.css). */
:root {
  --font-sans: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
  --font-mono: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px; --space-6: 24px; --space-8: 32px;
  --radius-sm: 4px; --radius-md: 6px; --radius-lg: 8px; --radius-pill: 999px;
  --menu-width: 200px; --menu-width-collapsed: 72px; --topbar-height: 72px; --drawer-width: 560px;
  --radius-xl: 10px; --fs-caption: 12px; --lh-caption: 16px; --ls-caption: .4px; --fs-subtitle: 14px; --lh-subtitle: 16px; --ls-subtitle: .1px;
  --fs-p2: 14px; --lh-p2: 20px; --ls-p2: .25px; --fs-navbar: 10px; --lh-navbar: 16px; --ls-navbar: .33px; --fs-badge: 12px; --ls-badge: .29px;
  --icon-chevron-down: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  --primary: #E00024; --primary-active: #C4001F; --text-on-primary: #FFFFFF;
  --success: #00BFB4; --alert: #FFC800; --offline: #A681AB;
  --surface-page: #F7F9FC; --surface: #FFFFFF; --surface-bar: #F1F4F8;
  --surface-field: #F1F4F8; --surface-hover: #F7F9FC; --surface-active: #F1F4F8; --surface-inverse: #333333;
  --divider: #E4E9F2; --control-border: #C5CEE0; --text-secondary: #8F9BB3; --shadow: 0 5px 6px 0 rgba(197,206,224,.5); --shadow-float: 0 0 6px 0 rgba(197,206,224,.5);
  --text: #000000; --text-title: #333333; --text-weak: #666666; --text-section: #999999; --text-disabled: #CCCCCC;
  --brand-text: #E00024; --link: #00897F; --error-text: #C8102E; --alert-text: #996F00;
  --container-primary: #FBDFE3; --container-info: #E3F0F0; --container-alert: #FFF1BF; --container-offline: #F1EAF1;
  --chip-fluid: #E4E9F2; --overlay: rgba(51,51,51,.6);
  --shadow-window: 0 2px 6px 0 rgba(110,123,147,.25), 0 12px 32px 0 rgba(110,123,147,.3);
  --ok: #00897F; --ok-bg: #E3F0F0; --warn: #996F00; --warn-bg: #FFF1BF; --bad: #C8102E; --bad-bg: #FBDFE3;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --surface-page: #12151B; --surface: #1A1E26; --surface-bar: #171B22;
    --surface-field: #242A35; --surface-hover: #232833; --surface-active: #262B35; --surface-inverse: #F1F4F8;
    --divider: #2C3340; --control-border: #8F9BB3; --text-secondary: #A9B4C9; --shadow: none; --shadow-float: 0 4px 16px 0 rgba(0,0,0,.6);
    --text: #F1F4F8; --text-title: #F1F4F8; --text-weak: #C5CEE0; --text-section: #8F9BB3; --text-disabled: #5C6578;
    --brand-text: #EC677D; --link: #66D8D3; --error-text: #FFA3B0; --alert-text: #FFC800;
    --container-primary: #4A1520; --container-info: #0F3B39; --container-alert: #3D3200; --container-offline: #35213A;
    --chip-fluid: #2C3340; --overlay: rgba(0,0,0,.6);
    --shadow-window: 0 4px 16px 0 rgba(0,0,0,.6), 0 16px 40px 0 rgba(0,0,0,.5);
    --ok: #66D8D3; --ok-bg: #0F3B39; --warn: #FFC800; --warn-bg: #3D3200; --bad: #FFA3B0; --bad-bg: #4A1520;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --surface-page: #12151B; --surface: #1A1E26; --surface-bar: #171B22;
  --surface-field: #242A35; --surface-hover: #232833; --surface-active: #262B35; --surface-inverse: #F1F4F8;
  --divider: #2C3340; --control-border: #8F9BB3; --text-secondary: #A9B4C9; --shadow: none; --shadow-float: 0 4px 16px 0 rgba(0,0,0,.6);
  --text: #F1F4F8; --text-title: #F1F4F8; --text-weak: #C5CEE0; --text-section: #8F9BB3; --text-disabled: #5C6578;
  --brand-text: #EC677D; --link: #66D8D3; --error-text: #FFA3B0; --alert-text: #FFC800;
  --container-primary: #4A1520; --container-info: #0F3B39; --container-alert: #3D3200; --container-offline: #35213A;
  --chip-fluid: #2C3340; --overlay: rgba(0,0,0,.6);
  --shadow-window: 0 4px 16px 0 rgba(0,0,0,.6), 0 16px 40px 0 rgba(0,0,0,.5);
  --ok: #66D8D3; --ok-bg: #0F3B39; --warn: #FFC800; --warn-bg: #3D3200; --bad: #FFA3B0; --bad-bg: #4A1520;
  color-scheme: dark;
}
* { box-sizing: border-box; }
[hidden] { display: none !important; }
html, body { height: 100%; }
body { margin: 0; font: 400 14px/20px var(--font-sans); letter-spacing: .25px; color: var(--text); background: var(--surface-page); }
a { color: var(--link); }
button, input, select, textarea { font: inherit; color: inherit; }
button { cursor: pointer; }
:focus-visible { outline: 2px solid var(--link); outline-offset: 2px; }
code, .mono { font-family: var(--font-mono); font-size: 12.5px; }
h1, h2, h3 { margin: 0; color: var(--text-title); text-wrap: balance; }
h2 { font-size: 20px; line-height: 24px; font-weight: 700; }
h3 { font-size: 14px; line-height: 20px; font-weight: 700; }
.eyebrow { font-size: 12px; line-height: 16px; letter-spacing: .6px; text-transform: uppercase; color: var(--text-section); font-weight: 500; }
.muted { color: var(--text-weak); }
.num { font-variant-numeric: tabular-nums; }
.health { display: flex; gap: var(--space-3); flex-wrap: wrap; font-size: 12px; color: var(--text-weak); }
.health span { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-disabled); display: inline-block; flex: none; }
.dot.ok { background: var(--success); } .dot.warn { background: var(--alert); } .dot.bad { background: var(--primary); }
.field { height: 36px; padding: 0 var(--space-3); border: 1px solid var(--control-border); border-radius: var(--radius-md); background: var(--surface-field); min-width: 0; }
.field:focus { border-color: var(--text-title); }
.btn { height: 36px; padding: 0 var(--space-3); border-radius: var(--radius-md); border: 1px solid var(--control-border); background: var(--surface); color: var(--text-title); font-weight: 500; white-space: nowrap; display: inline-flex; align-items: center; gap: 6px; text-decoration: none; }
.btn:hover { background: var(--surface-hover); }
.btn.primary { background: var(--primary); border-color: var(--primary); color: var(--text-on-primary); }
.btn.primary:hover { background: var(--primary-active); }
.btn.sm { height: 28px; padding: 0 10px; font-size: 12px; }
.btn.danger { color: var(--error-text); }
.btn:disabled { opacity: .5; cursor: default; }
.content { padding: var(--space-6) var(--space-6) var(--space-8); min-width: 0; }
.content > section { display: none; }
.content > section.active { display: block; }
.view-head { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--space-4); flex-wrap: wrap; margin-bottom: var(--space-4); }
.view-head p { margin: 4px 0 0; color: var(--text-weak); max-width: 64ch; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: var(--space-3); margin-bottom: var(--space-6); }
.tile { background: var(--surface); border: 1px solid var(--divider); border-radius: var(--radius-lg); padding: var(--space-4); display: flex; flex-direction: column; gap: 4px; text-decoration: none; color: inherit; }
.tile .big { font-size: 24px; line-height: 28px; font-weight: 700; color: var(--text-title); }
.tile .sub { font-size: 12px; color: var(--text-weak); }
.two { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: var(--space-4); align-items: start; }
.card { background: var(--surface); border: 1px solid var(--divider); border-radius: var(--radius-lg); padding: var(--space-4); min-width: 0; }
.card h3 { margin-bottom: var(--space-3); }
.card .tablewrap td, .card .tablewrap th { padding: 8px 8px; }
td.time { white-space: nowrap; }
#recent td { max-width: 132px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.attn { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.attn li { display: grid; grid-template-columns: 4px 1fr auto; gap: var(--space-3); align-items: start; padding: 10px 0; border-top: 1px solid var(--divider); }
.attn li:first-child { border-top: 0; padding-top: 0; }
.attn .stripe { width: 4px; border-radius: 2px; align-self: stretch; background: var(--alert); }
.attn .stripe.bad { background: var(--primary); } .attn .stripe.info { background: var(--success); }
.attn .why { font-size: 12px; color: var(--text-weak); }
.toolbar { display: flex; gap: var(--space-2); align-items: center; flex-wrap: wrap; margin-bottom: var(--space-3); }
.toolbar .field { flex: 1 1 220px; }
.chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip { height: 28px; padding: 0 10px; border-radius: var(--radius-pill); border: 1px solid var(--divider); background: var(--surface); font-size: 12px; color: var(--text-weak); display: inline-flex; align-items: center; gap: 6px; }
.chip[aria-pressed="true"] { background: var(--container-primary); border-color: transparent; color: var(--brand-text); font-weight: 500; }
.pill { display: inline-flex; align-items: center; height: 20px; padding: 0 8px; border-radius: var(--radius-pill); font-size: 12px; font-weight: 500; white-space: nowrap; }
.pill.read { background: var(--ok-bg); color: var(--ok); } .pill.write { background: var(--bad-bg); color: var(--bad); }
.pill.server { background: var(--chip-fluid); color: var(--text-weak); } .pill.client { background: var(--container-offline); color: var(--offline); }
.pill.app { background: var(--chip-fluid); color: var(--text-weak); font-family: var(--font-mono); font-weight: 400; }
.pill.ok { background: var(--ok-bg); color: var(--ok); } .pill.err { background: var(--bad-bg); color: var(--bad); } .pill.warn { background: var(--warn-bg); color: var(--warn); }
.pill.tag { background: var(--container-info); color: var(--ok); }
.tablewrap { background: var(--surface); border: 1px solid var(--divider); border-radius: var(--radius-lg); overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; font-size: 12px; letter-spacing: .4px; text-transform: uppercase; color: var(--text-section); font-weight: 500; padding: 10px 12px; border-bottom: 1px solid var(--divider); white-space: nowrap; }
td { padding: 10px 12px; border-bottom: 1px solid var(--divider); vertical-align: middle; }
tr:last-child td { border-bottom: 0; }
tbody tr.row { cursor: pointer; }
tbody tr.row:hover td { background: var(--surface-hover); }
tbody tr[aria-selected="true"] td { background: var(--surface-active); box-shadow: inset 3px 0 0 var(--primary); }
td.name { font-weight: 500; color: var(--text-title); white-space: nowrap; }
td .desc { display: block; font-size: 12px; color: var(--text-weak); max-width: 52ch; white-space: normal; }
.apps { display: flex; gap: 4px; flex-wrap: wrap; }
.toggle { width: 34px; height: 20px; border-radius: var(--radius-pill); background: var(--control-border); border: 0; position: relative; flex: none; }
.toggle::after { content: ""; position: absolute; top: 2px; left: 2px; width: 16px; height: 16px; border-radius: 50%; background: #fff; transition: left 150ms; }
.toggle[aria-checked="true"] { background: var(--success); } .toggle[aria-checked="true"]::after { left: 16px; }
.never { color: var(--alert-text); font-size: 12px; }
.scrim { position: fixed; inset: 0; background: var(--overlay); z-index: 30; display: none; }
@media (min-width: 861px) { .scrim { display: none !important; } }
.drawer { position: fixed; top: 0; right: 0; bottom: 0; width: min(var(--drawer-width), 100vw); background: var(--surface); box-shadow: var(--shadow-window); z-index: 40; transform: translateX(104%); transition: transform 200ms cubic-bezier(.2,0,0,1); display: flex; flex-direction: column; padding-top: env(safe-area-inset-top, 0px); }
.drawer.open { transform: none; }
@media (prefers-reduced-motion: reduce) { .drawer { transition: none; } .toggle::after { transition: none; } }
.drawer-head { padding: var(--space-4) var(--space-4) 0; border-bottom: 1px solid var(--divider); }
.drawer-head .title { display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap; }
.drawer-head h2 { font-family: var(--font-mono); font-size: 18px; overflow-wrap: anywhere; }
.drawer-head .close { margin-left: auto; }
.tabs { display: flex; gap: 2px; overflow-x: auto; margin-top: var(--space-3); }
.tabs button { background: none; border: 0; padding: 8px 10px; color: var(--text-weak); font-weight: 500; border-bottom: 2px solid transparent; white-space: nowrap; }
.tabs button[aria-selected="true"] { color: var(--brand-text); border-bottom-color: var(--primary); }
.drawer-body { padding: var(--space-4); overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: var(--space-4); }
.drawer-body > div[role="tabpanel"] { display: none; flex-direction: column; gap: var(--space-4); }
.drawer-body > div[role="tabpanel"].active { display: flex; }
.kv { display: grid; grid-template-columns: 120px 1fr; gap: 6px var(--space-3); font-size: 13px; margin: 0; }
.kv dt { color: var(--text-section); } .kv dd { margin: 0; min-width: 0; overflow-wrap: anywhere; }
.form { display: flex; flex-direction: column; gap: var(--space-3); }
.form label { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--text-weak); }
.form .field, .form textarea, .form select { width: 100%; }
.form textarea { min-height: 96px; padding: var(--space-2) var(--space-3); border: 1px solid var(--control-border); border-radius: var(--radius-md); background: var(--surface-field); resize: vertical; font-family: var(--font-mono); font-size: 12.5px; }
.form textarea.prose { font-family: var(--font-sans); font-size: 14px; }
.form .row { display: flex; gap: var(--space-3); flex-wrap: wrap; } .form .row > label { flex: 1 1 140px; }
.hint { font-size: 12px; color: var(--text-section); }
.err { font-size: 12px; color: var(--error-text); }
pre { margin: 0; padding: var(--space-3); background: var(--surface-field); border-radius: var(--radius-md); overflow-x: auto; font-family: var(--font-mono); font-size: 12px; line-height: 18px; color: var(--text); white-space: pre-wrap; overflow-wrap: anywhere; }
.snip { display: flex; flex-direction: column; gap: 6px; }
.snip .label { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); }
.result { border: 1px solid var(--divider); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: 6px; }
.result .meta { display: flex; gap: var(--space-3); font-size: 12px; color: var(--text-weak); flex-wrap: wrap; }
.confirm { border-left: 4px solid var(--primary); background: var(--container-primary); color: var(--text); padding: var(--space-3); border-radius: var(--radius-md); font-size: 13px; display: flex; flex-direction: column; gap: var(--space-2); }
.confirm label { display: flex; gap: 8px; align-items: center; }
.diff { font-family: var(--font-mono); font-size: 12px; line-height: 18px; border: 1px solid var(--divider); border-radius: var(--radius-md); overflow: auto; max-height: 360px; }
.diff div { padding: 1px 10px; white-space: pre-wrap; overflow-wrap: anywhere; }
.diff .del { background: var(--bad-bg); color: var(--bad); } .diff .add { background: var(--ok-bg); color: var(--ok); }
.versions { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.versions li { display: flex; gap: var(--space-3); align-items: center; padding: 8px 0; border-top: 1px solid var(--divider); font-size: 13px; flex-wrap: wrap; }
.versions li:first-child { border-top: 0; }
.versions .btn { margin-left: auto; }
.proptable td, .proptable th { padding: 6px 10px; font-size: 12.5px; }
.appcards { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: var(--space-4); }
.appcard { background: var(--surface); border: 1px solid var(--divider); border-radius: var(--radius-lg); padding: var(--space-4); display: flex; flex-direction: column; gap: var(--space-3); min-width: 0; }
.appcard .head { display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap; }
.appcard .head h3 { font-family: var(--font-mono); font-size: 15px; }
.appcard .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-2); }
.appcard .stats div { background: var(--surface-field); border-radius: var(--radius-md); padding: 8px 10px; }
.appcard .stats b { display: block; font-size: 18px; line-height: 22px; color: var(--text-title); }
.appcard .stats span { font-size: 12px; color: var(--text-weak); }
.keys { display: flex; flex-direction: column; gap: 6px; font-size: 13px; }
.keys div { display: flex; gap: var(--space-2); align-items: center; flex-wrap: wrap; }
.keys .btn { margin-left: auto; }
.newkey { background: var(--container-alert); border-radius: var(--radius-md); padding: var(--space-3); display: flex; flex-direction: column; gap: 6px; font-size: 13px; }
.editor { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.preview { border: 1px solid var(--divider); border-radius: var(--radius-md); padding: var(--space-3); font-size: 13px; line-height: 20px; min-width: 0; white-space: pre-wrap; overflow-wrap: anywhere; }
.summary { display: flex; gap: var(--space-6); flex-wrap: wrap; margin-bottom: var(--space-3); font-size: 13px; color: var(--text-weak); }
.summary b { color: var(--text-title); font-size: 16px; margin-right: 4px; }
.impls td:first-child { font-family: var(--font-mono); font-weight: 500; }
.empty { padding: var(--space-6); text-align: center; color: var(--text-weak); }
.toast { position: fixed; left: 50%; bottom: calc(24px + env(safe-area-inset-bottom, 0px)); transform: translateX(-50%); background: var(--surface-inverse); color: var(--surface); padding: 10px 16px; border-radius: var(--radius-md); font-size: 13px; z-index: 60; box-shadow: var(--shadow-window); opacity: 0; pointer-events: none; transition: opacity 150ms; max-width: 90vw; }
.toast.show { opacity: 1; }
@media (max-width: 600px) {
  #tooltable th:nth-child(n+4):not(:last-child), #tooltable td:nth-child(n+4):not(:last-child) { display: none; }
  #tooltable td .desc { display: none; }
  #skilltable th:nth-child(n+3):not(:last-child), #skilltable td:nth-child(n+3):not(:last-child) { display: none; }
  .editor { grid-template-columns: 1fr; }
}
@media (max-width: 860px) {
  .content { padding: var(--space-4); }
  .kv { grid-template-columns: 1fr; }
}

/* ── the shell, as Cortex and Slides (their layout.css, vendor-theme.css, style.css): the side menu, the top bar with
   the profile at the right, the content, the status bar ── */
#app { display: grid; height: 100%; grid-template-columns: var(--menu-width) minmax(0, 1fr); grid-template-rows: var(--topbar-height) minmax(0, 1fr) auto; }
#app.menu-collapsed { grid-template-columns: var(--menu-width-collapsed) minmax(0, 1fr); }
#icon-bar { grid-column: 1; grid-row: 1 / 3; min-height: 0; overflow: visible; position: relative; z-index: 21; display: flex; flex-direction: column; align-items: stretch; user-select: none;
  padding: 26px var(--space-4) var(--space-4); background: var(--surface); border-right: 1px solid var(--divider); }
#app > header { grid-column: 2; grid-row: 1; display: flex; align-items: center; gap: var(--space-2); min-width: 0; padding: var(--space-3) var(--space-6); background: var(--surface-bar); }
#below-bar { grid-column: 2; grid-row: 2; min-width: 0; min-height: 0; overflow: auto; }
#status-bar { grid-column: 1 / -1; grid-row: 3; }
h1.brand { display: none; }
.logo-dark { display: none; }
:root[data-theme="dark"] .logo-light { display: none; } :root[data-theme="dark"] .logo-dark { display: block; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) .logo-light { display: none; } :root:not([data-theme="light"]) .logo-dark { display: block; } }
/* the side menu (Figma): the wordmark, then sections 16px apart, each a Caption title with its items 8px below;
   items 48px, 10px radius, padding 7 x 11px, a 24px icon, 12px gap, a Paragraph 2 label; the view on screen has a red
   icon and label and no background. The collapse button: a 32px circle on the menu's right edge, 56px from the top. */
.menu-logo { margin: 0 11px 26px; }
.menu-logo img { width: 83px; height: 18px; }
.menu-logo .logo-light { display: block; }
.menu-logo .rail-logo { display: none; }
.menu-logo .rail-logo img { width: 40px; height: 40px; }
/* the application's name under the wordmark, as Cortex's "C O R T E X": thin capitals spread to exactly the logo's
   83px (SVG textLength does the spacing), in --text-weak */
.menu-logo .product { display: block; width: 83px; height: 12px; margin-top: var(--space-2); color: var(--text-weak); }
.menu-logo .product svg { display: block; width: 83px; height: 12px; overflow: visible; }
.menu-logo .product text { font: 400 10px var(--font-sans); fill: currentColor; }
.menu-section { margin: var(--space-4) 0 var(--space-2); color: var(--text-section); white-space: nowrap; overflow: hidden; font: 400 var(--fs-caption)/var(--lh-caption) var(--font-sans); letter-spacing: var(--ls-caption); }
.icon-bar-group { display: flex; flex-direction: column; align-items: stretch; width: 100%; }
.icon-bar-group > .menu-section:first-child { margin-top: 0; }
.icon-bar-spacer { flex: 1; }
.icon-bar-btn { display: flex; align-items: center; justify-content: flex-start; gap: var(--space-3); width: 100%; height: 48px; padding: 7px 11px; border: 0; border-radius: var(--radius-xl); background: transparent; color: var(--text); text-align: left; cursor: pointer; font: 400 var(--fs-p2)/var(--lh-p2) var(--font-sans); letter-spacing: var(--ls-p2); position: relative; }
.icon-bar-btn:hover { background: var(--surface-hover); }
.icon-bar-btn .menu-icon { flex: none; width: 24px; height: 24px; }
.icon-bar-label { flex: 1 1 auto; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.icon-bar-btn-active { color: var(--brand-text); }
.icon-bar-btn-active .menu-icon { color: var(--primary); }
.menu-collapse { position: absolute; right: -16px; top: 56px; z-index: 22; width: 32px; height: 32px; padding: 0; border-radius: 50%; display: grid; place-items: center; background: var(--surface); border: 1px solid var(--divider); box-shadow: var(--shadow); color: var(--text); cursor: pointer; }
.menu-collapse:hover { background: var(--surface-hover); }
.menu-collapse::before { content: ''; width: 16px; height: 16px; background: currentColor; transform: rotate(180deg); -webkit-mask: var(--icon-chevron-down) center / 16px 16px no-repeat; mask: var(--icon-chevron-down) center / 16px 16px no-repeat; transform: rotate(90deg); }
.menu-collapse[aria-expanded="false"]::before { transform: rotate(-90deg); }
#app.menu-collapsed #icon-bar { padding-left: var(--space-3); padding-right: var(--space-3); }
#app.menu-collapsed .icon-bar-btn { justify-content: center; padding: 7px 0; }
#app.menu-collapsed .icon-bar-label { display: none; }
#app.menu-collapsed .menu-section { height: 1px; margin: var(--space-3) var(--space-1); background: var(--divider); font-size: 0; }
#app.menu-collapsed .icon-bar-group > .menu-section:first-child { display: none; }
#app.menu-collapsed .menu-logo { margin: 0 0 26px; text-align: center; }
#app.menu-collapsed .menu-logo > img, #app.menu-collapsed .menu-logo .product { display: none !important; }
#app.menu-collapsed .menu-logo .rail-logo { display: flex; justify-content: center; margin-top: calc((18px - 40px) / 2); }
/* the top bar: the health at the left (where Cortex has its menus); the profile at the right */
/* the top bar's menus (Cortex's menubar): Subtitle 2 buttons 40px tall, 4px radius, open in --brand-text; dropdowns
   --surface-raised, 10px radius, items Paragraph 2, ticked items --brand-text bold, notes in --text-secondary */
#menubar { position: static; height: 40px; flex: 1 1 auto; min-width: 0; display: flex; align-items: center; gap: 4px; user-select: none; color: var(--text); font: 700 var(--fs-subtitle)/var(--lh-subtitle) var(--font-sans); letter-spacing: var(--ls-subtitle); }
.menu { position: relative; }
.menu-btn { display: flex; align-items: center; height: 40px; padding: 0 12px; border-radius: var(--radius-sm); white-space: nowrap; cursor: pointer; }
.menu-btn:hover, .menu.open > .menu-btn { background: var(--surface-hover); }
.menu.open > .menu-btn { background: var(--surface); color: var(--brand-text); }
.dropdown { display: none; position: absolute; top: calc(100% + 8px); left: 0; z-index: 5000; min-width: 240px; padding: 8px 0; background: var(--surface); color: var(--text); border: 1px solid var(--divider); border-radius: var(--radius-xl); box-shadow: var(--shadow-window); font: 400 var(--fs-p2)/var(--lh-p2) var(--font-sans); letter-spacing: var(--ls-p2); }
.menu.open > .dropdown { display: block; }
.menu-item { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 8px 16px; cursor: pointer; white-space: nowrap; }
.menu-item:hover { background: var(--surface-hover); }
.menu-item.disabled { color: var(--text-disabled); pointer-events: none; }
.menu-item.ticked { color: var(--brand-text); font-weight: 700; }
.menu-item > span:first-child { display: inline-flex; align-items: center; }
.check { display: inline-flex; width: 20px; align-items: center; }
.check .dot { margin: 0; }
.menu-note { color: var(--text-secondary); }
.menu-note::before { content: "("; } .menu-note::after { content: ")"; }
.menubar-sep { height: 1px; margin: 8px 0; background: var(--divider); }
.shortcut { color: var(--text-secondary); font: 400 var(--fs-caption)/var(--lh-caption) var(--font-sans); letter-spacing: var(--ls-caption); }
#status-bar .focus-name { line-height: 28px; }
/* Help: the manual's contents beside its page (Cortex shows them in the Outline panel); the sheet's Markdown rules
   are Cortex's (style.css .markdown) */
.help-frame { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: var(--space-8); align-items: start; }
.help-contents { position: sticky; top: 0; max-height: calc(100vh - var(--topbar-height) - 28px - var(--space-8)); overflow-y: auto; font-size: 13px; padding-right: var(--space-2); }
.help-contents .eyebrow { margin: var(--space-4) 0 var(--space-1); }
.help-contents .eyebrow:first-child { margin-top: 0; }
.help-contents a { display: block; padding: 5px 10px; border-radius: var(--radius-md); color: var(--text); text-decoration: none; overflow-wrap: anywhere; }
.help-contents a:hover { background: var(--surface-hover); }
.help-contents a.current { color: var(--brand-text); font-weight: 700; }
.help-sheet { min-width: 0; max-width: 80ch; }
.help-bar { display: flex; align-items: center; gap: var(--space-3); min-height: 28px; margin-bottom: var(--space-3); }
.markdown { font-size: 14px; line-height: 20px; color: var(--text); }
.markdown h1 { margin: 0 0 var(--space-3); font-size: 24px; line-height: 28.8px; font-weight: 700; color: var(--text-title); }
.markdown h2 { margin: var(--space-6) 0 var(--space-2); font-size: 16px; line-height: 24px; font-weight: 700; color: var(--text); }
.markdown h3 { margin: var(--space-4) 0 var(--space-1); font-size: 14px; font-weight: 700; }
.markdown p, .markdown li { line-height: 1.55; }
.markdown p { margin: 0 0 var(--space-3); }
.markdown ul, .markdown ol { padding-left: 22px; margin: 0 0 var(--space-3); }
.markdown table { border-collapse: collapse; margin: var(--space-2) 0 var(--space-4); display: block; max-width: 100%; overflow-x: auto; }
.markdown th, .markdown td { border-bottom: 1px solid var(--divider); padding: var(--space-2) var(--space-3); text-align: left; vertical-align: top; }
.markdown th { color: var(--text-section); font-weight: 500; }
.markdown code { background: var(--surface-field); padding: 1px 4px; border-radius: var(--radius-sm); font-family: var(--font-mono); font-size: var(--fs-caption); }
.markdown pre { margin: 0 0 var(--space-3); }
.markdown pre code { background: none; padding: 0; font-size: 12px; }
.markdown blockquote { border-left: 3px solid var(--divider); margin: var(--space-2) 0; padding-left: var(--space-3); color: var(--text-weak); }
.markdown img { display: block; max-width: 100%; height: auto; margin: var(--space-3) 0; border: 1px solid var(--divider); border-radius: var(--radius-md); }
.markdown a { color: var(--link); }
.manual-next { margin: var(--space-8) 0 0; padding-top: var(--space-4); border-top: 1px solid var(--divider); display: flex; flex-direction: column; gap: 6px; }
.manual-next-link { border: 0; background: none; padding: 0; text-align: left; color: var(--text); cursor: pointer; font: inherit; }
.manual-next-label { color: var(--text-section); }
.manual-next-title { color: var(--link); font-weight: 700; }
.manual-next-end { color: var(--text-section); }
.menu-toggle { display: none; }
@media (max-width: 1100px) { .help-frame { grid-template-columns: 1fr; } .help-contents { position: static; max-height: none; border-bottom: 1px solid var(--divider); padding-bottom: var(--space-3); } }
/* phone: the menus in a drawer under the header */
@media (max-width: 833px) {
  .menu-toggle { display: grid; place-items: center; flex: none; width: 44px; height: 44px; padding: 0; border: 0; border-radius: 50%; background: transparent; color: var(--text); cursor: pointer; }
  header.menus-open #menubar { display: flex; flex-direction: column; align-items: stretch; gap: 0; position: fixed; top: 56px; left: 0; right: 0; bottom: 64px; height: auto; z-index: 30; padding: var(--space-2); overflow-y: auto; background: var(--surface); }
  header.menus-open .menu-btn { height: 44px; }
  header.menus-open .dropdown { position: static; min-width: 0; box-shadow: none; border: 0; border-radius: 0; padding: 0 0 8px 16px; }
}
#status-bar button.status-right { border: 0; background: none; font: inherit; letter-spacing: inherit; cursor: pointer; }
#status-bar .status-right .dot { margin-right: 6px; }
#token { margin-left: auto; width: 220px; }
/* the signed-in user widget (Cortex's identity.js and style.css) */
.identity { position: relative; flex: 0 0 auto; display: flex; align-items: center; margin-left: auto; }
#token + .identity { margin-left: 0; }
.identity-btn { display: flex; align-items: center; min-height: 0; height: 48px; gap: var(--space-2); padding: 0 var(--space-2); border: 0; border-radius: var(--radius-sm); background: transparent; color: var(--text); cursor: pointer; }
.identity-btn:hover { background: var(--surface-hover); }
.identity-face { position: relative; flex: none; display: grid; place-items: center; width: 24px; height: 24px; border-radius: 50%; overflow: hidden; background: var(--container-primary); color: var(--text); }
.identity-initials { font: 700 10px/1 var(--font-sans); letter-spacing: 0; }
.identity-avatar { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.identity-btn-name { max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font: 700 var(--fs-subtitle)/var(--lh-subtitle) var(--font-sans); letter-spacing: var(--ls-subtitle); }
.identity-chevron { flex: none; width: 24px; height: 24px; background: currentColor; -webkit-mask: var(--icon-chevron-down) center / 24px 24px no-repeat; mask: var(--icon-chevron-down) center / 24px 24px no-repeat; }
.identity-menu { position: absolute; top: calc(100% + 4px); right: 0; z-index: 5000; min-width: 15rem; padding: var(--space-2) 0; background: var(--surface); border: 1px solid var(--divider); border-radius: var(--radius-lg); box-shadow: var(--shadow-window); }
.identity-menu.settings-menu { position: fixed; top: auto; right: auto; }
.identity-who { padding: var(--space-2) var(--space-4) var(--space-3); }
.identity-name { font: 700 var(--fs-subtitle)/var(--lh-subtitle) var(--font-sans); letter-spacing: var(--ls-subtitle); }
.identity-email { margin-top: var(--space-1); color: var(--text-weak); overflow-wrap: anywhere; font-size: var(--fs-caption); line-height: var(--lh-caption); letter-spacing: var(--ls-caption); }
.identity-divider { height: 1px; margin: var(--space-2) 0; background: var(--divider); }
.identity-item { display: flex; align-items: center; justify-content: flex-start; gap: var(--space-3); width: 100%; min-height: 36px; padding: 0 var(--space-4); border: 0; border-radius: 0; background: transparent; color: var(--text); text-decoration: none; text-align: left; cursor: pointer; font: 400 var(--fs-p2)/var(--lh-p2) var(--font-sans); letter-spacing: var(--ls-p2); }
.identity-item:hover { background: var(--surface-hover); }
.identity-icon { display: inline-flex; width: 16px; justify-content: center; }
.header-settings { display: none; place-items: center; flex: none; width: 44px; height: 44px; min-height: 0; margin-left: auto; padding: 0; border: 0; border-radius: 50%; background: transparent; color: var(--text); cursor: pointer; }
.header-settings svg { width: 24px; height: 24px; }
/* the status bar (Cortex's vendor-theme.css): 28px, --surface, a --divider top line, Caption text in --text-secondary;
   from the left the host pill (red), the view with the focus (bold) and its details 16px apart; at the right what
   concerns the whole page, ending with the connection dot (--success on, --primary off) */
#status-bar { height: 28px; flex-shrink: 0; display: flex; align-items: center; gap: var(--space-4); padding: 0 var(--space-2) 0 0; background: var(--surface); border-top: 1px solid var(--divider); color: var(--text-secondary); font: 400 var(--fs-caption)/var(--lh-caption) var(--font-sans); letter-spacing: var(--ls-caption); white-space: nowrap; overflow: hidden; z-index: 3; }
#status-bar .status-pill, #status-bar .status-item, #status-bar .status-right { display: inline-flex; align-items: center; gap: 4px; padding: 0; height: 100%; font-size: var(--fs-caption); color: var(--text-secondary); }
#status-bar .status-pill.host { padding: 0 var(--space-4); background: var(--primary); color: var(--text-on-primary); font-weight: 700; }
#status-bar b { color: var(--text); font-weight: 700; }
#status-bar .focus-name { display: inline-block; max-width: 40ch; overflow: hidden; text-overflow: ellipsis; color: var(--text); font-weight: 700; }
#status-bar .status-details { display: inline-flex; align-items: center; gap: var(--space-4); min-width: 0; }
#status-bar .status-details:empty, #status-bar .status-item:empty { display: none; }
#status-bar .status-spacer { flex: 1; }
#status-bar .status-right { padding: 0 8px; }
#status-bar .status-item.conn::before { content: ""; display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; background: var(--primary); }
#status-bar .status-item.conn.on::before { background: var(--success); }
/* tablet: the rail is the menu; the button opens the full menu over the page */
@media (min-width: 834px) and (max-width: 1279px) {
  #app, #app.menu-collapsed { grid-template-columns: var(--menu-width-collapsed) minmax(0, 1fr); }
  #app:not(.menu-expanded) #icon-bar { padding-left: var(--space-3); padding-right: var(--space-3); }
  #app:not(.menu-expanded) .icon-bar-btn { justify-content: center; padding: 7px 0; }
  #app:not(.menu-expanded) .icon-bar-label { display: none; }
  #app:not(.menu-expanded) .menu-section { height: 1px; margin: var(--space-3) var(--space-1); background: var(--divider); font-size: 0; }
  #app:not(.menu-expanded) .icon-bar-group > .menu-section:first-child { display: none; }
  #app:not(.menu-expanded) .menu-logo { margin: 0 0 26px; text-align: center; }
  #app:not(.menu-expanded) .menu-logo > img, #app:not(.menu-expanded) .menu-logo .product { display: none !important; }
  #app:not(.menu-expanded) .menu-logo .rail-logo { display: flex; justify-content: center; margin-top: calc((18px - 40px) / 2); }
  #app.menu-expanded #icon-bar { position: fixed; left: 0; top: 0; bottom: 28px; width: var(--menu-width); padding-left: var(--space-4); padding-right: var(--space-4); box-shadow: var(--shadow-window); }
}
/* phone: a 56px header with the wordmark, the Settings icon and the profile's face; the bottom bar with five items;
   no status bar */
@media (max-width: 833px) {
  #app, #app.menu-collapsed { grid-template-columns: minmax(0, 1fr); grid-template-rows: 56px minmax(0, 1fr) auto; }
  #app > header { grid-column: 1; grid-row: 1; padding: 0 var(--space-2); background: var(--surface-page); }
  h1.brand { display: flex; align-items: center; gap: 10px; min-width: 0; margin: 0 auto 0 var(--space-2); }
  h1.brand img { width: 83px; height: 18px; flex: none; }
  .brand-name { padding-left: 10px; border-left: 1px solid var(--divider); color: var(--text-section); font: 700 var(--fs-subtitle)/var(--lh-subtitle) var(--font-sans); letter-spacing: var(--ls-subtitle); }
  #menubar, #token { display: none; }
  .identity-btn-name, .identity-chevron { display: none; }
  .header-settings { display: grid; }
  .header-settings + .identity { margin-left: 0; }
  .identity-face { width: 32px; height: 32px; }
  #below-bar { grid-column: 1; grid-row: 2; }
  #icon-bar { grid-column: 1; grid-row: 3; flex-direction: row; align-items: flex-end; justify-content: space-between; height: 64px; padding: 0 var(--space-4) 6px; border: 1px solid var(--divider); border-bottom: 0; border-radius: var(--radius-xl) var(--radius-xl) 0 0; box-shadow: var(--shadow-float); z-index: 25; }
  .menu-logo, .menu-collapse, .menu-section, .icon-bar-spacer, .icon-bar-bottom { display: none !important; }
  .icon-bar-group { flex-direction: row; justify-content: space-between; width: 100%; }
  .icon-bar-btn, #app.menu-collapsed .icon-bar-btn { flex-direction: column; justify-content: flex-start; gap: 0; width: auto; min-width: 54px; height: auto; padding: var(--space-2) 0 0; border-radius: 0; color: var(--text-secondary); }
  .icon-bar-btn:hover { background: transparent; }
  .icon-bar-label, #app.menu-collapsed .icon-bar-label { display: block; flex: none; overflow: visible; color: var(--text-secondary); font: 700 var(--fs-navbar)/var(--lh-navbar) var(--font-sans); letter-spacing: var(--ls-navbar); }
  .icon-bar-btn-active .icon-bar-label { color: var(--brand-text); }
  #status-bar { display: none; }
  .content { padding-bottom: var(--space-8); }
}
</style>
</head>
<body>
<div id="app">
  <!-- the side menu (as Cortex's sidebar.js): the Banco CTT wordmark and the product, then the views under section
       titles; Settings at the bottom. Desktop: 200px, collapsible to a 72px rail. Tablet: the rail. Phone: the bottom bar. -->
  <nav id="icon-bar" aria-label="Views"></nav>
  <header>
    <!-- phone: the menus are in a drawer behind this button (as Cortex's menu-commands.js) -->
    <button type="button" id="menu-toggle" class="menu-toggle" aria-label="Menus" title="Menus" aria-expanded="false"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
    <!-- the phone's header carries the wordmark (on wider screens it is at the top of the side menu) -->
    <h1 class="brand"><img class="logo-light" src="data:image/svg+xml;base64,PHN2ZyBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJub25lIiBvdmVyZmxvdz0idmlzaWJsZSIgc3R5bGU9ImRpc3BsYXk6IGJsb2NrOyIgd2lkdGg9IjgzLjAwMDEiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCA4My4wMDAxIDE4IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8ZyBpZD0iT3RoZXJzL0xvZ28gQ1RUIj4KPHBhdGggaWQ9ImN0dCIgZD0iTTczLjE3MDYgNC42NDE0OUg3NS4zMDI0VjcuMzAyNjJINzMuMTcwNlYxMy41MzVDNzMuMTcwNiAxNC4zNzI5IDczLjcyODQgMTQuNjIgNzQuMjYxNCAxNC42MkM3NC41MDM2IDE0LjYyIDc1LjAxMTcgMTQuNTk0NiA3NS4zMDI0IDE0LjUyMDRWMTcuMDA4N0M3NC41OTk2IDE3LjEzMjUgNzMuMzg4OSAxNy4yMDU5IDcyLjgwNzMgMTcuMjA1OUM3MC4yODc5IDE3LjIwNTkgNjkuNzA2NyAxNS44MjU4IDY5LjcwNjcgMTMuODc5OFYzLjAzNjAyTDczLjE3MDYgMS4xOTMyNVY0LjY0MTQ5Wk04MC40MzkxIDQuNjQxNDlIODIuNTcxOVY3LjMwMjYySDgwLjQzOTFWMTMuNTM1QzgwLjQzOTEgMTQuMzcyOSA4MC45OTY5IDE0LjYyIDgxLjUyOTkgMTQuNjJDODEuNzcyMSAxNC42MiA4Mi4yODExIDE0LjU5NDcgODIuNTcxOSAxNC41MjA0VjE3LjAwODdDODEuODY5MyAxNy4xMzI1IDgwLjY1OCAxNy4yMDU5IDgwLjA3NjggMTcuMjA1OUM3Ny41NTczIDE3LjIwNTkgNzYuOTc2MiAxNS44MjU4IDc2Ljk3NjIgMTMuODc5OFYzLjAzNjAyTDgwLjQzOTEgMS4xOTMyNVY0LjY0MTQ5Wk02NC43NjYzIDQuMzQ0NjJDNjUuOTc2MiA0LjM0NDYyIDY3LjIzNjUgNC41OTA4MyA2OC4zNTEyIDQuOTM1NDRMNjcuODY2OCA3LjQ5Nzk0QzY2Ljc3NTggNy4xNTMzNSA2Ni4wNDk5IDcuMDA1NzUgNjUuMTc3NCA3LjAwNTc1QzYzLjA5NSA3LjAwNTg1IDYyLjIyMTMgOC41ODE2OSA2Mi4yMjEzIDEwLjc0OTlDNjIuMjIxNCAxMi45MTggNjMuMDk1MSAxNC40OTQ5IDY1LjE3NzQgMTQuNDk1QzY2LjA1IDE0LjQ5NSA2Ni43NzU4IDE0LjM0NjUgNjcuODY2OCAxNC4wMDE4TDY4LjM1MTIgMTYuNTY0M0M2Ny4yMzY1IDE2LjkwODkgNjUuOTc2MiAxNy4xNTUyIDY0Ljc2NjMgMTcuMTU1MkM2MC43MjAzIDE3LjE1NTEgNTguNTg4NiAxNC41OTMxIDU4LjU4ODUgMTAuNzQ5OUM1OC41ODg1IDYuOTMxNDQgNjAuNzIwMiA0LjM0NDY4IDY0Ljc2NjMgNC4zNDQ2MloiIGZpbGw9IiNFMDAwMjQiLz4KPHBhdGggaWQ9IkNvbWJpbmVkIFNoYXBlIiBkPSJNMS42MTcxOSA1Ljg5ODc3SDEuNjY2MDJDMi41NTkyNSA1LjAzOTEyIDMuODM4NzkgNC40MjUxNCA1LjMxMTUyIDQuNDI1MTRDOC42NDM2NyA0LjQyNTE5IDEwLjA0NDkgNy4yMjQzIDEwLjA0NDkgMTAuODA5OUMxMC4wNDQ5IDE0LjM5NDkgOC4yODE5NSAxNy4xOTQ3IDQuMzk0NTMgMTcuMTk0N0MyLjcwNDA4IDE3LjE5NDcgMS4xMTAyNiAxNi44MDIzIDAgMTYuMjEyM1YwLjI1MDMzN0gxLjYxNzE5VjUuODk4NzdaTTE3LjE1NzIgNC40MjQxN0MxOS41NzE4IDQuNDI0MTcgMjEuNDA2MSA1LjYwMzI2IDIxLjQwNjIgOC4xODE5OFYxNi45NDk2SDE5Ljk4MjRMMTkuNzg5MSAxNS4zMjg1QzE4LjM4ODkgMTYuNzI4MyAxNy4wNjExIDE3LjE5NDYgMTUuNTE1NiAxNy4xOTQ3QzEzLjUzNTEgMTcuMTk0NyAxMS45NjQ5IDE2LjExNDQgMTEuOTY0OCAxNC4xNDk4QzExLjk2NDggMTEuNDQ4NSAxNC42NDU0IDEwLjA0OTEgMTkuNzg5MSA5LjY1NTYxVjguMjMwODFDMTkuNzg4OSA2LjU4NjEgMTguNzk5NCA1LjYyODM1IDE2LjkxNSA1LjYyODI3QzE1LjY4MzggNS42MjgyNyAxNC4yNTk4IDYuMDQ2MDcgMTMuMDA0OSA2LjUxMzAzTDEyLjY2NiA1LjM1Nzc2QzE0LjIzNTMgNC44MTggMTUuNzU3IDQuNDI0MjUgMTcuMTU3MiA0LjQyNDE3Wk00MS43NTY4IDQuNDI1MTRDNDIuODE5OSA0LjQyNTE1IDQzLjk3ODggNC42NzA4OCA0NC44NzIxIDQuOTY1MThMNDQuNjMwOSA2LjE5MjcyQzQzLjY4OSA1Ljg5NzY4IDQyLjgxOTkgNS43MDI1MSA0MS45MjY4IDUuNzAyNDlDMzguODM1OSA1LjcwMjQ5IDM3Ljc3MjUgOC4wNTk3OCAzNy43NzI1IDEwLjgwOTlDMzcuNzcyNSAxMy41NjA3IDM4LjgzNTkgMTUuOTE3MyA0MS45MjY4IDE1LjkxNzNDNDIuODE5OSAxNS45MTczIDQzLjY4OSAxNS43MjE0IDQ0LjYzMDkgMTUuNDI3MUw0NC44NzIxIDE2LjY1NDZDNDMuOTc4OCAxNi45NDg5IDQyLjgxOTggMTcuMTk0NyA0MS43NTY4IDE3LjE5NDdDMzcuODIxNSAxNy4xOTQ3IDM2LjA4NDEgMTQuNDkzMiAzNi4wODQgMTAuODA5OUMzNi4wODQgNy4xNTEzMyAzNy44MjE0IDQuNDI1MTQgNDEuNzU2OCA0LjQyNTE0Wk01MS4yMDIxIDQuNDI0MTdDNTQuODk2MiA0LjQyNDE3IDU2LjUxMzcgNy4zNzEzMSA1Ni41MTM3IDEwLjgwOTlDNTYuNTEzNyAxNC4yNDc4IDU0Ljg5NjIgMTcuMTk0NyA1MS4yMDIxIDE3LjE5NDdDNDcuNDgzIDE3LjE5NDcgNDUuODg5NiAxNC4yNDc4IDQ1Ljg4OTYgMTAuODA5OUM0NS44ODk3IDcuMzcxMzEgNDcuNDgzIDQuNDI0MTcgNTEuMjAyMSA0LjQyNDE3Wk0zMC4xODM2IDQuNDI1MTRDMzIuNTc0NSA0LjQyNTI0IDMzLjc4MTIgNS43NTE1OCAzMy43ODEyIDguMzc5MjRWMTYuOTQ5NkgzMi4xNjMxVjguNjQ4NzdDMzIuMTYzMSA3LjEwMjE2IDMxLjU2IDUuNzc1NzMgMjkuNTA3OCA1Ljc3NTczQzI3Ljg4OTcgNS43NzU3NiAyNi40MTY1IDYuODU2MzIgMjUuNjY4IDcuNDk0NDhWMTYuOTQ5NkgyNC4wNTE4VjQuNjMzMTVIMjUuNDk5TDI1LjY2OCA2LjM2NDU5QzI2Ljg5OTMgNS4yNTk0NCAyOC4zOTcxIDQuNDI1MTQgMzAuMTgzNiA0LjQyNTE0Wk00Ljc1Njg0IDUuNzc1NzNDMy4yODQyIDUuNzc1NzkgMi4xNzMwNCA2LjUxMjY0IDEuNjE3MTkgNi45Nzg4NVYxNS4zNTI5QzIuNDE0NDMgMTUuNzk1MSAzLjM4MDIxIDE1Ljk5MjUgNC4zNzAxMiAxNS45OTI1QzcuMTk1MTIgMTUuOTkyNSA4LjM1NDM5IDEzLjgwNiA4LjM1NDQ5IDEwLjg4NDFDOC4zNTQ0OSA4LjA1OTY3IDcuMzM5ODQgNS43NzU3MyA0Ljc1Njg0IDUuNzc1NzNaTTUxLjIwMjEgNS42MjgyN0M0OC41MjEgNS42MjgyNyA0Ny41ODAxIDguMDM1MDEgNDcuNTgwMSAxMC44MDk5QzQ3LjU4MDEgMTMuNTg0OCA0OC41MjEgMTUuOTkxNSA1MS4yMDIxIDE1Ljk5MTVDNTMuODgxOSAxNS45OTE1IDU0LjgyNDIgMTMuNTg0OCA1NC44MjQyIDEwLjgwOTlDNTQuODI0MiA4LjAzNTAxIDUzLjg4MTkgNS42MjgyNyA1MS4yMDIxIDUuNjI4MjdaTTE5Ljc4OTEgMTAuNzExM0MxNS43MzMxIDEwLjk1NjggMTMuNTg0MyAxMi4yMzQxIDEzLjU4NCAxMy45MDM3QzEzLjU4NCAxNS4xMDcyIDE0LjQwNTIgMTUuOTE3MyAxNS45NzQ2IDE1LjkxNzNDMTcuNTY4MiAxNS45MTcyIDE4Ljg3MTUgMTUuMTU2MSAxOS43ODkxIDE0LjE3NDJWMTAuNzExM1oiIGZpbGw9ImJsYWNrIi8+CjwvZz4KPC9zdmc+Cg==" alt="Banco CTT" width="83" height="18"><img class="logo-dark" src="data:image/svg+xml;base64,PHN2ZyBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJub25lIiBvdmVyZmxvdz0idmlzaWJsZSIgc3R5bGU9ImRpc3BsYXk6IGJsb2NrOyIgd2lkdGg9IjgzLjAwMDEiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCA4My4wMDAxIDE4IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8ZyBpZD0iT3RoZXJzL0xvZ28gQ1RUIj4KPHBhdGggaWQ9ImN0dCIgZD0iTTczLjE3MDYgNC42NDE0OUg3NS4zMDI0VjcuMzAyNjJINzMuMTcwNlYxMy41MzVDNzMuMTcwNiAxNC4zNzI5IDczLjcyODQgMTQuNjIgNzQuMjYxNCAxNC42MkM3NC41MDM2IDE0LjYyIDc1LjAxMTcgMTQuNTk0NiA3NS4zMDI0IDE0LjUyMDRWMTcuMDA4N0M3NC41OTk2IDE3LjEzMjUgNzMuMzg4OSAxNy4yMDU5IDcyLjgwNzMgMTcuMjA1OUM3MC4yODc5IDE3LjIwNTkgNjkuNzA2NyAxNS44MjU4IDY5LjcwNjcgMTMuODc5OFYzLjAzNjAyTDczLjE3MDYgMS4xOTMyNVY0LjY0MTQ5Wk04MC40MzkxIDQuNjQxNDlIODIuNTcxOVY3LjMwMjYySDgwLjQzOTFWMTMuNTM1QzgwLjQzOTEgMTQuMzcyOSA4MC45OTY5IDE0LjYyIDgxLjUyOTkgMTQuNjJDODEuNzcyMSAxNC42MiA4Mi4yODExIDE0LjU5NDcgODIuNTcxOSAxNC41MjA0VjE3LjAwODdDODEuODY5MyAxNy4xMzI1IDgwLjY1OCAxNy4yMDU5IDgwLjA3NjggMTcuMjA1OUM3Ny41NTczIDE3LjIwNTkgNzYuOTc2MiAxNS44MjU4IDc2Ljk3NjIgMTMuODc5OFYzLjAzNjAyTDgwLjQzOTEgMS4xOTMyNVY0LjY0MTQ5Wk02NC43NjYzIDQuMzQ0NjJDNjUuOTc2MiA0LjM0NDYyIDY3LjIzNjUgNC41OTA4MyA2OC4zNTEyIDQuOTM1NDRMNjcuODY2OCA3LjQ5Nzk0QzY2Ljc3NTggNy4xNTMzNSA2Ni4wNDk5IDcuMDA1NzUgNjUuMTc3NCA3LjAwNTc1QzYzLjA5NSA3LjAwNTg1IDYyLjIyMTMgOC41ODE2OSA2Mi4yMjEzIDEwLjc0OTlDNjIuMjIxNCAxMi45MTggNjMuMDk1MSAxNC40OTQ5IDY1LjE3NzQgMTQuNDk1QzY2LjA1IDE0LjQ5NSA2Ni43NzU4IDE0LjM0NjUgNjcuODY2OCAxNC4wMDE4TDY4LjM1MTIgMTYuNTY0M0M2Ny4yMzY1IDE2LjkwODkgNjUuOTc2MiAxNy4xNTUyIDY0Ljc2NjMgMTcuMTU1MkM2MC43MjAzIDE3LjE1NTEgNTguNTg4NiAxNC41OTMxIDU4LjU4ODUgMTAuNzQ5OUM1OC41ODg1IDYuOTMxNDQgNjAuNzIwMiA0LjM0NDY4IDY0Ljc2NjMgNC4zNDQ2MloiIGZpbGw9IiNFMDAwMjQiLz4KPHBhdGggaWQ9IkNvbWJpbmVkIFNoYXBlIiBkPSJNMS42MTcxOSA1Ljg5ODc3SDEuNjY2MDJDMi41NTkyNSA1LjAzOTEyIDMuODM4NzkgNC40MjUxNCA1LjMxMTUyIDQuNDI1MTRDOC42NDM2NyA0LjQyNTE5IDEwLjA0NDkgNy4yMjQzIDEwLjA0NDkgMTAuODA5OUMxMC4wNDQ5IDE0LjM5NDkgOC4yODE5NSAxNy4xOTQ3IDQuMzk0NTMgMTcuMTk0N0MyLjcwNDA4IDE3LjE5NDcgMS4xMTAyNiAxNi44MDIzIDAgMTYuMjEyM1YwLjI1MDMzN0gxLjYxNzE5VjUuODk4NzdaTTE3LjE1NzIgNC40MjQxN0MxOS41NzE4IDQuNDI0MTcgMjEuNDA2MSA1LjYwMzI2IDIxLjQwNjIgOC4xODE5OFYxNi45NDk2SDE5Ljk4MjRMMTkuNzg5MSAxNS4zMjg1QzE4LjM4ODkgMTYuNzI4MyAxNy4wNjExIDE3LjE5NDYgMTUuNTE1NiAxNy4xOTQ3QzEzLjUzNTEgMTcuMTk0NyAxMS45NjQ5IDE2LjExNDQgMTEuOTY0OCAxNC4xNDk4QzExLjk2NDggMTEuNDQ4NSAxNC42NDU0IDEwLjA0OTEgMTkuNzg5MSA5LjY1NTYxVjguMjMwODFDMTkuNzg4OSA2LjU4NjEgMTguNzk5NCA1LjYyODM1IDE2LjkxNSA1LjYyODI3QzE1LjY4MzggNS42MjgyNyAxNC4yNTk4IDYuMDQ2MDcgMTMuMDA0OSA2LjUxMzAzTDEyLjY2NiA1LjM1Nzc2QzE0LjIzNTMgNC44MTggMTUuNzU3IDQuNDI0MjUgMTcuMTU3MiA0LjQyNDE3Wk00MS43NTY4IDQuNDI1MTRDNDIuODE5OSA0LjQyNTE1IDQzLjk3ODggNC42NzA4OCA0NC44NzIxIDQuOTY1MThMNDQuNjMwOSA2LjE5MjcyQzQzLjY4OSA1Ljg5NzY4IDQyLjgxOTkgNS43MDI1MSA0MS45MjY4IDUuNzAyNDlDMzguODM1OSA1LjcwMjQ5IDM3Ljc3MjUgOC4wNTk3OCAzNy43NzI1IDEwLjgwOTlDMzcuNzcyNSAxMy41NjA3IDM4LjgzNTkgMTUuOTE3MyA0MS45MjY4IDE1LjkxNzNDNDIuODE5OSAxNS45MTczIDQzLjY4OSAxNS43MjE0IDQ0LjYzMDkgMTUuNDI3MUw0NC44NzIxIDE2LjY1NDZDNDMuOTc4OCAxNi45NDg5IDQyLjgxOTggMTcuMTk0NyA0MS43NTY4IDE3LjE5NDdDMzcuODIxNSAxNy4xOTQ3IDM2LjA4NDEgMTQuNDkzMiAzNi4wODQgMTAuODA5OUMzNi4wODQgNy4xNTEzMyAzNy44MjE0IDQuNDI1MTQgNDEuNzU2OCA0LjQyNTE0Wk01MS4yMDIxIDQuNDI0MTdDNTQuODk2MiA0LjQyNDE3IDU2LjUxMzcgNy4zNzEzMSA1Ni41MTM3IDEwLjgwOTlDNTYuNTEzNyAxNC4yNDc4IDU0Ljg5NjIgMTcuMTk0NyA1MS4yMDIxIDE3LjE5NDdDNDcuNDgzIDE3LjE5NDcgNDUuODg5NiAxNC4yNDc4IDQ1Ljg4OTYgMTAuODA5OUM0NS44ODk3IDcuMzcxMzEgNDcuNDgzIDQuNDI0MTcgNTEuMjAyMSA0LjQyNDE3Wk0zMC4xODM2IDQuNDI1MTRDMzIuNTc0NSA0LjQyNTI0IDMzLjc4MTIgNS43NTE1OCAzMy43ODEyIDguMzc5MjRWMTYuOTQ5NkgzMi4xNjMxVjguNjQ4NzdDMzIuMTYzMSA3LjEwMjE2IDMxLjU2IDUuNzc1NzMgMjkuNTA3OCA1Ljc3NTczQzI3Ljg4OTcgNS43NzU3NiAyNi40MTY1IDYuODU2MzIgMjUuNjY4IDcuNDk0NDhWMTYuOTQ5NkgyNC4wNTE4VjQuNjMzMTVIMjUuNDk5TDI1LjY2OCA2LjM2NDU5QzI2Ljg5OTMgNS4yNTk0NCAyOC4zOTcxIDQuNDI1MTQgMzAuMTgzNiA0LjQyNTE0Wk00Ljc1Njg0IDUuNzc1NzNDMy4yODQyIDUuNzc1NzkgMi4xNzMwNCA2LjUxMjY0IDEuNjE3MTkgNi45Nzg4NVYxNS4zNTI5QzIuNDE0NDMgMTUuNzk1MSAzLjM4MDIxIDE1Ljk5MjUgNC4zNzAxMiAxNS45OTI1QzcuMTk1MTIgMTUuOTkyNSA4LjM1NDM5IDEzLjgwNiA4LjM1NDQ5IDEwLjg4NDFDOC4zNTQ0OSA4LjA1OTY3IDcuMzM5ODQgNS43NzU3MyA0Ljc1Njg0IDUuNzc1NzNaTTUxLjIwMjEgNS42MjgyN0M0OC41MjEgNS42MjgyNyA0Ny41ODAxIDguMDM1MDEgNDcuNTgwMSAxMC44MDk5QzQ3LjU4MDEgMTMuNTg0OCA0OC41MjEgMTUuOTkxNSA1MS4yMDIxIDE1Ljk5MTVDNTMuODgxOSAxNS45OTE1IDU0LjgyNDIgMTMuNTg0OCA1NC44MjQyIDEwLjgwOTlDNTQuODI0MiA4LjAzNTAxIDUzLjg4MTkgNS42MjgyNyA1MS4yMDIxIDUuNjI4MjdaTTE5Ljc4OTEgMTAuNzExM0MxNS43MzMxIDEwLjk1NjggMTMuNTg0MyAxMi4yMzQxIDEzLjU4NCAxMy45MDM3QzEzLjU4NCAxNS4xMDcyIDE0LjQwNTIgMTUuOTE3MyAxNS45NzQ2IDE1LjkxNzNDMTcuNTY4MiAxNS45MTcyIDE4Ljg3MTUgMTUuMTU2MSAxOS43ODkxIDE0LjE3NDJWMTAuNzExM1oiIGZpbGw9IiNGMUY0RjgiLz4KPC9nPgo8L3N2Zz4K" alt="Banco CTT" width="83" height="18"><span class="brand-name">MCP Server</span></h1>
    <nav id="menubar" aria-label="Main menu"></nav>
    <input id="token" class="field" type="password" placeholder="admin token (for writes)" aria-label="Admin token" autocomplete="off">
    <div class="identity" id="identity" hidden></div>
  </header>
  <div id="below-bar">
  <main class="content">
    <section id="view-overview">
      <div class="view-head"><div><h2>Overview</h2><p>What is live, what needs a decision, and what the last calls were.</p></div></div>
      <div class="tiles" id="tiles"></div>
      <div class="two">
        <div class="card"><h3>Needs attention</h3><ul class="attn" id="attention"></ul></div>
        <div class="card"><h3>Recent activity</h3><div class="tablewrap" style="border:0"><table id="recent"><thead><tr><th>Time</th><th>App</th><th>Tool</th><th>On behalf of</th><th>Status</th></tr></thead><tbody></tbody></table></div><p style="margin:12px 0 0"><a href="#activity">All activity →</a></p></div>
      </div>
    </section>
    <section id="view-tools">
      <div class="view-head"><div><h2>Tools</h2><p>Every tool the service offers, by app. Select a row for its schema, a Try it form, connection snippets, its calls and its history.</p></div><button class="btn primary" id="newtool">+ New tool</button></div>
      <div class="toolbar">
        <input class="field" id="q" type="search" placeholder="Filter by name, description, impl, app  ( / )" aria-label="Filter tools">
        <div class="chips" id="appchips"></div>
        <div class="chips" id="tierchips"><button class="chip" data-tier="" aria-pressed="true">any tier</button><button class="chip" data-tier="read">read</button><button class="chip" data-tier="write">write</button></div>
        <button class="chip" id="enabledonly" aria-pressed="false">enabled only</button>
      </div>
      <div class="tablewrap"><table id="tooltable"><thead><tr><th>Name</th><th>Apps</th><th>Tier</th><th>Exec</th><th>Impl</th><th>Last used</th><th class="num">Calls 24 h</th><th>Enabled</th></tr></thead><tbody></tbody></table></div>
    </section>
    <section id="view-skills">
      <div class="view-head"><div><h2>Skills</h2><p>Instructions several consumers must apply the same way, owned here and versioned. App-tuned system prompts stay in their apps. Served over MCP as prompts and as <code>skill://</code> resources.</p></div><button class="btn primary" id="newskill">+ New skill</button></div>
      <div class="tablewrap"><table id="skilltable"><thead><tr><th>Name</th><th>Apps</th><th>Tags</th><th>Expects tools</th><th class="num">Version</th><th>Updated</th><th>Enabled</th></tr></thead><tbody></tbody></table></div>
    </section>
    <section id="view-apps">
      <div class="view-head"><div><h2>Apps</h2><p>The application catalog: each app's record (owner, contact, status), its endpoint, its keys, what it is offered, and what it called. Tools and skills are offered to registered apps only; keys are issued to them only.</p></div><button class="btn primary" id="newapp">+ New app</button></div>
      <div class="appcards" id="appcards"></div>
    </section>
    <section id="view-activity">
      <div class="view-head"><div><h2>Activity</h2><p>Every invocation: who, for which app, on whose behalf, how long, with what outcome.</p></div><a class="btn" id="csv" href="activity.csv?window=24h">Export CSV</a></div>
      <div class="toolbar">
        <div class="chips" id="winchips"><button class="chip" data-win="1h">1 h</button><button class="chip" data-win="24h" aria-pressed="true">24 h</button><button class="chip" data-win="7d">7 d</button><button class="chip" data-win="30d">30 d</button></div>
        <select class="field" id="act-app" aria-label="App"><option value="">all apps</option></select>
        <select class="field" id="act-ok" aria-label="Status"><option value="">any status</option><option value="true">ok</option><option value="false">error</option></select>
        <input class="field" id="act-q" type="search" placeholder="tool, caller, person, error text" aria-label="Search activity">
      </div>
      <div class="summary" id="act-summary"></div>
      <div class="tablewrap"><table id="acttable"><thead><tr><th>Time</th><th>App</th><th>Tool</th><th>Caller</th><th>On behalf of</th><th>Via</th><th class="num">Duration</th><th>Status</th></tr></thead><tbody></tbody></table></div>
      <p style="margin-top:8px"><button class="btn sm" id="act-more" hidden>Load more</button></p>
    </section>
    <section id="view-help">
      <div class="help-frame">
        <aside class="help-contents" id="help-contents" aria-label="Contents"></aside>
        <div class="help-sheet">
          <div class="help-bar"><button type="button" class="btn sm" id="help-back" hidden><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01"/></svg>Contents</button><span class="eyebrow" id="help-crumb"></span></div>
          <article class="markdown guide manual" id="help-article"></article>
          <div class="manual-next" id="help-next"></div>
        </div>
      </div>
    </section>
    <section id="view-settings">
      <div class="view-head"><div><h2>Settings</h2><p>Implementations and what binds to them, backends, the auth mode, and export.</p></div></div>
      <div class="two">
        <div class="card"><h3 id="impls-h">Implementations</h3><div class="tablewrap" style="border:0"><table class="impls" id="impltable"><thead><tr><th>Impl</th><th>Bound tools</th></tr></thead><tbody></tbody></table></div><p class="hint" id="impls-note" style="margin-top:8px"></p></div>
        <div class="card"><h3>Backends</h3><dl class="kv" id="backends"></dl><h3 style="margin-top:16px">Auth and retention</h3><dl class="kv" id="authkv"></dl>
          <h3 style="margin-top:16px">OAuth clients</h3>
          <p class="hint" id="oauth-issuer"></p>
          <div class="keys" id="oauth-clients"></div>
          <h3 style="margin-top:16px">Export and import</h3>
          <div style="display:flex;gap:8px;flex-wrap:wrap"><a class="btn" href="admin/export">Registry JSON</a><a class="btn" id="export-app" href="admin/export">Registry · one app</a><a class="btn" href="activity.csv?window=30d">Activity CSV · 30 d</a><label class="btn">Import (dry run)<input type="file" id="import" accept="application/json" hidden></label></div>
          <div id="import-out" style="margin-top:12px"></div>
        </div>
      </div>
    </section>
  </main>
  </div>
  <footer id="status-bar">
    <!-- from the left: the service, the view with the focus, its details; at the right: what concerns the whole page -->
    <span class="status-pill host" id="sb-host" title="This service">mcp-service</span>
    <span class="status-item focus-name" id="sb-focus"></span>
    <span class="status-details" id="sb-details"></span>
    <span class="status-spacer"></span>
    <button type="button" class="status-right" id="sb-backends" title="The backends the implementations depend on (Monitoring menu, Settings)"></button>
    <span class="status-right" id="sb-keys" title="App keys: whether every call must present one"></span>
    <span class="status-right" id="sb-record" title="The invocation record"></span>
    <span class="status-item conn off" id="status">disconnected</span>
  </footer>
</div>
<div class="scrim" id="scrim"></div>
<aside class="drawer" id="drawer" aria-label="Detail" aria-hidden="true">
  <div class="drawer-head">
    <div class="title"><h2 id="d-name"></h2><span class="pill" id="d-p1"></span><span class="pill" id="d-p2"></span><button class="btn sm close" id="close">Close</button></div>
    <div class="tabs" role="tablist" id="tabs"></div>
  </div>
  <div class="drawer-body" id="d-body"></div>
</aside>
<div class="toast" id="toast" role="status"></div>
<!-- the interface language (Cortex's i18n.js, reduced): English as written, or Portuguese looked up as the page is built.
     Kept under localStorage mcp.uiLanguage; ?lang=pt|en in the address sets it. The dictionary is admin/i18n/pt.js. -->
<script>
(function () {
  var KEY = 'mcp.uiLanguage';
  var lang = 'en';
  try {
    var q = location.search.indexOf('lang=') >= 0 ? location.search.split('lang=')[1].slice(0, 2) : '';
    if (q === 'pt' || q === 'en') { localStorage.setItem(KEY, q); }
    lang = localStorage.getItem(KEY) === 'pt' ? 'pt' : 'en';
  } catch (e) { /* storage unavailable: English */ }
  window.uiLanguage = function () { return lang; };
  window.mcpT = function (s) { return s; };
  if (lang !== 'pt') return;
  document.documentElement.lang = 'pt-PT';
  // the content areas: what people and programs wrote, never translated
  var CONTENT = ['.notranslate', 'textarea', 'input', 'code', 'pre', '.mono', 'td.name', '.desc', '.pill.app', '.pill.tag',
    '.identity-name', '.identity-email', '.identity-btn-name', 'article.manual', '.preview', '.markdown',
    '.diff', '.result pre', '.kv dd .mono', '.menu-note', '.apps'].join(', ');
  var CONTENT_ATTR = CONTENT.split(', ').filter(function (s) { return s !== 'textarea' && s !== 'input'; }).join(', ');
  var exact = Object.create(null), templates = [];
  function holes(s) {
    var parts = [], order = [], cur = '', i = 0;
    while (i < s.length) {
      if (s[i] === '{') { var j = s.indexOf('}', i); var n = j > i ? s.slice(i + 1, j) : '';
        if (n !== '' && String(Number(n)) === n) { parts.push(cur); cur = ''; order.push(Number(n)); i = j + 1; continue; } }
      cur += s[i]; i += 1;
    }
    parts.push(cur); return { parts: parts, order: order };
  }
  function load(dict) {
    Object.keys(dict).forEach(function (en) {
      if (en.indexOf('{0}') < 0) { exact[en] = dict[en]; return; }
      var h = holes(en); templates.push({ parts: h.parts, order: h.order, to: dict[en] });
    });
    templates.sort(function (a, b) { return b.parts.join('').length - a.parts.join('').length; });
  }
  function fill(to, values) {
    var out = '', i = 0;
    while (i < to.length) {
      if (to[i] === '{') { var j = to.indexOf('}', i); var n = j > i ? to.slice(i + 1, j) : '';
        if (n !== '' && String(Number(n)) === n && values[Number(n)] !== undefined) { out += values[Number(n)]; i = j + 1; continue; } }
      out += to[i]; i += 1;
    }
    return out;
  }
  function matchTemplate(text) {
    for (var k = 0; k < templates.length; k++) {
      var tp = templates[k], parts = tp.parts, last = parts.length - 1;
      if (!text.startsWith(parts[0]) || !text.endsWith(parts[last])) continue;
      if (text.length < parts[0].length + parts[last].length) continue;
      var pos = parts[0].length, values = [], ok = true;
      for (var p = 1; p <= last; p++) {
        if (p < last && parts[p] === '') { ok = false; break; }
        var at = p === last ? text.length - parts[last].length : text.indexOf(parts[p], pos);
        if (at < pos) { ok = false; break; }
        var value = text.slice(pos, at);
        if (value === '') { ok = false; break; }
        values[tp.order[p - 1]] = translate(value, true);
        pos = at + parts[p].length;
      }
      if (ok) return fill(tp.to, values);
    }
    return null;
  }
  function translate(text, inner) {
    if (!text) return null;
    var start = 0, end = text.length;
    while (start < end && (text[start] === ' ' || text[start] === '\n' || text[start] === '\t')) start++;
    while (end > start && (text[end - 1] === ' ' || text[end - 1] === '\n' || text[end - 1] === '\t')) end--;
    var core = text.slice(start, end);
    if (!core) return null;
    var hit = exact[core];
    if (hit === undefined) hit = matchTemplate(core);
    if (hit == null) return inner ? text : null;
    return text.slice(0, start) + hit + text.slice(end);
  }
  window.mcpT = function (s) { var r = translate(String(s)); return r == null ? s : r; };
  var ATTRS = ['title', 'placeholder', 'aria-label'];
  var wroteText = new WeakMap(), wroteAttr = new WeakMap();
  function excluded(el) { return !!(el && el.closest && el.closest(CONTENT)); }
  function excludedAttr(el) { return !!(el && el.closest && el.closest(CONTENT_ATTR)); }
  function doText(node) {
    var el = node.parentElement;
    if (!el || el.tagName === 'SCRIPT' || el.tagName === 'STYLE') return;
    if (excluded(el)) return;
    if (wroteText.get(node) === node.nodeValue) return;
    var r = translate(node.nodeValue);
    if (r != null && r !== node.nodeValue) { node.nodeValue = r; wroteText.set(node, r); }
  }
  function doAttrs(el) {
    if (excludedAttr(el)) return;
    var mine = wroteAttr.get(el);
    for (var i = 0; i < ATTRS.length; i++) {
      var v = el.getAttribute(ATTRS[i]);
      if (!v || (mine && mine[ATTRS[i]] === v)) continue;
      var r = translate(v);
      if (r != null && r !== v) { el.setAttribute(ATTRS[i], r); if (!mine) { mine = {}; wroteAttr.set(el, mine); } mine[ATTRS[i]] = r; }
    }
  }
  function walk(root) {
    if (root.nodeType === 3) { doText(root); return; }
    if (root.nodeType !== 1) return;
    doAttrs(root);
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    var n = w.nextNode();
    while (n) { if (n.nodeType === 3) doText(n); else doAttrs(n); n = w.nextNode(); }
  }
  var observer = new MutationObserver(function (records) {
    for (var i = 0; i < records.length; i++) {
      var r = records[i];
      if (r.type === 'childList') for (var j = 0; j < r.addedNodes.length; j++) walk(r.addedNodes[j]);
      else if (r.type === 'characterData') doText(r.target);
      else if (r.type === 'attributes') doAttrs(r.target);
    }
  });
  function start() {
    load(window.MCP_PT || {});
    observer.observe(document.documentElement, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTRS });
    if (document.body) walk(document.body);
  }
  if (window.MCP_PT) start(); else window.__mcpI18nStart = start;
})();
</script>
<script src="admin/i18n/pt.js"></script>
<script>if (window.__mcpI18nStart) window.__mcpI18nStart();</script>
<!-- the Markdown renderer and its sanitiser: Cortex's vendored copies (marked 15.0.12, DOMPurify 3.2.6), served beside the page -->
<script src="admin/vendor/marked.min.js"></script>
<script src="admin/vendor/purify.min.js"></script>
<script>
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).split('&').join('&amp;').split('<').join('&lt;').split('>').join('&gt;').split('"').join('&quot;');
  const pillApps = apps => '<span class="apps">' + (apps || []).map(a => `<span class="pill app">${esc(a)}</span>`).join('') + '</span>';
  const execOf = t => ((t.config || {}).execution || 'server');
  const ago = iso => { if (!iso) return null; const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000); if (m < 1) return 'just now'; if (m < 60) return m + ' min ago'; const h = Math.floor(m / 60); if (h < 24) return h + ' h ago'; const d = Math.floor(h / 24); return d < 60 ? d + ' d ago' : new Date(iso).toISOString().slice(0, 10); };
  const day = iso => iso ? String(iso).slice(0, 10) : '';
  const ms = v => v == null ? '—' : (v >= 1000 ? (v / 1000).toFixed(2) + ' s' : v + ' ms');
  const PAGE_URL = location.href.split('#')[0].split('?')[0];
  const ADMIN_AT = PAGE_URL.lastIndexOf('/admin');
  const BASE = ADMIN_AT >= 0 ? PAGE_URL.slice(0, ADMIN_AT + 1) : PAGE_URL;
  const PUBLIC = BASE.endsWith('/') ? BASE.slice(0, -1) : BASE;

  // ── auth token (session only) ──
  const tokenEl = $('token');
  try { tokenEl.value = sessionStorage.getItem('mcp_admin_token') || ''; } catch (e) {}
  tokenEl.addEventListener('change', () => { try { sessionStorage.setItem('mcp_admin_token', tokenEl.value); } catch (e) {} });
  const headers = (json) => { const h = {}; if (json) h['content-type'] = 'application/json'; if (tokenEl.value) h['Authorization'] = 'Bearer ' + tokenEl.value; return h; };
  async function api(path, method, body) {
    const r = await fetch(path, { method: method || 'GET', headers: headers(!!body), body: body ? JSON.stringify(body) : undefined, cache: 'no-store' });
    let data = null; try { data = await r.json(); } catch (e) {}
    if (!r.ok) { const d = data && (data.detail || (data.error && (data.error.message || data.error)) ); throw new Error((r.status === 401 && !ME.admin ? 'Not allowed: paste the admin token in the bar, or sign in on the domain. ' : '') + (typeof d === 'string' ? d : JSON.stringify(d || r.status))); }
    return data;
  }
  let tt; function toast(m) { $('toast').textContent = m; $('toast').classList.add('show'); clearTimeout(tt); tt = setTimeout(() => $('toast').classList.remove('show'), 2600); }
  function copy(text) { (navigator.clipboard && navigator.clipboard.writeText(text) || Promise.reject()).then(() => toast('Copied'), () => toast('Select the text to copy it')); }

  // ── state ──
  let ME = { kind: 'anonymous', admin: false, via: 'none' };
  let win = '24h', actCursor;
  let REG = { tools: [], skills: [], apps: [], impls: [], impl_tools: {}, orphans: [], unused_impls: [], keys: [], summary: { tools: [] }, counts: {} };
  let HEALTH = {};
  let current = null;          // { kind: 'tool'|'skill', name }
  let appFilter = '', tierFilter = '', enabledOnly = false, q = '';

  async function loadAll() {
    const [reg, health, me] = await Promise.all([api('admin/registry'), api('admin/health'), api('admin/me').catch(() => ME)]);
    REG = reg; HEALTH = health; ME = me; renderWho();
    try { REG.machine_clients = (await api('oauth/clients')).clients.filter(c => c.kind === 'machine'); } catch (e) { REG.machine_clients = []; }
    renderMenubar(); renderHeader(); renderNav(); renderOverview(); renderTools(); renderSkills(); renderApps(); renderSettings();
    $('act-app').innerHTML = '<option value="">all apps</option>' + REG.apps.map(a => `<option>${esc(a)}</option>`).join('');
  }

  // ── the side menu (Cortex's sidebar.js): one outline icon set, 24px, in currentColor ──
  const icon = (inner) => `<svg class="menu-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`;
  const ICONS = {
    overview: icon('<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>'),
    tools: icon('<path d="M14.7 6.3a4 4 0 0 0-5.4 5.2L4 16.8 7.2 20l5.3-5.3a4 4 0 0 0 5.2-5.4l-2.7 2.7-2.3-2.3z"/>'),
    skills: icon('<path d="M13 3 5 14h6l-1 7 8-11h-6z"/>'),
    apps: icon('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 2.5 15.3 0 18M12 3c-2.5 2.7-2.5 15.3 0 18"/>'),
    activity: icon('<path d="M3 12h4l3-8 4 16 3-8h4"/>'),
    settings: icon('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>'),
  };
  const SUN = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><line x1="12" y1="2.5" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="21.5"/><line x1="2.5" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="21.5" y2="12"/><line x1="5.3" y1="5.3" x2="7" y2="7"/><line x1="17" y1="17" x2="18.7" y2="18.7"/><line x1="5.3" y1="18.7" x2="7" y2="17"/><line x1="17" y1="7" x2="18.7" y2="5.3"/></svg>';
  const MOON = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/></svg>';
  const SECTIONS = [
    { title: 'Workspace', entries: [{ key: 'overview', label: 'Overview', title: 'Overview: health, what needs a decision, the last calls' }] },
    { title: 'Catalog', entries: [
      { key: 'tools', label: 'Tools', title: 'Tools: what the service offers, by app' },
      { key: 'skills', label: 'Skills', title: 'Skills: instructions served as prompts and resources' },
      { key: 'apps', label: 'Apps', title: 'Apps: endpoints, keys, what each is offered' }] },
    { title: 'Operate', entries: [{ key: 'activity', label: 'Activity', title: 'Activity: every invocation' }] },
  ];
  const app = document.getElementById('app');
  const bar = $('icon-bar');
  const buttons = {};
  function menuButton(e, action) {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'icon-bar-btn'; b.innerHTML = ICONS[e.key];
    b.append(Object.assign(document.createElement('span'), { className: 'icon-bar-label', textContent: e.label }));
    b.title = e.title; b.dataset.key = e.key;
    b.addEventListener('click', (ev) => { ev.stopPropagation(); if (action) action(b); else location.hash = e.key; if (!action) app.classList.remove('menu-expanded'); paintCollapse(); });
    buttons[e.key] = b;
    return b;
  }
  const logo = Object.assign(document.createElement('div'), { className: 'menu-logo' });
  logo.innerHTML = '<img class="logo-light" src="data:image/svg+xml;base64,PHN2ZyBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJub25lIiBvdmVyZmxvdz0idmlzaWJsZSIgc3R5bGU9ImRpc3BsYXk6IGJsb2NrOyIgd2lkdGg9IjgzLjAwMDEiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCA4My4wMDAxIDE4IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8ZyBpZD0iT3RoZXJzL0xvZ28gQ1RUIj4KPHBhdGggaWQ9ImN0dCIgZD0iTTczLjE3MDYgNC42NDE0OUg3NS4zMDI0VjcuMzAyNjJINzMuMTcwNlYxMy41MzVDNzMuMTcwNiAxNC4zNzI5IDczLjcyODQgMTQuNjIgNzQuMjYxNCAxNC42MkM3NC41MDM2IDE0LjYyIDc1LjAxMTcgMTQuNTk0NiA3NS4zMDI0IDE0LjUyMDRWMTcuMDA4N0M3NC41OTk2IDE3LjEzMjUgNzMuMzg4OSAxNy4yMDU5IDcyLjgwNzMgMTcuMjA1OUM3MC4yODc5IDE3LjIwNTkgNjkuNzA2NyAxNS44MjU4IDY5LjcwNjcgMTMuODc5OFYzLjAzNjAyTDczLjE3MDYgMS4xOTMyNVY0LjY0MTQ5Wk04MC40MzkxIDQuNjQxNDlIODIuNTcxOVY3LjMwMjYySDgwLjQzOTFWMTMuNTM1QzgwLjQzOTEgMTQuMzcyOSA4MC45OTY5IDE0LjYyIDgxLjUyOTkgMTQuNjJDODEuNzcyMSAxNC42MiA4Mi4yODExIDE0LjU5NDcgODIuNTcxOSAxNC41MjA0VjE3LjAwODdDODEuODY5MyAxNy4xMzI1IDgwLjY1OCAxNy4yMDU5IDgwLjA3NjggMTcuMjA1OUM3Ny41NTczIDE3LjIwNTkgNzYuOTc2MiAxNS44MjU4IDc2Ljk3NjIgMTMuODc5OFYzLjAzNjAyTDgwLjQzOTEgMS4xOTMyNVY0LjY0MTQ5Wk02NC43NjYzIDQuMzQ0NjJDNjUuOTc2MiA0LjM0NDYyIDY3LjIzNjUgNC41OTA4MyA2OC4zNTEyIDQuOTM1NDRMNjcuODY2OCA3LjQ5Nzk0QzY2Ljc3NTggNy4xNTMzNSA2Ni4wNDk5IDcuMDA1NzUgNjUuMTc3NCA3LjAwNTc1QzYzLjA5NSA3LjAwNTg1IDYyLjIyMTMgOC41ODE2OSA2Mi4yMjEzIDEwLjc0OTlDNjIuMjIxNCAxMi45MTggNjMuMDk1MSAxNC40OTQ5IDY1LjE3NzQgMTQuNDk1QzY2LjA1IDE0LjQ5NSA2Ni43NzU4IDE0LjM0NjUgNjcuODY2OCAxNC4wMDE4TDY4LjM1MTIgMTYuNTY0M0M2Ny4yMzY1IDE2LjkwODkgNjUuOTc2MiAxNy4xNTUyIDY0Ljc2NjMgMTcuMTU1MkM2MC43MjAzIDE3LjE1NTEgNTguNTg4NiAxNC41OTMxIDU4LjU4ODUgMTAuNzQ5OUM1OC41ODg1IDYuOTMxNDQgNjAuNzIwMiA0LjM0NDY4IDY0Ljc2NjMgNC4zNDQ2MloiIGZpbGw9IiNFMDAwMjQiLz4KPHBhdGggaWQ9IkNvbWJpbmVkIFNoYXBlIiBkPSJNMS42MTcxOSA1Ljg5ODc3SDEuNjY2MDJDMi41NTkyNSA1LjAzOTEyIDMuODM4NzkgNC40MjUxNCA1LjMxMTUyIDQuNDI1MTRDOC42NDM2NyA0LjQyNTE5IDEwLjA0NDkgNy4yMjQzIDEwLjA0NDkgMTAuODA5OUMxMC4wNDQ5IDE0LjM5NDkgOC4yODE5NSAxNy4xOTQ3IDQuMzk0NTMgMTcuMTk0N0MyLjcwNDA4IDE3LjE5NDcgMS4xMTAyNiAxNi44MDIzIDAgMTYuMjEyM1YwLjI1MDMzN0gxLjYxNzE5VjUuODk4NzdaTTE3LjE1NzIgNC40MjQxN0MxOS41NzE4IDQuNDI0MTcgMjEuNDA2MSA1LjYwMzI2IDIxLjQwNjIgOC4xODE5OFYxNi45NDk2SDE5Ljk4MjRMMTkuNzg5MSAxNS4zMjg1QzE4LjM4ODkgMTYuNzI4MyAxNy4wNjExIDE3LjE5NDYgMTUuNTE1NiAxNy4xOTQ3QzEzLjUzNTEgMTcuMTk0NyAxMS45NjQ5IDE2LjExNDQgMTEuOTY0OCAxNC4xNDk4QzExLjk2NDggMTEuNDQ4NSAxNC42NDU0IDEwLjA0OTEgMTkuNzg5MSA5LjY1NTYxVjguMjMwODFDMTkuNzg4OSA2LjU4NjEgMTguNzk5NCA1LjYyODM1IDE2LjkxNSA1LjYyODI3QzE1LjY4MzggNS42MjgyNyAxNC4yNTk4IDYuMDQ2MDcgMTMuMDA0OSA2LjUxMzAzTDEyLjY2NiA1LjM1Nzc2QzE0LjIzNTMgNC44MTggMTUuNzU3IDQuNDI0MjUgMTcuMTU3MiA0LjQyNDE3Wk00MS43NTY4IDQuNDI1MTRDNDIuODE5OSA0LjQyNTE1IDQzLjk3ODggNC42NzA4OCA0NC44NzIxIDQuOTY1MThMNDQuNjMwOSA2LjE5MjcyQzQzLjY4OSA1Ljg5NzY4IDQyLjgxOTkgNS43MDI1MSA0MS45MjY4IDUuNzAyNDlDMzguODM1OSA1LjcwMjQ5IDM3Ljc3MjUgOC4wNTk3OCAzNy43NzI1IDEwLjgwOTlDMzcuNzcyNSAxMy41NjA3IDM4LjgzNTkgMTUuOTE3MyA0MS45MjY4IDE1LjkxNzNDNDIuODE5OSAxNS45MTczIDQzLjY4OSAxNS43MjE0IDQ0LjYzMDkgMTUuNDI3MUw0NC44NzIxIDE2LjY1NDZDNDMuOTc4OCAxNi45NDg5IDQyLjgxOTggMTcuMTk0NyA0MS43NTY4IDE3LjE5NDdDMzcuODIxNSAxNy4xOTQ3IDM2LjA4NDEgMTQuNDkzMiAzNi4wODQgMTAuODA5OUMzNi4wODQgNy4xNTEzMyAzNy44MjE0IDQuNDI1MTQgNDEuNzU2OCA0LjQyNTE0Wk01MS4yMDIxIDQuNDI0MTdDNTQuODk2MiA0LjQyNDE3IDU2LjUxMzcgNy4zNzEzMSA1Ni41MTM3IDEwLjgwOTlDNTYuNTEzNyAxNC4yNDc4IDU0Ljg5NjIgMTcuMTk0NyA1MS4yMDIxIDE3LjE5NDdDNDcuNDgzIDE3LjE5NDcgNDUuODg5NiAxNC4yNDc4IDQ1Ljg4OTYgMTAuODA5OUM0NS44ODk3IDcuMzcxMzEgNDcuNDgzIDQuNDI0MTcgNTEuMjAyMSA0LjQyNDE3Wk0zMC4xODM2IDQuNDI1MTRDMzIuNTc0NSA0LjQyNTI0IDMzLjc4MTIgNS43NTE1OCAzMy43ODEyIDguMzc5MjRWMTYuOTQ5NkgzMi4xNjMxVjguNjQ4NzdDMzIuMTYzMSA3LjEwMjE2IDMxLjU2IDUuNzc1NzMgMjkuNTA3OCA1Ljc3NTczQzI3Ljg4OTcgNS43NzU3NiAyNi40MTY1IDYuODU2MzIgMjUuNjY4IDcuNDk0NDhWMTYuOTQ5NkgyNC4wNTE4VjQuNjMzMTVIMjUuNDk5TDI1LjY2OCA2LjM2NDU5QzI2Ljg5OTMgNS4yNTk0NCAyOC4zOTcxIDQuNDI1MTQgMzAuMTgzNiA0LjQyNTE0Wk00Ljc1Njg0IDUuNzc1NzNDMy4yODQyIDUuNzc1NzkgMi4xNzMwNCA2LjUxMjY0IDEuNjE3MTkgNi45Nzg4NVYxNS4zNTI5QzIuNDE0NDMgMTUuNzk1MSAzLjM4MDIxIDE1Ljk5MjUgNC4zNzAxMiAxNS45OTI1QzcuMTk1MTIgMTUuOTkyNSA4LjM1NDM5IDEzLjgwNiA4LjM1NDQ5IDEwLjg4NDFDOC4zNTQ0OSA4LjA1OTY3IDcuMzM5ODQgNS43NzU3MyA0Ljc1Njg0IDUuNzc1NzNaTTUxLjIwMjEgNS42MjgyN0M0OC41MjEgNS42MjgyNyA0Ny41ODAxIDguMDM1MDEgNDcuNTgwMSAxMC44MDk5QzQ3LjU4MDEgMTMuNTg0OCA0OC41MjEgMTUuOTkxNSA1MS4yMDIxIDE1Ljk5MTVDNTMuODgxOSAxNS45OTE1IDU0LjgyNDIgMTMuNTg0OCA1NC44MjQyIDEwLjgwOTlDNTQuODI0MiA4LjAzNTAxIDUzLjg4MTkgNS42MjgyNyA1MS4yMDIxIDUuNjI4MjdaTTE5Ljc4OTEgMTAuNzExM0MxNS43MzMxIDEwLjk1NjggMTMuNTg0MyAxMi4yMzQxIDEzLjU4NCAxMy45MDM3QzEzLjU4NCAxNS4xMDcyIDE0LjQwNTIgMTUuOTE3MyAxNS45NzQ2IDE1LjkxNzNDMTcuNTY4MiAxNS45MTcyIDE4Ljg3MTUgMTUuMTU2MSAxOS43ODkxIDE0LjE3NDJWMTAuNzExM1oiIGZpbGw9ImJsYWNrIi8+CjwvZz4KPC9zdmc+Cg==" alt="Banco CTT" width="83" height="18"><img class="logo-dark" src="data:image/svg+xml;base64,PHN2ZyBwcmVzZXJ2ZUFzcGVjdFJhdGlvPSJub25lIiBvdmVyZmxvdz0idmlzaWJsZSIgc3R5bGU9ImRpc3BsYXk6IGJsb2NrOyIgd2lkdGg9IjgzLjAwMDEiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCA4My4wMDAxIDE4IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8ZyBpZD0iT3RoZXJzL0xvZ28gQ1RUIj4KPHBhdGggaWQ9ImN0dCIgZD0iTTczLjE3MDYgNC42NDE0OUg3NS4zMDI0VjcuMzAyNjJINzMuMTcwNlYxMy41MzVDNzMuMTcwNiAxNC4zNzI5IDczLjcyODQgMTQuNjIgNzQuMjYxNCAxNC42MkM3NC41MDM2IDE0LjYyIDc1LjAxMTcgMTQuNTk0NiA3NS4zMDI0IDE0LjUyMDRWMTcuMDA4N0M3NC41OTk2IDE3LjEzMjUgNzMuMzg4OSAxNy4yMDU5IDcyLjgwNzMgMTcuMjA1OUM3MC4yODc5IDE3LjIwNTkgNjkuNzA2NyAxNS44MjU4IDY5LjcwNjcgMTMuODc5OFYzLjAzNjAyTDczLjE3MDYgMS4xOTMyNVY0LjY0MTQ5Wk04MC40MzkxIDQuNjQxNDlIODIuNTcxOVY3LjMwMjYySDgwLjQzOTFWMTMuNTM1QzgwLjQzOTEgMTQuMzcyOSA4MC45OTY5IDE0LjYyIDgxLjUyOTkgMTQuNjJDODEuNzcyMSAxNC42MiA4Mi4yODExIDE0LjU5NDcgODIuNTcxOSAxNC41MjA0VjE3LjAwODdDODEuODY5MyAxNy4xMzI1IDgwLjY1OCAxNy4yMDU5IDgwLjA3NjggMTcuMjA1OUM3Ny41NTczIDE3LjIwNTkgNzYuOTc2MiAxNS44MjU4IDc2Ljk3NjIgMTMuODc5OFYzLjAzNjAyTDgwLjQzOTEgMS4xOTMyNVY0LjY0MTQ5Wk02NC43NjYzIDQuMzQ0NjJDNjUuOTc2MiA0LjM0NDYyIDY3LjIzNjUgNC41OTA4MyA2OC4zNTEyIDQuOTM1NDRMNjcuODY2OCA3LjQ5Nzk0QzY2Ljc3NTggNy4xNTMzNSA2Ni4wNDk5IDcuMDA1NzUgNjUuMTc3NCA3LjAwNTc1QzYzLjA5NSA3LjAwNTg1IDYyLjIyMTMgOC41ODE2OSA2Mi4yMjEzIDEwLjc0OTlDNjIuMjIxNCAxMi45MTggNjMuMDk1MSAxNC40OTQ5IDY1LjE3NzQgMTQuNDk1QzY2LjA1IDE0LjQ5NSA2Ni43NzU4IDE0LjM0NjUgNjcuODY2OCAxNC4wMDE4TDY4LjM1MTIgMTYuNTY0M0M2Ny4yMzY1IDE2LjkwODkgNjUuOTc2MiAxNy4xNTUyIDY0Ljc2NjMgMTcuMTU1MkM2MC43MjAzIDE3LjE1NTEgNTguNTg4NiAxNC41OTMxIDU4LjU4ODUgMTAuNzQ5OUM1OC41ODg1IDYuOTMxNDQgNjAuNzIwMiA0LjM0NDY4IDY0Ljc2NjMgNC4zNDQ2MloiIGZpbGw9IiNFMDAwMjQiLz4KPHBhdGggaWQ9IkNvbWJpbmVkIFNoYXBlIiBkPSJNMS42MTcxOSA1Ljg5ODc3SDEuNjY2MDJDMi41NTkyNSA1LjAzOTEyIDMuODM4NzkgNC40MjUxNCA1LjMxMTUyIDQuNDI1MTRDOC42NDM2NyA0LjQyNTE5IDEwLjA0NDkgNy4yMjQzIDEwLjA0NDkgMTAuODA5OUMxMC4wNDQ5IDE0LjM5NDkgOC4yODE5NSAxNy4xOTQ3IDQuMzk0NTMgMTcuMTk0N0MyLjcwNDA4IDE3LjE5NDcgMS4xMTAyNiAxNi44MDIzIDAgMTYuMjEyM1YwLjI1MDMzN0gxLjYxNzE5VjUuODk4NzdaTTE3LjE1NzIgNC40MjQxN0MxOS41NzE4IDQuNDI0MTcgMjEuNDA2MSA1LjYwMzI2IDIxLjQwNjIgOC4xODE5OFYxNi45NDk2SDE5Ljk4MjRMMTkuNzg5MSAxNS4zMjg1QzE4LjM4ODkgMTYuNzI4MyAxNy4wNjExIDE3LjE5NDYgMTUuNTE1NiAxNy4xOTQ3QzEzLjUzNTEgMTcuMTk0NyAxMS45NjQ5IDE2LjExNDQgMTEuOTY0OCAxNC4xNDk4QzExLjk2NDggMTEuNDQ4NSAxNC42NDU0IDEwLjA0OTEgMTkuNzg5MSA5LjY1NTYxVjguMjMwODFDMTkuNzg4OSA2LjU4NjEgMTguNzk5NCA1LjYyODM1IDE2LjkxNSA1LjYyODI3QzE1LjY4MzggNS42MjgyNyAxNC4yNTk4IDYuMDQ2MDcgMTMuMDA0OSA2LjUxMzAzTDEyLjY2NiA1LjM1Nzc2QzE0LjIzNTMgNC44MTggMTUuNzU3IDQuNDI0MjUgMTcuMTU3MiA0LjQyNDE3Wk00MS43NTY4IDQuNDI1MTRDNDIuODE5OSA0LjQyNTE1IDQzLjk3ODggNC42NzA4OCA0NC44NzIxIDQuOTY1MThMNDQuNjMwOSA2LjE5MjcyQzQzLjY4OSA1Ljg5NzY4IDQyLjgxOTkgNS43MDI1MSA0MS45MjY4IDUuNzAyNDlDMzguODM1OSA1LjcwMjQ5IDM3Ljc3MjUgOC4wNTk3OCAzNy43NzI1IDEwLjgwOTlDMzcuNzcyNSAxMy41NjA3IDM4LjgzNTkgMTUuOTE3MyA0MS45MjY4IDE1LjkxNzNDNDIuODE5OSAxNS45MTczIDQzLjY4OSAxNS43MjE0IDQ0LjYzMDkgMTUuNDI3MUw0NC44NzIxIDE2LjY1NDZDNDMuOTc4OCAxNi45NDg5IDQyLjgxOTggMTcuMTk0NyA0MS43NTY4IDE3LjE5NDdDMzcuODIxNSAxNy4xOTQ3IDM2LjA4NDEgMTQuNDkzMiAzNi4wODQgMTAuODA5OUMzNi4wODQgNy4xNTEzMyAzNy44MjE0IDQuNDI1MTQgNDEuNzU2OCA0LjQyNTE0Wk01MS4yMDIxIDQuNDI0MTdDNTQuODk2MiA0LjQyNDE3IDU2LjUxMzcgNy4zNzEzMSA1Ni41MTM3IDEwLjgwOTlDNTYuNTEzNyAxNC4yNDc4IDU0Ljg5NjIgMTcuMTk0NyA1MS4yMDIxIDE3LjE5NDdDNDcuNDgzIDE3LjE5NDcgNDUuODg5NiAxNC4yNDc4IDQ1Ljg4OTYgMTAuODA5OUM0NS44ODk3IDcuMzcxMzEgNDcuNDgzIDQuNDI0MTcgNTEuMjAyMSA0LjQyNDE3Wk0zMC4xODM2IDQuNDI1MTRDMzIuNTc0NSA0LjQyNTI0IDMzLjc4MTIgNS43NTE1OCAzMy43ODEyIDguMzc5MjRWMTYuOTQ5NkgzMi4xNjMxVjguNjQ4NzdDMzIuMTYzMSA3LjEwMjE2IDMxLjU2IDUuNzc1NzMgMjkuNTA3OCA1Ljc3NTczQzI3Ljg4OTcgNS43NzU3NiAyNi40MTY1IDYuODU2MzIgMjUuNjY4IDcuNDk0NDhWMTYuOTQ5NkgyNC4wNTE4VjQuNjMzMTVIMjUuNDk5TDI1LjY2OCA2LjM2NDU5QzI2Ljg5OTMgNS4yNTk0NCAyOC4zOTcxIDQuNDI1MTQgMzAuMTgzNiA0LjQyNTE0Wk00Ljc1Njg0IDUuNzc1NzNDMy4yODQyIDUuNzc1NzkgMi4xNzMwNCA2LjUxMjY0IDEuNjE3MTkgNi45Nzg4NVYxNS4zNTI5QzIuNDE0NDMgMTUuNzk1MSAzLjM4MDIxIDE1Ljk5MjUgNC4zNzAxMiAxNS45OTI1QzcuMTk1MTIgMTUuOTkyNSA4LjM1NDM5IDEzLjgwNiA4LjM1NDQ5IDEwLjg4NDFDOC4zNTQ0OSA4LjA1OTY3IDcuMzM5ODQgNS43NzU3MyA0Ljc1Njg0IDUuNzc1NzNaTTUxLjIwMjEgNS42MjgyN0M0OC41MjEgNS42MjgyNyA0Ny41ODAxIDguMDM1MDEgNDcuNTgwMSAxMC44MDk5QzQ3LjU4MDEgMTMuNTg0OCA0OC41MjEgMTUuOTkxNSA1MS4yMDIxIDE1Ljk5MTVDNTMuODgxOSAxNS45OTE1IDU0LjgyNDIgMTMuNTg0OCA1NC44MjQyIDEwLjgwOTlDNTQuODI0MiA4LjAzNTAxIDUzLjg4MTkgNS42MjgyNyA1MS4yMDIxIDUuNjI4MjdaTTE5Ljc4OTEgMTAuNzExM0MxNS43MzMxIDEwLjk1NjggMTMuNTg0MyAxMi4yMzQxIDEzLjU4NCAxMy45MDM3QzEzLjU4NCAxNS4xMDcyIDE0LjQwNTIgMTUuOTE3MyAxNS45NzQ2IDE1LjkxNzNDMTcuNTY4MiAxNS45MTcyIDE4Ljg3MTUgMTUuMTU2MSAxOS43ODkxIDE0LjE3NDJWMTAuNzExM1oiIGZpbGw9IiNGMUY0RjgiLz4KPC9nPgo8L3N2Zz4K" alt="Banco CTT" width="83" height="18">'
    + '<span class="product" role="img" aria-label="MCP Server"><svg width="83" height="12" viewBox="0 0 83 12" aria-hidden="true"><text x="0" y="10" textLength="83" lengthAdjust="spacing">MCP SERVER</text></svg></span>'
    + '<span class="rail-logo" role="img" aria-label="Banco CTT"><img class="logo-light" src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2My41NiA2My41NiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPCEtLSBCYW5jbyBDVFQncyBhcHAgaWNvbiwgImJjdHQiOiB0aGUgYiBhbmQgdGhlIGN0dCBvZiBiYW5jb2N0dC1sb2dvLnN2ZyAoaXRzIHBhdGhzLCB1bmNoYW5nZWQpLCB0aGUgd29yZG1hcmsncyBvd24gc3BhY2UgYmV0d2VlbiB0aGVtLCBvbiBhIHRpbGUgaW4gdGhlIGxpZ2h0IHBhZ2UgY29sb3VyICh0aGUgdG9rZW4gc3VyZmFjZS1wYWdlKTsgdGhlIGxldHRlcnMgMy4zJSBsYXJnZXIgdGhhbiB0aGUgd29yZG1hcmsncywgYXMgbWVhc3VyZWQgb24gQmFuY28gQ1RUJ3MgaWNvbiAtLT4KPHJlY3Qgd2lkdGg9IjYzLjU2IiBoZWlnaHQ9IjYzLjU2IiByeD0iOS42IiBmaWxsPSIjRjdGOUZDIi8+CjxnIHRyYW5zZm9ybT0idHJhbnNsYXRlKDEzLjEzNDQgMjIuNzYxOSkgc2NhbGUoMS4wMzMpIj4KPHBhdGggZD0iTTEuNjE3MTkgNS44OTg3N0gxLjY2NjAyQzIuNTU5MjUgNS4wMzkxMiAzLjgzODc5IDQuNDI1MTQgNS4zMTE1MiA0LjQyNTE0QzguNjQzNjcgNC40MjUxOSAxMC4wNDQ5IDcuMjI0MyAxMC4wNDQ5IDEwLjgwOTlDMTAuMDQ0OSAxNC4zOTQ5IDguMjgxOTUgMTcuMTk0NyA0LjM5NDUzIDE3LjE5NDdDMi43MDQwOCAxNy4xOTQ3IDEuMTEwMjYgMTYuODAyMyAwIDE2LjIxMjNWMC4yNTAzMzdIMS42MTcxOVY1Ljg5ODc3Wk00Ljc1Njg0IDUuNzc1NzNDMy4yODQyIDUuNzc1NzkgMi4xNzMwNCA2LjUxMjY0IDEuNjE3MTkgNi45Nzg4NVYxNS4zNTI5QzIuNDE0NDMgMTUuNzk1MSAzLjM4MDIxIDE1Ljk5MjUgNC4zNzAxMiAxNS45OTI1QzcuMTk1MTIgMTUuOTkyNSA4LjM1NDM5IDEzLjgwNiA4LjM1NDQ5IDEwLjg4NDFDOC4zNTQ0OSA4LjA1OTY3IDcuMzM5ODQgNS43NzU3MyA0Ljc1Njg0IDUuNzc1NzNaIiBmaWxsPSJibGFjayIvPgo8cGF0aCB0cmFuc2Zvcm09InRyYW5zbGF0ZSgtNDYuNDcgMCkiIGQ9Ik03My4xNzA2IDQuNjQxNDlINzUuMzAyNFY3LjMwMjYySDczLjE3MDZWMTMuNTM1QzczLjE3MDYgMTQuMzcyOSA3My43Mjg0IDE0LjYyIDc0LjI2MTQgMTQuNjJDNzQuNTAzNiAxNC42MiA3NS4wMTE3IDE0LjU5NDYgNzUuMzAyNCAxNC41MjA0VjE3LjAwODdDNzQuNTk5NiAxNy4xMzI1IDczLjM4ODkgMTcuMjA1OSA3Mi44MDczIDE3LjIwNTlDNzAuMjg3OSAxNy4yMDU5IDY5LjcwNjcgMTUuODI1OCA2OS43MDY3IDEzLjg3OThWMy4wMzYwMkw3My4xNzA2IDEuMTkzMjVWNC42NDE0OVpNODAuNDM5MSA0LjY0MTQ5SDgyLjU3MTlWNy4zMDI2Mkg4MC40MzkxVjEzLjUzNUM4MC40MzkxIDE0LjM3MjkgODAuOTk2OSAxNC42MiA4MS41Mjk5IDE0LjYyQzgxLjc3MjEgMTQuNjIgODIuMjgxMSAxNC41OTQ3IDgyLjU3MTkgMTQuNTIwNFYxNy4wMDg3QzgxLjg2OTMgMTcuMTMyNSA4MC42NTggMTcuMjA1OSA4MC4wNzY4IDE3LjIwNTlDNzcuNTU3MyAxNy4yMDU5IDc2Ljk3NjIgMTUuODI1OCA3Ni45NzYyIDEzLjg3OThWMy4wMzYwMkw4MC40MzkxIDEuMTkzMjVWNC42NDE0OVpNNjQuNzY2MyA0LjM0NDYyQzY1Ljk3NjIgNC4zNDQ2MiA2Ny4yMzY1IDQuNTkwODMgNjguMzUxMiA0LjkzNTQ0TDY3Ljg2NjggNy40OTc5NEM2Ni43NzU4IDcuMTUzMzUgNjYuMDQ5OSA3LjAwNTc1IDY1LjE3NzQgNy4wMDU3NUM2My4wOTUgNy4wMDU4NSA2Mi4yMjEzIDguNTgxNjkgNjIuMjIxMyAxMC43NDk5QzYyLjIyMTQgMTIuOTE4IDYzLjA5NTEgMTQuNDk0OSA2NS4xNzc0IDE0LjQ5NUM2Ni4wNSAxNC40OTUgNjYuNzc1OCAxNC4zNDY1IDY3Ljg2NjggMTQuMDAxOEw2OC4zNTEyIDE2LjU2NDNDNjcuMjM2NSAxNi45MDg5IDY1Ljk3NjIgMTcuMTU1MiA2NC43NjYzIDE3LjE1NTJDNjAuNzIwMyAxNy4xNTUxIDU4LjU4ODYgMTQuNTkzMSA1OC41ODg1IDEwLjc0OTlDNTguNTg4NSA2LjkzMTQ0IDYwLjcyMDIgNC4zNDQ2OCA2NC43NjYzIDQuMzQ0NjJaIiBmaWxsPSIjRTAwMDI0Ii8+CjwvZz4KPC9zdmc+Cg==" alt="" width="40" height="40"><img class="logo-dark" src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2My41NiA2My41NiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPCEtLSB0aGUgZGFyayB0aGVtZSdzOiBCYW5jbyBDVFQncyByZWQgdmVyc2lvbiwgdGhlIGIgYW5kIHRoZSBjdHQgaW4gd2hpdGUgb24gdGhlIGxvZ28ncyByZWQgKCNFMDAwMjQpLCB0aGUgbGlnaHQgaWNvbidzIHJvdW5kZWQgY29ybmVyczsgdGhlIGxldHRlcnMgMy4zJSBsYXJnZXIgdGhhbiB0aGUgd29yZG1hcmsncywgYXMgbWVhc3VyZWQgb24gQmFuY28gQ1RUJ3MgaWNvbiAtLT4KPHJlY3Qgd2lkdGg9IjYzLjU2IiBoZWlnaHQ9IjYzLjU2IiByeD0iOS42IiBmaWxsPSIjRTAwMDI0Ii8+CjxnIHRyYW5zZm9ybT0idHJhbnNsYXRlKDEzLjEzNDQgMjIuNzYxOSkgc2NhbGUoMS4wMzMpIj4KPHBhdGggZD0iTTEuNjE3MTkgNS44OTg3N0gxLjY2NjAyQzIuNTU5MjUgNS4wMzkxMiAzLjgzODc5IDQuNDI1MTQgNS4zMTE1MiA0LjQyNTE0QzguNjQzNjcgNC40MjUxOSAxMC4wNDQ5IDcuMjI0MyAxMC4wNDQ5IDEwLjgwOTlDMTAuMDQ0OSAxNC4zOTQ5IDguMjgxOTUgMTcuMTk0NyA0LjM5NDUzIDE3LjE5NDdDMi43MDQwOCAxNy4xOTQ3IDEuMTEwMjYgMTYuODAyMyAwIDE2LjIxMjNWMC4yNTAzMzdIMS42MTcxOVY1Ljg5ODc3Wk00Ljc1Njg0IDUuNzc1NzNDMy4yODQyIDUuNzc1NzkgMi4xNzMwNCA2LjUxMjY0IDEuNjE3MTkgNi45Nzg4NVYxNS4zNTI5QzIuNDE0NDMgMTUuNzk1MSAzLjM4MDIxIDE1Ljk5MjUgNC4zNzAxMiAxNS45OTI1QzcuMTk1MTIgMTUuOTkyNSA4LjM1NDM5IDEzLjgwNiA4LjM1NDQ5IDEwLjg4NDFDOC4zNTQ0OSA4LjA1OTY3IDcuMzM5ODQgNS43NzU3MyA0Ljc1Njg0IDUuNzc1NzNaIiBmaWxsPSIjRkZGRkZGIi8+CjxwYXRoIHRyYW5zZm9ybT0idHJhbnNsYXRlKC00Ni40NyAwKSIgZD0iTTczLjE3MDYgNC42NDE0OUg3NS4zMDI0VjcuMzAyNjJINzMuMTcwNlYxMy41MzVDNzMuMTcwNiAxNC4zNzI5IDczLjcyODQgMTQuNjIgNzQuMjYxNCAxNC42MkM3NC41MDM2IDE0LjYyIDc1LjAxMTcgMTQuNTk0NiA3NS4zMDI0IDE0LjUyMDRWMTcuMDA4N0M3NC41OTk2IDE3LjEzMjUgNzMuMzg4OSAxNy4yMDU5IDcyLjgwNzMgMTcuMjA1OUM3MC4yODc5IDE3LjIwNTkgNjkuNzA2NyAxNS44MjU4IDY5LjcwNjcgMTMuODc5OFYzLjAzNjAyTDczLjE3MDYgMS4xOTMyNVY0LjY0MTQ5Wk04MC40MzkxIDQuNjQxNDlIODIuNTcxOVY3LjMwMjYySDgwLjQzOTFWMTMuNTM1QzgwLjQzOTEgMTQuMzcyOSA4MC45OTY5IDE0LjYyIDgxLjUyOTkgMTQuNjJDODEuNzcyMSAxNC42MiA4Mi4yODExIDE0LjU5NDcgODIuNTcxOSAxNC41MjA0VjE3LjAwODdDODEuODY5MyAxNy4xMzI1IDgwLjY1OCAxNy4yMDU5IDgwLjA3NjggMTcuMjA1OUM3Ny41NTczIDE3LjIwNTkgNzYuOTc2MiAxNS44MjU4IDc2Ljk3NjIgMTMuODc5OFYzLjAzNjAyTDgwLjQzOTEgMS4xOTMyNVY0LjY0MTQ5Wk02NC43NjYzIDQuMzQ0NjJDNjUuOTc2MiA0LjM0NDYyIDY3LjIzNjUgNC41OTA4MyA2OC4zNTEyIDQuOTM1NDRMNjcuODY2OCA3LjQ5Nzk0QzY2Ljc3NTggNy4xNTMzNSA2Ni4wNDk5IDcuMDA1NzUgNjUuMTc3NCA3LjAwNTc1QzYzLjA5NSA3LjAwNTg1IDYyLjIyMTMgOC41ODE2OSA2Mi4yMjEzIDEwLjc0OTlDNjIuMjIxNCAxMi45MTggNjMuMDk1MSAxNC40OTQ5IDY1LjE3NzQgMTQuNDk1QzY2LjA1IDE0LjQ5NSA2Ni43NzU4IDE0LjM0NjUgNjcuODY2OCAxNC4wMDE4TDY4LjM1MTIgMTYuNTY0M0M2Ny4yMzY1IDE2LjkwODkgNjUuOTc2MiAxNy4xNTUyIDY0Ljc2NjMgMTcuMTU1MkM2MC43MjAzIDE3LjE1NTEgNTguNTg4NiAxNC41OTMxIDU4LjU4ODUgMTAuNzQ5OUM1OC41ODg1IDYuOTMxNDQgNjAuNzIwMiA0LjM0NDY4IDY0Ljc2NjMgNC4zNDQ2MloiIGZpbGw9IiNGRkZGRkYiLz4KPC9nPgo8L3N2Zz4K" alt="" width="40" height="40"></span>';
  const tablet = window.matchMedia('(min-width: 834px) and (max-width: 1279px)');
  const collapse = Object.assign(document.createElement('button'), { type: 'button', className: 'menu-collapse' });
  function paintCollapse() {
    const open = tablet.matches ? app.classList.contains('menu-expanded') : !app.classList.contains('menu-collapsed');
    collapse.title = open ? 'Collapse the menu' : 'Expand the menu'; collapse.setAttribute('aria-label', collapse.title); collapse.setAttribute('aria-expanded', String(open));
  }
  collapse.addEventListener('click', (ev) => { ev.stopPropagation(); if (tablet.matches) app.classList.toggle('menu-expanded'); else { const c = app.classList.toggle('menu-collapsed'); try { localStorage.setItem('mcp.menuCollapsed', c ? '1' : '0'); } catch (e) {} } paintCollapse(); });
  try { app.classList.toggle('menu-collapsed', localStorage.getItem('mcp.menuCollapsed') === '1'); } catch (e) {}
  document.addEventListener('click', (ev) => { if (app.classList.contains('menu-expanded') && !bar.contains(ev.target)) { app.classList.remove('menu-expanded'); paintCollapse(); } });
  bar.append(logo, collapse);
  const topGroup = Object.assign(document.createElement('div'), { className: 'icon-bar-group' });
  for (const sct of SECTIONS) { topGroup.append(Object.assign(document.createElement('div'), { className: 'menu-section', textContent: sct.title })); for (const e of sct.entries) topGroup.append(menuButton(e)); }
  bar.append(topGroup, Object.assign(document.createElement('div'), { className: 'icon-bar-spacer' }));
  const bottomGroup = Object.assign(document.createElement('div'), { className: 'icon-bar-group icon-bar-bottom' });
  bottomGroup.append(menuButton({ key: 'settings', label: 'Settings', title: 'Settings' }, openSettingsMenu));
  bar.append(bottomGroup);
  paintCollapse();
  // on a phone the bar is the five views: Settings is the header's action icon, opening the same menu
  { const b = document.createElement('button'); b.type = 'button'; b.className = 'header-settings'; b.title = 'Settings'; b.setAttribute('aria-label', 'Settings'); b.innerHTML = ICONS.settings; b.addEventListener('click', (ev) => { ev.stopPropagation(); openSettingsMenu(b); }); $('identity').before(b); }

  // ── the interface language (Cortex's Preferences): the item names the language you would switch TO; the page
  // reloads into it, since it is translated as it is built ──
  const GLOBE = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 2.5 15.3 0 18M12 3c-2.5 2.7-2.5 15.3 0 18"/></svg>';
  function languageItem() {
    const pt = window.uiLanguage && window.uiLanguage() === 'pt';
    const b = document.createElement('button'); b.type = 'button'; b.className = 'identity-item'; b.setAttribute('role', 'menuitem');
    b.innerHTML = `<span class="identity-icon">${GLOBE}</span><span class="notranslate">${pt ? 'English' : 'Português'}</span>`;
    b.addEventListener('click', (ev) => { ev.stopPropagation(); try { localStorage.setItem('mcp.uiLanguage', pt ? 'en' : 'pt'); } catch (e) {} location.reload(); });
    return b;
  }
  // ── the Settings pull-down beside the item (Cortex's settings.js): the theme, then the Settings view ──
  let settingsMenu = null;
  const effectiveTheme = () => document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  function setTheme(t) { document.documentElement.dataset.theme = t; try { localStorage.setItem('mcp_theme', t); } catch (e) {} }
  function closeSettingsMenu() { if (settingsMenu) { settingsMenu.remove(); settingsMenu = null; } }
  function openSettingsMenu(anchor) {
    if (settingsMenu) { closeSettingsMenu(); return; }
    settingsMenu = document.createElement('div'); settingsMenu.className = 'identity-menu settings-menu'; settingsMenu.setAttribute('role', 'menu');
    const dark = effectiveTheme() === 'dark';
    const theme = document.createElement('button'); theme.type = 'button'; theme.className = 'identity-item'; theme.setAttribute('role', 'menuitem');
    theme.innerHTML = `<span class="identity-icon">${dark ? SUN : MOON}</span><span>${dark ? 'Light theme' : 'Dark theme'}</span>`;
    theme.addEventListener('click', () => { setTheme(dark ? 'light' : 'dark'); closeSettingsMenu(); });
    const div = document.createElement('div'); div.className = 'identity-divider';
    const open = document.createElement('button'); open.type = 'button'; open.className = 'identity-item'; open.setAttribute('role', 'menuitem');
    open.innerHTML = '<span class="identity-icon">' + ICONS.settings.split('class="menu-icon" width="24" height="24"').join('width="16" height="16"') + '</span><span>Settings</span>';
    open.addEventListener('click', () => { closeSettingsMenu(); location.hash = 'settings'; });
    const exp = document.createElement('a'); exp.className = 'identity-item'; exp.setAttribute('role', 'menuitem'); exp.href = 'admin/export'; exp.textContent = 'Export the registry';
    settingsMenu.append(theme, languageItem(), div, open, exp);
    document.body.append(settingsMenu);
    const r = anchor.getBoundingClientRect(), phone = matchMedia('(max-width: 833px)').matches;
    if (phone) { settingsMenu.style.top = (r.bottom + 4) + 'px'; settingsMenu.style.right = (window.innerWidth - r.right) + 'px'; settingsMenu.style.left = 'auto'; }
    else { settingsMenu.style.left = (r.right + 8) + 'px'; settingsMenu.style.top = Math.max(8, Math.min(r.top, window.innerHeight - 180)) + 'px'; }
    setTimeout(() => document.addEventListener('click', closeSettingsMenu, { once: true }), 0);
  }

  // ── the signed-in user widget (Cortex's identity.js): the face (photo or initials), the name, a chevron; the pull-down ──
  const initialsOf = (t) => { const w = String(t || '').trim().split(' ').filter(Boolean); return w.length >= 2 ? (w[0][0] + w[1][0]).toUpperCase() : String(t || '?').slice(0, 2).toUpperCase(); };
  function initIdentity(root, me) {
    root.replaceChildren();
    if (!(me && me.via === 'proxy' && me.email)) { root.hidden = true; return; }
    root.hidden = false;
    const button = document.createElement('button'); button.type = 'button'; button.className = 'identity-btn'; button.setAttribute('aria-haspopup', 'menu'); button.setAttribute('aria-expanded', 'false');
    button.title = me.name ? `${me.name} (${me.email})` : me.email;
    const face = document.createElement('span'); face.className = 'identity-face';
    const fallback = document.createElement('span'); fallback.className = 'identity-initials'; fallback.textContent = initialsOf(me.name || me.email); face.append(fallback);
    if (me.picture) { const img = document.createElement('img'); img.className = 'identity-avatar'; img.alt = ''; img.referrerPolicy = 'no-referrer'; img.addEventListener('load', () => { fallback.hidden = true; }); img.addEventListener('error', () => img.remove()); img.src = me.picture; face.append(img); }
    const shown = document.createElement('span'); shown.className = 'identity-btn-name'; shown.textContent = me.name || me.email;
    const chev = document.createElement('span'); chev.className = 'identity-chevron'; chev.setAttribute('aria-hidden', 'true');
    button.append(face, shown, chev); root.append(button);
    const menu = document.createElement('div'); menu.className = 'identity-menu'; menu.setAttribute('role', 'menu'); menu.hidden = true;
    menu.innerHTML = `<div class="identity-who"><div class="identity-name">${esc(me.name || '')}</div><div class="identity-email">${esc(me.email)}${me.admin ? ' · administrator' : ''}</div></div>`;
    const dark = effectiveTheme() === 'dark';
    const theme = document.createElement('button'); theme.type = 'button'; theme.className = 'identity-item'; theme.setAttribute('role', 'menuitemcheckbox');
    theme.innerHTML = `<span class="identity-icon">${dark ? SUN : MOON}</span><span>${dark ? 'Light theme' : 'Dark theme'}</span>`;
    theme.addEventListener('click', (ev) => { ev.stopPropagation(); setTheme(effectiveTheme() === 'dark' ? 'light' : 'dark'); close(); initIdentity(root, me); });
    const div = document.createElement('div'); div.className = 'identity-divider';
    const langItem = languageItem();
    const out = document.createElement('a'); out.className = 'identity-item'; out.setAttribute('role', 'menuitem'); out.href = me.sign_out || '/oauth2-entra/sign_out'; out.textContent = 'Sign out';
    menu.append(theme, langItem, div, out); root.append(menu);
    const close = () => { menu.hidden = true; button.setAttribute('aria-expanded', 'false'); };
    button.addEventListener('click', (ev) => { ev.stopPropagation(); menu.hidden = !menu.hidden; button.setAttribute('aria-expanded', String(!menu.hidden)); });
    document.addEventListener('click', (ev) => { if (!root.contains(ev.target)) close(); });
    document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') close(); });
  }

  // ── the status bar (Cortex's statusbar.js): the view with the focus and its details; at the right, the whole page ──
  const VIEW_TITLES = { overview: 'Overview', tools: 'Tools', skills: 'Skills', apps: 'Apps', activity: 'Activity', settings: 'Settings', help: 'Help' };
  let currentView = 'overview';
  function renderStatus() {
    const s = REG.summary || {}, c = REG.counts || {};
    const details = {
      overview: [`${s.calls || 0} calls in 24 h`, s.errors ? `${s.errors} errors` : 'no errors'],
      tools: [`${c.tools_enabled}/${c.tools} enabled`, appFilter ? `app ${appFilter}` : `${c.apps} apps`, tierFilter ? `${tierFilter} tier` : null, q ? `filter "${q}"` : null],
      skills: [`${c.skills} skills`, `${c.skills_enabled} enabled`],
      apps: [`${c.apps} apps`, `${REG.keys.filter(k => !k.revoked_at).length} active keys`],
      activity: [`window ${win}`, $('act-app').value ? `app ${$('act-app').value}` : null],
      settings: [`${REG.impls.length} implementations`, REG.orphans.length ? `${REG.orphans.length} orphans` : 'no orphans'],
      help: [HELP.title, HELP.page].filter(Boolean),
    }[currentView] || [];
    $('sb-host').textContent = 'mcp-service' + (HEALTH.version ? ' ' + HEALTH.version : '');
    $('sb-focus').textContent = VIEW_TITLES[currentView] || '';
    $('sb-details').replaceChildren(...details.filter(Boolean).map(t => Object.assign(document.createElement('span'), { textContent: t })));
    const b = HEALTH.backends || {}; const states = Object.values(b).map(dotOf); const bad = states.filter(x => x === 'bad').length, warn = states.filter(x => x === 'warn').length;
    $('sb-backends').innerHTML = `<i class="dot ${bad ? 'bad' : warn ? 'warn' : 'ok'}"></i>backends ${bad ? bad + ' down' : warn ? warn + ' degraded' : states.length + ' ok'}`;
    $('sb-keys').textContent = `keys ${HEALTH.app_keys || '…'}`;
    $('sb-record').textContent = `record ${HEALTH.record_args ? 'with arguments' : 'digests'} · ${HEALTH.retention_days || '…'} d`;
    const st = $('status'); st.classList.toggle('on', !!HEALTH.service); st.classList.toggle('off', !HEALTH.service); st.textContent = HEALTH.service ? 'connected' : 'disconnected';
  }

  // ── the top bar's menus (Cortex's MenuBar.js, reduced): a model of menus whose items are rebuilt each time a menu
  // opens, so ticks, the apps and the backends are always current ──
  const dotOf = v => v === 'ok' || v === 'configured' || v === 'mounted' ? 'ok' : (v === 'degraded' ? 'warn' : 'bad');
  const menubar = $('menubar');
  const MENUS = () => [
    { label: 'Catalog', items: [
      { label: 'New tool…', command: () => openEditor('tool') },
      { label: 'New skill…', command: () => openEditor('skill') },
      { sep: true },
      { label: 'Refresh', shortcut: 'R', command: () => loadAll().then(() => toast('Refreshed')) },
      { sep: true },
      { label: 'Export the registry', href: 'admin/export' },
      { label: `Export the ${appFilter || 'filtered'} app`, href: 'admin/export?app=' + encodeURIComponent(appFilter), enabled: !!appFilter },
      { label: 'Import (dry run)…', command: () => { location.hash = 'settings'; $('import').click(); } },
    ] },
    { label: 'Apps', items: REG.apps.length ? REG.apps.flatMap((a, i) => {
        const keys = REG.keys.filter(k => k.app === a && !k.revoked_at).length, tools = REG.tools.filter(t => (t.apps || []).includes(a)).length;
        const rec = appRecord(a);
        return [{ label: rec ? (rec.display_name || a) : a, note: `${!rec ? 'not registered · ' : rec.status === 'retired' ? 'retired · ' : ''}${tools} tools · ${keys ? keys + ' key' + (keys > 1 ? 's' : '') : 'no key'}`, ticked: appFilter === a,
                  command: () => { location.hash = 'app-' + a; setTimeout(() => { const el = $('app-' + a); if (el) el.scrollIntoView({ block: 'start' }); }, 50); } }];
      }).concat([{ sep: true }, { label: 'Show every app in Tools', command: () => { location.hash = 'tools'; setAppFilter(''); }, enabled: !!appFilter }])
      : [{ label: 'No apps yet', enabled: false }] },
    { label: 'Activity', items: [
      ...[['1h', 'Last hour'], ['24h', 'Last 24 hours'], ['7d', 'Last 7 days'], ['30d', 'Last 30 days']].map(([w, l]) => ({ label: l, radio: true, ticked: win === w, command: () => { win = w; [...$('winchips').children].forEach(c => c.setAttribute('aria-pressed', c.dataset.win === w)); location.hash = 'activity'; loadActivity(true); renderStatus(); } })),
      { sep: true },
      { label: 'Only errors', checkbox: true, ticked: $('act-ok').value === 'false', command: () => { $('act-ok').value = $('act-ok').value === 'false' ? '' : 'false'; location.hash = 'activity'; loadActivity(true); } },
      { sep: true },
      { label: 'Export CSV', href: $('csv').getAttribute('href') },
    ] },
    { label: 'View', items: [
      ...views.filter(v => v !== 'help').map(v => ({ label: VIEW_TITLES[v], radio: true, ticked: currentView === v, command: () => { location.hash = v; } })),
      { sep: true },
      { label: app.classList.contains('menu-collapsed') ? 'Expand the menu' : 'Collapse the menu', command: () => collapse.click() },
      { label: 'Dark theme', checkbox: true, ticked: effectiveTheme() === 'dark', command: () => setTheme(effectiveTheme() === 'dark' ? 'light' : 'dark') },
    ] },
    { label: 'Monitoring', items: [
      { label: 'mcp-service', note: HEALTH.service ? 'ok' : 'unreachable', dot: HEALTH.service ? 'ok' : 'bad', command: () => { location.hash = 'overview'; } },
      ...Object.entries(HEALTH.backends || {}).map(([k, v]) => ({ label: k, note: v, dot: dotOf(v), command: () => { location.hash = 'settings'; } })),
      { sep: true },
      { label: 'App keys', note: HEALTH.app_keys || '…', command: () => { location.hash = 'settings'; } },
      { label: 'Needs attention', note: `${ATTENTION.length || 'nothing'}`, command: () => { location.hash = 'overview'; } },
      { sep: true },
      { label: 'Refresh health', command: () => api('admin/health').then(h => { HEALTH = h; renderStatus(); toast('Health refreshed'); }) },
    ] },
    { label: 'Help', items: [
      { label: 'User Manual', command: () => openManual('manual') },
      { label: 'Integration Guide', command: () => openManual('guide') },
      { label: 'Technical Architecture', command: () => openManual('architecture') },
      { label: 'Keyboard Shortcuts…', command: () => openManual('manual', '01-05-keyboard-shortcuts.md') },
      { sep: true },
      { label: 'Connect an app or an agent…', command: () => openManual('guide', '01-overview.md') },
      { label: 'The MCP endpoint', note: `${PUBLIC}/mcp/{app}/`, command: () => copy(`${PUBLIC}/mcp/`) },
      { sep: true },
      { label: `About mcp-service ${HEALTH.version || ''}`, command: () => toast(`mcp-service ${HEALTH.version || ''} · ${REG.impls.length} implementations · ${(HEALTH.backends ? Object.keys(HEALTH.backends).length : 0)} backends`) },
    ] },
  ];
  let ATTENTION = [];
  let openMenu = null;
  function closeMenus() { menubar.querySelectorAll('.menu.open').forEach(m => m.classList.remove('open')); openMenu = null; }
  function buildDropdown(menu, items) {
    const dd = document.createElement('div'); dd.className = 'dropdown';
    for (const it of items) {
      if (it.sep) { dd.append(Object.assign(document.createElement('div'), { className: 'menubar-sep' })); continue; }
      const el = document.createElement(it.href ? 'a' : 'div'); el.className = 'menu-item' + (it.ticked ? ' ticked' : '') + (it.enabled === false ? ' disabled' : '');
      if (it.href) { el.href = it.href; el.style.textDecoration = 'none'; el.style.color = 'inherit'; }
      const left = document.createElement('span'); const check = document.createElement('span'); check.className = 'check';
      if (it.dot) check.innerHTML = `<i class="dot ${it.dot}"></i>`; else if (it.ticked) check.textContent = it.radio ? '●' : '✓';
      left.append(check, it.label);
      if (it.note) { const n = document.createElement('span'); n.className = 'menu-note'; n.textContent = it.note; left.append(' ', n); }
      const right = document.createElement('span'); if (it.shortcut) { right.className = 'shortcut'; right.textContent = it.shortcut; }
      el.append(left, right);
      if (it.command) el.addEventListener('click', (ev) => { ev.stopPropagation(); closeMenus(); it.command(); });
      else if (it.href) el.addEventListener('click', () => closeMenus());
      dd.append(el);
    }
    return dd;
  }
  function renderMenubar() {
    menubar.replaceChildren();
    MENUS().forEach((m, i) => {
      const menu = document.createElement('div'); menu.className = 'menu';
      const btn = document.createElement('div'); btn.className = 'menu-btn'; btn.textContent = m.label; btn.setAttribute('role', 'button'); btn.tabIndex = 0;
      btn.addEventListener('click', (ev) => { ev.stopPropagation(); const was = menu.classList.contains('open'); closeMenus(); if (!was) { menu.querySelector('.dropdown')?.remove(); menu.append(buildDropdown(m, MENUS()[i].items)); menu.classList.add('open'); openMenu = i; } });
      btn.addEventListener('mouseenter', () => { if (openMenu !== null && openMenu !== i) btn.click(); });
      menu.append(btn);
      menubar.append(menu);
    });
  }
  document.addEventListener('click', () => { closeMenus(); document.querySelector('#app > header').classList.remove('menus-open'); $('menu-toggle').setAttribute('aria-expanded', 'false'); });
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') { closeMenus(); return; }
    if (ev.altKey && !ev.ctrlKey && !ev.metaKey && ev.key.length === 1) {      // Alt+C, Alt+A, Alt+T, Alt+V, Alt+M, Alt+H
      const i = MENUS().findIndex(m => m.label[0].toLowerCase() === ev.key.toLowerCase());
      if (i >= 0 && menubar.children[i]) { ev.preventDefault(); menubar.children[i].querySelector('.menu-btn').click(); }
    }
  });
  $('menu-toggle').addEventListener('click', (ev) => { ev.stopPropagation(); const hd = document.querySelector('#app > header'); const open = hd.classList.toggle('menus-open'); $('menu-toggle').setAttribute('aria-expanded', String(open)); if (open) { closeMenus(); menubar.querySelectorAll('.menu').forEach((m, i) => { m.querySelector('.dropdown')?.remove(); m.append(buildDropdown(m, MENUS()[i].items)); m.classList.add('open'); }); } });

  // ── Help: the manuals, as Cortex's menu-commands.js opens its User Manual and Developer SDK: README.md is the
  // contents (chapters "## n. Title", pages "- [Title](file.md)"); a page's links open in place; "Next" follows ──
  const MANUALS = {
    manual: { root: (window.uiLanguage && window.uiLanguage() === 'pt') ? 'admin/help/manual/pt/' : 'admin/help/manual/', title: 'User Manual' },
    guide: { root: 'admin/help/guide/', title: 'Integration Guide' },
    architecture: { doc: 'admin/docs/architecture', title: 'Technical Architecture' },
  };
  let HELP = { which: null, title: '', page: '' };
  const contentsCache = {};
  async function manualContents(which) {
    if (contentsCache[which]) return contentsCache[which];
    const r = await fetch(MANUALS[which].root + 'README.md', { cache: 'no-cache' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const out = [];
    for (const line of (await r.text()).split('\n')) {
      if (line.startsWith('## ')) out.push({ chapter: line.slice(3).trim(), pages: [] });
      else if (line.startsWith('- [') && out.length) { const mid = line.indexOf(']('), end = line.indexOf(')', mid); if (mid > 0 && end > mid) out.at(-1).pages.push({ title: line.slice(3, mid), file: line.slice(mid + 2, end) }); }
    }
    contentsCache[which] = out;
    return out;
  }
  const render = (md) => DOMPurify.sanitize(marked.parse(md || ''));
  async function openManual(which, page) {
    const m = MANUALS[which]; if (!m) return;
    page = page || (m.doc ? '' : 'README.md');
    const url = m.doc || (m.root + page);
    let md;
    try { const r = await fetch(url, { cache: 'no-cache' }); if (!r.ok) throw new Error(`HTTP ${r.status}`); md = await r.text(); }
    catch (e) { toast(`Could not load ${m.title}: ${e.message}`); return; }
    const article = $('help-article'); article.innerHTML = render(md); article.dataset.page = page;
    for (const img of article.querySelectorAll('img')) { const src = img.getAttribute('src') || ''; if (src && !src.includes(':') && !src.startsWith('/')) img.src = (m.root || '') + src; img.loading = 'lazy'; }
    const title = article.querySelector('h1')?.textContent || m.title;
    HELP = { which, title: m.title, page: page && page !== 'README.md' ? title : (m.doc ? title : 'Contents') };
    $('help-back').hidden = !page || page === 'README.md';
    $('help-crumb').textContent = m.title;
    // the contents column: a manual's chapters and pages (the open one marked); a document's own sections
    const col = $('help-contents'); col.replaceChildren();
    if (m.doc) {
      col.append(Object.assign(document.createElement('div'), { className: 'eyebrow', textContent: m.title }));
      article.querySelectorAll('h2').forEach((h, i) => { h.id = h.id || 'sec-' + i; const a = document.createElement('a'); a.href = '#'; a.textContent = h.textContent; a.addEventListener('click', (ev) => { ev.preventDefault(); h.scrollIntoView({ block: 'start', behavior: 'smooth' }); }); col.append(a); });
    } else {
      const toc = document.createElement('a'); toc.href = '#help-' + which; toc.textContent = 'Contents'; toc.className = page === 'README.md' ? 'current' : ''; col.append(toc);
      try {
        const chapters = await manualContents(which);
        for (const c of chapters) { if (!c.pages.length) continue; col.append(Object.assign(document.createElement('div'), { className: 'eyebrow', textContent: c.chapter })); for (const pg of c.pages) { const a = document.createElement('a'); a.href = `#help-${which}/${pg.file}`; a.textContent = pg.title; if (pg.file === page) a.className = 'current'; col.append(a); } }
        const all = chapters.flatMap(c => c.pages), at = all.findIndex(pg => pg.file === page), following = all[at + 1];
        const next = $('help-next'); next.replaceChildren();
        if (following) { const b = document.createElement('button'); b.type = 'button'; b.className = 'manual-next-link'; b.innerHTML = `<span class="manual-next-label">Next:</span> <span class="manual-next-title">${esc(following.title)}</span>`; b.addEventListener('click', () => { location.hash = `help-${which}/${following.file}`; }); next.append(b); }
        else if (page !== 'README.md') next.append(Object.assign(document.createElement('span'), { className: 'manual-next-end', textContent: 'End of the manual' }));
      } catch (e) { col.append(Object.assign(document.createElement('div'), { className: 'err', textContent: e.message })); }
    }
    if (m.doc) $('help-next').replaceChildren();
    // links to another page of the manual open in place
    article.onclick = (e) => { const a = e.target.closest('a[href]'); const href = a?.getAttribute('href') || ''; if (href.endsWith('.md') && !href.includes('/') && !href.includes(':')) { e.preventDefault(); location.hash = `help-${which}/${href}`; } };
    const want = m.doc ? 'help-' + which : `help-${which}/${page}`;
    if (location.hash.slice(1) !== want && !(page === 'README.md' && location.hash.slice(1) === 'help-' + which)) history.replaceState(null, '', '#' + want);
    show('help'); $('below-bar').scrollTo(0, 0);
  }

  // ── header: nothing to draw now; the monitoring lives in the Monitoring menu, the status bar and Settings ──
  function renderHeader() { renderStatus(); }
  function renderWho() {
    initIdentity($('identity'), ME);
    tokenEl.hidden = !!(ME.via === 'proxy' && ME.admin);   // the proxy proved who they are: no token to paste
  }
  const canWrite = () => ME.admin || !!tokenEl.value;
  function renderNav() { renderStatus(); }
  const views = ['overview', 'tools', 'skills', 'apps', 'activity', 'settings', 'help'];
  function show(view) {
    currentView = view;
    views.forEach(v => $('view-' + v).classList.toggle('active', v === view));
    Object.entries(buttons).forEach(([k, b]) => b.classList.toggle('icon-bar-btn-active', k === view));
    if (view === 'activity') loadActivity(true);
    $('below-bar').scrollTo(0, 0);
    renderStatus();
  }
  function route() {
    const h = (location.hash || '#overview').slice(1);
    if (h.startsWith('tool-')) { show('tools'); openTool(h.slice(5)); return; }
    if (h.startsWith('skill-')) { show('skills'); openSkill(h.slice(6)); return; }
    if (h.startsWith('try-')) { show('tools'); openTool(h.slice(4)); selectTab('t-try'); return; }
    if (h.startsWith('connect-')) { show('tools'); openTool(h.slice(8)); selectTab('t-connect'); return; }
    if (h.startsWith('app-')) { show('apps'); return; }
    if (h.startsWith('app=')) { show('tools'); setAppFilter(h.slice(4)); return; }
    if (h.startsWith('help-')) { const rest = h.slice(5); const slash = rest.indexOf('/'); const which = slash < 0 ? rest : rest.slice(0, slash); const page = slash < 0 ? undefined : rest.slice(slash + 1); if (MANUALS[which]) { openManual(which, page); return; } }
    if (h.startsWith('menu-')) { show('overview'); const i = MENUS().findIndex(m => m.label.toLowerCase() === h.slice(5)); if (i >= 0) setTimeout(() => menubar.children[i].querySelector('.menu-btn').click(), 300); return; }
    show(views.includes(h) ? h : 'overview');
  }
  window.addEventListener('hashchange', route);

  $('sb-backends').addEventListener('click', () => { location.hash = 'settings'; });
  // ── overview ──
  async function renderOverview() {
    const s = REG.summary || {}, c = REG.counts || {};
    const keyed = new Set(REG.keys.filter(k => !k.revoked_at).map(k => k.app));
    $('tiles').innerHTML = `
      <a class="tile" href="#tools"><span class="eyebrow">Tools</span><span class="big num">${c.tools_enabled} <span class="muted" style="font-size:14px;font-weight:400">/ ${c.tools} enabled</span></span><span class="sub">${c.apps} apps · ${REG.impls.length} implementations</span></a>
      <a class="tile" href="#skills"><span class="eyebrow">Skills</span><span class="big num">${c.skills}</span><span class="sub">${c.skills_enabled} enabled · served as prompts and resources</span></a>
      <a class="tile" href="#apps"><span class="eyebrow">Apps</span><span class="big num">${c.apps}</span><span class="sub">${REG.apps.filter(a => keyed.has(a)).length} with an active key · ${REG.apps.filter(a => !keyed.has(a)).length} without</span></a>
      <a class="tile" href="#activity"><span class="eyebrow">Calls · last 24 h</span><span class="big num">${s.calls || 0}</span><span class="sub">${s.errors ? `<span style="color:var(--bad)">${s.errors} errors (${(100 * s.errors / s.calls).toFixed(1)}%)</span>` : 'no errors'} · p95 ${ms(s.p95_ms)}</span></a>`;
    try {
      const a = await api('admin/attention'); ATTENTION = a.items;
      $('attention').innerHTML = a.items.length ? a.items.map(i => `<li><span class="stripe ${i.level}"></span><div><b>${esc(i.title)}</b><div class="why">${esc(i.why)}</div></div><a class="btn sm" href="${esc(i.go)}">Open</a></li>`).join('') : '<li><span class="stripe info"></span><div>Nothing needs a decision.</div><span></span></li>';
    } catch (e) { $('attention').innerHTML = `<li><span class="stripe bad"></span><div>${esc(e.message)}</div><span></span></li>`; }
    try {
      const r = await api('activity?limit=8&window=30d');
      $('recent').tBodies[0].innerHTML = r.calls.length ? r.calls.map(x => actRow(x, true)).join('') : '<tr><td colspan="5" class="muted">No calls recorded yet.</td></tr>';
    } catch (e) {}
  }
  const actRow = (r, short, noTool) => `<tr><td class="muted time" title="${esc(r.ts)}">${ago(r.ts)}</td><td><span class="pill app">${esc(r.app || '?')}</span></td>${noTool ? '' : `<td class="mono">${esc(r.tool)}</td>`}${short ? '' : `<td class="mono muted">${esc(r.caller)}</td>`}<td class="muted">${esc(r.on_behalf_of || '—')}</td>${short ? '' : `<td><span class="pill server">${esc(r.transport)}</span></td><td class="num">${ms(r.duration_ms)}</td>`}<td>${r.ok ? '<span class="pill ok">ok</span>' : `<span class="pill err" title="${esc(r.error)}">error</span>${short ? '' : ` <span class="muted" style="font-size:12px">${esc(r.error)}</span>`}`}</td></tr>`;

  // ── tools ──
  function setAppFilter(a) { appFilter = a || ''; [...$('appchips').children].forEach(c => c.setAttribute('aria-pressed', c.dataset.app === appFilter)); renderTools(); renderStatus(); }
  $('q').addEventListener('input', e => { q = e.target.value.toLowerCase(); renderTools(); renderStatus(); });
  $('enabledonly').addEventListener('click', e => { enabledOnly = !enabledOnly; e.currentTarget.setAttribute('aria-pressed', enabledOnly); renderTools(); });
  $('appchips').addEventListener('click', e => { const b = e.target.closest('.chip'); if (b) setAppFilter(b.dataset.app); });
  $('tierchips').addEventListener('click', e => { const b = e.target.closest('.chip'); if (!b) return; tierFilter = b.dataset.tier; [...$('tierchips').children].forEach(c => c.setAttribute('aria-pressed', c === b)); renderTools(); });
  function renderTools() {
    $('appchips').innerHTML = [''].concat(REG.apps).map(a => `<button class="chip" data-app="${esc(a)}" aria-pressed="${a === appFilter}">${a || 'all apps'}</button>`).join('');
    const rows = REG.tools.filter(t => (!appFilter || (t.apps || []).includes(appFilter)) && (!tierFilter || t.tier === tierFilter) && (!enabledOnly || t.enabled) && (!q || [t.name, t.description, t.impl, (t.apps || []).join(' ')].join(' ').toLowerCase().includes(q)));
    $('tooltable').tBodies[0].innerHTML = rows.length ? rows.map(t => `<tr class="row" data-name="${esc(t.name)}" aria-selected="${current && current.kind === 'tool' && current.name === t.name}">
      <td class="name">${esc(t.name)}<span class="desc">${esc(t.description)}</span></td><td>${pillApps(t.apps)}</td>
      <td><span class="pill ${t.tier}">${t.tier}</span></td><td><span class="pill ${execOf(t)}">${execOf(t)}</span></td>
      <td class="mono muted">${esc(t.impl)}</td><td class="${t.last_used ? 'muted' : 'never'}">${t.last_used ? ago(t.last_used) : (execOf(t) === 'client' ? '<span class="muted">client</span>' : 'never')}</td><td class="num">${t.calls_24h || 0}</td>
      <td><button class="toggle" aria-checked="${t.enabled}" aria-label="Enabled" data-toggle="tool" data-name="${esc(t.name)}"></button></td></tr>`).join('') : '<tr><td colspan="8" class="empty">No tool matches. Clear the filter or create one.</td></tr>';
  }
  async function toggleEnabled(kind, name, el) {
    const rec = (kind === 'tool' ? REG.tools : REG.skills).find(x => x.name === name);
    try { await api(`${kind}s/${encodeURIComponent(name)}/enabled`, 'PATCH', { enabled: !rec.enabled }); toast(`${name} ${!rec.enabled ? 'enabled' : 'disabled'}`); await loadAll(); }
    catch (e) { toast(e.message); }
  }
  document.addEventListener('click', e => {
    const tg = e.target.closest('[data-toggle]');
    if (tg) { e.stopPropagation(); toggleEnabled(tg.dataset.toggle, tg.dataset.name, tg); return; }
    const row = e.target.closest('tr.row[data-name]');
    if (row && row.closest('#tooltable')) { location.hash = 'tool-' + row.dataset.name; return; }
    if (row && row.closest('#skilltable')) { location.hash = 'skill-' + row.dataset.name; return; }
    const cp = e.target.closest('[data-copy]'); if (cp) { copy($(cp.dataset.copy).textContent); }
  });

  // ── drawer plumbing ──
  function openDrawer(name, p1, p2, tabs, build) {
    $('d-name').textContent = name; $('d-p1').className = 'pill ' + p1[0]; $('d-p1').textContent = p1[1]; $('d-p2').className = 'pill ' + p2[0]; $('d-p2').textContent = p2[1];
    $('d-p2').hidden = !p2[1];
    $('tabs').innerHTML = tabs.map((t, i) => `<button role="tab" aria-selected="${i === 0}" data-tab="${t[0]}">${t[1]}</button>`).join('');
    $('d-body').innerHTML = tabs.map((t, i) => `<div role="tabpanel" id="${t[0]}" class="${i === 0 ? 'active' : ''}"></div>`).join('');
    build();
    $('drawer').classList.add('open'); $('drawer').setAttribute('aria-hidden', 'false'); $('scrim').style.display = 'block';
  }
  function closeDrawer() { $('drawer').classList.remove('open'); $('drawer').setAttribute('aria-hidden', 'true'); $('scrim').style.display = 'none'; current = null; renderTools(); renderSkills(); if (location.hash.startsWith('#tool-') || location.hash.startsWith('#skill-')) history.replaceState(null, '', location.hash.startsWith('#tool-') ? '#tools' : '#skills'); }
  $('close').addEventListener('click', closeDrawer); $('scrim').addEventListener('click', closeDrawer);
  function selectTab(id) { document.querySelectorAll('#tabs [role=tab]').forEach(b => b.setAttribute('aria-selected', b.dataset.tab === id)); document.querySelectorAll('#d-body [role=tabpanel]').forEach(p => p.classList.toggle('active', p.id === id)); }
  $('tabs').addEventListener('click', e => { const b = e.target.closest('[role=tab]'); if (b) selectTab(b.dataset.tab); });

  // ── snippets ──
  function snippets(app, tool) {
    const key = tokenEl.value && tokenEl.value.startsWith('mcpk_') ? tokenEl.value : 'mcpk_…';
    const url = `${PUBLIC}/mcp/${app}/`;
    const s = {
      curl: tool ? `curl -s -X POST '${PUBLIC}/tools/${tool.name}/invoke?app=${app}' \\\n  -H 'Authorization: Bearer ${key}' -H 'X-On-Behalf-Of: person@example.com' \\\n  -H 'content-type: application/json' -d '{"args": ${JSON.stringify(exampleArgs(tool))}}'` : `curl -s '${PUBLIC}/tools/manifest?app=${app}' -H 'Authorization: Bearer ${key}'`,
      code: `claude mcp add --transport http ${app} ${url} \\\n  --header "Authorization: Bearer ${key}"`,
      desktop: JSON.stringify({ mcpServers: { [app]: { type: 'http', url, headers: { Authorization: `Bearer ${key}` } } } }, null, 2),
      python: tool ? `r = httpx.post(f"{BASE}/tools/${tool.name}/invoke", params={"app": "${app}"},\n               headers={"Authorization": f"Bearer {KEY}", "X-On-Behalf-Of": user},\n               json={"args": args}, timeout=60)\nr.raise_for_status(); result = r.json()["result"]` : `r = httpx.get(f"{BASE}/tools/manifest", params={"app": "${app}"}, headers={"Authorization": f"Bearer {KEY}"})`,
    };
    s.oauth = `claude mcp add --transport http ${app} ${url}
# or, in claude.ai: Settings › Connectors › Add custom connector › ${url}
# the client discovers the OAuth server, you sign in with Microsoft and allow it; no key to paste`;
    s.machine = `# a program: a machine client of app ${app} (Apps › New machine client), the client credentials grant
TOKEN=$(curl -s -X POST ${PUBLIC}/oauth/token -d grant_type=client_credentials -d client_id=mcpm_… -d client_secret=… | jq -r .access_token)
curl -s -X POST '${PUBLIC}/tools/${tool ? tool.name : '<tool>'}/invoke?app=${app}' -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' -d '{"args": ${tool ? JSON.stringify(exampleArgs(tool)) : '{}'}}'`;
    return `<p class="hint" style="margin:0">Snippets for app <code>${esc(app)}</code>. With OAuth the client signs you in; with a key, paste it (mcpk_…) in the bar to fill the placeholder.</p>
      ${[['OAuth 2.1 · any MCP client', 'oauth'], ['OAuth 2.1 · a program (client credentials)', 'machine'], ['curl · REST invoke with a key', 'curl'], ['Claude Code · with a key', 'code'], ['Claude Desktop · mcpServers', 'desktop'], ['Python · httpx', 'python']].map(([l, k]) => `<div class="snip"><div class="label"><span class="eyebrow">${l}</span><button class="btn sm" data-copy="sn-${k}">Copy</button></div><pre id="sn-${k}">${esc(s[k])}</pre></div>`).join('')}`;
  }
  function exampleArgs(tool) {
    const out = {}; const props = (tool.input_schema || {}).properties || {};
    for (const [k, p] of Object.entries(props)) { if ((tool.input_schema.required || []).includes(k)) out[k] = p.default != null ? p.default : (p.type === 'integer' || p.type === 'number' ? 1 : p.type === 'boolean' ? true : (p.enum ? p.enum[0] : 'example')); }
    return out;
  }

  // ── diff (line LCS) ──
  function diffLines(a, b) {
    const A = a.split('\n'), B = b.split('\n'), n = A.length, m = B.length;
    const L = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
    for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) L[i][j] = A[i] === B[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
    const out = []; let i = 0, j = 0;
    while (i < n && j < m) { if (A[i] === B[j]) { out.push(['', A[i]]); i++; j++; } else if (L[i + 1][j] >= L[i][j + 1]) { out.push(['del', A[i++]]); } else { out.push(['add', B[j++]]); } }
    while (i < n) out.push(['del', A[i++]]); while (j < m) out.push(['add', B[j++]]);
    return out;
  }
  const pretty = o => JSON.stringify(o, null, 2);
  const stripMeta = r => { const c = { ...r }; delete c.last_used; delete c.calls_24h; delete c.errors_24h; delete c.updated_at; delete c.version; return c; };
  const diffHtml = (a, b) => { const d = diffLines(pretty(a), pretty(b)); return d.some(x => x[0]) ? `<div class="diff">${d.map(x => `<div class="${x[0]}">${x[0] === 'del' ? '- ' : x[0] === 'add' ? '+ ' : '  '}${esc(x[1])}</div>`).join('')}</div>` : '<p class="hint">No change.</p>'; };

  // ── tool drawer ──
  function openTool(name) {
    const t = REG.tools.find(x => x.name === name); if (!t) { toast('Unknown tool ' + name); return; }
    current = { kind: 'tool', name }; renderTools();
    const props = (t.input_schema || {}).properties || {}, req = (t.input_schema || {}).required || [];
    openDrawer(t.name, [t.tier, t.tier], [execOf(t), execOf(t)],
      [['t-overview', 'Overview'], ['t-schema', 'Schema'], ['t-try', 'Try it'], ['t-connect', 'Connect'], ['t-activity', 'Activity'], ['t-history', 'History'], ['t-edit', 'Edit']], () => {
      const impl = REG.impls.includes(t.impl) ? `<code>${esc(t.impl)}</code> · shipped` : (execOf(t) === 'client' ? `<code>${esc(t.impl)}</code> · executed by the app's page, never here` : `<code>${esc(t.impl)}</code> · <span class="err">no implementation with this name</span>`);
      $('t-overview').innerHTML = `<p style="margin:0">${esc(t.description)}</p><dl class="kv">
        <dt>Offered to</dt><dd>${pillApps(t.apps)}</dd>
        <dt>Endpoints</dt><dd class="mono">${(t.apps || []).map(a => `/mcp/${esc(a)}/ · POST /tools/${esc(t.name)}/invoke?app=${esc(a)}`).join('<br>')}</dd>
        <dt>Implementation</dt><dd>${impl}</dd>
        <dt>Annotations</dt><dd><code>readOnlyHint: ${t.tier === 'read'}</code> · <code>destructiveHint: ${t.tier === 'write' && !!t.destructive}</code> · <code>idempotentHint: ${t.tier === 'read' || !!t.idempotent}</code></dd>
        <dt>Calls</dt><dd>${t.calls_24h || 0} in 24 h${t.errors_24h ? `, ${t.errors_24h} errors` : ''} · last used ${t.last_used ? ago(t.last_used) : 'never'}</dd>
        <dt>Version</dt><dd>v${t.version} · updated ${day(t.updated_at)} · created ${day(t.created_at)}</dd></dl>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><button class="toggle" aria-checked="${t.enabled}" aria-label="Enabled" data-toggle="tool" data-name="${esc(t.name)}"></button><span>Enabled</span><button class="btn sm" id="d-edit" style="margin-left:auto">Edit</button><button class="btn sm danger" id="d-del">Delete</button></div><div id="d-delconfirm"></div>`;
      $('d-edit').addEventListener('click', () => selectTab('t-edit'));
      $('d-del').addEventListener('click', () => confirmDelete('tool', t));
      $('t-schema').innerHTML = `<div class="label" style="display:flex;justify-content:space-between;align-items:center"><h3>Input schema</h3><button class="btn sm" id="d-raw">Raw JSON</button></div>
        <div class="tablewrap" id="d-proptable"><table class="proptable"><thead><tr><th>Property</th><th>Type</th><th>Required</th><th>Default</th><th>Description</th></tr></thead><tbody>${Object.keys(props).length ? Object.entries(props).map(([k, p]) => `<tr><td class="mono">${esc(k)}</td><td>${esc(p.type || (p.enum ? 'enum' : 'any'))}</td><td>${req.includes(k) ? 'yes' : ''}</td><td class="mono">${esc(p.default != null ? JSON.stringify(p.default) : '')}</td><td class="muted">${esc(p.description || '')}</td></tr>`).join('') : '<tr><td colspan="5" class="muted">No properties: this tool takes no arguments.</td></tr>'}</tbody></table></div>
        <pre id="d-rawpre" hidden>${esc(pretty(t.input_schema))}</pre><p class="hint">${t.output_schema ? 'Output schema declared: results are returned as structured content too.' : 'Output schema: none declared. Results are returned as text.'}</p>${t.output_schema ? `<pre>${esc(pretty(t.output_schema))}</pre>` : ''}`;
      $('d-raw').addEventListener('click', () => { const p = $('d-rawpre'); p.hidden = !p.hidden; $('d-proptable').hidden = !p.hidden; });
      // Try it
      const field = (k, p) => { const d = p.default != null ? JSON.stringify(p.default) : ''; if (p.enum) return `<select class="field" data-arg="${esc(k)}" data-type="enum"><option value="">(none)</option>${p.enum.map(v => `<option>${esc(v)}</option>`).join('')}</select>`; if (p.type === 'boolean') return `<select class="field" data-arg="${esc(k)}" data-type="boolean"><option value="">(none)</option><option>false</option><option>true</option></select>`; if (p.type === 'integer' || p.type === 'number') return `<input class="field" type="number" data-arg="${esc(k)}" data-type="${p.type}" placeholder="${esc(d)}">`; if (p.type === 'string' || !p.type) return `<input class="field" data-arg="${esc(k)}" data-type="string" placeholder="${esc(d || p.description || '')}">`; return `<textarea data-arg="${esc(k)}" data-type="json" placeholder="JSON ${esc(p.type)}"></textarea>`; };
      $('t-try').innerHTML = execOf(t) === 'client' ? '<p class="hint">This tool is executed by the app\'s own page. The service only serves its schema, so there is nothing to run here.</p>' : `<div class="form" id="d-form"><label>app<select class="field" id="d-app">${(t.apps || []).map(a => `<option>${esc(a)}</option>`).join('')}</select></label>${Object.entries(props).map(([k, p]) => `<label>${esc(k)}${req.includes(k) ? ' *' : ''}${field(k, p)}<span class="hint">${esc(p.description || '')}</span></label>`).join('') || '<p class="hint">No arguments. Run calls the tool with an empty object.</p>'}</div>
        <div id="d-confirm" class="confirm" ${t.tier === 'write' ? '' : 'hidden'}><span>This is a <b>write-tier</b> tool${t.destructive ? ' marked destructive' : ''}. Running it changes something outside this service.</span><label><input type="checkbox" id="d-ack"> I understand, run it against <code id="d-confirm-app">${esc((t.apps || [])[0] || '')}</code></label></div>
        <div style="display:flex;gap:8px"><button class="btn primary" id="d-run">Run</button><button class="btn" id="d-copycurl">Copy as curl</button></div>
        <div class="result" id="d-result" hidden><div class="meta" id="d-meta"></div><pre id="d-resultpre"></pre></div>`;
      if (execOf(t) !== 'client') {
        const args = () => { const out = {}; let bad = null; document.querySelectorAll('#d-form [data-arg]').forEach(el => { const v = el.value; if (v === '') return; const ty = el.dataset.type; try { out[el.dataset.arg] = ty === 'integer' ? parseInt(v, 10) : ty === 'number' ? parseFloat(v) : ty === 'boolean' ? v === 'true' : ty === 'json' ? JSON.parse(v) : v; } catch (e) { bad = el.dataset.arg; } }); return { out, bad }; };
        $('d-app').addEventListener('change', () => { $('d-confirm-app').textContent = $('d-app').value; });
        $('d-copycurl').addEventListener('click', () => { const a = args(); copy(`curl -s -X POST '${PUBLIC}/tools/${t.name}/invoke?app=${$('d-app').value}' -H 'Authorization: Bearer mcpk_…' -H 'content-type: application/json' -d '${JSON.stringify({ args: a.out })}'`); });
        $('d-run').addEventListener('click', async () => {
          if (t.tier === 'write' && !$('d-ack').checked) { toast('Tick the confirmation to run a write-tier tool'); return; }
          const a = args(); if (a.bad) { toast(`${a.bad}: not valid JSON`); return; }
          if (!canWrite()) { toast('Paste the admin token in the bar, or sign in on the domain: Try it runs as you'); return; }
          const started = performance.now(); $('d-run').disabled = true;
          try {
            const r = await fetch(`tools/${encodeURIComponent(t.name)}/invoke?app=${encodeURIComponent($('d-app').value)}`, { method: 'POST', headers: headers(true), body: JSON.stringify({ args: a.out }) });
            let data = null; try { data = await r.json(); } catch (e) { data = await r.text(); }
            $('d-meta').innerHTML = `<span class="pill ${r.ok ? 'ok' : 'err'}">${r.status}</span><span class="num">${ms(Math.round(performance.now() - started))}</span><span>recorded as caller <code>${esc(ME.via === 'proxy' && ME.email ? ME.email : 'console')}</code></span>`;
            $('d-resultpre').textContent = typeof data === 'string' ? data : pretty(data.result !== undefined ? data.result : data);
            $('d-result').hidden = false;
          } catch (e) { toast(e.message); } finally { $('d-run').disabled = false; }
        });
      }
      $('t-connect').innerHTML = snippets((t.apps || [])[0] || 'app', t);
      $('t-activity').innerHTML = '<p class="hint">Loading…</p>';
      api(`activity?tool=${encodeURIComponent(t.name)}&limit=50&window=30d`).then(r => { $('t-activity').innerHTML = `<div class="tablewrap"><table><thead><tr><th>Time</th><th>App</th><th>Caller</th><th>On behalf of</th><th>Via</th><th class="num">Duration</th><th>Status</th></tr></thead><tbody>${r.calls.length ? r.calls.map(x => actRow(x, false, true)).join('') : '<tr><td colspan="7" class="muted">No calls recorded for this tool in 30 days.</td></tr>'}</tbody></table></div>`; }).catch(e => { $('t-activity').innerHTML = `<p class="err">${esc(e.message)}</p>`; });
      loadHistory('tool', t);
      $('t-edit').innerHTML = editorForm('tool', t);
      wireEditor('tool', t);
    });
    selectTab('t-overview');
  }

  function confirmDelete(kind, rec) {
    const box = $('d-delconfirm'); const apps = rec.apps || [];
    box.innerHTML = `<div class="confirm" style="margin-top:12px"><span>Delete <b>${esc(rec.name)}</b>? ${apps.length > 1 ? `It is offered to ${apps.length} apps; deleting removes it from all of them.` : ''} Its history is kept and it can be restored from there.</span><div style="display:flex;gap:8px"><button class="btn sm danger" id="d-delyes">Delete ${kind}</button><button class="btn sm" id="d-delno">Keep</button></div></div>`;
    $('d-delno').addEventListener('click', () => { box.innerHTML = ''; });
    $('d-delyes').addEventListener('click', async () => { try { await api(`${kind}s/${encodeURIComponent(rec.name)}`, 'DELETE'); toast(`Deleted ${rec.name}`); closeDrawer(); await loadAll(); } catch (e) { toast(e.message); } });
  }

  async function loadHistory(kind, rec) { return loadHistoryInto(kind, rec.name, $(kind === 'tool' ? 't-history' : 's-history'), rec); }
  async function loadHistoryInto(kind, name, el, rec) {
    rec = rec || { name };
    el.innerHTML = '<p class="hint">Loading…</p>';
    try {
      const h = (await api(`${kind}s/${encodeURIComponent(rec.name)}/history`)).history.slice().reverse();
      if (!h.length) { el.innerHTML = '<p class="hint">No history recorded yet: this record predates the history log. Its next change starts the log.</p>'; return; }
      el.innerHTML = `<ul class="versions">${h.map((e, i) => `<li><b>${e.version ? 'v' + e.version : esc(e.action)}</b><span class="muted">${day(e.ts)} · ${esc(e.action)} · ${esc(e.actor)}</span>${i === 0 ? '<span class="pill server">current</span>' : (e.record ? `<button class="btn sm" data-restore="${e.version}">Restore</button>` : '')}</li>`).join('')}</ul>
        ${h.length > 1 && h[0].record && h[1].record ? `<h3>v${h[1].version} → v${h[0].version}</h3>${diffHtml(stripMeta(h[1].record), stripMeta(h[0].record))}` : ''}`;
      el.querySelectorAll('[data-restore]').forEach(b => b.addEventListener('click', async () => { try { await api(`${kind}s/${encodeURIComponent(rec.name)}/restore`, 'POST', { version: parseInt(b.dataset.restore, 10) }); toast(`Restored v${b.dataset.restore} as a new version`); await loadAll(); (kind === 'tool' ? openTool : openSkill)(rec.name); } catch (e) { toast(e.message); } }));
    } catch (e) { el.innerHTML = `<p class="err">${esc(e.message)}</p>`; }
  }

  // ── editor (tools and skills) ──
  function editorForm(kind, rec) {
    const isNew = !rec.name;
    const registered = (REG.app_records || []).map(r => r.name);
    const appsField = `<label>apps (the registered apps this is offered to)<span class="chips" style="margin-top:4px">${registered.map(a => `<label class="chip" style="cursor:pointer"><input type="checkbox" data-app-check="${esc(a)}" ${(rec.apps || []).includes(a) ? 'checked' : ''} style="margin:0 4px 0 0">${esc(a)}</label>`).join('') || '<span class="hint">No registered apps: Apps › New app first.</span>'}</span><input class="field" data-f="apps" value="${esc((rec.apps || []).filter(a => !registered.includes(a)).join(', '))}" placeholder="other names, comma-separated (must be registered to save)" style="margin-top:6px"></label>`;
    if (kind === 'tool') return `<div class="form">
      <div class="row"><label>name${isNew ? ' *' : ''}<input class="field" data-f="name" value="${esc(rec.name || '')}" ${isNew ? '' : 'readonly'}></label><label>display name<input class="field" data-f="display_name" value="${esc(rec.display_name || '')}"></label></div>
      <label>description<textarea class="prose" data-f="description">${esc(rec.description || '')}</textarea></label>
      ${appsField}
      <div class="row"><label>tier<select class="field" data-f="tier"><option ${rec.tier !== 'write' ? 'selected' : ''}>read</option><option ${rec.tier === 'write' ? 'selected' : ''}>write</option></select></label>
      <label>execution<select class="field" data-f="execution"><option ${execOf(rec) !== 'client' ? 'selected' : ''}>server</option><option ${execOf(rec) === 'client' ? 'selected' : ''}>client</option></select></label>
      <label>impl<select class="field" data-f="impl">${REG.impls.map(i => `<option ${rec.impl === i ? 'selected' : ''}>${esc(i)}</option>`).join('')}<option value="__other" ${rec.impl && !REG.impls.includes(rec.impl) ? 'selected' : ''}>other (client id)…</option></select></label>
      <label>client impl id<input class="field" data-f="impl_other" value="${esc(rec.impl && !REG.impls.includes(rec.impl) ? rec.impl : '')}" placeholder="client_ui"></label></div>
      <div class="row"><label><span><input type="checkbox" data-f="destructive" ${rec.destructive ? 'checked' : ''}> destructive (write tier)</span></label><label><span><input type="checkbox" data-f="idempotent" ${rec.idempotent ? 'checked' : ''}> idempotent</span></label><label><span><input type="checkbox" data-f="enabled" ${rec.enabled !== false ? 'checked' : ''}> enabled</span></label></div>
      <label>input schema (JSON Schema)<textarea data-f="input_schema">${esc(pretty(rec.input_schema || { type: 'object', properties: {}, required: [] }))}</textarea><span class="err" data-err="input_schema"></span></label>
      <label>output schema (optional)<textarea data-f="output_schema">${esc(rec.output_schema ? pretty(rec.output_schema) : '')}</textarea><span class="err" data-err="output_schema"></span></label>
      <label>config (JSON)<textarea data-f="config">${esc(pretty(rec.config || {}))}</textarea><span class="err" data-err="config"></span></label>
      <div style="display:flex;gap:8px"><button class="btn primary" data-act="preview">Save…</button></div><div data-out="diff"></div></div>`;
    return `<div class="form">
      <div class="row"><label>name${isNew ? ' *' : ''}<input class="field" data-f="name" value="${esc(rec.name || '')}" ${isNew ? '' : 'readonly'}></label><label>display name<input class="field" data-f="display_name" value="${esc(rec.display_name || '')}"></label></div>
      <label>description<textarea class="prose" data-f="description" style="min-height:60px">${esc(rec.description || '')}</textarea></label>
      ${appsField}
      <div class="row"><label>tags (comma-separated)<input class="field" data-f="tags" value="${esc((rec.tags || []).join(', '))}"></label><label>expects tools (comma-separated)<input class="field" data-f="tools" value="${esc((rec.tools || []).join(', '))}"></label></div>
      <label>arguments (JSON list of {name, description, required, default})<textarea data-f="arguments">${esc(pretty(rec.arguments || []))}</textarea><span class="err" data-err="arguments"></span></label>
      <label>content (Markdown; {{name}} marks an argument)<textarea class="prose" data-f="content" style="min-height:160px">${esc(rec.content || '')}</textarea></label>
      <label><span><input type="checkbox" data-f="enabled" ${rec.enabled !== false ? 'checked' : ''}> enabled</span></label>
      <div style="display:flex;gap:8px"><button class="btn primary" data-act="preview">Save…</button></div><div data-out="diff"></div></div>`;
  }
  function readEditor(kind, root) {
    const v = f => { const el = root.querySelector(`[data-f="${f}"]`); return el ? (el.type === 'checkbox' ? el.checked : el.value) : undefined; };
    const list = s => String(s || '').split(',').map(x => x.trim()).filter(Boolean);
    const json = (f, fallback) => { const el = root.querySelector(`[data-f="${f}"]`); const err = root.querySelector(`[data-err="${f}"]`); if (err) err.textContent = ''; if (!el.value.trim()) return fallback; try { return JSON.parse(el.value); } catch (e) { if (err) err.textContent = 'Not valid JSON: ' + e.message; throw new Error(f + ' is not valid JSON'); } };
    const checked = [...root.querySelectorAll('[data-app-check]:checked')].map(el => el.dataset.appCheck);
    const body = { display_name: v('display_name'), description: v('description'), apps: [...new Set(checked.concat(list(v('apps'))))], enabled: !!v('enabled') };
    if (kind === 'tool') {
      body.tier = v('tier'); body.destructive = !!v('destructive'); body.idempotent = !!v('idempotent');
      body.impl = v('impl') === '__other' ? v('impl_other') : v('impl');
      body.input_schema = json('input_schema', { type: 'object' }); body.output_schema = json('output_schema', null); body.config = json('config', {});
      body.config = { ...body.config }; if (v('execution') === 'client') body.config.execution = 'client'; else delete body.config.execution;
      if (body.output_schema === null) delete body.output_schema;
    } else {
      body.tags = list(v('tags')); body.tools = list(v('tools')); body.arguments = json('arguments', []); body.content = v('content');
    }
    return { name: (v('name') || '').trim(), body };
  }
  function wireEditor(kind, rec) {
    const root = $(kind === 'tool' ? 't-edit' : 's-edit');
    root.querySelector('[data-act="preview"]').addEventListener('click', () => {
      let r; try { r = readEditor(kind, root); } catch (e) { toast(e.message); return; }
      if (!r.name) { toast('A name is required'); return; }
      if (!r.body.apps.length) { toast('Offer it to at least one app'); return; }
      const before = rec.name ? stripMeta(rec) : {}; const after = { ...before, ...r.body, name: r.name };
      const out = root.querySelector('[data-out="diff"]');
      out.innerHTML = `<h3 style="margin:12px 0 8px">${rec.name ? 'Changes to save' : 'Record to create'}</h3>${diffHtml(before, after)}<div style="display:flex;gap:8px;margin-top:8px"><button class="btn primary" data-act="save">Save ${kind}</button><button class="btn" data-act="cancel">Cancel</button></div>`;
      out.querySelector('[data-act="cancel"]').addEventListener('click', () => { out.innerHTML = ''; });
      out.querySelector('[data-act="save"]').addEventListener('click', async () => {
        try { await api(`${kind}s/${encodeURIComponent(r.name)}`, 'PUT', r.body); toast(`Saved ${r.name}`); await loadAll(); location.hash = `${kind}-${r.name}`; (kind === 'tool' ? openTool : openSkill)(r.name); }
        catch (e) { toast(e.message); }
      });
    });
  }
  function openEditor(kind) {
    current = null;
    openDrawer(`New ${kind}`, ['server', ''], ['server', ''], [[kind === 'tool' ? 't-edit' : 's-edit', 'Editor']], () => {
      $(kind === 'tool' ? 't-edit' : 's-edit').innerHTML = editorForm(kind, { apps: appFilter ? [appFilter] : [], tier: 'read', enabled: true });
      wireEditor(kind, {});
    });
  }
  $('newtool').addEventListener('click', () => openEditor('tool'));
  $('newskill').addEventListener('click', () => openEditor('skill'));

  // ── skills ──
  function renderSkills() {
    $('skilltable').tBodies[0].innerHTML = REG.skills.length ? REG.skills.map(s => `<tr class="row" data-name="${esc(s.name)}" aria-selected="${current && current.kind === 'skill' && current.name === s.name}"><td class="name">${esc(s.name)}<span class="desc">${esc(s.description)}</span></td><td>${pillApps(s.apps)}</td><td><span class="apps">${(s.tags || []).map(t => `<span class="pill tag">${esc(t)}</span>`).join('')}</span></td><td class="mono muted">${esc((s.tools || []).join(', ') || '—')}</td><td class="num">v${s.version}</td><td class="muted time">${day(s.updated_at)}</td><td><button class="toggle" aria-checked="${s.enabled}" aria-label="Enabled" data-toggle="skill" data-name="${esc(s.name)}"></button></td></tr>`).join('')
      : '<tr><td colspan="7" class="empty">No skills yet. A skill is an instruction several consumers must apply the same way (a citation convention, a language rule, a disclosure). App-tuned system prompts stay in their apps.</td></tr>';
  }
  function openSkill(name) {
    const s = REG.skills.find(x => x.name === name); if (!s) { toast('Unknown skill ' + name); return; }
    current = { kind: 'skill', name }; renderSkills();
    openDrawer(s.name, ['tag', 'skill'], ['server', `v${s.version}`],
      [['s-overview', 'Overview'], ['s-content', 'Content'], ['s-try', 'Try it'], ['s-connect', 'Connect'], ['s-history', 'History'], ['s-edit', 'Edit']], () => {
      const offered = new Set(REG.tools.filter(t => (t.apps || []).some(a => (s.apps || []).includes(a))).map(t => t.name));
      $('s-overview').innerHTML = `<p style="margin:0">${esc(s.description)}</p><dl class="kv">
        <dt>Offered to</dt><dd>${pillApps(s.apps)}</dd>
        <dt>Served as</dt><dd class="mono">prompts/get ${esc(s.name)} · resource skill://${esc(s.name)}</dd>
        <dt>Arguments</dt><dd>${(s.arguments || []).length ? (s.arguments || []).map(a => `<code>${esc(a.name)}</code>${a.required ? ' *' : ''} ${esc(a.description || '')}`).join('<br>') : '<span class="muted">none</span>'}</dd>
        <dt>Expects tools</dt><dd>${(s.tools || []).length ? (s.tools || []).map(t => offered.has(t) ? `<a href="#tool-${esc(t)}">${esc(t)}</a>` : `<code>${esc(t)}</code> <span class="muted">(the app's own)</span>`).join(', ') : '<span class="muted">none</span>'}</dd>
        <dt>Tags</dt><dd>${(s.tags || []).map(t => `<span class="pill tag">${esc(t)}</span>`).join(' ') || '<span class="muted">none</span>'}</dd>
        <dt>Version</dt><dd>v${s.version} · updated ${day(s.updated_at)} · created ${day(s.created_at)}</dd></dl>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><button class="toggle" aria-checked="${s.enabled}" aria-label="Enabled" data-toggle="skill" data-name="${esc(s.name)}"></button><span>Enabled</span><button class="btn sm" id="s-editbtn" style="margin-left:auto">Edit</button><button class="btn sm danger" id="s-del">Delete</button></div><div id="d-delconfirm"></div>`;
      $('s-editbtn').addEventListener('click', () => selectTab('s-edit'));
      $('s-del').addEventListener('click', () => confirmDelete('skill', s));
      $('s-content').innerHTML = `<div class="eyebrow">Content · as stored (placeholders unresolved)</div><div class="preview">${esc(s.content)}</div>`;
      $('s-try').innerHTML = `<div class="form" id="s-form">${(s.arguments || []).map(a => `<label>${esc(a.name)}${a.required ? ' *' : ''}<input class="field" data-arg="${esc(a.name)}" placeholder="${esc(a.default != null ? a.default : a.description || '')}"><span class="hint">${esc(a.description || '')}</span></label>`).join('') || '<p class="hint">No arguments.</p>'}</div><div><button class="btn primary" id="s-render">Render as prompts/get</button></div><div class="result" id="s-result" hidden><div class="eyebrow">What a client receives</div><div class="preview" id="s-rendered"></div></div>`;
      $('s-render').addEventListener('click', async () => { const args = {}; document.querySelectorAll('#s-form [data-arg]').forEach(el => { if (el.value) args[el.dataset.arg] = el.value; }); try { const r = await api(`skills/${encodeURIComponent(s.name)}/render`, 'POST', { arguments: args }); $('s-rendered').textContent = r.messages[0].content; $('s-result').hidden = false; } catch (e) { toast(e.message); } });
      $('s-connect').innerHTML = snippets((s.apps || [])[0] || 'app', null) + `<div class="snip"><div class="label"><span class="eyebrow">As a resource</span><button class="btn sm" data-copy="sn-res">Copy</button></div><pre id="sn-res">resources/read  skill://${esc(s.name)}   (text/markdown)\nprompts/get     ${esc(s.name)}${(s.arguments || []).length ? '  arguments: ' + (s.arguments || []).map(a => a.name).join(', ') : ''}</pre></div>`;
      loadHistory('skill', s);
      $('s-edit').innerHTML = editorForm('skill', s);
      wireEditor('skill', s);
    });
    selectTab('s-overview');
  }

  // ── apps ──
  const appRecord = (a) => (REG.app_records || []).find(r => r.name === a);
  function renderApps() {
    const byTool = {}; (REG.summary.tools || []).forEach(t => { byTool[t.tool] = t; });
    $('appcards').innerHTML = REG.apps.map(a => {
      const rec = appRecord(a);
      const ks = REG.keys.filter(k => k.app === a && !k.revoked_at);
      const tools = REG.tools.filter(t => (t.apps || []).includes(a)), skills = REG.skills.filter(s => (s.apps || []).includes(a));
      const calls = tools.reduce((n, t) => n + (t.calls_24h || 0), 0), errs = tools.reduce((n, t) => n + (t.errors_24h || 0), 0);
      const status = !rec ? '<span class="pill err">not registered</span>' : rec.status === 'retired' ? '<span class="pill warn">retired</span>' : (ks.length ? '<span class="pill ok">key active</span>' : '<span class="pill warn">no key</span>');
      return `<div class="appcard" id="app-${esc(a)}">
        <div class="head"><h3>${esc(a)}</h3>${status}<button class="btn sm" data-editapp="${esc(a)}" style="margin-left:auto">${rec ? 'Edit' : 'Register'}</button><button class="btn sm" data-connect="${esc(a)}">Connect</button></div>
        ${rec ? `<div><b>${esc(rec.display_name || a)}</b>${rec.description ? ` <span class="muted">· ${esc(rec.description)}</span>` : ''}</div><div class="muted" style="font-size:12px">${rec.owner ? 'owner ' + esc(rec.owner) : '<span class="never">no owner</span>'}${rec.contact ? ' · ' + esc(rec.contact) : ''}${(rec.tags || []).length ? ' · ' + rec.tags.map(t => `<span class="pill tag">${esc(t)}</span>`).join(' ') : ''}</div>` : '<div class="never">Named by a tool or a skill, but not in the catalog: register it, or withdraw the offer.</div>'}
        <div class="mono muted" style="font-size:12px">/mcp/${esc(a)}/ · /tools?app=${esc(a)}</div>
        <div class="stats"><a href="#app=${esc(a)}" style="text-decoration:none;color:inherit"><b class="num">${tools.length}</b><span>tools</span></a><div><b class="num">${skills.length}</b><span>skills</span></div><div><b class="num">${calls}</b><span>calls 24 h · ${errs} err</span></div></div>
        <div class="keys"><div class="eyebrow">Keys</div>${ks.map(k => `<div><code>${esc(k.name)}</code><span class="muted">${esc(k.id)} · created ${day(k.created_at)} · expires ${day(k.expires_at)} · used ${k.last_used_at ? ago(k.last_used_at) : 'never'}</span><button class="btn sm danger" data-revoke="${esc(k.id)}" data-app="${esc(a)}">Revoke</button></div>`).join('') || '<div class="muted">None. Calls from this app are recorded as anonymous.</div>'}
          <div><input class="field" data-keyname="${esc(a)}" placeholder="key name (which program)" style="flex:1"><select class="field" data-keydays="${esc(a)}"><option value="90">90 days</option><option value="180">180 days</option><option value="365">365 days</option></select><button class="btn sm" data-newkey="${esc(a)}">+ New key</button></div><div data-keyout="${esc(a)}"></div></div>
        <div class="keys"><div class="eyebrow" title="OAuth 2.1 client credentials: a program that speaks for this app with an expiring token instead of a key">Machine clients</div>${(REG.machine_clients || []).filter(c => c.app === a).map(c => `<div><code>${esc(c.client_name)}</code><span class="muted">${esc(c.client_id)} · ${esc((c.scopes || []).join(' '))} · registered ${day(c.created_at)} · used ${c.last_used_at ? ago(c.last_used_at) : 'never'}</span><button class="btn sm danger" data-delmc="${esc(c.client_id)}" data-app="${esc(a)}">Remove</button></div>`).join('') || '<div class="muted">None. A machine client gets tokens with its id and secret (client_credentials), no person behind it.</div>'}
          <div><input class="field" data-mcname="${esc(a)}" placeholder="client name (which program)" style="flex:1"><label class="chip" style="cursor:pointer"><input type="checkbox" data-mcwrite="${esc(a)}" style="margin:0 4px 0 0">tools:write</label><button class="btn sm" data-newmc="${esc(a)}">+ New machine client</button></div><div data-mcout="${esc(a)}"></div></div>
        <div data-connectout="${esc(a)}"></div></div>`;
    }).join('') || '<p class="empty">No apps yet. An app appears when a tool or skill is offered to it.</p>';
    $('appcards').querySelectorAll('[data-newkey]').forEach(b => b.addEventListener('click', async () => {
      const a = b.dataset.newkey, name = $('appcards').querySelector(`[data-keyname="${a}"]`).value, days = $('appcards').querySelector(`[data-keydays="${a}"]`).value;
      try { const r = await api(`apps/${encodeURIComponent(a)}/keys`, 'POST', { name, expires_days: parseInt(days, 10) });
        const out = $('appcards').querySelector(`[data-keyout="${a}"]`); out.innerHTML = `<div class="newkey"><b>Copy this key now. It is shown once.</b><div style="display:flex;gap:8px;align-items:center"><code id="nk-${esc(r.record.id)}" style="overflow-wrap:anywhere">${esc(r.key)}</code><button class="btn sm" data-copy="nk-${esc(r.record.id)}">Copy</button></div><span class="muted">${esc(r.record.name)} · expires ${day(r.record.expires_at)}</span></div>`; toast('Key created'); }
      catch (e) { toast(e.message); }
    }));
    $('appcards').querySelectorAll('[data-revoke]').forEach(b => b.addEventListener('click', () => {
      const row = b.parentElement; if (b.dataset.sure !== '1') { b.dataset.sure = '1'; b.textContent = 'Confirm revoke'; setTimeout(() => { b.dataset.sure = ''; b.textContent = 'Revoke'; }, 4000); return; }
      api(`apps/${encodeURIComponent(b.dataset.app)}/keys/${encodeURIComponent(b.dataset.revoke)}`, 'DELETE').then(() => { toast('Key revoked'); loadAll(); }).catch(e => toast(e.message));
    }));
    $('appcards').querySelectorAll('[data-connect]').forEach(b => b.addEventListener('click', () => { const out = $('appcards').querySelector(`[data-connectout="${b.dataset.connect}"]`); out.innerHTML = out.innerHTML ? '' : snippets(b.dataset.connect, null); }));
    $('appcards').querySelectorAll('[data-editapp]').forEach(b => b.addEventListener('click', () => openAppEditor(b.dataset.editapp)));
    $('appcards').querySelectorAll('[data-newmc]').forEach(b => b.addEventListener('click', async () => {
      const a = b.dataset.newmc, name = $('appcards').querySelector(`[data-mcname="${a}"]`).value, write = $('appcards').querySelector(`[data-mcwrite="${a}"]`).checked;
      try { const r = await api(`apps/${encodeURIComponent(a)}/clients`, 'POST', { name, scopes: write ? ['tools:read', 'tools:write'] : ['tools:read'] });
        const out = $('appcards').querySelector(`[data-mcout="${a}"]`);
        out.innerHTML = `<div class="newkey"><b>Copy the client id and secret now. The secret is shown once.</b><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><code id="mcid-${esc(r.client_id)}">${esc(r.client_id)}</code><button class="btn sm" data-copy="mcid-${esc(r.client_id)}">Copy id</button></div><div style="display:flex;gap:8px;align-items:center"><code id="mcsec-${esc(r.client_id)}" style="overflow-wrap:anywhere">${esc(r.client_secret)}</code><button class="btn sm" data-copy="mcsec-${esc(r.client_id)}">Copy secret</button></div><span class="muted">POST ${esc(PUBLIC)}/oauth/token · grant_type=client_credentials · scope ${esc(r.scopes.join(' '))}</span></div>`; toast('Machine client created'); }
      catch (e) { toast(e.message); }
    }));
    $('appcards').querySelectorAll('[data-delmc]').forEach(b => b.addEventListener('click', () => {
      if (b.dataset.sure !== '1') { b.dataset.sure = '1'; b.textContent = 'Confirm remove'; setTimeout(() => { b.dataset.sure = ''; b.textContent = 'Remove'; }, 4000); return; }
      api(`apps/${encodeURIComponent(b.dataset.app)}/clients/${encodeURIComponent(b.dataset.delmc)}`, 'DELETE').then(() => { toast('Machine client removed'); loadAll(); }).catch(e => toast(e.message));
    }));
  }
  // ── the app record's editor (the catalog): name, display name, description, owner, contact, status, tags ──
  function openAppEditor(name) {
    const rec = name ? (appRecord(name) || { name }) : {};
    current = null;
    openDrawer(name || 'New app', ['app', 'app'], ['server', rec.status || ''], [['a-edit', 'Record'], ['a-history', 'History']], () => {
      $('a-edit').innerHTML = `<div class="form">
        <div class="row"><label>name${name ? '' : ' *'}<input class="field" data-f="name" value="${esc(rec.name || '')}" ${name ? 'readonly' : ''} placeholder="letters, digits, - and _"></label><label>display name<input class="field" data-f="display_name" value="${esc(rec.display_name || '')}"></label></div>
        <label>description<textarea class="prose" data-f="description" style="min-height:60px">${esc(rec.description || '')}</textarea></label>
        <div class="row"><label>owner<input class="field" data-f="owner" value="${esc(rec.owner || '')}" placeholder="team or person"></label><label>contact<input class="field" data-f="contact" value="${esc(rec.contact || '')}" placeholder="address or channel"></label></div>
        <div class="row"><label>status<select class="field" data-f="status"><option ${rec.status !== 'retired' ? 'selected' : ''}>active</option><option ${rec.status === 'retired' ? 'selected' : ''}>retired</option></select></label><label>tags (comma-separated)<input class="field" data-f="tags" value="${esc((rec.tags || []).join(', '))}"></label></div>
        <p class="hint">A retired app answers nobody: its endpoint and its tools refuse calls, and no key can be issued to it. Its records and keys stay.</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn primary" id="a-save">Save app</button>${name && appRecord(name) ? '<button class="btn danger" id="a-del">Delete app</button>' : ''}</div><div id="a-out"></div></div>`;
      $('a-save').addEventListener('click', async () => {
        const v = f => { const el = $('a-edit').querySelector(`[data-f="${f}"]`); return el ? el.value : ''; };
        const n = (v('name') || '').trim(); if (!n) { toast('A name is required'); return; }
        const body = { display_name: v('display_name'), description: v('description'), owner: v('owner'), contact: v('contact'), status: v('status'), tags: String(v('tags') || '').split(',').map(x => x.trim()).filter(Boolean) };
        try { await api(`apps/${encodeURIComponent(n)}`, 'PUT', body); toast(`Saved ${n}`); await loadAll(); location.hash = 'app-' + n; closeDrawer(); } catch (e) { toast(e.message); }
      });
      const del = $('a-del');
      if (del) del.addEventListener('click', () => {
        const use = { tools: REG.tools.filter(t => (t.apps || []).includes(name)).length, skills: REG.skills.filter(s => (s.apps || []).includes(name)).length, keys: REG.keys.filter(k => k.app === name && !k.revoked_at).length };
        const inUse = use.tools + use.skills + use.keys > 0;
        $('a-out').innerHTML = `<div class="confirm" style="margin-top:12px"><span>Delete <b>${esc(name)}</b>?${inUse ? ` It is offered ${use.tools} tool(s) and ${use.skills} skill(s) and holds ${use.keys} active key(s): deleting withdraws the offers and revokes the keys.` : ''} Its history is kept.</span><div style="display:flex;gap:8px"><button class="btn sm danger" id="a-delyes">Delete app${inUse ? ' and withdraw' : ''}</button><button class="btn sm" id="a-delno">Keep</button></div></div>`;
        $('a-delno').addEventListener('click', () => { $('a-out').innerHTML = ''; });
        $('a-delyes').addEventListener('click', async () => { try { await api(`apps/${encodeURIComponent(name)}${inUse ? '?force=true' : ''}`, 'DELETE'); toast(`Deleted ${name}`); closeDrawer(); await loadAll(); } catch (e) { toast(e.message); } });
      });
      if (name) loadHistoryInto('app', name, $('a-history')); else $('a-history').innerHTML = '<p class="hint">No history yet.</p>';
    });
  }
  $('newapp').addEventListener('click', () => openAppEditor(''));

  // ── activity ──
  actCursor = null;
  $('winchips').addEventListener('click', e => { const b = e.target.closest('.chip'); if (!b) return; win = b.dataset.win; [...$('winchips').children].forEach(c => c.setAttribute('aria-pressed', c === b)); loadActivity(true); renderStatus(); });
  ['act-app', 'act-ok', 'act-q'].forEach(id => $(id).addEventListener(id === 'act-q' ? 'input' : 'change', () => loadActivity(true)));
  $('act-more').addEventListener('click', () => loadActivity(false));
  function actParams() { const p = new URLSearchParams({ window: win, limit: '100' }); if ($('act-app').value) p.set('app', $('act-app').value); if ($('act-ok').value) p.set('ok', $('act-ok').value); if ($('act-q').value) p.set('q', $('act-q').value); return p; }
  async function loadActivity(reset) {
    const p = actParams(); if (!reset && actCursor) p.set('cursor', actCursor);
    $('csv').href = 'activity.csv?' + p.toString();
    try {
      const [r, s] = await Promise.all([api('activity?' + p.toString()), reset ? api(`activity/summary?window=${win}${$('act-app').value ? '&app=' + encodeURIComponent($('act-app').value) : ''}`) : null]);
      if (s) $('act-summary').innerHTML = `<span><b class="num">${s.calls}</b> calls</span><span><b class="num" style="color:var(--bad)">${s.errors}</b> errors</span><span><b class="num">${ms(s.p95_ms)}</b> p95</span>${s.tools[0] ? `<span><b>${esc(s.tools[0].tool)}</b> most called</span>` : ''}`;
      const html = r.calls.map(x => actRow(x, false)).join('');
      $('acttable').tBodies[0].innerHTML = (reset ? '' : $('acttable').tBodies[0].innerHTML) + (html || (reset ? '<tr><td colspan="8" class="empty">No calls in this window.</td></tr>' : ''));
      actCursor = r.next_cursor; $('act-more').hidden = !actCursor;
    } catch (e) { toast(e.message); }
  }

  // ── settings ──
  function renderSettings() {
    $('impls-h').textContent = `Implementations · ${REG.impls.length}`;
    $('impltable').tBodies[0].innerHTML = REG.impls.map(i => { const bound = REG.impl_tools[i] || []; return `<tr><td>${esc(i)}</td><td>${bound.length ? bound.map(n => { const t = REG.tools.find(x => x.name === n); return `<a href="#tool-${esc(n)}">${esc(n)}</a> <span class="muted">(${esc((t.apps || []).join(', '))})</span>`; }).join('<br>') : '<span class="muted">unused</span>'}</td></tr>`; }).join('');
    $('impls-note').innerHTML = (REG.orphans.length ? `<span class="err">${REG.orphans.length} orphan record(s): ${esc(REG.orphans.join(', '))}.</span> ` : 'No orphan records. ') + (REG.unused_impls.length ? `Unused implementations: ${esc(REG.unused_impls.join(', '))}.` : 'No unused implementations.');
    const b = HEALTH.backends || {};
    $('backends').innerHTML = Object.keys(b).map(k => `<dt>${esc(k)}</dt><dd><span class="pill ${b[k] === 'ok' || b[k] === 'configured' || b[k] === 'mounted' ? 'ok' : (b[k] === 'degraded' ? 'warn' : 'err')}">${esc(b[k])}</span></dd>`).join('');
    $('authkv').innerHTML = `<dt>Sign-in</dt><dd><span class="pill ${HEALTH.proxy_identity === 'configured' ? 'ok' : 'warn'}">${HEALTH.proxy_identity === 'configured' ? 'Microsoft Entra ID' : 'off'}</span> ${HEALTH.proxy_identity === 'configured' ? 'the domain proxy (oauth2-proxy-entra) names the person; the service trusts it with the proxy secret (MCP_PROXY_SECRET)' : 'set MCP_PROXY_SECRET to trust the proxy\'s X-Auth-Request-Email'}</dd>
      <dt>OAuth 2.1</dt><dd><span class="pill ok">on</span> MCP clients sign people in through the domain and act within their scopes (tools:read, tools:write, admin)</dd>
      <dt>Admin token</dt><dd><span class="pill ${HEALTH.admin_auth === 'bearer' ? 'ok' : 'warn'}">${HEALTH.admin_auth === 'bearer' ? 'set' : 'open (dev)'}</span> programmatic writes, and the page off the domain</dd>
      <dt>App keys</dt><dd><span class="pill ${HEALTH.app_keys === 'required' ? 'ok' : 'warn'}">${esc(HEALTH.app_keys)}</span> ${HEALTH.app_keys === 'required' ? 'every call needs a key (MCP_REQUIRE_KEYS=1)' : 'read-tier tools answer anonymous calls; write-tier never does (set MCP_REQUIRE_KEYS=1)'}</dd>
      <dt>Record args</dt><dd><span class="pill server">${HEALTH.record_args ? 'on (read-tier only)' : 'off'}</span> ${HEALTH.record_args ? '' : 'digests only (MCP_RECORD_ARGS=1 to keep read-tier arguments)'}</dd>
      <dt>Retention</dt><dd>${HEALTH.retention_days} days · pruned daily (MCP_RETENTION_DAYS)</dd>`;
    $('oauth-issuer').textContent = HEALTH.oauth ? `Issuer ${HEALTH.oauth.issuer} · clients register themselves (RFC 7591) and people allow them on the consent page.` : '';
    api('oauth/clients').then(r => {
      $('oauth-clients').innerHTML = r.clients.length ? r.clients.map(c => `<div><code>${esc(c.client_name)}</code>${c.kind === 'machine' ? `<span class="pill app">machine · ${esc(c.app)}</span>` : '<span class="pill server">person</span>'}<span class="muted">${esc(c.client_id)} · ${esc(c.token_endpoint_auth_method)} · registered ${day(c.created_at)} · used ${c.last_used_at ? ago(c.last_used_at) : 'never'}${c.kind === 'machine' ? '' : ` · ${c.active_refresh_tokens} active token${c.active_refresh_tokens === 1 ? '' : 's'}`}</span><button class="btn sm danger" data-delclient="${esc(c.client_id)}">Remove</button></div>`).join('') : '<div class="muted">No client has registered yet.</div>';
      $('oauth-clients').querySelectorAll('[data-delclient]').forEach(b => b.addEventListener('click', () => { if (b.dataset.sure !== '1') { b.dataset.sure = '1'; b.textContent = 'Confirm remove'; setTimeout(() => { b.dataset.sure = ''; b.textContent = 'Remove'; }, 4000); return; } api(`oauth/clients/${encodeURIComponent(b.dataset.delclient)}`, 'DELETE').then(() => { toast('Client removed'); renderSettings(); }).catch(e => toast(e.message)); }));
    }).catch(() => {});
    $('export-app').href = 'admin/export' + (appFilter ? '?app=' + encodeURIComponent(appFilter) : '');
    $('export-app').textContent = 'Registry · ' + (appFilter || 'one app (filter Tools first)');
  }
  $('import').addEventListener('change', async e => {
    const f = e.target.files[0]; if (!f) return;
    let data; try { data = JSON.parse(await f.text()); } catch (err) { toast('Not a JSON file'); return; }
    const tools = Object.values(data.tools || {}), skills = Object.values(data.skills || {});
    const plan = [];
    for (const [kind, list, cur] of [['tool', tools, REG.tools], ['skill', skills, REG.skills]]) for (const r of list) { if (!r.name) continue; const ex = cur.find(x => x.name === r.name); if (!ex) plan.push({ kind, name: r.name, action: 'create', rec: r }); else if (pretty(stripMeta(ex)) !== pretty(stripMeta(r))) plan.push({ kind, name: r.name, action: 'update', rec: r, before: ex }); }
    $('import-out').innerHTML = `<p><b>${f.name}</b>: ${tools.length} tools, ${skills.length} skills in the file. ${plan.length ? `${plan.filter(p => p.action === 'create').length} to create, ${plan.filter(p => p.action === 'update').length} to update:` : 'Nothing differs from the registry.'}</p>${plan.map(p => `<div style="margin:6px 0"><b>${p.action}</b> ${p.kind} <code>${esc(p.name)}</code>${p.before ? diffHtml(stripMeta(p.before), stripMeta(p.rec)) : ''}</div>`).join('')}${plan.length ? '<button class="btn primary" id="import-apply">Apply ' + plan.length + ' change(s)</button>' : ''}`;
    const btn = $('import-apply'); if (btn) btn.addEventListener('click', async () => { let n = 0; for (const p of plan) { const body = { ...p.rec }; ['name', 'version', 'created_at', 'updated_at', 'last_used', 'calls_24h', 'errors_24h'].forEach(k => delete body[k]); try { await api(`${p.kind}s/${encodeURIComponent(p.name)}`, 'PUT', body); n++; } catch (err) { toast(`${p.name}: ${err.message}`); } } toast(`Applied ${n} of ${plan.length}`); await loadAll(); });
    e.target.value = '';
  });

  // ── theme, keys ──
  try { const t = localStorage.getItem('mcp_theme'); if (t) document.documentElement.dataset.theme = t; } catch (e) {}
  document.addEventListener('keydown', e => { if (e.key === 'r' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName) && !e.ctrlKey && !e.metaKey) { loadAll().then(() => toast('Refreshed')); } if (e.key === 'Escape') closeDrawer(); if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) { e.preventDefault(); show('tools'); $('q').focus(); } });

  history.scrollRestoration = 'manual';
  loadAll().then(route).catch(e => { $('tiles').innerHTML = `<p class="err">${esc(e.message)}</p>`; });
  setInterval(() => api('admin/health').then(h => { HEALTH = h; renderHeader(); }).catch(() => { HEALTH = { ...HEALTH, service: '' }; renderStatus(); }), 30000);
})();
</script>
</body>
</html>
"""
