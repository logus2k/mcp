FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# docker CLI CLIENT only (talks to the host daemon via the bind-mounted socket) — the nginx_register_app
# tool runs `docker exec proxy_server nginx -t / -s reload` to validate + reload after writing a route.
RUN apt-get update \
 && apt-get install -y --no-install-recommends docker-cli \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# the documents the Help menu serves (admin.py DOCS)
COPY documents/technical_architecture.md documents/console_specification.md ./documents/

# The test stage: `docker build --target test .` runs the suite against this exact image.
FROM base AS test
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY tests ./tests
RUN python -m pytest -q tests

FROM base AS app
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
