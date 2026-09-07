# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-IMPL-007_deployment_pipeline"
# purpose: "Technical Specification and Documentation for Docker Containerization, CI/CD Pipeline, and Monitoring Stack"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

# DNK-IMPL-007: Deployment Pipeline Technical Specification

This document specifies the deployment, containerization, orchestration, and monitoring infrastructure for the DNK OS MVP production release.

---

## 1. Docker Containerization

The production app is split into two lightweight, decoupled dockerized components to optimize resource utilization and deployment speed.

### 1.1 API Container (`Dockerfile.api`)
- **Base image**: `python:3.12-slim` (lightweight, stable).
- **Execution entrypoint**: `uvicorn services.dnk_canvas_api.main:app --host 0.0.0.0 --port 8000`.

### 1.2 Web Container (`Dockerfile.web`)
- **Base image**: `node:20-alpine` (highly optimized Node.js base).
- **Compilation**: Executes `npm run build` to generate static pages and SSR artifacts for Next.js 14.
- **Serving**: Runs `npm run start` on port `3000`.

### 1.3 Service Orchestration (`docker-compose.yml`)
Binds `api`, `web`, `db` (pgvector:pg16), and `redis` together into a single, unified Docker network with volume-backed persistent storage (`pgdata`, `redisdata`).

---

## 2. CI/CD (GitHub Actions)

Located at `.github/workflows/deploy.yml`.

The pipeline executes three sequential jobs on every push or PR to `main`:
1. **Test**: Runs the entire pytest suite including validation and path hygiene.
2. **Build**: Builds Docker images for the API and Web applications using buildx.
3. **Deploy**: Triggers remote deployment on the production server via SSH, pulling latest main branch changes, building, and restarting containers.

---

## 3. Monitoring Stack

Located at `monitoring/docker-compose.monitoring.yml`.

- **Prometheus** (`prometheus.yml`): Scrapes CPU/RAM and request counts from API and Web. Evaluates alert rules.
- **Alertmanager** (`alertmanager.yml`): Evaluates alerts routing.
- **Grafana**: Out-of-the-box dashboards for CPU, RAM, error rates, and latencies.
- **Loki**: Centralized log aggregation.

---

## 4. Alert Rules

Located at `monitoring/alerts.yml`.

Two critical triggers are active:
- **HighErrorRate**: Fires if HTTP 500 error rate exceeds `5%` for 5 consecutive minutes.
- **HighResponseTime**: Fires if 95th percentile response latency exceeds `2.0 seconds` for 5 consecutive minutes.

---

## 5. Verification and Tests

Located at `tests/verification/test_deployment_pipeline.py`.

The suite verifies:
1. `test_docker_build_api` - checks API Dockerfile structures and CMD instructions.
2. `test_docker_build_web` - checks Web Dockerfile structures and Next.js building rules.
3. `test_docker_compose_up` - validates docker-compose orchestration schema and dependencies.
4. `test_api_health` - simulates uvicorn backend healthcheck endpoints.
5. `test_web_health` - simulates next.js frontend UP status and API reachability.
6. `test_monitoring_stack` - validates compose-monitoring structures.
7. `test_alerts` - validates alerting rules, expressions, and evaluates thresholds.
