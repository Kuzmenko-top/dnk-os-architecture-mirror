# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tasks_DNK-OS-002-TASK-INTAKE"
# purpose: "Task Intake Specification for DNK-OS-002 Server-Side GitHub Read-Only Adapter"
# author: "DNK-e.com Maksym"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

# DNK-OS-002 Task Intake Specification

- **Task Name:** DNK-OS-002 Server-Side GitHub Read-Only Adapter
- **Base Commit:** `6e87df1fea33b02517d9f39cbf6059b55b302760` (`main`)
- **Target Branch:** `feature/dnk-os-002-github-adapter`
- **Scope:** Server-side GitHub read-only adapter (`apps/api/services/github_adapter.py`), normalized models (`github_models.py`), and `GET /api/tasks/{task_id}` metadata integration.

## Invariants & Prohibitions
1. **Zero Browser Token:** GitHub token used exclusively on server side (`GITHUB_TOKEN` env var).
2. **Zero Writes:** No GitHub mutation calls (create PR, push commit, merge, update issue).
3. **Zero DB Migrations:** No schema modifications or database migrations.
4. **Host Lock:** Fixed outbound target `https://api.github.com` with repository allowlist.
5. **Bounded Timeout:** 5.0 seconds timeout with 60-second in-memory TTL cache.
6. **Fail-Closed Security:** 401/403 HTTP errors fail closed with zero fallback.
