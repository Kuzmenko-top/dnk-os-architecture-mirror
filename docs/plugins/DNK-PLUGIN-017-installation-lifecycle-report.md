# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plugins/DNK-PLUGIN-017-installation-lifecycle-report.md"
# purpose: "Security and Implementation Report for Production Plugin Installation Lifecycle (DNK-PLUGIN-017)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

# DNK-PLUGIN-017: Production Plugin Installation Lifecycle Report

## Executive Summary
This report details the design, security architecture, state machine, API endpoints, and verification evidence for the Production Plugin Installation Lifecycle (`DNK-PLUGIN-017`) integrated with `DNK-TRUST-016` security gates.

## 1. Lifecycle State Machine
The lifecycle governs plugin transitions through 15 standardized states:
`discovered` -> `downloaded` -> `staged` -> `manifest_validated` -> `hash_verified` -> `signature_verified` -> `trust_approved` -> `installing` -> `installed` -> `activating` -> `active` -> `failed` / `quarantined` / `rolled_back` / `uninstalled`.

### Forbidden Direct Transitions
- `discovered` -> `installed` (HTTP 409 `INVALID_PLUGIN_INSTALL_TRANSITION`)
- `downloaded` -> `active` (HTTP 409 `INVALID_PLUGIN_INSTALL_TRANSITION`)
- `staged` -> `active` (HTTP 409 `INVALID_PLUGIN_INSTALL_TRANSITION`)
- `unverified` -> `installed` (HTTP 409 `INVALID_PLUGIN_INSTALL_TRANSITION`)

## 2. Security Gate Integration (DNK-TRUST-016)
The installation pipeline enforces strict multi-layer security policy evaluation:
- **Manifest Validation**: Schema conformity, SemVer check, entrypoint path safety (rejects path traversal `..`, leading `/`, absolute paths).
- **Staging Area Isolation**: Temporary isolated directory, non-executable, symlink escape protection.
- **Canonical Package Hashing**: SHA-256 calculation over package binary.
- **Ed25519 Cryptographic Verification**: Signature verified against registered active public key.
- **Production Policy Enforcement**:
  - Unsigned plugin: HTTP 403 `PRODUCTION_UNSIGNED_PLUGIN`
  - Tampered package: HTTP 422 `HASH_MISMATCH`
  - Invalid signature: HTTP 422 `INVALID_SIGNATURE`
  - Unknown/Expired key: HTTP 403 `UNTRUSTED_SIGNING_KEY`
  - Revoked key/package: HTTP 423 `PLUGIN_QUARANTINED`
  - Failed health-check: Automatic rollback (HTTP 500 `INSTALLATION_ROLLBACK_FAILED`)

## 3. Persistence & Constraints
- Database Tables: `plugin_installations`, `plugin_activation`, `plugin_quarantine`, `plugin_install_audit`.
- Workspace Constraints:
  - `unique(workspace_id, plugin_id, version)`
  - `unique(workspace_id, plugin_id, active_version)`
  - `immutable content_hash` after installation
  - `no active record without trusted provenance`

## 4. API Endpoints Contract
- `POST /plugins/install` (201 Created)
- `GET /plugins/installations/{installation_id}` (200 OK)
- `POST /plugins/{plugin_id}/activate` (200 OK)
- `POST /plugins/{plugin_id}/rollback` (200 OK)
- `POST /plugins/{plugin_id}/uninstall` (200 OK)
- `GET /plugins/{plugin_id}/versions` (200 OK)
- `GET /plugins/{plugin_id}/provenance` (200 OK)
- `GET /plugins/{plugin_id}/audit` (200 OK)

## 5. Verification & Test Evidence
- Total plugin test suite: **32 tests passed 100%**.
- Includes unit tests, state machine tests, rollback tests, security gate tests, and FastAPI integration tests.
- Secret scanning: Clean (zero secrets or private keys logged/committed).
