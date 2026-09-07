---
name: cloud-native-production-deployment
description: Use when configuring production Docker, K8s, Helm & CI/CD.
version: 1.0.0
author: DNK-e.com Maksym
license: MIT
metadata:
  hermes:
    tags: [docker, k8s, helm, cicd, devops, production]
    related_skills: [docker-compose-troubleshooting, multi-region-edge-routing]
---

# Cloud-Native Production Deployment Architecture

This skill provides the standard architecture and implementation patterns for zero-downtime, security-hardened production deployments using Docker, Docker Compose, Kubernetes (K8s), Helm, and GitHub Actions CI/CD.

## When to Use
- Authoring or hardening multi-stage Dockerfiles (`Dockerfile.api`, `Dockerfile.web`, `Dockerfile.worker`) for production with non-root security.
- Structuring multi-tier `docker-compose.prod.yml` network segmentation (frontend, backend, data).
- Designing Kubernetes manifests and Helm charts with HPA, PDB, RollingUpdate, and Ingress TLS.
- Implementing GitHub Actions CI/CD pipelines with GHCR, Buildx caching, Trivy scanning, and zero-downtime rollouts.

## Core Architectural Invariants

### 1. Multi-Stage Container Hardening
- **Non-Root Execution**: Never run as `root`. Always create and switch to non-root users (e.g. `appuser:10001` or `nextjs:10001`).
- **Minimal Footprint**: Use slim/alpine base images (`python:3.12-slim`, `node:20-alpine`) with multi-stage builds separating build tools from runtime containers.
- **Embedded Healthchecks**: Every Dockerfile must declare an explicit `HEALTHCHECK` with reasonable timeouts and retry intervals.
- **Security Capabilities**: Drop all Linux capabilities (`ALL`) and enforce `readOnlyRootFilesystem` or non-privileged escalation in Kubernetes security contexts.

### 2. Multi-Tier Network Segmentation (Docker Compose)
Isolate tiers to prevent direct database/cache exposure to public ingress:
- `dnk_frontend_net`: Ingress gateway, Next.js web application.
- `dnk_backend_net`: FastAPI API service, Next.js web, background workers.
- `dnk_data_net`: PostgreSQL (`pgvector`), Redis, internal caching layer (isolated from frontend).

### 3. Kubernetes & Helm Cloud-Native Manifests
- **Zero-Downtime Updates**: Configure `RollingUpdate` with `maxSurge: 25%` and `maxUnavailable: 0%`.
- **Three-Tier Probes**:
  - `startupProbe`: Allows cold-start initialization before health checking.
  - `livenessProbe`: Restarts deadlocked or crashed pods.
  - `readinessProbe`: Removes unready pods from the Ingress / Service traffic pool.
- **High Availability & Autoscaling**:
  - `HorizontalPodAutoscaler` (HPA) targeting 70% CPU and 80% Memory utilization.
  - `PodDisruptionBudget` (PDB) with `minAvailable: 1` to survive node drains.
- **Ingress & TLS**: Standard TLS via cert-manager (`letsencrypt-prod`) with automatic SSL redirection and WebSocket proxy headers.

### 4. CI/CD Pipeline Automation (GitHub Actions)
- **Pre-Deploy Quality Gate**: Execute full test suites (`verify_all.sh` / pytest) before building container images.
- **Multi-Arch Build & GHCR Caching**: Use Docker Buildx with GitHub Actions caching (`cache-from: type=gha`, `cache-to: type=gha,mode=max`) for `linux/amd64` and `linux/arm64`.
- **Vulnerability Scanning**: Automated Trivy / Grype container image vulnerability scanning blocking `CRITICAL` CVEs.
- **GitOps Rolling Rollout**: Safe rollout via `helm upgrade --install --wait --timeout 10m` or `kubectl rollout restart`.

## Pitfalls & Defensive Patterns
- **Go Template Syntax in YAML Linters**: Helm template blocks (`{{- if ... -}}`) at the top level of `.yaml` files will fail standard YAML parsers. Ensure template wrappers maintain valid document structure or quote expressions when needed.
- **Database Network Leaks**: Ensure production database services are attached exclusively to backend/data networks, never directly to public/frontend bridge networks.
- **Ephemeral Storage Limits**: In read-only filesystems or non-root containers, mount `emptyDir` or named volumes for writable paths like `/tmp` or cache directories.
