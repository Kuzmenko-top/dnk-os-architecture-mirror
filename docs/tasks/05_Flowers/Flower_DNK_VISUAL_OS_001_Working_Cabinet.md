# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_DNK_VISUAL_OS_001_Working_Cabinet.md"
# purpose: "Task Flower tracking execution of Visual DNK OS MVP Working Cabinet (DNK-VISUAL-OS-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "In_Progress"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 🌸 Task Flower: DNK-VISUAL-OS-001 — Visual DNK OS MVP (Working Cabinet)

## Task Metadata
- **Plant Scale:** Task_Flower
- **Task ID:** `DNK-VISUAL-OS-001`
- **Specification:** `docs/tech/specs/DNK-VISUAL-OS-001_working_cabinet.md`
- **Base Branch:** `main`
- **Status:** `In_Progress` (Tech Spec Completed & Approved)

---

## 🎯 Objectives & Deliverables
1. **Deliverable 1 (Completed):** Tech Spec Visual DNK OS MVP (`docs/tech/specs/DNK-VISUAL-OS-001_working_cabinet.md`).
2. **Deliverable 2 (Next Step):** Implement Workspace Layout & Multi-tenancy Isolation (Sidebar, Header, Viewport, Drawer) reusing existing Stitch/Gateway components where applicable.
3. **Deliverable 3:** Implement Module Routing (Overview, Task Flowers, Canvas, Agents, Approvals, Reports).
4. **Deliverable 4:** Connect API Endpoints & State Providers with Fail-Closed `X-Workspace-Id` Authorization.
5. **Deliverable 5:** End-to-End Verification & DoD Audit.

---

## 📊 Acceptance Criteria & Definition of Done (DoD)
- [x] **Tech Spec Created:** Comprehensive technical specification generated and verified against path hygiene.
- [ ] **Cabinet Layout:** Three-pane responsive working cabinet UI matching spec.
- [ ] **Multi-tenancy Guard:** Fail-closed `X-Workspace-Id` workspace header enforcement.
- [ ] **Module Views:** Working views for Overview, Flowers, Canvas, Swarms, Approvals, Reports.
- [ ] **E2E Test Suite:** Green unit, integration, and path hygiene tests.
