# --- DNK-MRH-HEADER ---
# mrh_id: "docs/specs/DNK_CANVAS_DATA_MODEL.md"
# purpose: "Database Schema and Data Model Specification for Embedded DNK Canvas"
# canonical_source: true
# status: "Active"
# version: "1.3.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 🗄️ DNK OS DATA MODEL SPECIFICATION: DNK CANVAS DATABASE SCHEMA

This document details the PostgreSQL relational database schema for the **DNK Canvas Engine**, managed under the `hub_memory` schema. This data model guarantees robust persistence, revision histories, asset deduplication, and task traceability.

---

## 1. Schema Diagram Overview (Logical Model)

```
 +------------------------+             +------------------------+
 |    canvas_documents    |             |    canvas_revisions    |
 +------------------------+             +------------------------+
 | PK id (UUID)           |<----+       | PK id (UUID)           |
 |    workspace_id (UUID) |     |       | FK document_id (UUID)  |-----> FK parent_revision_id
 |    title (VARCHAR)     |     +------o|    revision_number (INT|
 |    description (TEXT)  |             |    scene_json (JSONB)  |
 |    document_type (VAR) |             |    scene_checksum (TXT)|
 | FK curr_revision (UUID)|             |    created_by (VARCHAR)|
 |    created_by (VARCHAR)|             |    created_at (TZ)     |
 |    created_at (TZ)     |             |    change_summary (TXT)|
 |    updated_at (TZ)     |             +------------------------+
 |    status (VARCHAR)    |
 |    metadata (JSONB)    |             +------------------------+
 +------------------------+             |     canvas_assets      |
      |                                 +------------------------+
      |      +--------------------+     | PK id (UUID)           |
      +----->|    canvas_links    |     |    workspace_id (UUID) |
      |      +--------------------+     |    storage_key (VARCHAR|
      |      | PK id (UUID)       |     |    sha256 (VARCHAR)    |
      |      | FK document_id(UUID|     |    status (VARCHAR)    |
      |      |    element_id (TXT)|     |    mime_type (VARCHAR) |
      |      |    entity_type(VAR)|     |    byte_size (INT)     |
      |      |    entity_id (VAR) |     |    width (INT, NULL)   |
      |      |    relation_type   |     |    height (INT, NULL)  |
      |      |    created_at (TZ) |     |    created_at (TZ)     |
      |      +--------------------+     |    UNIQUE(work_id,sha) |
      |                                 +------------------------+
      |                                              ^
      |      +--------------------+                  |
      +----->| canvas_asset_links |------------------+
      |      +--------------------+
      |      | PK id (UUID)       |
      |      | FK asset_id (UUID) |
      |      | FK document_id(UUID|
      |      |    element_id (TXT)|
      |      |    relation_type   |
      |      |    created_at (TZ) |
      |      +--------------------+
      |
      |      +--------------------+
      +----->| canvas_audit_events|
             +--------------------+
             | PK id (UUID)       |
             | FK document_id(UUID|
             |    actor_type (VAR)|
             |    actor_id (VAR)  |
             |    event_type (VAR)|
             | FK revision_id(UUID|
             |    payload (JSONB) |
             |    created_at (TZ) |
             +--------------------+
```

---

## 2. PostgreSQL DDL Specification

All tables are created under the `hub_memory` schema.

### 2.1. Documents Table: `canvas_documents`

Tracks top-level metadata, lifecycle state, and scope boundaries for each visual workspace.

```sql
CREATE TABLE hub_memory.canvas_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    document_type VARCHAR(64) NOT NULL DEFAULT 'excalidraw',
    current_revision_id UUID, -- circular constraint deferred to after revisions creation
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    metadata JSONB DEFAULT '{}'::jsonb NOT NULL
);

-- Indices
CREATE INDEX idx_canvas_docs_workspace ON hub_memory.canvas_documents(workspace_id);
CREATE INDEX idx_canvas_docs_status ON hub_memory.canvas_documents(status);
```

### 2.2. Revisions Table: `canvas_revisions`

Stores complete scene snapshots. The actual elements and state of the Excalidraw board are stored here as a raw `JSONB` document.

```sql
CREATE TABLE hub_memory.canvas_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES hub_memory.canvas_documents(id) ON DELETE CASCADE,
    revision_number INT NOT NULL,
    scene_json JSONB NOT NULL,
    scene_checksum VARCHAR(64) NOT NULL, -- SHA-256 hash of scene_json string for data integrity
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    change_summary TEXT,
    parent_revision_id UUID REFERENCES hub_memory.canvas_revisions(id) ON DELETE SET NULL,
    
    CONSTRAINT uq_document_revision UNIQUE (document_id, revision_number)
);

-- Add Foreign Key to canvas_documents now that revisions exists
ALTER TABLE hub_memory.canvas_documents 
ADD CONSTRAINT fk_current_revision FOREIGN KEY (current_revision_id) 
REFERENCES hub_memory.canvas_revisions(id) ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED;

-- Indices
CREATE INDEX idx_canvas_revisions_doc ON hub_memory.canvas_revisions(document_id);
CREATE INDEX idx_canvas_revisions_created ON hub_memory.canvas_revisions(created_at);
```

### 2.3. Assets Table: `canvas_assets` (Workspace-Scoped Asset Library)

Tracks external binary files (such as screenshots, annotations, and wireframes) uploaded directly to the S3-compatible cloud storage. It decouples documents from storage to allow multiple documents to share the same verified screenshot safely.

To guarantee tenant isolation, deduplication is scoped per-workspace via `UNIQUE (workspace_id, sha256)` preventing cross-workspace asset leakage.

```sql
CREATE TABLE hub_memory.canvas_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    storage_key VARCHAR(512) NOT NULL UNIQUE, -- S3 absolute path / key
    sha256 VARCHAR(64) NOT NULL, -- Asset SHA-256 hash
    status VARCHAR(32) NOT NULL DEFAULT 'pending_upload', -- pending_upload, uploaded, verifying, verified, rejected, deleted
    mime_type VARCHAR(128) NOT NULL,
    byte_size INT NOT NULL,
    width INT,
    height INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT uq_workspace_sha256 UNIQUE (workspace_id, sha256)
);

-- Indices
CREATE INDEX idx_canvas_assets_workspace ON hub_memory.canvas_assets(workspace_id);
CREATE INDEX idx_canvas_assets_hash ON hub_memory.canvas_assets(sha256);
```

### 2.4. Asset Links Table: `canvas_asset_links` (Partial-Index-Guaranteed Uniqueness)

Links a global workspace-scoped S3 asset reference to a specific document and canvas element. PostgreSQL `NULL` values are handled using two partial unique indexes instead of a single nullable unique constraint.

```sql
CREATE TABLE hub_memory.canvas_asset_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES hub_memory.canvas_assets(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES hub_memory.canvas_documents(id) ON DELETE CASCADE,
    element_id VARCHAR(255) NULL, -- Excalidraw element node UUID (null indicates document-level asset)
    relation_type VARCHAR(64) NOT NULL DEFAULT 'references',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 1. Uniqueness for node-level asset links (when element_id is NOT NULL)
CREATE UNIQUE INDEX uq_canvas_asset_element_link
ON hub_memory.canvas_asset_links (
    document_id,
    element_id,
    asset_id
)
WHERE element_id IS NOT NULL;

-- 2. Uniqueness for document-level asset links (when element_id is NULL)
CREATE UNIQUE INDEX uq_canvas_asset_document_link
ON hub_memory.canvas_asset_links (
    document_id,
    asset_id
)
WHERE element_id IS NULL;

-- Indices
CREATE INDEX idx_canvas_asset_links_doc ON hub_memory.canvas_asset_links(document_id);
CREATE INDEX idx_canvas_asset_links_asset ON hub_memory.canvas_asset_links(asset_id);
```

### 2.5. Links Table: `canvas_links` (Partial-Index-Guaranteed Uniqueness)

Connects coordinates and objects (such as Excalidraw element UUIDs) within the canvas space directly to domain entities inside the DNK OS Task Forest, competitor research databases, or active execution logs.

PostgreSQL `NULL` values are handled using two distinct partial unique indexes instead of a single nullable unique constraint to prevent duplicate links.

```sql
CREATE TABLE hub_memory.canvas_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES hub_memory.canvas_documents(id) ON DELETE CASCADE,
    element_id VARCHAR(255) NULL, -- Excalidraw element node UUID (null indicates document-level link)
    entity_type VARCHAR(64) NOT NULL, -- competitor, screenshot, insight, flower, adr, agent_run
    entity_id VARCHAR(255) NOT NULL, -- Canonical string identifier or UUID
    relation_type VARCHAR(64) NOT NULL DEFAULT 'references',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 1. Uniqueness for node-level links (when element_id is NOT NULL)
CREATE UNIQUE INDEX uq_canvas_element_link
ON hub_memory.canvas_links (
    document_id,
    element_id,
    entity_type,
    entity_id,
    relation_type
)
WHERE element_id IS NOT NULL;

-- 2. Uniqueness for document-level links (when element_id is NULL)
CREATE UNIQUE INDEX uq_canvas_document_link
ON hub_memory.canvas_links (
    document_id,
    entity_type,
    entity_id,
    relation_type
)
WHERE element_id IS NULL;

-- Indices
CREATE INDEX idx_canvas_links_doc ON hub_memory.canvas_links(document_id);
CREATE INDEX idx_canvas_links_entity ON hub_memory.canvas_links(entity_type, entity_id);
```

### 2.6. Audit Events Table: `canvas_audit_events`

Maintains a tamper-proof audit trail tracking human-editor and agentic-swarm mutations alike. Useful for monitoring agentic actions and triggering recovery procedures.

```sql
CREATE TABLE hub_memory.canvas_audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES hub_memory.canvas_documents(id) ON DELETE CASCADE,
    actor_type VARCHAR(64) NOT NULL, -- human, agent
    actor_id VARCHAR(255) NOT NULL, -- User UUID or Agent Identifier (e.g., dnk_koder)
    event_type VARCHAR(128) NOT NULL, -- create, edit_scene, link_entity, unlink_entity, add_asset, delete, force_commit
    revision_id UUID REFERENCES hub_memory.canvas_revisions(id) ON DELETE SET NULL,
    payload JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indices
CREATE INDEX idx_canvas_audit_doc ON hub_memory.canvas_audit_events(document_id);
CREATE INDEX idx_canvas_audit_actor ON hub_memory.canvas_audit_events(actor_type, actor_id);
CREATE INDEX idx_canvas_audit_type ON hub_memory.canvas_audit_events(event_type);
```

---

## 3. Storage Optimization & Separation Rules

To prevent database bloating and lag in the frontend:
1. **Raw Canvas Elements Separated**: Large assets are stored in object storage (MinIO/S3), while metadata are indexed in `canvas_assets` and linked via `canvas_asset_links`.
2. **Checksum Integrity Enforcement**: All revision inputs are hashed on the client-side (`scene_checksum`). The FastAPI backend recalculates the hash to guarantee no data was corrupted during transit.
3. **No Embedded Base64**: The client code strips raw base64 images from Excalidraw exports, uploads them separately, and maps them to standard asset nodes containing `asset_id`.
