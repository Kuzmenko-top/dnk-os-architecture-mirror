# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/Sector_01_Core/Tree_01_Persistence/Bush_01_Postgres/Flower_DNK_USER_WORKSPACE_MVP_002.md"
# purpose: "Implement PostgreSQL persistence and connection pool for workspace_service."
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Completed"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

# [x] DNK-USER-WORKSPACE-MVP-002: PostgreSQL Persistence & Connection Pool

## 🎯 МЕТА
Замінити in-memory persistence у `workspace_service` на реальний PostgreSQL шар з connection pool, підготувати основу для RLS і Vault.

## 🚧 ОБМЕЖЕННЯ
- Не змінювати `core/` без необхідності.
- Зберегти існуючі API контракти (`/api/v1/workspaces/*`).
- Додати тести на новий persistence layer.
- Використовувати `asyncpg` + `SQLAlchemy 2.0`.

## ✨ ВИМОГИ
- [x] Реалізувати `WorkspaceRepository` з CRUD операціями для:
  - workspaces
  - prompts
  - diffs
  - approvals
  - snapshots
  - commits
  - audit_trail
- [x] Додати Alembic міграції для таблиць:
  - `workspaces`, `workspace_nodes`, `workspace_edges`
  - `workspace_prompts`, `workspace_diffs`, `workspace_approvals`
  - `workspace_snapshots`, `workspace_commits`, `workspace_audit_trail`, `workspace_idempotency_cache`
- [x] Інтегрувати connection pool (`asyncpg.create_pool` у `DatabaseManager`).
- [x] Замінити in-memory словники у `workspace_service` на виклики репозиторію.
- [x] Додати integration tests з PostgreSQL persistence (`tests/workspace/test_workspace_postgres_persistence.py`).

## ✅ DoD (Definition of Done)
- [x] Alembic міграції створено та протестовано (`002_workspace_persistence_tables.py`).
- [x] `workspace_service` підтримує та використовує PostgreSQL репозиторії.
- [x] Додано integration tests (pytest + asyncpg).
- [x] CI проходить (78/78 tests pass, path hygiene verified).
- [x] Документація оновлена (`docs/reports/LAST_EXECUTION_REPORT.md`).
