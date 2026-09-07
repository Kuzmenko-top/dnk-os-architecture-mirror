# --- DNK-MRH-HEADER ---
# mrh_id: "docs/user-guides/TROUBLESHOOTING.md"
# purpose: "Comprehensive Troubleshooting Guide covering 10 common issues, root causes, and verified fixes."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# DNK OS Troubleshooting Guide

This guide provides immediate diagnosis, root cause analysis, and step-by-step remediation procedures for 10 common issues in DNK OS.

---

## 1. Absolute Path Violation in Preflight Gate
- **Symptom**: `bash scripts/verify_all.sh` fails during Step [2/4] with `Path hygiene violation: found absolute path`.
- **Root Cause**: Hardcoded `/Users/...` or machine-specific paths committed to source code or configuration files.
- **Remediation**:
  1. Inspect the offending file flagged in the preflight output.
  2. Replace absolute strings with relative paths (`./` or `../`).
  3. Re-run `python3 scripts/system/preflight_sync.py --mode fast` to confirm.

---

## 2. WebSocket Connection Dropped (`/ws/canvas`)
- **Symptom**: Canvas UI displays "Disconnected from server. Retrying..." repeatedly.
- **Root Cause**: Missing heartbeat ping within 30 seconds or invalid workspace auth header during initial handshake.
- **Remediation**:
  1. Check browser network tab for WebSocket status code 1006 or 4003.
  2. Verify backend API is running on port 8000.
  3. Ensure client sends periodic ping frames (`{ "type": "ping" }`) every 15s.

---

## 3. High-Concurrency TestClient Thread Deadlock
- **Symptom**: Integration tests hang indefinitely when running parallel load benchmarks.
- **Root Cause**: Reusing a single Starlette `TestClient` instance across multiple concurrent threads.
- **Remediation**:
  1. Isolate `TestClient` instances per worker thread using `threading.local()`.
  2. Set explicit request timeouts (e.g. `timeout=5.0`).
  3. Set `os.environ["TESTING"] = "1"` to bypass security rate limiters during test execution.

---

## 4. SpendGuard Budget Exhaustion (`429 Quota Exceeded`)
- **Symptom**: Agent API calls return `429 Too Many Requests: Workspace budget exceeded`.
- **Root Cause**: Workspace monthly token allocation or USD cap has been reached.
- **Remediation**:
  1. Inspect usage: `dnk_get_workspace_spending("ws-alpha-001")`.
  2. Review heavy R&D loops and optimize token usage with context diet.
  3. Adjust workspace limits in `core/orchestrator/spend_guard.py` if authorized.

---

## 5. Liquid Template Syntax Error in Shopify Validation
- **Symptom**: `dnk_shopify_validate_liquid` reports `Unbalanced tag: {% if %} missing {% endif %}`.
- **Root Cause**: Mismatched Liquid control tags or malformed JSON in `{% schema %}` blocks.
- **Remediation**:
  1. Open the `.liquid` file and verify all block tags (`if`, `unless`, `for`) are properly terminated.
  2. Run `dnk_shopify_validate_liquid(content_or_path="...")` to locate the exact syntax error line.

---

## 6. SCONES Memory Search Returning Stale Results
- **Symptom**: SCONES semantic retrieval returns deprecated architecture rules.
- **Root Cause**: Low importance score on new records or stale cache in vector index.
- **Remediation**:
  1. Insert updated rule with high importance (`importance=0.95`).
  2. Specify exact topic filters in `scones_get_memories(query=topic)`.

---

## 7. Python Virtualenv Module Import Errors (`ModuleNotFoundError`)
- **Symptom**: Pytest fails with `ModuleNotFoundError: No module named 'fastapi'` or similar.
- **Root Cause**: Commands executed with system Python rather than the project virtual environment.
- **Remediation**:
  1. Always invoke tools using `./.venv/bin/pytest` or `./.venv/bin/python`.
  2. Ensure `PYTHONPATH=.` is exported in the shell environment.

---

## 8. Git Commit Blocked by Pre-Commit Watchdog
- **Symptom**: Git commit hook fails with `Pre-commit check failed`.
- **Root Cause**: Unstaged files, failing regression tests, or unformatted files.
- **Remediation**:
  1. Run `bash scripts/verify_all.sh` directly to identify failing checks.
  2. Fix all syntax, security, or unit test errors until tests are 100% Green.
  3. Stage all related changes and re-attempt commit.

---

## 9. Canvas Graph OCC Merge Conflict
- **Symptom**: Server responds with `409 Conflict: Graph revision mismatch` on mutation.
- **Root Cause**: Two clients modified the same canvas node attributes concurrently from different base revisions.
- **Remediation**:
  1. Fetch latest graph snapshot via `GET /api/v1/canvas/graph`.
  2. Execute 3-way structural merge using `dnk_workspace_occ_merge`.
  3. Apply resolved graph state and increment revision counter.

---

## 10. Web Audio API Silent in Browser Tutorial
- **Symptom**: Sound effects do not play during interactive tutorial onboarding.
- **Root Cause**: Browser autoplay policy blocks Web Audio `AudioContext` prior to first user gesture, or sound is muted by user toggle.
- **Remediation**:
  1. Verify user has interacted with the document (click or keypress).
  2. Check `AudioContext.state`; resume via `audioCtx.resume()` inside click handler.
  3. Ensure `soundEnabled` toggle in `RealTimeFeedback` is active.
