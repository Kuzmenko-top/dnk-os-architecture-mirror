# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-SEC-040_personalive-execution-sandbox.md"
# purpose: "Security Sandbox & Hardening: Path traversal, SpendGuard, and rate limiting"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🛡️ Security Hardening DNK-SEC-040: PersonaLive

## 1. Path Traversal & File Access Sanitization
- Input paths for `reference_image` and `audio_source` are strictly sanitized:
  - Must NOT contain `..` path escalation patterns.
  - Must NOT start with absolute root `/` or system paths (`/etc/`, `/var/`, `/sys/`).
  - Violations immediately raise `ValueError` and trigger HTTP 400 Bad Request.

## 2. SpendGuard GPU Ceiling Enforcement
- Every request dynamically computes duration = `max_frames / fps`.
- Cost is tracked cumulatively and bounded by `spendguard_budget_usd`.
- Exceeding the ceiling triggers `RuntimeError` and HTTP 429 Too Many Requests.
