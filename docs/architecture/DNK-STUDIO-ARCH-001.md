# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STUDIO-ARCH-001"
# purpose: "Canonical Studio Architecture Charter: Consolidating Canvas, Cabinet, TaskDNA, A2A, Open Design, and Stitch into Unified Visual OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym & Antigravity Orchestrator"
# --- END DNK-MRH-HEADER ---

# 🏛️ DNK-STUDIO-ARCH-001: Canonical Studio Architecture Charter

## Executive Summary

DNK OS has progressed beyond initial prototyping into a feature-rich, multi-module monorepo. The core objective of **DNK-STUDIO-ARCH-001** is **canonicalization and consolidation**: establishing a Single Source of Truth (SSOT) across all backend API routers, frontend entrypoints, execution DAGs, realtime transports, and design systems.

Rather than generating disparate, disconnected tools (`/cabinet`, `/canvas`, `/taskdna`, `/whiteboard`, `/os`), DNK OS consolidates into **One Canonical Studio Shell**:
- **Launchpad & Workspace Spaces**: Inspired by *CapCut My-Edit* & *Taskade Spaces*.
- **Spatial Infinite Canvas & Stage**: Inspired by *Google Stitch* & *Open Design Sandbox*.
- **Autonomous Execution Engine**: Powered by *14 Swarm Agents*, *TaskDNA DAG*, *A2A Federation*, and *SCONES L3 Memory*.

---

## 🧭 The 6 Core Tenets of Canonicalization

1. **One Shell, Many Modalities**:
   - The user never jumps between fragmented tools. The Studio Shell provides a unified layout (Top Navigation, Left Capability Library, Central Infinite Stage, Right Context Inspector, Bottom Execution Timeline).
2. **TaskDNA as the Execution SSOT**:
   - Canvas nodes and edges are visual projections of backend `TaskDNA` graphs. The frontend never simulates side-effects or parallel fake states.
3. **Fail-Closed Governance & Approval Gates**:
   - External mutations (Shopify product updates, GitHub PR merges, deployment pushes) strictly require passing through the `ApprovalNode` gate with immutable audit records.
4. **Open Design as the Generative Engine**:
   - The 100+ design systems and code generators in `visual_shell/open_design` provide live tokens, CSS modules, and component templates directly to the Studio Canvas.
5. **A2A Federation Event SSOT**:
   - All agent communications, lifecycle transitions, and telemetry flow through the standard `DNKEventEnvelope` over WebSockets (interactive) and SSE (telemetry streams).
6. **Zero-Waste Path & Context Hygiene**:
   - Strict adherence to `DNK_HUB/` context firewall, relative imports (`./`, `../`), and MRH headers (`DNK-STD-0075`).

---

## 🗺️ Architectural Document Index

| Document | Purpose |
| :--- | :--- |
| **[DNK-STUDIO-ARCH-001-current-state.md](./DNK-STUDIO-ARCH-001-current-state.md)** | Full inventory of routes, backend routers, Real vs Mock audit, and duplication analysis. |
| **[DNK-STUDIO-ARCH-001-target-state.md](./DNK-STUDIO-ARCH-001-target-state.md)** | Target 4-zone layout, Unified Studio Shell, Multi-mode stage, and Session Store design. |
| **[DNK-STUDIO-ARCH-001-api-contracts.md](./DNK-STUDIO-ARCH-001-api-contracts.md)** | SSOT API contracts, Node Manifest v1, Edge Semantics, and Event Envelope schemas. |
| **[DNK-STUDIO-ARCH-001-migration-plan.md](./DNK-STUDIO-ARCH-001-migration-plan.md)** | Deprecation roadmap, routing redirects, and PR-sized execution milestones. |
| **[DNK-STUDIO-ARCH-001-evidence.json](../audit/DNK-STUDIO-ARCH-001-evidence.json)** | Machine-readable evidence file with route mappings, file paths, and test statuses. |
