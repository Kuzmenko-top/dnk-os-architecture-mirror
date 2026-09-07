# --- DNK-MRH-HEADER ---
# mrh_id: "software-development/adversarial-code-verification/references/adversarial_probe_library.md"
# purpose: "Adversarial Probe Library, ASR Metrics, 3-Stage Gate & Two-Track License Firewall Reference."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Adversarial Probe Library & 3-Stage Active Gate Taxonomy

## 1. 3-Stage Gate Timing & SLAs

| Gate Stage | Target SLA | Trigger | Scope & Checks | Blocker Action |
|---|---|---|---|---|
| **Gate 1: PR Fast-Path** | < 5 min | Pre-commit / `gh pr create` | AST leaks, `/Users/...` paths, MRH headers, basic injection probes | Blocks PR merge |
| **Gate 2: Pre-Deploy** | 10-15 min | Staging deployment | SSRF, SQLi in raw queries, CORS/CSRF, async deadlocks, deep PyRIT probes | Blocks release tag |
| **Gate 3: Production Canary** | 1-2 min | Cron (every 30 min) | Behavioral drift detection, canary endpoints, SLA regressions | Alerts oncall & halts traffic |

## 2. Attack Success Rate (ASR) Formula & Thresholds

$$\text{ASR} = \frac{\text{Confirmed Exploits}}{\text{Total Probes Run} - \text{Refuted False Positives}} \times 100\%$$

- **Target Threshold for PR / Gate Approval:** $\text{ASR} < 5.0\%$ (Target: $0.0\%$).
- **Benign Noise Cutoff:** Any finding refuted by the Blue Team defender layer (e.g. test fixtures, mock data, `[REDACTED]`) is categorized as a false positive.

## 3. Two-Track License Firewall

Integrated into the pre-commit & CI/CD pipeline (`scripts/check_license_policy.py` & `.github/workflows/license-firewall.yml`):

- **Track 1 (Permissive — Auto-Approve)**:
  - Allowed licenses: `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `CC0-1.0`, `Unlicense`, `PSF`, `MIT-0`.
  - Action: Auto-approve; triggers Pydantic adapter creation.
- **Track 2 (Copyleft / Restrictive — Block & Synthesize)**:
  - Restricted licenses: `GPL-2.0`, `GPL-3.0`, `AGPL-3.0`, `LGPL-2.1`, `LGPL-3.0`, `MPL-2.0`, `SSPL`, `EUPL`.
  - Action: Blocked in strict mode; triggers Clean-Room Isolation specification generation (`docs/tech/clean_room/DNK-CLEANROOM-XXX.md`).

## 4. Probe Library Taxonomy (226+ Scenarios)

Categorized attack vectors implemented in `core/security/adversarial_probe_library.py`:

| Category | Count | Key Vectors |
|---|---|---|
| **TOKEN_LEAK** | 25 | Secret key exfiltration, API key dumping, environment variable extraction |
| **PATH_TRAVERSAL** | 15 | Directory escape, system file access, absolute path violations |
| **PROMPT_INJECTION** | 45 | DAN overrides, jailbreak wrappers, delimiter bypass, roleplay hijacking, multi-language bypass |
| **SSRF** | 30 | Cloud metadata (`169.254.169.254`), internal loopback access, DNS rebinding |
| **SQL_INJECTION** | 35 | Raw query exploits, ORM bypass, time-based blind SQLi (`pg_sleep`) |
| **ASYNC_DEADLOCK_REDOS** | 36 | ReDoS catastrophic backtracking, unawaited async deadlocks, blocking sleep |
| **CORS_CSRF** | 40 | Wildcard origin headers, null origin bypass, unauthorized cross-site requests |

## 5. Pitfalls & Best Practices

- **Path Hygiene Compatibility**: Probe test payloads must use generic placeholders (`/Users/<username>/`) rather than hardcoded real user paths to avoid triggering static path hygiene checkers.
- **Inline Python Escaping**: In bash verification scripts (`verify_all.sh`), avoid double-quote string escaping issues in Python one-liners by assigning dictionary lookups to temporary local variables.
