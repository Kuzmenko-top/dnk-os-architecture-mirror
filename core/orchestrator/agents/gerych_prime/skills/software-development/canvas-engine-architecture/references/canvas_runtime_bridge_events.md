# --- DNK-MRH-HEADER ---
# mrh_id: "skills/canvas-engine-architecture/references/canvas_runtime_bridge_events.md"
# purpose: "Reference guide for Canvas Runtime Bridge event publishing, Redis transport, and Pydantic serialization."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Canvas Runtime Bridge: Lifecycle Events & Transport Reference

## 1. Node Lifecycle Event Mapping
When bridging visual Infinite Canvas or selection scenarios with LangGraph and EventBus:
- **Node Creation (`node.created`)**:
  - Emitted when a new node appears or is registered within a canvas selection execution DAG.
  - Event payload carries node metadata, coordinates/bounds, node type, and execution ID.
- **Node Execution (`node.executed`)**:
  - Emitted when a node completes or fails execution.
  - Carries execution duration, status (`completed` or `error`), output data, and updated state.

## 2. Event Serialization Pitfall & Solution (Pydantic v2 + Redis)
- **Problem**:
  Calling `event.model_dump()` on a Pydantic model with `datetime` fields (e.g. `timestamp`, `updated_at`) yields native Python `datetime` objects.
  Passing this directly into `json.dumps(payload_dict)` raises:
  `TypeError: Object of type datetime is not JSON serializable`.
- **Solution**:
  Always serialize using `event.model_dump(mode="json")` in Pydantic v2:
  ```python
  payload_dict = event.model_dump(mode="json")
  json_payload = json.dumps(payload_dict)
  redis_client.publish(channel, json_payload)
  ```
  This automatically converts `datetime` objects into standard ISO 8601 strings.

## 3. Graceful Fallback & Non-blocking Redis Transport
- Always wrap Redis publication in try/except blocks.
- If Redis is unreachable or unconfigured in headless/CI test environments, log a debug message and gracefully fall back to local `RuntimeEventBus` without raising unhandled exceptions or failing the scenario.

## 4. Canvas Selection Execution Scenario Pattern
- A selection scenario coordinates multiple nodes within a bounding box:
  1. Register a virtual `CanvasSelectionParser` node (`node.created`).
  2. Register all selected nodes (`node.created`).
  3. Emit execution results for selection context parsing (`node.executed`).
  4. Emit execution results for each child node (`node.executed`).
  5. Produce a terminal `GraphExecutionSnapshot` capturing `last_sequence_number`, `node_states`, and `status`.
