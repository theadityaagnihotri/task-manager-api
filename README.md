# Task Manager API

A small, production-structured REST API for managing tasks, built as the
application layer for a Kubernetes CI/CD + GitOps portfolio project.

## 1. Project Overview

This is intentionally a simple CRUD API. Its purpose isn't to be a
feature-rich app — it exists to give a Kubernetes/GitOps pipeline something
real to build, test, containerize, deploy, and monitor. Every endpoint here
maps to something that pipeline will exercise.

## 2. Architecture

```
task-manager/
├── app/
│   ├── main.py        # FastAPI app, routes, middleware, metrics
│   ├── database.py     # SQLAlchemy engine/session setup
│   ├── models.py        # ORM model (Task)
│   ├── schemas.py       # Pydantic request/response models
│   ├── crud.py           # DB operations
│   └── config.py          # Env-var driven settings (APP_VERSION, etc.)
├── tests/
│   └── test_api.py     # pytest suite, uses isolated in-memory SQLite
├── Dockerfile
└── requirements.txt
```

Request flow: `main.py` routes → `crud.py` (DB logic) → `models.py` (SQLAlchemy
ORM) → SQLite. `schemas.py` validates/serializes everything at the API
boundary. This separation is what lets SQLite be swapped for Postgres later
without touching route logic.

## 3. Features

- Full CRUD on tasks (`/tasks`)
- `/health` — lightweight liveness/readiness endpoint
- `/version` — reads `APP_VERSION` env var, used to demo rolling deployments
- `/metrics` — Prometheus-format metrics (request count, latency, active requests)
- Auto-generated docs at `/docs` (Swagger) and `/redoc`
- SQLite persistence, structured so Postgres is a drop-in swap later

## 4. Local Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 5. Running Without Docker

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs`.

## 6. Running With Docker

```bash
docker build -t task-manager .
docker run -p 8000:8000 task-manager
```

Visit `http://localhost:8000/docs`.

To demonstrate a version change (as you would during a rolling deployment):

```bash
docker run -p 8000:8000 -e APP_VERSION=1.1.0 task-manager
curl http://localhost:8000/version
# {"version": "1.1.0"}
```

## 7. API Endpoints

| Method | Path            | Description        |
|--------|-----------------|---------------------|
| GET    | `/health`       | Liveness/readiness check |
| GET    | `/version`      | Current app version |
| GET    | `/metrics`      | Prometheus metrics |
| GET    | `/tasks`        | List all tasks |
| GET    | `/tasks/{id}`   | Get one task |
| POST   | `/tasks`        | Create a task |
| PUT    | `/tasks/{id}`   | Update a task |
| DELETE | `/tasks/{id}`   | Delete a task |

## 8. Running Tests

```bash
pytest
```

Tests run against an isolated in-memory SQLite database — no external DB or
network dependency required.

## 9. Example curl Commands

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn Kubernetes", "description": "Prepare for CKA"}'

curl http://localhost:8000/tasks

curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

curl -X DELETE http://localhost:8000/tasks/1
```

## 10. Environment Variables

| Variable       | Default                  | Purpose |
|----------------|---------------------------|---------|
| `APP_VERSION`  | `1.0.0`                   | Returned by `/version`; change + redeploy to demo a rolling update |
| `DATABASE_URL` | `sqlite:///./tasks.db`    | SQLAlchemy connection string; swap for a Postgres URL later without code changes |
| `APP_NAME`     | `task-manager`            | Used in structured logs |

See `.env.example`.

## 11. How This Fits the Future Kubernetes CI/CD Pipeline

This repository is intentionally scoped to the **application only** — no
Kubernetes manifests, Helm charts, Argo CD config, or GitHub Actions workflows
live here. Those will live in a separate GitOps/infra repo, keeping app code
and deployment config cleanly separated (a standard GitOps practice).

What's already in place to support that pipeline, once built:

- **Docker**: production-appropriate `Dockerfile` (slim base, non-root user)
  ready to build and push.
- **GitHub Actions (planned)**: `pytest` runs cleanly and independently, so a
  "run tests" CI stage has a real, meaningful gate.
- **Image registry (planned)**: image builds cleanly with `docker build`,
  ready to tag and push to GHCR.
- **Kubernetes probes (planned)**: `/health` is deliberately lightweight and
  DB-independent, making it safe to wire directly into `livenessProbe` and
  `readinessProbe`.
- **Rolling deployments (planned)**: `/version` reflects the `APP_VERSION` env
  var baked into the image, so a version bump + redeploy is directly
  observable via `GET /version`.
- **Argo CD / GitOps (planned)**: no manifests here by design — the separate
  infra repo will hold the Kubernetes/Helm config that Argo CD watches.
- **Prometheus + Grafana (planned)**: `/metrics` already exposes
  `http_requests_total`, `http_request_duration_seconds`, and
  `http_requests_active` in Prometheus format, ready to scrape once a
  ServiceMonitor/scrape config is added.
- **Observability**: structured logs on task create/update/delete and on
  startup, useful for demoing `kubectl logs`.

None of the above (Kubernetes, CI/CD, Argo CD, Prometheus scraping) is
implemented yet — this repo is the application layer only.
# CI/CD pipeline demo commit
# rollback demo v2
