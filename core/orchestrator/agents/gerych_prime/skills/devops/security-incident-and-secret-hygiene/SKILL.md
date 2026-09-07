---
name: security-incident-and-secret-hygiene
description: "Use when handling secret leaks, token rotation, PR scans."
category: devops
version: "1.1.0"
author: "DNK OS Architecture & Security Team"
license: "MIT"
metadata:
  hermes:
    tags: ["security", "secret-hygiene", "tokens", "incident-response", "pr-verification", "least-privilege", "secret-scanner", "history-sanitation"]
    related_skills: ["github-pr-workflow", "requesting-code-review"]
---

# 🛡️ Security Incident & Secret Hygiene Protocol

Standard operating procedure for preventing, detecting, and remediating secret leaks, enforcing least-privilege token access, maintaining fail-closed CI gates, and handling safe Git history sanitation.

## When to Use
- Whenever a token, API key, or credential appears in terminal output, logs, chat, or commit diffs (P0 Incident).
- Before creating or approving Pull Requests (Pre-commit / Pre-merge Secret Gate).
- When configuring agent credentials or generating non-sensitive verification evidence.
- When planning or executing historical credential purging and Git history rewriting.

---

## 🚨 P0 Incident Lifecycle & State Machine

Never claim an incident is "fully remediated" prematurely. Strict state machine:

1. **State: `containment_in_progress` (Fail-Closed)**
   - Hardcoded fallbacks removed from current tracked tree.
   - PR merge strictly blocked (`merge_permitted: false`).
   - `old_token_revoked` set to `awaiting_owner_action` until explicit owner confirmation.
   - No sensitive token values in chat, terminal, PR body, or JSON evidence.
2. **State: `contained_rotation_complete`**
   - Owner revokes compromised credential in provider console.
   - New least-privilege credential created and stored exclusively in Secrets Vault or ignored `.env`.
   - Re-scans of current tree and PR diff return 100% clean.
3. **State: `historical_sanitation_planned` / `remediated`**
   - For repository history leaks, a separate isolated plan (e.g., `SEC-HISTORY-001`) is prepared and executed under owner supervision.

---

## 🔍 Centralized Secret Scanner SSOT & Patterns

Use word boundaries (`\b`) and precise token delimiters (including underscores):

```python
SECRET_PATTERNS = {
    "github_classic_pat": r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b",
    "github_fine_grained_pat": r"\bgithub_pat_[A-Za-z0-9_]{20,}\b",
    "aws_access_key": r"\bAKIA[0-9A-Z]{16}\b",
    "google_api_key": r"\bAIza[0-9A-Za-z_-]{20,}\b",
    "openai_or_compatible_key": r"\bsk-[A-Za-z0-9_-]{20,}\b",
    "shopify_admin_token": r"\bshpat_[A-Za-z0-9]+\b",
    "shopify_secret": r"\bshpss_[A-Za-z0-9]+\b",
}
```

### Scanner Invariants & Exactness Rules
- **Exact PAT Syntax**: Always enforce the literal underscore `_` directly following prefix classes. Example: `r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"`, NOT `r"\bgh[pousr][A-Za-z0-9_]{20,}\b"`.
- **Pattern Contract Tests & Anti-Pattern Prevention**: Every security scanner test suite MUST contain an exact contract test asserting literal regex strings from `SECRET_PATTERNS`. CRITICAL PITFALL: Ensure contract tests assert the *correct security specification*, not the buggy implementation. Codifying an incorrect regex (e.g. asserting missing `_` literal) formally enforces a broken security policy as passing.
  ```python
  def test_github_classic_pat_pattern_contract() -> None:
      # Must assert literal underscore after prefix class:
      assert SECRET_PATTERNS["github_classic_pat"] == r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"
  ```
- **Mandatory Negative & Boundary Unit Tests**: Every secret detector pattern MUST include negative test cases in `test_secret_scanner.py`:
  - Missing delimiter on long realistic strings (e.g. `ghpabcdefghijklmnopqrstuvwxyz1234567890` -> 0 findings, while `ghp_...` -> 1 finding)
  - Wrong separator (e.g. `ghp-example-placeholder` -> 0 findings)
  - Below minimum length boundary (e.g. `ghp_` -> 0 findings)
  - Boundary/prefix corruption (e.g. `xghp_...` -> 0 findings)
- **Evidence & Code Synchronization**: JSON audit evidence (`DNK-SECURITY-REMEDIATION-xxx.json`) MUST match the scanner SSOT code byte-for-byte. Never report premature `contained_rotation_complete` or `merge_permitted: true` until:
  1. GitHub diff visibly contains the exact required pattern;
  2. Contract and negative tests pass;
  3. Token revocation is confirmed by the owner;
  4. PR diff scans are 100% clean.
- **Immediate Containment on Accidental In-Chat Leak**: If a user or process pastes a new token into chat or terminal, immediately issue a P0 alert instructing revocation without repeating, logging, or persisting the exposed secret.
- **Redaction First**: Never print the matched secret in stdout, logs, or error messages. Output only secret type, file path, line number, and a fingerprint (e.g., `gho_...[REDACTED]...cdef`).
- **Fail-Closed Gate**: Scanner MUST return a non-zero exit code (`exit(1)`) on any un-allowlisted candidate.
- **Strict Allowlist**: Allowlist ONLY explicitly harmless test placeholders (e.g., `ghp_example_...`, `AKIAEXAMPLE...`). Never allow real token prefixes.
- **Verifiable Reporting**: In security audit reviews, quote the exact source line and diff from tracked files rather than paraphrasing regex patterns.
- **GitHub Diff Verification vs Local Narrative**: Never substitute narrative summary reports for GitHub-verifiable evidence. Every security closeout gate requires:
  1. Pull Request URL & Branch Head SHA.
  2. Direct GitHub file diff links for scanner, tests, and CI workflows.
  3. Non-sensitive incident JSON state (`status: containment_in_progress`, `old_token_revoked: awaiting_owner_action`, `merge_permitted: false`).
  4. Explicit negative test proof verifying delimiter enforcement (`ghp...` without literal `_` does not match).
- **Phantom PR & Loop-Breaking Invariant**: Always verify remote branch and PR existence via `gh pr list` / `gh pr view` or `git ls-remote` before entering an audit wait loop. If an agent or collaborator references a non-existent ("phantom") PR or simulated local state, immediately query remote status to verify. If the PR does not exist on GitHub:
  1. Break the waiting loop immediately.
  2. Confirm whether root credential revocation has been completed by the owner (Containment Complete).
  3. Defer secondary hardening (scanner regex, test suites) to normal development tasks rather than blocking indefinitely on non-existent PR artifacts.
- **Automated Audit False-Positive Invariant**: When building or running security scan scripts (e.g. `security_audit.sh` or pre-commit checks) checking for hardcoded credentials:
  1. *Build Artifact Exclusion*: Strictly exclude `.next/`, `node_modules/`, `.venv/`, `.git/`, and `dist/` directories to prevent flagging bundled libraries or minified client chunks.
  2. *Literal Assignment vs Argument Pass-Through*: Never rely on naive `grep -r "password="` or `"api_key="`. Distinguish string literal assignments (`password\s*=\s*["'][^"']+["']`) from parameter bindings (`password=req.password`, `password=True`), variable lookups, or regex pattern definitions.
  3. *Virtual/Mock Provider Placeholders*: Explicitly allowlist framework mock keys (e.g. `moa-virtual-provider`, `inspect-only`, `[REDACTED]`) to prevent breaking CI on synthetic test fixtures.

---

## 📋 Non-Sensitive Security Remediation Evidence

When closing a security incident or attaching evidence to a PR, record **only non-sensitive metadata**.

Example `docs/audit/DNK-SECURITY-REMEDIATION-xxx.json`:
```json
{
  "incident_id": "SEC-INC-YYYY-MM-DD-001",
  "status": "containment_in_progress",
  "merge_permitted": false,
  "affected_credential": "github_classic_token",
  "historical_leak_commits": ["0d1d71cc97", "0e84bb4103", "ed83177377"],
  "old_token_revoked": "awaiting_owner_action",
  "new_token_least_privilege": {
    "metadata": "read",
    "contents": "read_write",
    "pull_requests": "read_write",
    "admin_scopes": false
  },
  "secret_scan_current_tree": "passed",
  "secret_scan_reachable_history": "scanned_historical_leak_identified",
  "pr_diff_secret_scan": "passed",
  "storage_mechanism": "secrets_vault_and_ignored_env",
  "test_scope": "architecture baseline relevant suite",
  "generated_at": "2026-08-30T17:00:00Z"
}
```

---

## 🧹 Git History Sanitation Protocol (`SEC-HISTORY-001`)

When secrets are committed into historical git revisions:
1. **Scope Separation (MANDATORY)**: Never mix security scanner/hardening implementation code into pure documentation or architecture baseline PRs (e.g. keep PR #55 docs-only, PR #56 for security tooling & gates).
2. **Pre-flight Sanitation Safety Invariants**:
   - Confirm repository visibility (private vs public).
   - Identify all protected branches and active PR branches.
   - Identify linked submodule commits and deployment references (e.g., `DNK_HUB`).
   - Freeze writes / announce maintenance window.
   - Create encrypted off-platform backup of git bundle: `git bundle create dnk_hub_pre_history_rewrite.bundle --all`.
   - Test rewrite on a mirror clone first.
   - Review rewritten refs before force push.
   - Force push only after explicit owner approval.
   - Re-clone production CI checkout after rewrite.
   - Revoke all old credentials even if rewritten history is 100% clean.
3. **Execute via `git-filter-repo`**: Purge exact token expressions across all branches, blobs, and tags.
4. **Integrity Audit**: Run `git fsck --full`, invalidate CI build caches, and coordinate remote force-pushes.
