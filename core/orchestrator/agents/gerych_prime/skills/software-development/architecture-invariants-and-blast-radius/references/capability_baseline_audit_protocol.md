# Evidence-Backed Capability Baseline & Architecture Audit Protocol

This protocol guides autonomous agents when conducting a read-only architecture capability baseline and technical audit across large multi-domain repositories (e.g. 2,000+ tests, micro-services, and multi-tier agent runtimes).

## 1. Core Audit Invariants

1. **Strict Read-Only Stance**:
   - Zero modifications to existing source code, configuration, or test files.
   - Do not refactor, clean up, or touch files during the audit pass.
   - Output must be consolidated into a single evidence-backed baseline report (e.g. `docs/audit/DNK_OS_CAPABILITY_BASELINE_v0.1.md`).

2. **Honest Status Classification (No Hallucinated Readiness)**:
   - `PROVEN`: Verified by an executed test suite command, exit code 0, recent commit hash, or verifiable machine evidence artifact.
   - `PARTIAL`: Module exists and partially works, but has failing tests, drift in schema/contracts, or flaky execution.
   - `DOCUMENTED_ONLY`: Present in markdown, specs, or prompt profiles, but without executable code or tests.
   - `UNKNOWN`: Module or behavior cannot be proven without external infrastructure or unauthenticated third-party services.
   - **Never** declare "100%", "production-ready", or "fully completed" without exact executed command output.

## 2. Partitioned Test Suite Discovery (Preventing Monolithic Timeout)

Running 2,000+ tests monolithically (`pytest`) often times out or exhausts memory. Partition tests by domain suites and run fast bounded passes:

```python
# Scan and test domain suites independently
suites = [
    'tests/core',
    'tests/canvas',
    'tests/a2a',
    'tests/auth',
    'tests/security',
    'tests/shopify',
    'tests/analytics',
    'tests/monitoring',
    'tests/deployment'
]
# Run pytest per suite with short timeout and summary-only reporter
# e.g., ./.venv/bin/pytest tests/core/test_task_triage.py -q
```

## 3. Interpreter & Environment SSOT Check

Always verify the active virtual environment before running diagnostic scripts:
- Standard system Python (`/usr/bin/python3`) often lacks project dependencies (`yaml`, `pytest`, `fastapi`).
- Explicitly invoke `./.venv/bin/python3` and `./.venv/bin/pytest`.

## 4. Route & Entry Point Reality Check

Do not trust documentation for API and frontend routes; extract live definitions:
- **FastAPI Endpoints**: Parse `apps/api/main.py` for all `app.include_router(...)` calls. Detect accidental duplicate router inclusions that inflate OpenAPI schemas.
- **Next.js Pages**: Scan for `app/**/page.tsx` and `pages/**/*.tsx` to index true reachable frontend routes.
- **CLI & Launchers**: Verify launcher scripts (`scripts/system/gerych.sh --version`) and check for process locking mechanisms (`process_guard.py`).

## 5. Architectural Debt & Risk Detection Pattern

Inspect for:
1. **Duplicate Router Mounts**: Search `apps/api/main.py` for repeated router registrations.
2. **External CLI Token Reliance**: Check if runtime launchers depend on external interactive CLI state (e.g. `gcloud auth print-access-token` 40-min cached tokens).
3. **Vault / Docs Desynchronization**: Verify note-sync tests (e.g. Obsidian markdown filenames) to catch naming drift early.
