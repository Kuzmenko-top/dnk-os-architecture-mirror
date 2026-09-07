# --- DNK-MRH-HEADER ---
# mrh_id: "docs_operations_hermes_upgrade_runbook"
# purpose: "Step-by-step phased runbook for safe staged upgrades of Hermes Agent runtime in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

# 🛠️ Hermes Agent Staged Upgrade Runbook (DNK-HUB-ARCH-002)

## ⚠️ PROHIBITION OF BLIND RSYNC
Direct blind `rsync` or directory overwrites of `core/hermes_agent` are **STRICTLY PROHIBITED**.
Investigation confirmed that `core/hermes_agent` contains active DNK OS modifications and custom components:
- Local modifications in `run_agent.py` and `toolsets.py`
- Custom tools under `tools/`
- Custom lint and validation tools (`check_mrh.py`, `update_mrh.py`)
- Monorepo database caches (`canvas_production_fallback.db`)
- Video and UI audit manifests (`DNK-VIDEO-AUDIT-AND-PLAN.md`)

A blind `rsync` would obliterate these mission-critical integrations. All upgrades must follow the phased staging workflow below.

---

## Phase A: Freeze
Before any operations:
1. Ensure no background cron tasks or active subagents are running.
2. Stop the local Hermes gateway and background workers:
   ```bash
   pkill -f "hermes gateway" || true
   pkill -f "hermes run" || true
   ```
3. Record git status and commit SHA in the hub:
   ```bash
   git rev-parse HEAD > /tmp/dnk_hub_pre_upgrade_sha.txt
   git status --porcelain > /tmp/dnk_hub_pre_upgrade_status.txt
   ```

---

## Phase B: Baseline & State Snapshot
Capture full baseline states and hashes:
```bash
# 1. Backup Hermes state directory
tar -czf ~/.hermes_backup_v0.20.5_$(date +%Y%m%d_%H%M%S).tar.gz ~/.hermes

# 2. Record runtime lock and hashes
uv pip freeze --python core/hermes_agent/.venv/bin/python > /tmp/hermes_v0.20.5_pip_freeze.txt
sha256sum core/hermes_agent/pyproject.toml > /tmp/hermes_pyproject_sha.txt
sha256sum core/hermes_agent/run_agent.py > /tmp/hermes_run_agent_sha.txt
```

---

## Phase C: Staging Runtime Isolation
Install and configure the new version in an isolated sibling directory:
```bash
# 1. Download official upstream v0.21.0 release tarball
curl -L https://github.com/NousResearch/hermes-agent/archive/refs/tags/v2026.8.31.tar.gz -o /tmp/hermes_v0.21.0.tar.gz

# 2. Extract into staging directory
mkdir -p core/hermes_agent_staging
tar -xzf /tmp/hermes_v0.21.0.tar.gz -C core/hermes_agent_staging --strip-components=1

# 3. Create dedicated staging virtual environment
uv venv core/hermes_agent_staging/.venv --python 3.12
source core/hermes_agent_staging/.venv/bin/activate
uv pip install -e core/hermes_agent_staging
deactivate
```

---

## Phase D: Compatibility & Patch Audit
1. **Diff Analysis**: Perform a clean diff between upstream files and DNK customized files:
   ```bash
   diff -u core/hermes_agent_staging/run_agent.py core/hermes_agent/run_agent.py > /tmp/run_agent_dnk_diff.patch || true
   diff -u core/hermes_agent_staging/toolsets.py core/hermes_agent/toolsets.py > /tmp/toolsets_dnk_diff.patch || true
   ```
2. **Port DNK Customizations**: Carefully apply custom patches to `core/hermes_agent_staging/` without copying obsolete upstream code.
3. **Database Migration Verification**: Verify whether `~/.hermes/state.db` schema requires migrations by testing against an isolated SQLite copy:
   ```bash
   cp ~/.hermes/state.db /tmp/hermes_test_state.db
   # Test staging binary on test DB
   ```

---

## Phase E: Canary Testing
Run read-only and sandbox smoke tests in staging:
```bash
# Execute staging test suite
core/hermes_agent_staging/.venv/bin/python -m pytest core/hermes_agent_staging/tests/unit -k "not integration"
```
Verify the 7 core capability gates:
- [ ] Bot Mode persona initialization
- [ ] Peer messaging normalized event emission
- [ ] Cron continuity memory scoping
- [ ] Live subagent steering / stopping
- [ ] Structured schema validation
- [ ] Protected instruction file approval prompts
- [ ] MCP lifecycle and toolset loading

---

## Phase F: Controlled Promotion & Rollback

### Controlled Promotion (Only with Maxim's explicit sign-off)
```bash
# Swap runtimes atomically
mv core/hermes_agent core/hermes_agent_backup_v0.20.5
mv core/hermes_agent_staging core/hermes_agent
# Update system symlink if needed
ln -sf $(pwd)/core/hermes_agent/.venv/bin/hermes ~/.local/bin/hermes
hermes doctor
```

### Rollback Runbook (Triggered on any failure)
```bash
# 1. Terminate running processes
pkill -f "hermes" || true

# 2. Revert runtime swap
rm -rf core/hermes_agent
mv core/hermes_agent_backup_v0.20.5 core/hermes_agent
ln -sf $(pwd)/core/hermes_agent/.venv/bin/hermes ~/.local/bin/hermes

# 3. Restore ~/.hermes if state was touched
# tar -xzf ~/.hermes_backup_v0.20.5_*.tar.gz -C ~/

# 4. Run baseline health check
hermes --version
hermes doctor
```
