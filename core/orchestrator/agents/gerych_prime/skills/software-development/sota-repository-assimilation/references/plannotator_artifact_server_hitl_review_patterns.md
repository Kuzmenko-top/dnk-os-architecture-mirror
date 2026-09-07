# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/plannotator_artifact_server_hitl_review_patterns.md"
# purpose: "Visual HITL Review, DOM Pinning & Agent Dispatch Mailbox patterns assimilated from plannotator/artifact-server."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# author: "Gerych Prime & DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Plannotator Artifact Server: Visual HITL Review & Agent Dispatch Patterns

- **Upstream Repository**: `https://github.com/plannotator/artifact-server`
- **Verified Commit**: `2251e42a94bf27f8ff2c855eeed3093deb354937` (Tag: `v0.1.0`)
- **License**: `AGPL-3.0-only` (Track 2 Clean-Room Synthesis & Sovereign Sidecar Protocol)
- **Classification**: Visual Human-In-The-Loop (HITL) Review, Sandboxed Staging & Agent Dispatch Engine

---

## 1. Track 2 Legal Compliance Boundary (AGPL-3.0-only)

Because AGPL-3.0 contains strong network copyleft (Section 13), internal systems must maintain strict architectural separation:

```
┌────────────────────────────────────────────────────────┐
│      Sovereign Sidecar (Untouched Docker Container)    │
│           plannotator/artifact-server:latest           │
│           (Runs on port :3100, local SQLite DB)        │
└───────────────────────────▲────────────────────────────┘
                            │ Standard HTTP REST & MCP SSE/stdio
                            │ (No library linking / No vendored code)
┌───────────────────────────▼────────────────────────────┐
│              DNK OS Proprietary Swarm Core             │
│        (Hermes Prime, FastAPI apps/api, React Canvas)  │
└────────────────────────────────────────────────────────┘
```

1. **Zero Vendoring**: Never copy upstream TypeScript source files into `DNK_HUB`.
2. **Sidecar Deployment**: Run upstream as an external decoupled container. Network APIs across processes do not trigger copyleft infection.
3. **Clean-Room Specification**: Internal UI/API implementations in DNK OS (e.g. `ArtifactReviewOverlay.tsx`, `dnk_artifact_router.py`) are authored from clean specifications.

---

## 2. MCP Server Specification (31 Tools + 1 Resource)

The MCP server exposes exactly 31 tools via `registerNudgedTool` and 1 resource template:

1. **System & Capabilities (1)**:
   - `artifact_capabilities`: Returns server capabilities, storage drivers, version limits.
2. **Projects & Git Lineage (6)**:
   - `project_list`, `project_create`, `project_rename`
   - `project_git_history_status`, `project_git_history_estimate`, `project_set_git_history`
   - `artifact_history_clone_token`
3. **Artifacts & Staging (14)**:
   - `artifact_list`, `artifact_get`, `artifact_open`, `artifact_version_list`, `artifact_diff`
   - `artifact_create_upload`, `artifact_commit_upload` (multi-file atomic staging)
   - `artifact_set_visibility`, `artifact_set_tags`, `artifact_restore_version`, `artifact_delete`
   - `artifact_link`, `artifact_capture`, `artifact_relink` (tracking local directory changes)
4. **Comments & Annotations (8)**:
   - `comment_list`, `comment_get`, `comment_create`, `comment_reply`
   - `comment_resolve`, `comment_update`, `comment_delete`, `comment_clear`
5. **Agent Mailbox (1)**:
   - `dispatch_inbox`: Supports operations `list`, `claim`, `delivered`, `failed`.
6. **Resource Template (1)**:
   - `artifact-version-manifest`: URI template `artifact://{projectId}/{artifactId}/versions/{versionId}/manifest`.

---

## 3. Tool-Result Nudges Steering Channel (`src/mcp/tool-result-nudges.ts`)

Because standard MCP is a pull-only client protocol without server-push to LLM agents:
- **Heading**: `nudgeHeading = "— artifact server —"`
- **Character Budget**: `maximumNudgeCharacters = 400`
- **Exclusion Rule**: `nudgeFreeTools = ["dispatch_inbox"]` (avoids nudging an agent that is already draining the inbox).
- **Behavior**: When pending dispatched tasks exist, any tool result appends a markdown notice reminding the agent to call `dispatch_inbox(operation: "claim")`.

---

## 4. Precision DOM Pinning & Review Frame Protocol v1

### Schema: `ReviewAnchor` & `HtmlElementAnchor`
```typescript
interface HtmlElementAnchor {
  selector: string;           // CSS selector path
  tagName: string;            // Element tag (e.g. "BUTTON")
  text?: string;              // Up to 400 chars of inner text for fuzzy recovery
  point: {
    x: number;                // 0.0 to 1.0 relative to bounding rect
    y: number;
  };
}

interface ReviewAnchor {
  type: "point" | "html-element";
  point?: { x: number; y: number };
  html?: HtmlElementAnchor;
  htmlAdditionalTargets?: HtmlElementAnchor[];
}
```

### postMessage Protocol (`reviewProtocolVersion = 1`)
- **Host ➔ Frame**:
  - `as-review-init`: Initial load payload (code, CSS tokens, annotations, readOnly).
  - `as-review-annotations`: Update pins array without iframe re-render.
  - `as-review-theme`: Toggle light/dark theme tokens.
  - `as-review-annotate-mode`: Set annotation cursor mode (`active: boolean`).
  - `as-review-focus`: Scroll and highlight specific `threadId`.
- **Frame ➔ Host**:
  - `as-review-ready`: Sandbox initialized and listeners mounted.
  - `as-review-submit`: User clicked to place a comment with `ReviewAnchor`.
  - `as-review-select`: User clicked an existing pin badge.
  - `as-review-annotate-mode-request`: Sandbox requests annotate mode toggle.
  - `as-review-unanchored`: List of pin IDs whose DOM selectors could not be resolved.

---

## 5. Asynchronous Pull-Based Agent Mailbox Pattern (`dispatch_inbox`)

```
Reviewer (UI) ──► Bundles 3-4 visual pins ──► Clicks "Dispatch to Agent"
                                                         │
                                                         ▼
                                             Server queues Dispatch ID
                                                         │
                                                         ▼
Agent Polling Loop ──► dispatch_inbox(operation: "list")
                   ──► dispatch_inbox(operation: "claim") ➔ Locks package, receives markdown brief
                   ──► dispatch_inbox(operation: "delivered") ➔ Confirms execution start
                   ──► Modifies code + runs tests (verify_all.sh)
                   ──► comment_reply(threadId, "Fixed button alignment in commit abc123")
                   ──► comment_resolve(threadId)
```

---

## 6. Audit & Assimilation Verification Invariants
1. **Never guess tool counts**: Read the registration source directly (e.g. `registerNudgedTool` loops).
2. **Relative path discipline**: Documentation and notes must exclusively use `./docs/tech/...` and `vault:<note.md>`. Absolute `/Users/...` paths are strictly forbidden.
3. **Line-by-line verification**: Validate AST schemas and wire protocol constants against upstream code before authoring implementation specs.

---

## 7. Clean-Room Hexagonal Synthesis & In-Tree Adapter (Phase 041 Implementation)

While external instances can run via Docker sidecars, monorepo micro-agents require high-performance, in-process, non-copyleft artifact management under MIT:

### Core Architecture:
1. **Hexagonal Port (`ArtifactServerPort`) & Adapter (`DNKArtifactServerAdapter`)**:
   - Location: `core/adapters/dnk_artifact_server_adapter.py`
   - Zero AGPL code exposure: built from pure Python standard libraries (`difflib`, `re`, `json`, `datetime.timezone`).
2. **Version Immutability & Unified Diff**:
   - Each artifact stores an ordered sequence of immutable versions (`v1`, `v2`, ...).
   - `render_diff(v_a, v_b)`: Computes clean unified diffs on text/code payloads via `difflib.unified_diff`, providing instant visual review feedback for swarm agents.
3. **Line-Anchored Annotations & Thread Lifecycle**:
   - Comments attach directly to `line_number`, track state (`open` -> `resolved`), store resolution timestamp (`resolved_at`), and reference resolving user/agent.
4. **SpendGuard & Path Traversal Guards**:
   - Strict filename/ID sanitization (`^[a-zA-Z0-9_\-\.]+$`), rejecting directory traversal attempts (`../`).
   - Hard payload size enforcement (max 10MB default) protecting runtime memory and storage budgets.
5. **FastAPI Endpoints**:
   - Mounted at `/artifacts` (`apps/api/routers/artifacts.py`) with Pydantic v2 schemas (`apps/api/schemas/artifacts.py`) and Dependency Injection via `get_artifact_adapter()`.
