# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-DEPLOY-001_production_deployment_spec.md"
# purpose: "TaskDNA Specification for DNK-DEPLOY-001 Production Deployment Configuration, Multi-Stage Containerization, Kubernetes Manifests, Helm Charts, and CI/CD Pipelines."
# canonical_source: true
# alters_files: [
#   "Dockerfile.api",
#   "Dockerfile.web",
#   "Dockerfile.worker",
#   "docker-compose.prod.yml",
#   "deployments/k8s/*",
#   "deployments/helm/*",
#   ".github/workflows/ci.yml",
#   ".github/workflows/deploy.yml",
#   "tests/deployment/*"
# ]
# triggers_tasks: ["DNK-DEPLOY-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🚀 DNK-DEPLOY-001: Production Deployment Configuration & Cloud-Native Infrastructure Specification

## 1. Executive Summary & Objectives

**DNK-DEPLOY-001** establishes the enterprise-grade, zero-downtime, cloud-native deployment infrastructure for the **DNK OS** ecosystem. It provides multi-stage, hardened containerization, high-availability orchestration across Docker Compose and Kubernetes (K8s), Helm chart packaging for dev/staging/prod environments, and GitOps-ready GitHub Actions CI/CD automation.

### Key Architectural Invariants:
1. **Security & Least Privilege**: All containers run as non-root users (`uid: 10001`, `gid: 10001`) with read-only root filesystems where applicable, zero ambient root privileges, and vulnerability scanning via Trivy/Grype.
2. **High Availability & Zero Downtime**: Rolling updates with Pod Disruption Budgets (PDB), Horizontal Pod Autoscaling (HPA) driven by CPU/Memory/RPS, and graceful shutdown handlers.
3. **Multi-Tier Network Segmentation**: Isolated network tiers (`frontend_net`, `backend_net`, `data_net`) preventing direct external access to databases and cache instances.
4. **Observable & Self-Healing**: Liveness, readiness, and startup health probes instrumented across all workloads, integrated with Prometheus/Grafana and auto-healing triggers.

---

## 2. TaskDNA Decomposition & Evolutionary DAG

```
                      ┌────────────────────────────────────────┐
                      │ DNK-DEPLOY-001: Production Deployment  │
                      └───────────────────┬────────────────────┘
                                          │
        ┌───────────────────┬─────────────┴───────┬───────────────────┐
        ▼                   ▼                     ▼                   ▼
┌───────────────┐   ┌───────────────┐     ┌───────────────┐   ┌───────────────┐
│    Phase 1    │   │    Phase 2    │     │    Phase 3    │   │    Phase 4    │
│ Containerize  │──►│ Kubernetes &  │────►│ CI/CD GitOps  │──►│ Healthchecks, │
│  Multi-Stage  │   │  Helm Charts  │     │   Pipelines   │   │ Tests & Gate  │
└───────────────┘   └───────────────┘     └───────────────┘   └───────────────┘
```

### Dependency DAG:
- **Phase 1: TaskDNA Spec & Production Containerization**
  - Multi-stage `Dockerfile.api` (FastAPI backend, non-root `appuser:10001`).
  - Multi-stage `Dockerfile.web` (Next.js standalone frontend, non-root `nextjs:10001`).
  - Multi-stage `Dockerfile.worker` (TaskDNA/Celery background worker, non-root `appuser:10001`).
  - `docker-compose.prod.yml` with PostgreSQL (pgvector), Redis (AOF), API, Web, Worker, Traefik/Nginx Gateway, Prometheus & Grafana.
- **Phase 2: Kubernetes Manifests & Helm Chart**
  - K8s manifests in `deployments/k8s/`: Namespace, ConfigMaps, Secrets, Deployments, Services, Ingress (TLS cert-manager), HPA, PDB.
  - Helm Chart in `deployments/helm/dnk-os/` with parameterized `values.yaml`, `values-staging.yaml`, `values-prod.yaml`.
- **Phase 3: CI/CD GitHub Actions Pipelines**
  - `.github/workflows/ci.yml` (Quality Gate, Lint, Type Check, Security Vulnerability Scanning).
  - `.github/workflows/deploy.yml` (Docker Buildx multi-arch, GHCR publish, automated Blue-Green/Rolling deployment).
- **Phase 4: Healthchecks, Smoke Tests & Evidence Package**
  - Automated deployment test suite in `tests/deployment/`.
  - Verification of Liveness, Readiness, and Startup probes.
  - Master Quality Gate validation (`scripts/verify_all.sh`) & Evidence generation.

---

## 3. Container Security & Multi-Stage Architecture

### Container Profiles:

| Component | Base Image | Multi-Stage Layers | Non-Root UID:GID | Health Check Endpoint |
|---|---|---|---|---|
| **API Backend** | `python:3.12-slim` | `builder` -> `runner` | `10001:10001` (`appuser`) | `GET /api/v1/health/liveness` |
| **Web Frontend** | `node:20-alpine` | `deps` -> `builder` -> `runner` | `10001:10001` (`nextjs`) | `GET /api/health` |
| **Background Worker** | `python:3.12-slim` | `builder` -> `runner` | `10001:10001` (`appuser`) | `python -m services.health_worker` |
| **Database** | `pgvector/pgvector:pg16` | Official Alpine | `999:999` (`postgres`) | `pg_isready -U dnk -d dnk_os` |
| **Cache/Bus** | `redis:7-alpine` | Official Alpine | `999:999` (`redis`) | `redis-cli ping` |
| **Gateway** | `nginx:1.27-alpine` | Alpine Reverse Proxy | `101:101` (`nginx`) | `GET /healthz` |

---

## 4. Kubernetes Topology & Resource Allocation

```
[ Internet / Clients ]
         │ (HTTPS / TLS 1.3)
         ▼
[ Ingress Controller (Nginx / Traefik + Cert-Manager) ]
         │
    ┌────┴──────────────────────────┐
    ▼                               ▼
[ Service: dnk-web ]          [ Service: dnk-api ]
  (ClusterIP :3000)             (ClusterIP :8000)
    │                             │
    ├──► Pod: dnk-web-1           ├──► Pod: dnk-api-1 (HPA: min 2, max 10)
    └──► Pod: dnk-web-2           ├──► Pod: dnk-api-2
                                  └──► Pod: dnk-api-3
                                          │
                                  ┌───────┴───────────────┐
                                  ▼                       ▼
                         [ StatefulSet: db ]     [ StatefulSet: redis ]
                           (PostgreSQL + pgvector) (Redis Sentinel/AOF)
                                  ▲                       ▲
                                  │                       │
                         [ Deployment: dnk-worker ] ──────┘
                           (TaskDNA / EventStream)
```

---

## 5. Master Quality Gate & Compliance

- **MRH Header**: Mandatory on all YAML, Dockerfile, Python, and Markdown files (`DNK-STD-0075`).
- **Path Hygiene**: 100% relative paths (`./`, `../`), zero hardcoded absolute filesystem paths.
- **Security Scans**: 0 High/Critical CVEs allowed in base container images.
- **Verification**: `tests/deployment/` test suite integrated into `scripts/verify_all.sh`.
