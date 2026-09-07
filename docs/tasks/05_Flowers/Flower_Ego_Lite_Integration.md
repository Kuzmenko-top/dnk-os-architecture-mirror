---
id: flower_ego_lite_integration
title: "🌸 Квітка: Ego Lite Integration"
type: task_flower
plant_scale: flower
parent_id: bush_self_improving_swarm_engine
status: completed
verification_status: passed
tags:
  - dnk-task-forest
  - dnk-task-flower
  - ego-lite
  - browser-automation
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_Ego_Lite_Integration.md"
# purpose: "Canonical documentation and task tracking note for Ego-Lite browser-automation harness"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# plant_scale: "flower"
# --- END DNK-MRH-HEADER ---

**Task Flower Note: Ego-Lite Browser-Automation Harness Integration**

**Root Node:** DNK OS Integration - Ego-Lite (CDP Browser-Automation Harness)

**Branches:**

1. **CDP Transport & Session Attach**
	* Priority: High
	* Checklist:
		+ Understand `ego.sendCDPMessage` transport and caching mechanism
		+ Handle 2-second TTL for session caching
		+ Implement auto-reattach logic on session loss
	* Metadata: Estimated time: 1 week, Resources required: 1 engineer

2. **Element Resolution Protocol**
	* Priority: High
	* Checklist:
		+ Resolve target forms: `@backendNodeId` refs and `loc=...` selectors
		+ Implement automatic re-snapshot when ref map is empty
		+ Classify errors into transient (retryable) and permanent
	* Metadata: Estimated time: 1 week, Resources required: 1 engineer

3. **Task Space Governance**
	* Priority: Medium
	* Checklist:
		+ Support `useOrCreateTaskSpace` and `claimTaskSpace` for ownership
		+ Define ownership model transitions (`agent` ➔ `user` / user-owned takeover)
		+ Track task space completed states using `completeTaskSpace` with `keep`
	* Metadata: Estimated time: 1 week, Resources required: 1 engineer

4. **Python Adapter & Bridge Integration**
	* Priority: High
	* Checklist:
		+ Implement `DNKEgoBrowserAdapter` in `core/adapters/ego_browser_adapter.py`
		+ Expose `start()`, `stop()`, `send_command()`, `run_command()`, `list_task_spaces()`
		+ Ensure complete path protection and relative-only constraints in adapter
	* Metadata: Estimated time: 1 week, Resources required: 1 engineer

5. **Sandbox & Docker Security Audit**
	* Priority: Medium
	* Checklist:
		+ Run ego-browser CLI fully inside the Docker container to ensure zero-host pollution
		+ Mount the skill directory `skills/ego-browser/` securely
		+ Enforce relative-only path constraints on all runtime IO operations
	* Metadata: Estimated time: 1 week, Resources required: 1 engineer

**Metadata:**
* Estimated project duration: 5 weeks
* Resources required: 1 senior engineer
* Dependencies: Dockerized Node 22+ runtime, closed-source ego lite app bindings
* Risks: Changes in closed-source CDP bindings, permission denied locks in Docker volumes
* Assumptions: Ego-Lite binary is bundled correctly under Docker container
* Success criteria: `DNKEgoBrowserAdapter` is verified with unit tests and runs fully inside Docker

**Task Flower Status:**
* In progress: None
* Planned: None
* Completed: CDP Transport & Session Attach, Element Resolution Protocol, Task Space Governance, Python Adapter & Bridge Integration, Sandbox & Docker Security Audit
