# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/audit_exclusion_manifest_patterns.md"
# purpose: "Audit Exclusion Journal & Fingerprinted Assimilated Project Registry patterns."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-01"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ Audit Exclusion Journal & Assimilated Project Registry Patterns

## 🎯 Purpose
To prevent catastrophic audit latency, context flooding, and false-positive churn during full-depth repository audits by registering high-scale assimilated applications, vendored libraries, secret stores, and runtime environments in a centralized SSOT manifest.

---

## 📋 1. Three-Tier Exclusion Taxonomy

```yaml
# config/audit_exclusions.yaml

# Category 1: Ephemeral Runtime, Build Caches & Test Artifacts
environments_and_build:
  - ".venv"
  - "node_modules"
  - ".next"
  - "dist"
  - "build"
  - "__pycache__"
  - ".pytest_cache"
  - ".turbo"
  - ".git"
  - "audio_cache"
  - "image_cache"
  - "terminal-sessions"
  - "pastes"
  - "logs"
  - "state.db"

# Category 2: Secrets, Private Keys & Local Ephemeral Databases
secrets_and_credentials:
  - "auth.json"
  - "*.pem"
  - "*.key"
  - "*.token"
  - ".env"
  - ".env.*"
  - "*.db"
  - "*.sqlite*"

# Category 3: Certified Assimilated Projects (High-Scale Vendored Trees)
assimilated_projects:
  - id: "open-design-lab"
    name: "Open Design Lab"
    path: "projects/open_design_lab"
    category: "assimilated_app"
    license: "Apache-2.0"
    track: "Track 1 (Permissive)"
    audit_status: "VERIFIED"
    skip_deep_scan: true
    fingerprint_manifest: "projects/open_design_lab/README.md"
```

---

## ⚡ 2. Structural Fingerprint Verification (Zero-Waste Traversal)

When full-depth repository auditors (`scripts/system/full_directory_audit.py`) traverse the file tree:
1. Prune traversal at the top-level boundary of registered assimilated projects.
2. Compute or verify a deterministic SHA-256 fingerprint from the project's root manifest / lockfile / README.
3. Log the verified fingerprint in the audit ledger without recursing into thousands of nested node/source files.
4. Keep the Master Quality Gate (`bash scripts/verify_all.sh`) fast, robust, and 100% green.
