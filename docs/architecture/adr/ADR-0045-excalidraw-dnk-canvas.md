# --- DNK-MRH-HEADER ---
# mrh_id: "docs/adr/ADR-0045-excalidraw-dnk-canvas.md"
# purpose: "Architecture Decision Record: Embedded Excalidraw-based DNK Canvas"
# canonical_source: true
# status: "Accepted"
# version: "1.1.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 🏛️ ARCHITECTURAL DECISION RECORD (ADR-0045)

## TITLE: Embedded Excalidraw Integration for DNK OS Canvas Engine

---

## 1. Context and Problem Statement

For competitive analysis, visual modeling, and strategic ideation, the DNK OS team has been utilizing an external Excalidraw interface. This has introduced serious friction:
- **Data Fragmentation**: Scenes are stored in ephemeral local storage or isolated browser sessions, leading to accidental data loss.
- **Traceability Gap**: No native mapping exists between visual elements (nodes) on the canvas and core entities (Competitors, Insights, Task Forest Flowers, ADRs, or active Agent Runs).
- **Agentic Blindness**: AI agents cannot programmatically query or modify visual layouts to aid human engineers.
- **Asset Bloat**: Large screenshots embedded inside Excalidraw JSON scenes as raw Base64 strings crash databases and sluggishly load over network streams.

---

## 2. Decision: GO / NO-GO for Excalidraw Integration

**Decision: GO (Accepted)**

We will embed `@excalidraw/excalidraw` directly as the official frontend canvas component of DNK OS, while establishing a secure, scalable, and persistent self-hosted backend.

### Comparison: Embedded Excalidraw vs. Alternatives

| Criteria | `@excalidraw/excalidraw` (Winner) | Custom Canvas from Scratch (NO-GO) | Alternative (e.g., Tldraw / ReactFlow) |
| :--- | :--- | :--- | :--- |
| **Development Speed** | **High** (Pre-built rich editor with SVG/PNG/JSON support) | **Extremely Low** (Estimated 6+ months of core work) | **Medium** (Excellent APIs but different user habits) |
| **UX & Familiarity** | **Exceptional** (De facto industry standard) | **Low** (Hard to match Excalidraw rendering) | **High** (Tldraw has a beautiful interface) |
| **Agent Accessibility** | **High** (Standard structured JSON elements) | **High** (Complete custom controller) | **High** (Tldraw has structured elements too) |
| **Complexity & Debt** | **Low** (Excalidraw is decoupled as a pure visual editor) | **Extremely High** (High maintenance overhead) | **Low** (Good library support) |

---

## 3. Licensing, Security, and Self-Hosting Risks

- **Licensing**: The Excalidraw repository is MIT-licensed; commercial integration is permitted subject to preserving required copyright and license notices and reviewing third-party dependency licenses.
- **Asset Privacy & Self-Hosting**: We reject the public Excalidraw sharing backend. All scenes and asset blobs are stored locally/privately in our PostgreSQL and S3-compatible (MinIO) stores.
- **Bundle Weight**: `@excalidraw/excalidraw` relies on heavy browser libraries (Canvas API, canvas-roundrect-polyfill). To mitigate page-load latency, the component is dynamically imported with Next.js SSR disabled (`ssr: false`) and lazy loaded.

---

## 4. Architectural Model: Backend Database Ownership

As codified in `docs/architecture/canvas-backend-ownership.md`:
1. **FastAPI (`dnk_orchestrator`)** is the absolute owner of database persistence, revisions, and business validation.
2. **PostgreSQL** is the production data store. SQLite is limited to test fixtures.
3. **Decoupled Binary Storage**: Any screenshot or attachment is extracted on the client, hashed (SHA-256), uploaded directly to S3 via pre-signed URLs, and referenced in the scene JSON via UUID. No intermediate Express sidecar proxy is used on the critical path of Phase 1-3.

---

## 5. Concurrency Control (Optimistic Overwrite Protection)

To resolve race conditions during concurrent editing:
- No silent overrides are allowed.
- Every scene update request (`PUT`) must pass its `expected_revision` number.
- The server uses transactional row locks (`SELECT FOR UPDATE` on `canvas_documents`) to guarantee atomic updates and block overlapping saves.
- If the current revision number in PostgreSQL is higher, the backend throws a `409 Conflict`.
- The frontend interceptor triggers a "Merge Conflict" popup, allowing the user to view a diff, restore the server copy, or trigger a force-commit (restricted behind the Supervisor Approval Gate).

---

## 6. Consequences & Future Outlook

- **Immediate Gains**: Centralized persistence, automatic revision backup, native element-level linking to Task Forest, direct AI agent collaboration.
- **Trade-offs**: Next.js bundle sizes increase by ~1.2MB (lazy loaded). Self-hosted setups now require an S3-compatible backend (or MinIO container).
- **Collaboration**: Real-time WebSocket multi-user collaboration is deferred to **Phase 4** to ensure Phase 1-3 deliver immediate persistence and agentic utility without scheduling overhead.
