---
name: "open_canvas_assimilated"
description: "Assimilated patterns and components from langchain-ai/open-canvas"
version: "2.0.0"
category: "research"
assimilated_at: "2026-08-10"
---

# 🌐 Open-Canvas Assimilation Index

Meta-index for architecture, contracts, and security specs.

## 📁 Core Specifications

1. **[Research & Evidence Trail](../../docs/reports/rd_assimilation/open_canvas/RN-001_open-canvas-research.md)**
   - Summary of evidence, line mappings, and analyzed modules.

2. **[Architecture Specification](../../docs/tech/specs/DNK-ARCH-001_canvas-artifacts.md)**
   - Artifact DB schema on PostgreSQL (`hub_memory.artifacts`), ownerId validation, and Event Bus synchronization protocol.

3. **[Component Interfaces & Contracts](../../docs/tech/specs/DNK-COMP-001_editors.md)**
   - Type-safe TS Interfaces for `ArtifactRendererProps`, `CodeRendererProps`, and `TextRendererProps` alongside events (`onContentChange`, `onSelectionChange`).

4. **[Security & Egress Standards](../../docs/tech/standards/DNK-SEC-001_canvas-sandbox.md)**
   - Network isolation policies, Docker anonymous volume masks, and zero-host pollution enforcement.

## 🧪 Quick Recipes (How to Use This Skill)

### Recipe A: Using Editor Interfaces in Visual Shell (web_ui)

**Goal:** Integrate the rich editor side panel (`ProseMirror` / `CodeMirror`) into the Next.js visual shell.

- See: `DNK-COMP-001_editors.md` for interface contracts like `ArtifactRendererProps`.
- Implement state wrappers in your Next.js page:
  ```typescript
  import { ArtifactRendererProps } from '@/types/canvas';
  // Use state to track onContentChange and onSelectionChange
  ```
- Trigger updates over the event bus and preserve React Flow canvas nodes.

### Recipe B: PostgreSQL Schema & State Synchronization

**Goal:** Persist infinite canvas editor states to PostgreSQL.

- Reference database table structure specified in `DNK-ARCH-001_canvas-artifacts.md`.
- Ensure WebSocket handlers issue clean transactions on PostgreSQL:
  ```python
  # Always invoke conn.commit() inside the pool!
  with db_pool.get_connection() as conn:
      cursor = conn.cursor()
      cursor.execute("UPDATE hub_memory.artifacts SET content = %s WHERE id = %s", (content, artifact_id))
      conn.commit()
  ```
