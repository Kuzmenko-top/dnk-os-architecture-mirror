# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-001_canvas-artifacts.md"
# purpose: "DNK OS Architecture Spec for Canvas Artifacts"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-10"
# author: "Maxim"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 🏛️ ARCHITECTURE SPEC: CANVAS ARTIFACTS (DNK-ARCH-001)

## 📌 Artifact Data Model
In DNK OS, the canvas artifacts conform to the following schema:
```typescript
interface DNKArtifact {
  id: string;          // Unique UUID
  ownerId: string;     // Creator User UUID
  projectId: string;   // Project Scope UUID
  version: number;     // Monotonically increasing version index
  agentTraceId?: string; // Link to LangSmith/DNK trace
  type: 'code' | 'text' | 'schema';
  title: string;
  content: string;
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}
```

## 🗄️ PostgreSQL Schema Mapping
The artifacts reside in the database under `hub_memory.artifacts`:
```sql
CREATE TABLE hub_memory.artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    project_id UUID NOT NULL,
    version INT NOT NULL DEFAULT 1,
    agent_trace_id VARCHAR(255),
    type VARCHAR(32) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_artifacts_project ON hub_memory.artifacts (project_id);
CREATE UNIQUE INDEX idx_artifacts_version ON hub_memory.artifacts (id, version);
```

## 📡 Frontend-Agent Event Bus Protocol
The bi-directional synchronization between the React/Next.js Visual Shell and local/remote Agents uses the following workflow:

1. **Update Request**:
   - Event: `ARTIFACT_UPDATE_REQUESTED`
   - Payload: `{ artifactId: string, diff: string, traceId: string }`
   - Route: Front-end ➔ OmniRouter ➔ Background Worker Queue
2. **Patch Application**:
   - Event: `ARTIFACT_PATCH_APPLIED`
   - Payload: `{ artifactId: string, version: number, patchedContent: string }`
   - Route: Background Worker ➔ WebSocket Gateway ➔ Visual Shell Canvas

This decoupled architecture ensures non-blocking, offline-first reliability.
