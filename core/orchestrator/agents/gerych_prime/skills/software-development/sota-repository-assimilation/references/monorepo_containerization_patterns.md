# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/monorepo_containerization_patterns.md"
# purpose: "Standard patterns for Docker containerization and Next.js SSR build resolution in DNK monorepos."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-31"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Monorepo Containerization & Build Pitfalls

## 1. Docker Build Context Optimization in Monorepos
- **Problem**: When running `docker build` from the repo root in a multi-package monorepo, flat `.dockerignore` patterns (e.g. `node_modules`, `.venv`) only ignore root-level directories. Nested directories across packages get transferred to the daemon, causing multi-gigabyte context uploads and build timeouts.
- **Solution**: Use recursive glob wildcards in `.dockerignore`:
  ```dockerignore
  **/node_modules
  **/.venv
  **/.git
  **/.next
  **/dist
  **/build
  **/.pytest_cache
  **/.coverage
  ```

## 2. Multi-Stage Dockerfile Workspace Targeting
- Multi-stage Dockerfiles must accurately copy the active production web app directory (e.g., `apps/web/` instead of legacy/draft paths like `visual_shell/web_ui/`).
- Install frontend dependencies cleanly using `npm ci || npm install` before running the production build stage.

## 3. Next.js SSR Static Prerender Resolution
- **Problem**: Next.js App Router (`next build`) attempts to statically pre-render pages. Pages that consume runtime query parameters or dynamic browser APIs (such as analytics event streams, canvas query hooks, or monitor consoles) will fail during `next build` if not marked dynamic.
- **Solution**: Add explicit dynamic export at the top of client/monitoring routes:
  ```tsx
  export const dynamic = "force-dynamic";
  ```
- Ensure any window/browser event listeners are wrapped within `useEffect` or safe runtime guards (`typeof window !== 'undefined'`).
