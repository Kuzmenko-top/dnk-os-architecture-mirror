# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-SEC-038_patchright-execution-sandbox.md"
# purpose: "Security Architecture: Resource isolation, timing defenses, and sandbox security for Patchright."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🛡️ DNK-SEC-038: Patchright Execution Sandbox & Security Hardening

## 1. Threat Model & Sandbox Boundaries
Running full Chromium instances within an autonomous agent framework poses specific security and operational risks:

```
[Agent Core] <--- IPC / gRPC ---> [Isolated Chromium Sandbox] <--- TLS ---> [Target Web Target]
      |                                      |                                       |
  No secrets                             Tmpfs / RAM                              Third-party
  exposed to DOM                         Ephemeral Context                        Malicious JS
```

### Invariant 1: Ephemeral Context Isolation
- Every navigation session MUST launch with an isolated temporary user data directory (`tempfile.mkdtemp()`) stored on ephemeral tmpfs or securely wiped immediately upon context close.
- No cross-site cookie or session contamination between tasks or clients.

### Invariant 2: Secret & Credential Redaction
- DOM extraction results, page HTML, and screenshots MUST be scrubbed before passing into LLM context or SCONES memory.
- Passwords, credit cards, and session tokens are strictly filtered.

### Invariant 3: Proxy & Network Shielding
- High-volume scraping tasks must route through dedicated rotating proxies (Residential / Mobile) to prevent local host IP blacklisting.
- Strict DNS resolution guards to prevent SSRF against internal cluster services (`localhost`, `127.0.0.1`, `10.0.0.0/8`, `169.254.169.254`).

### Invariant 4: Resource & Process Governance
- Chromium child processes must be bounded with hard memory caps (e.g. 1GB per instance) and strict execution timeouts (default: 45s).
- Unhandled or zombie browser processes are auto-reaped via process supervisor to prevent host resource starvation.
