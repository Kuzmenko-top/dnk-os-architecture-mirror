---
mrh_id: "docs/reports/DNK_FULL_SYSTEM_AUDIT_REPORT.md"
purpose: "Comprehensive Full-Depth Directory & Security Audit Report with Exclusion Journal SSOT integration."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Verified"
version: "1.1.0"
updated_at: "2026-09-02"
author: "Gerych Core (Audit Engine)"
---

# 🛡️ DNK OS Comprehensive Full-Depth System Audit Report

**Execution Date**: `2026-09-02 22:39:24`  
**Workspace SSOT**: `$HUB_ROOT`  
**Auditor**: `Gerych Core (Swarm Auditor & Assimilation Engine)`  

---

## 📊 1. Executive Summary & Health Metrics

| Metric | Value | Status |
|---|---|---|
| **Total Directories Visited** | `1018` | 🟢 Complete |
| **Active Files Audited** | `5716` | 🟢 Verified |
| **Total Lines of Active Code** | `1,803,492` | 🟢 Scanned |
| **MRH Header Compliance** | `58.92%` (1675/2843) | 🟡 Active Transition |
| **Path Hygiene Violations** | `737` | ⚠️ Violations Tracked |
| **Secret / Key Leak Violations** | `16` | 🚨 Action Required |
| **Certified Assimilated Projects** | `6` | 🛡️ Fingerprinted & Protected |
| **Pruned Environment / Cache Trees** | `331` | ⚡ Zero-Waste Skip Active |

---

## 🧬 2. Certified Assimilated Projects (Exclusion Journal SSOT)
The following high-scale assimilated projects and vendored frameworks are certified and monitored via structural fingerprints, eliminating redundant recursive file churn during audits:

| ID | Subsystem Name | Path | License Track | Status | Fingerprint |
|---|---|---|---|---|---|
| `open_design_visual_shell` | **Open Design Visual Shell Reference Monorepo** | `visual_shell/open_design` | `Apache-2.0` (Track 1 (Permissive)) | `VERIFIED_ASSIMILATED` | `69bf5104af33cacb` |
| `hermes_agent_framework` | **Hermes Agent Framework Core (Nous Research Upstream Engine)** | `core/hermes_agent` | `MIT` (Track 1 (Permissive)) | `VERIFIED_ASSIMILATED` | `91e857a996553efb` |
| `gerych_prime_lsp` | **Gerych Prime LSP Tooling & Type Definitions** | `core/orchestrator/agents/gerych_prime/lsp` | `MIT / Apache-2.0` (Track 1 (Permissive)) | `VERIFIED_VENDORED` | `b1af047ac64ebde2` |
| `herich_librarian_lsp` | **Herich Librarian LSP Tooling & Type Definitions** | `core/orchestrator/agents/herich_librarian/lsp` | `MIT / Apache-2.0` (Track 1 (Permissive)) | `VERIFIED_VENDORED` | `cdf891f0628748ec` |
| `dnk_e_com_storefront` | **DNK E-Commerce Shopify OS 2.0 Theme Core** | `projects/03_DNK_E_COM` | `Proprietary / DNK OS` (Track 1 (Permissive)) | `VERIFIED_ASSIMILATED` | `8f4d9088121acfab` |
| `open_design_lab` | **Open Design Lab (Assimilated Canvas & Rendering Subsystem)** | `projects/open_design_lab` | `Apache-2.0` (Track 1 (Permissive)) | `VERIFIED_ASSIMILATED` | `a956ce15cf7cc02f` |

---

## 📁 3. Active Code Base Breakdown by File Extension

| Extension | Files Count | Lines of Code | Description |
|---|---|---|---|
| `.md` | `1553` | `219,108` | Markdown / Docs |
| `no_ext` | `1274` | `363,906` | Source / Config |
| `.py` | `1148` | `195,209` | Python Module |
| `.liquid` | `541` | `213,373` | Source / Config |
| `.json` | `268` | `223,843` | JSON / Schema |
| `.ts` | `212` | `25,974` | TypeScript / React |
| `.tsx` | `176` | `28,981` | TypeScript / React |
| `.js` | `117` | `33,107` | Source / Config |
| `.yaml` | `93` | `12,464` | YAML Spec |
| `.svg` | `34` | `141` | Source / Config |
| `.sh` | `32` | `3,028` | Shell Script |
| `.css` | `29` | `26,551` | Source / Config |
| `.sty` | `26` | `13,692` | Source / Config |
| `.tex` | `22` | `8,124` | Source / Config |
| `.jsx` | `19` | `2,631` | Source / Config |
| `.yml` | `17` | `1,068` | YAML Spec |
| `.png` | `17` | `160,357` | Source / Config |
| `.toml` | `12` | `199` | Source / Config |
| `.gitkeep` | `11` | `0` | Source / Config |
| `.lock` | `10` | `1,766` | Source / Config |

---

## ⚠️ 4. Path Hygiene Violations (Hardcoded Absolute Paths)

| File | Line | Snippet |
|---|---|---|
| `AGENTS.md` | Line 25 | `- Relative paths ONLY (`./`, `../`). Never construct or pass absolute `~` paths in tool calls, file searches, i` |
| `core/security/adversarial_review.py` | Line 122 | `description="Detected forbidden hardcoded user absolute path (~).",` |
| `core/security/adversarial_probe_library.py` | Line 342 | `path_pattern = re.compile(r'(?:/Users/|/etc/|/var/|C:\\|[a-zA-Z]:\\|\.\./|\%2e%2e)', re.IGNORECASE)` |
| `core/playbooks/scripts/legacy_relevance_auditor.py` | Line 92 | `if "/Users/" in content:` |
| `core/playbooks/scripts/enforce_relative_paths.py` | Line 19 | `pattern = re.compile(r"/Users/[a-zA-Z0-9_\.]+/")` |
| `core/orchestrator/agents/gerych_auditor/SOUL.md` | Line 8 | `- Performing static analysis, path hygiene audits (detecting hardcoded `~` paths or nested directories).` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_130439_297bdc_20260902_140754_633551.json` | Line 21 | `"content": "[The user attached an image but it couldn't be analyzed. You can try examining it with vision_analyze using ` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_130439_297bdc_20260902_140754_633551.json` | Line 32 | `"arguments": "{\"image_url\":\"$HUB_ROOT/core/orchestrator/agents/gerych_prime/i` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_130439_297bdc_20260902_140754_633551.json` | Line 59 | `"content": "{\"success\": true, \"name\": \"sota-repository-assimilation\", \"description\": \"Audit and assimilate open` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_130439_297bdc_20260902_140754_633551.json` | Line 84 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_130439_297bdc_20260902_140754_633551.json` | Line 117 | `"content": "{\"output\": \"/usr/local/bin/node\\n/usr/local/bin/npm\\n/usr/local/bin/pnpm\\n/usr/local/bin/npx\\n/usr/lo` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_162222_046250.json` | Line 53 | `"content": "{\"success\": true, \"name\": \"sota-repository-assimilation\", \"description\": \"Audit and assimilate open` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_162222_046250.json` | Line 84 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_162222_046250.json` | Line 109 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_162222_046250.json` | Line 184 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_162222_046250.json` | Line 209 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_162222_046250.json` | Line 234 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_162222_046250.json` | Line 259 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_162222_046250.json` | Line 284 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_162222_046250.json` | Line 309 | `"content": "{\"bytes_written\": 7947, \"dirs_created\": true, \"verified\": true, \"lint\": {\"status\": \"skipped\", \"` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_162222_046250.json` | Line 334 | `"content": "{\"bytes_written\": 7947, \"dirs_created\": true, \"verified\": true, \"lint\": {\"status\": \"skipped\", \"` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_115513_5325b6_20260902_115645_574240.json` | Line 21 | `"content": "Герич - як тобі ідея? \nЦе фундаментальний крок для переходу від хаотичного накопичення коду до **системної ` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_115513_5325b6_20260902_115534_727795.json` | Line 21 | `"content": "Герич - як тобі ідея? \nЦе фундаментальний крок для переходу від хаотичного накопичення коду до **системної ` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_160710_065895.json` | Line 53 | `"content": "{\"success\": true, \"name\": \"sota-repository-assimilation\", \"description\": \"Audit and assimilate open` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_160710_065895.json` | Line 84 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_160710_065895.json` | Line 109 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_160710_065895.json` | Line 184 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_160710_065895.json` | Line 209 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_160710_065895.json` | Line 234 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| `core/orchestrator/agents/gerych_prime/sessions/request_dump_20260902_160238_b4af21_20260902_160710_065895.json` | Line 259 | `"content": "<untrusted_tool_result source=\"browser_exec\">\nThe following content was retrieved from an external source` |
| ... and 707 more | | |

---

## 🚨 5. Security & Secret Exposure Alerts

| File | Type | Snippet |
|---|---|---|
| `core/orchestrator/agents/gerych_prime/skills/creative/comfyui/scripts/_common.py` | Potential Plaintext Secret | `COMF***_KEY` |
| `core/orchestrator/agents/herich_librarian/skills/creative/comfyui/scripts/_common.py` | Potential Plaintext Secret | `COMF***_KEY` |
| `tests/security/test_security_middleware.py` | Potential Plaintext Secret | `inte***cret` |
| `tests/auth/test_oidc_auth_service.py` | Potential Plaintext Secret | `Caro***d123` |
| `tests/a2a/test_a2a_federation_services.py` | Potential Plaintext Secret | `mesh***2026` |
| `tests/verification/test_secret_scanner.py` | GitHub Personal Access Token | `ghp_***7890` |
| `tests/verification/test_secret_scanner.py` | GitHub Personal Access Token | `ghp_***7890` |
| `tests/verification/test_secret_scanner.py` | GitHub Personal Access Token | `ghp_***7890` |
| `tests/verification/test_secret_scanner.py` | GitHub Personal Access Token | `ghp_***7890` |
| `tests/verification/test_secret_scanner.py` | GitHub Personal Access Token | `ghp_***7890` |
| `tests/verification/test_secret_scanner.py` | GitHub OAuth Token | `gho_***7890` |
| `tests/verification/test_secret_scanner.py` | GitHub OAuth Token | `gho_***7890` |
| `apps/api/routers/checkout_postpurchase_router.py` | Potential Plaintext Secret | `dnk_***cret` |
| `apps/api/services/web_pixel_ingestion.py` | Potential Plaintext Secret | `dnk_***t_v2` |
| `services/dnk_shopify/DNK-e.com/services/dnk_shopify/docs/tech/SHOPIFY_CONNECTION_INTELLIGENCE.md` | Potential Plaintext Secret | `shpa***oken` |
| `services/dnk_shopify/docs/tech/SHOPIFY_CONNECTION_INTELLIGENCE.md` | Potential Plaintext Secret | `shpa***oken` |

---

## 🔒 6. Audit Exclusion Manifest Invariants
- **Environments Excluded**: `.venv`, `node_modules`, `.next`, `dist`, `build`, `__pycache__`, `.pytest_cache`, `.turbo`, `.git`, `.od`, `audio_cache`, `image_cache`, `terminal-sessions`, `pastes`, `logs`.
- **Secrets Excluded**: `.env`, `.env.*`, `*.pem`, `*.key`, `*.token`, `*.db`, `*.sqlite3`, `auth.json`, `processes.json`.
- **Assimilated Projects**: Protected via root manifest fingerprinting (`config/audit_exclusions.yaml`).

**Certification**: 100% Zero-Waste Audit Protocol compliance verified.