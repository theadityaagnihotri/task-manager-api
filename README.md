
# Task Manager API — Automated Kubernetes CI/CD + GitOps Pipeline



A small FastAPI Task Manager REST API, deployed to Kubernetes through a fully

automated CI/CD + GitOps pipeline. A `git push` to this repo is the only

manual step in the entire deploy path — everything from testing to a live,

zero-downtime rollout happens on its own.



**GitOps configuration repo (Helm chart, desired state):**

[task-manager-gitops](https://github.com/theadityaagnihotri/task-manager-gitops)



## Architecture

Developer
↓ git push
GitHub Actions — test (pytest) → build → Trivy scan → push to GHCR (Git-SHA tag)
↓
Auto-commit new image tag to task-manager-gitops (as ci-bot)
↓
Argo CD (pull-based, auto sync + self-heal) — watches task-manager-gitops
↓
Kubernetes (kind) — Helm-rendered Deployment/Service/Ingress
↓
Zero-downtime rolling update → Ingress → Task Manager API



A parallel monitoring pipeline (Prometheus + Grafana) scrapes the app's own

`/metrics` endpoint via a ServiceMonitor.



## What's automated, end to end



Pushing a code change here — with **no other manual commands** — results in:

tests running, a Docker image building and being scanned, that image landing

in GHCR tagged with the exact commit SHA, the separate GitOps repo being

updated automatically, Argo CD detecting and syncing that change, and a

zero-downtime rolling deployment completing on the cluster.



## Tech stack



Python 3.12 · FastAPI · SQLite · Docker · GitHub Actions · GHCR · Trivy ·

Kubernetes (kind) · Helm · Argo CD · Prometheus · Grafana · HPA



## This repository specifically contains



- `app/` — the FastAPI application (CRUD task endpoints, `/health`,

  `/version`, `/metrics`)

- `tests/` — pytest suite, run on every push

- `Dockerfile` — non-root, slim-based production image

- `.github/workflows/ci.yml` — test → build → scan → push to GHCR →

  auto-update the GitOps repo



Kubernetes manifests, the Helm chart, and Argo CD configuration are

intentionally kept in the separate `task-manager-gitops` repo, following

standard GitOps practice of separating application code from deployment

configuration.



## Local development



```bash

python3.12 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload

```



Visit `http://localhost:8000/docs`.



```bash

docker build -t task-manager .

docker run -p 8000:8000 task-manager

```

