# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-SEC-041_artifact-server-execution-sandbox.md"
# purpose: "Security boundaries, validation sanitization, and SpendGuard policies for Artifact Server"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🛡️ Security Sandbox & Validation: Artifact Server (DNK-SEC-041)

## 1. Input Sanitization & Path Traversal Prevention
- Strict validation on artifact titles and metadata to reject directory traversal patterns (`..`, `/`, `\`).
- Artifact IDs are auto-generated cryptographic tokens (`art_<uuid12>`), preventing user-controlled file path overwrite.

## 2. SpendGuard & Storage Quotas
- Maximum artifact size: 5MB per individual artifact revision.
- Maximum versions per artifact: 100 revisions (auto-pruning or archive hook).
- In-memory bounds: Max 10,000 active cached artifacts before eviction to cold storage.

## 3. License Isolation
- Complete isolation from AGPL-3.0 upstream code. All implementations use native Python 3 standard library and FastAPI without third-party AGPL dependencies.
