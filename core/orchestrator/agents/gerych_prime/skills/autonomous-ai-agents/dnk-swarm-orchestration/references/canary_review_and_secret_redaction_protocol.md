---
mrh_id: "references/canary_review_and_secret_redaction_protocol.md"
purpose: "Systematic Verification of Canary Releases, Secret Leak Prevention, and Shopify Guardrails."
version: "1.0.0"
updated_at: "2026-09-03"
---

# 🛡️ Canary Review, Secret Redaction & Promotion Verification Protocol (Phase F)

This reference outlines the systematic, programmatic verification required during **Phase F (Canary Review & Promotion Recommendation)** before promoting a Swarm candidate (e.g., Hermes v0.21.0) to active Production runtime (v0.20.5).

---

## 🎯 1. The Five Boundaries of Verification

Each Canary/Staging release must be rigorously checked across five security and accounting boundaries:

### A. Evidence Independence & Integrity
All reported test claims must be backed by machine-readable, verifiable logs rather than narrative assertions.
- **Audit File**: `docs/audit/CANARY-PHASE-E-evidence.json`
- **Enforced Fields**:
  - `timestamp`: Precise ISO 8601 start/end timestamps.
  - `commands`: Actual executable CLI commands used to run tests.
  - `exit_codes`: UNIX process exit codes (including expected `SIGTERM / -15` handles).
  - `pids`: Operating system process identifiers of runner & child nodes.
  - `sha256`: Before/after cryptographic hashes of production files (`state.db`, `config.yaml`, `launcher`).
  - `runtime_path`: Path of the virtual environment interpreter executing the candidate.
  - `model_provider`: Active provider and model name (e.g. `vertex:gemini-3.8-flash`).
  - `checksum`: Cryptographic hash of the evidence manifest itself (`docs/audit/PHASE_F_EVIDENCE_MANIFEST.json`).

### B. Secret Boundary (The 5-Sink Leak Prevention Rule)
Redacting outputs with `[REDACTED]` in the final response is **necessary but insufficient**. You must prove that raw sensitive tokens (e.g., Anthropic `sk-ant-`, GitHub `ghp_`, Shopify `shpat_`) never enter any internal or external storage layers.

Verify the **5 Sinks** are 100% clean of raw secrets:
1. **Model Context**: Raw token is completely stripped before being passed to LLM API payloads.
2. **Stdout/Stderr Logs**: Terminal outputs contain only the masked regex replacement.
3. **Event Bus (Audit trail)**: Serially recorded events and event bus dumps contain masked values.
4. **State Checkpoints**: Saved runtime JSON checkpoints are purged of active credentials.
5. **Session DB**: SQL databases (such as `sessions.db`) mask user-agent conversation messages.

*Additionally, file access controls (`file_safety.py`) must intercept and return `Access Denied` on protected credentials/env paths.*

### C. Shopify Mutation Boundary (Policy Engine Gate)
For high-risk environments like `dnk-e.myshopify.com`, write/mutation requests must be blocked at the **policy engine** or **tool gateway** layer, rather than relying on mock APIs.
- **Verification Invariant**: The Policy Engine must intercept write operations (e.g., `theme.publish`, `product.delete`) and throw a forbidden exception (`ShopifyPilotWriteForbiddenError`).
- **Network Validation**: The HTTP interceptor/proxy must log **0 outbound network requests** sent to the Shopify Production endpoint.
- **Audit Logging**: A policy decision event (`denied`) must be recorded in the security log.

### D. Cost Accounting Invariant
Under iterative failure and recovery (retries), token costs must map to a deterministic mathematical relation:

$$\text{parent\_cost} = \text{own\_cost} + \sum \text{accepted\_child\_costs} + \sum \text{accepted\_tool\_costs}$$

- **Retry Attempt Mapping**: 
  - If a child execution fails, its attempt is recorded with `status: failed` and its tokens are added to the billing log (`cost_recorded: true`).
  - No `success_event` is emitted for a failed attempt.
  - The retry runs as a separate, distinct attempt. This prevents double-counting success events while preserving total monetary liability.

### E. Rollback State Preservation SLA
A rollback drill benchmark must prove that reverting the active launcher link to the previous stable release (v0.20.5) is extremely fast and leaves evidence intact.
- **SLA Threshold**: Config/symlink restoration must execute in $\le 30.0$ seconds.
- **Audit Isolation**: Canary verification evidence, logs (`~/.hermes_staging/audit/`), and checkpoints must **not** be deleted or overwritten by the rollback.
- **State Database Forward-Compatibility**: The stable production runner (v0.20.5) must be able to read and write to the shared database (`state.db`) after the staging candidate's execution, without schema corruption.

---

## 🛠️ 2. Verification Automation Script

Always write and execute an automated python test suite to programmatically verify the boundaries.

```python
# Example verification script: scripts/system/verify_phase_f_canary_review.py
import sys
import os
import hashlib
import sqlite3
import yaml

HUB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, HUB_ROOT)

def test_secret_boundary_sinks(raw_secret: str):
    # Verify 1. Checkpoints, 2. Logs, 3. Event Bus, 4. DB
    # Ensure raw_secret is nowhere to be found in plaintext.
    pass

def test_shopify_mutation_policy():
    # Attempt mock mutation; verify ShopifyPilotWriteForbiddenError is thrown.
    # Assert network request count == 0.
    pass
```

---

## 🚀 3. Phase F Sign-Off & Promotion Procedure

1. **Run Auditing Suite**: Run `.venv/bin/python scripts/system/run_canary_suite.py` to ensure functional success.
2. **Execute Boundary Verifier**: Run `.venv/bin/python scripts/system/verify_phase_f_canary_review.py` to assert security and accounting gates.
3. **Generate Evidence Manifest**: Execute `scripts/system/generate_evidence.py` to compile SHA-256 signatures of all involved files.
4. **Draft Reports**: Generate both `PHASE_F_CANARY_REVIEW.md` and `PHASE_F_PROMOTION_RECOMMENDATION.md`.
5. **Await Explicit Command**: Do NOT switch runtime symlinks or modify the production directory. Wait for Maxim's manual confirmation.

---

## 🛠️ 4. macOS Sandboxing, Tempfile, and PYTHONPATH Isolation Pitfalls

When executing multi-agent/multi-version testing in staging vs. production virtual environments, two critical OS-level integration issues can surface:

### A. macOS Sandboxing and `tempfile.NamedTemporaryFile`
- **Symptom**: Spawning virtualenv python subprocesses to execute generated scripts results in `can't open file ... [Errno 2] No such file or directory` or permissions errors, even though the file is reported as created on the parent process.
- **Cause**: On macOS, Python's default temp directory points to a sandboxed `/var/folders/` path. When a subprocess is launched inside an isolated virtual environment (especially via `uv` or custom toolchain paths), OS-level permission restrictions can block the virtualenv python from reading/opening files inside macOS system-private directory bounds.
- **Solution**: Always force the temporary file directory to reside within the active project workspace/staging tree where the runtime environment is guaranteed to have absolute, un-sandboxed access. Pass `dir="."` (or `dir=HERMES_HOME`) into the tempfile creator:
  ```python
  with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=".") as sf:
      sf.write(test_script_content)
      script_path = sf.name
  ```

### B. PYTHONPATH Destructive Overwrite Invariant
- **Symptom**: Subprocesses or unittest runners raise `ImportError: No module named <package>` or fail to resolve project-specific dependencies during boundary testing.
- **Cause**: Directly overwriting `env["PYTHONPATH"] = STAGING_DIR` inside verification scripts completely wipes out preexisting parent or system PYTHONPATH definitions. This starves Python of necessary paths required to locate standard packages.
- **Solution**: Always append/prepend paths using the OS-specific path separator (`os.pathsep`), preserving the existing environment paths:
  ```python
  existing_pythonpath = os.environ.get("PYTHONPATH", "")
  env["PYTHONPATH"] = f"{STAGING_DIR}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else STAGING_DIR
  ```
