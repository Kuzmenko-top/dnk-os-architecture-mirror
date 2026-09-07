# Monorepo Double-Nesting & Repository Reconciliation Protocol

## Overview
When auditing large repositories with submodules or nested checkouts (e.g., `DNK_HUB` with embedded `DNK_HUB`), repositories can suffer from "Double-Hub Mirroring" where duplicate folder trees drift out of sync across root and submodules.

## 🚨 Diagnosis Signals (Double-Nesting & Drift)
1. **Parallel Tree Structure**: Root directory (`DNK_HUB`) and nested directory (`DNK_HUB`) both contain top-level `apps/`, `services/`, `core/`, `scripts/`, `tests/`, `docs/`, `skills/`, `plugins/`.
2. **Tracked File Mirroring**: `git ls-files` in root reports ~14,000+ files, while `git ls-files` inside the nested checkout reports ~14,000+ identical files.
3. **Submodule Mapping Errors**: `git status` or `git submodule status` fails with `fatal: no submodule mapping found in .gitmodules` (e.g. for `services/dnk_shopify/DNK-e.com`).
   * **Remediation**: Either cleanly strip the internal git tracking via `rm -rf services/dnk_shopify/DNK-e.com/.git` and `git rm --cached services/dnk_shopify/DNK-e.com` (to commit as regular files inside the monorepo), or declare the proper URL mapping in a root `.gitmodules` file.
4. **Code Drift**: Modifications occur in root `apps/web/` while agents or automated scripts target `apps/web/`.

## 🛠️ Audit & Reconciliation Sequence
1. **Divergence Probe**:
   ```bash
   diff -qr --exclude='.git' --exclude='.venv' --exclude='node_modules' --exclude='__pycache__' apps/ apps/
   ```
2. **Single Source of Truth (SSOT) Decision**:
   - Establish root (`DNK_HUB`) as the unified monorepo.
   - Reconcile all unique or newer changes from the nested checkout (`DNK_HUB`) into root.
3. **Loose Asset Quarantine**:
   - Relocate root-dumped assets (e.g., Shopify theme files `assets/`, `sections/`, `snippets/`, `layout/`, `locales/`, `shopify.theme.toml`) into their dedicated service module (`services/dnk_shopify/`).
4. **Git Index Clean-up & Hygiene**:
   - Remove tracking of `.DS_Store`, local fallback databases (`canvas_production_fallback.db`), and transient test logs.
   - Enforce `.gitignore` entries for `*.db`, `*.sqlite`, `.DS_Store`, `visual_shell_db.json`.

## 🛡️ Monorepo Invariant & Security Verification Checklist
During monorepo audits, run these invariant checks:
1. **Agent Secret Exposure & Sanitization Policy**:
   - Audit `core/orchestrator/agents/*/config.yaml` for raw unmasked access tokens (`gho_...`, `Bearer ...`).
   - Replace with dynamic env variables (`${GITHUB_PERSONAL_ACCESS_TOKEN}`).
   - **Provider Token Containment Invariant**: Never revoke or invalidate credentials on the remote provider (GitHub/cloud) unless explicitly instructed by the user. Sanitize code and configs by substituting placeholders and ensuring secret scanners (`secret_scanner.py`) return 0 defects.
2. **Path Hygiene & Dynamic Root Resolution**:
   - Check all tooling and verification scripts (e.g., `check_mrh.py`, pre-commit hooks) for hardcoded absolute paths (`/Users/...`) or removed legacy directories (`DNK OS`, `DNKOS_MVP`).
   - Derive the repository root dynamically via `pathlib.Path(__file__).resolve().parents[...]`.
   - Exclude high-volume dirs (`node_modules`, `.venv`, `.next`, `visual_shell`, `assets`, `dist`, `build`) in-place in `os.walk` to prevent crawl timeouts.
   - For `DNK-STD-0075` MRH header validation, adhere strictly to canonical fields (`mrh_id`, `purpose`, `author`, `updated_at`/`date`, `version`, `status`). Do not mandate optional fields like `license` which cause false negatives across internal agents.
   - **Agent Checkpoints & Exclusions**: Dynamic JSON states and checkpoints generated under `core/orchestrator/agents/*/checkpoints/` can contain serialization paths. Exclude these from directory audits by declaring `checkpoints` in the `config/audit_exclusions.yaml` list.
3. **Verification Gate Suppression Hygiene & DB Migration Resilience**:
   - Inspect `scripts/verify_all.sh` for suppressed test suites (`-k "not ..."`). Suppressions usually hide integration test failures caused by unhandled environment dependencies (e.g. missing `pgvector` in local PostgreSQL).
   - In test fixtures running DB migrations, gracefully catch `(asyncpg.exceptions.UndefinedObjectError, asyncpg.exceptions.PostgresError)` on optional extension migrations (such as `006_create_knowledge_table.sql`). This unmasks all regression tests so `scripts/verify_all.sh` runs 100% Green without `-k` exclusions.

## 🚨 Remediated Monorepo Health Issues (TaskDNA-REMEDIATION-MONOREPO-HEALTH-003)

### 1. Submodule Integrity & Secret De-escalation
- **Symptom**: `git submodule status` crashes with `fatal: no submodule mapping found in .gitmodules for path 'services/dnk_shopify/DNK-e.com'`. The submodule folder exists on disk, but has no matching configuration in `.gitmodules`.
- **Workaround & Healing**:
  1. Always verify or create a valid `.gitmodules` mapping at root specifying the relative `path`, pure public HTTPS `url`, and `branch`:
     ```ini
     [submodule "services/dnk_shopify/DNK-e.com"]
         path = services/dnk_shopify/DNK-e.com
         url = https://github.com/DNKShopify/DNK-e.com.git
         branch = main
     ```
  2. **Secret Containment**: Check remote configuration of submodules. If there is a secret PAT token hardcoded in `remote.origin.url` (e.g., inside `.git/config` of the submodule), cleanly replace it with public HTTPS:
     ```bash
     git -C services/dnk_shopify/DNK-e.com remote set-url origin https://github.com/DNKShopify/DNK-e.com.git
     ```
  3. Synchronize, initialize, and confirm the submodule status:
     ```bash
     git submodule sync && git submodule init && git submodule status
     ```

### 2. Pre-Commit Guard Interpreter Selection
- **Symptom**: Triggering `python scripts/system/auto_precommit_guard.py` or verification scripts fails with `No module named pytest` or other missing package errors when executed with the global system interpreter.
- **Workaround & Healing**: Always invoke verification, pre-commit, or linting scripts using the explicit project virtual environment Python path:
  ```bash
  .venv/bin/python scripts/system/auto_precommit_guard.py
  ```

### 3. Pydantic Model UTC Deprecations (Python 3.12+)
- **Symptom**: Execution logs emit `DeprecationWarning: datetime.datetime.utcnow() is deprecated` and instruct to use timezone-aware objects.
- **Workaround & Healing**:
  - Replace `datetime.utcnow()` with `datetime.now(UTC)`.
  - Ensure `from datetime import datetime, UTC` is imported.
  - For Pydantic fields or database default schemas, replace `default=datetime.utcnow` with `default_factory=lambda: datetime.now(UTC)` to ensure the timezone-aware timestamp is dynamically generated at object instantiation rather than class compile-time.

### 4. Working Tree Sanitization & SQLite Ignorance
- Ensure local databases (e.g. `canvas_production_fallback.db`, `.db-journal`, `*.lock`, and JSON databases like `apps/api/visual_shell_db.json`) are completely excluded from tracking by appending them to `.gitignore`.
- Remove any cached databases from index:
  ```bash
  git rm --cached canvas_production_fallback.db 2>/dev/null || true
  ```
