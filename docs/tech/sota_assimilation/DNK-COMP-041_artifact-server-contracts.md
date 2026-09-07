# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-COMP-041_artifact-server-contracts.md"
# purpose: "Component contracts and data structures for Artifact Publishing and Revisioning"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 📋 Component Contracts: Artifact Server (DNK-COMP-041)

## 1. REST API Endpoints
- `POST /artifacts` — Create a new artifact (initiates version 1).
- `GET /artifacts` — List published artifacts (filterable by `artifact_type` and `creator`).
- `GET /artifacts/{artifact_id}` — Retrieve artifact details and content (optional `?version=N`).
- `POST /artifacts/{artifact_id}/versions` — Append a new version revision.
- `POST /artifacts/{artifact_id}/comments` — Post an inline review annotation.
- `GET /artifacts/health/status` — Operational health probe.

## 2. Core Schemas
- `ArtifactCreateRequest`: `{ title: str, content: str, artifact_type: str, creator: str, metadata: dict }`
- `ArtifactVersionCreateRequest`: `{ content: str, author: str, change_summary: str, metadata: dict }`
- `CommentCreateRequest`: `{ version: int, author: str, content: str, line_number: Optional[int] }`
- `ArtifactResponse`: Detailed view including current/requested versions, author, and comments.
