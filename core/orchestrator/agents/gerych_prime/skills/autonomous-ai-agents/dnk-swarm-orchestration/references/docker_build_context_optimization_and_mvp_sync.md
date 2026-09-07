# --- DNK-MRH-HEADER ---
# mrh_id: "references/docker_build_context_optimization_and_mvp_sync.md"
# purpose: "Docker Build Context Optimization, .dockerignore Hygiene, and MVP Sync Protocol."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym & Gerych"
# --- END DNK-MRH-HEADER ---

# 🐳 Docker Build Context Optimization & MVP Sync Protocol

## ⚠️ The Problem: Infinite Build Context Transfer & Timeouts
- **Symptom**: Executing `docker compose build` or `./scripts/deploy-mvp.sh` hangs indefinitely or hits the 300s/420s terminal execution timeout during the `transferring context` stage.
- **Cause**: Massive untracked directories, test caches, local sandboxes, and workspace assets (e.g., `visual_shell` [3.2 GB], `core/orchestrator/` [2.1 GB]) are copied into the Docker daemon build context because they are missing from the global or project-level `.dockerignore` file.
- **Impact**: Slow deployments, disk space exhaustion on development VMs, and broken automated MVP deployment loops.

---

## 🛠️ The Solution: Bulletproof `.dockerignore` Hygiene
Ensure the global `.dockerignore` at root (and any service-specific `.dockerignore` files) strictly excludes massive non-runtime dependencies while keeping required shared folders (e.g., `core/security` or `core/runtime_events` inside `core/`).

### Recommended Root `.dockerignore` Rules
```ignore
# Exclude massive local sandboxes & workspaces
visual_shell/
core/orchestrator/
core/hermes_agent_staging/

# Standard package manager and compilation targets
.venv/
venv/
__pycache__/
node_modules/
.next/
.git/
.gitignore
.DS_Store
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.hermes/
core/orchestrator/agents/*/sessions
core/orchestrator/agents/*/terminal-sessions
core/orchestrator/agents/*/cache
```

*By applying these rules, the build context size shrinks from **5.3 GB** to **~5 MB**, reducing build-time transfer from minutes/timeouts to less than **5 seconds**.*

---

## ⚙️ Docker Compose & Container Sync Protocol

1. **Rebuilding Stale Containers**:
   - Web interface and API endpoints are built into static container layers during `docker compose build`.
   - Modifying local files (such as `crud.py`, `main.py`, or Next.js components) WILL NOT reflect in running containers unless a rebuild and restart is triggered.
   - Run:
     ```bash
     bash scripts/deploy-mvp.sh
     ```
     or manually:
     ```bash
     docker compose -f docker-compose.mvp.yml down
     docker compose -f docker-compose.mvp.yml up --build -d
     ```

2. **Pre-flight Port Auditing**:
   - Before attempting `docker compose up`, verify that standard e-commerce and local-first ports are free:
     * Next.js: `3000`
     * FastAPI: `8000`
     * PostgreSQL: `5432`
     * Redis: `6379`
   - Release occupied ports by killing conflicting PIDs or stopping competing docker compose projects.
