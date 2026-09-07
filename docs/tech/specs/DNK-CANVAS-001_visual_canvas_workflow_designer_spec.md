# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-CANVAS-001-SPEC"
# purpose: "Technical Specification & Architecture for DNK OS Visual Canvas Workflow Designer & ReBurn Bridge (DNK-CANVAS-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-CANVAS-001-P1", "DNK-CANVAS-001-P2", "DNK-CANVAS-001-P3", "DNK-CANVAS-001-P4"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# DNK-CANVAS-001: Visual Canvas Workflow Designer & ReBurn Integration Bridge

## 1. Overview & Business Objectives
The **DNK OS Visual Canvas Workflow Designer** is the flagship product layer enabling drag-and-drop, no-code/low-code workflow design, visualization, validation, and real-time execution across the entire DNK OS Core Infrastructure.

It connects:
1. **A2A Agent Mesh (`DNK-A2A-004`)**: Autonomous multi-agent coordination, negotiation, and consensus execution.
2. **Event Streaming Platform (`DNK-STREAM-001`)**: Real-time event triggers, topic subscriptions, and SSE execution streams.
3. **Distributed Batch Engine (`DNK-BATCH-001`)**: High-throughput DAG task batch orchestration and parallel execution.
4. **Shopify E-Commerce Adapter (`DNK-SHOPIFY-001..005`)**: Store actions, inventory synchronization, order webhooks, customer tagging.
5. **ReBurn Hardware Bridge**: IoT, sensor telemetry ingestion, GPIO pin actuation, and edge hardware automation.

---

## 2. Architecture & Evolutionary TaskDNA

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Frontend: Visual Canvas Studio                         │
│   (Next.js App Router + React Flow + SSE Live Execution + Template Gallery)  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / SSE / WebSocket
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    Backend: Canvas Execution Engine                          │
│   - Workflow DAG Validation (Cycle Detection, Handle Mapping, Type Rules)    │
│   - Dynamic State Machine & Step Runner                                      │
│   - Real-time Event Streaming (SSE / Redis Streams)                          │
└──────────────┬───────────────────────┬──────────────────────┬───────────────┘
               │                       │                      │
       ┌───────▼────────┐      ┌───────▼────────┐     ┌───────▼────────┐
       │ DNK-A2A Mesh   │      │ DNK-BATCH-001  │     │ ReBurn Bridge  │
       │ Agent Workers  │      │ Batch DAG Exec │     │ Hardware / GPIO│
       └────────────────┘      └────────────────┘     └────────────────┘
```

---

## 3. Workflow Node Types Specification

| Node Type | Purpose | Configuration Parameters | Outputs / Handles |
|---|---|---|---|
| **A2A Agent Node** | Executes autonomous agent tasks via A2A Mesh protocol | `agent_id`, `role`, `task_prompt`, `capabilities`, `consensus_threshold`, `timeout_sec` | `output`, `status`, `error` |
| **Event Trigger Node** | Listens to Redis Stream / Webhook events | `stream_topic`, `event_type`, `filter_condition`, `debounce_ms`, `auto_ack` | `event_payload`, `timestamp` |
| **Batch Task Node** | Dispatches heavy compute/data tasks to Distributed Batch Engine | `batch_job_type`, `payload_template`, `max_retries`, `backoff_factor`, `priority` | `result`, `job_id`, `metrics` |
| **Shopify Action Node** | Executes GraphQL / REST actions against Shopify stores | `action_type` (`order_create`, `inventory_sync`, `customer_tag`), `shop_domain`, `mutation_params` | `shopify_response`, `resource_id` |
| **Hardware Action Node** | Controls ReBurn edge devices and reads sensor telemetry | `device_id`, `action_type` (`gpio_write`, `read_sensor`, `pwm_set`), `pin`, `payload` | `sensor_value`, `ack_status` |

---

## 4. Graph Execution & Validation Invariants

1. **Strict DAG Guarantee**: Cycle detection via Kahn's Topological Sort algorithm before execution.
2. **Handle Compatibility**: Typed ports with edge condition evaluation (e.g. `success`, `failure`, `condition: value > 100`).
3. **Execution State Persistence**: Every node transition emits an event to `DNK-STREAM-001` for zero-loss telemetry.
4. **Fault Tolerance & Retries**: Exponential backoff per node with isolated circuit breakers.
