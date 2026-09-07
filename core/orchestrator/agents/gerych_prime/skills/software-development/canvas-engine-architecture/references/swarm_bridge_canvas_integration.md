# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/canvas-engine-architecture/references/swarm_bridge_canvas_integration.md"
# purpose: "Reference architecture for Swarm Bridge, triggerNodeAgent, live log streaming and Langfuse telemetry on Canvas."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Swarm Bridge & Live Agent Log Streaming Architecture

This document specifies the bidirectional communication protocol between the Spatial Infinite Canvas (`@xyflow/react` + Zustand) and the multi-agent Swarm backend (`swarm_ws.py` / `canvas_v3_ws.py`).

## 1. End-to-End Lifecycle & Latency Contract

The Swarm Bridge guarantees sub-50ms dispatch latency from the moment a user triggers an action on a canvas node to the WebSocket transport dispatch:

1. **User Action:** Clicks "Run Agent" on a canvas node (e.g., `ShopifySpecNoteNode`, `VideoStoryboardNoteNode`).
2. **Optimistic UI Transition (<10ms):**
   - The node transitions to `status: "thinking"`.
   - The log stream initializes with an entry indicating task dispatch.
3. **Dispatch `TASK_EXECUTE`:**
   - Client sends JSON payload across active canvas WebSocket (`/api/v1/ws/canvas/{canvasId}`).
4. **Backend Ingestion & Step Streaming:**
   - Backend broadcasts `TASK_STATUS` (`thinking` -> `running`).
   - Streams granular `AGENT_LOG` events with execution steps (e.g. `context_hydration`, `prompt_assembly`, `execution_dispatch`).
5. **Completion & Langfuse Tracing:**
   - Backend emits final `TASK_STATUS` (`status: "completed"` or `"error"`) carrying `trace_id`, execution duration, and token accounting metrics.
   - Emits terminal `AGENT_LOG` (`level: "success"`, `step: "execution_complete"`).

---

## 2. Protocol Payloads

### A. Client Dispatch (`TASK_EXECUTE`)
```typescript
interface TaskExecutePayload {
  type: "TASK_EXECUTE";
  nodeId: string;
  taskType?: string; // e.g. "dnk_shopify", "dnk_video_ai_creator"
  context: {
    projectId?: string;
    prompt?: string;
    userSoul?: Record<string, any>; // Injected founder/business DNA
    [key: string]: any;
  };
}
```

### B. Backend Status Broadcast (`TASK_STATUS`)
```typescript
interface TaskStatusPayload {
  type: "TASK_STATUS";
  nodeId: string;
  status: "idle" | "thinking" | "running" | "completed" | "error";
  agent?: string;
  trace_id?: string; // Langfuse workflow execution trace ID
  result?: any;
  metrics?: {
    duration_sec: number;
    tokens_in: number;
    tokens_out: number;
    usd_cost: number;
  };
  timestamp?: number | string;
}
```

### C. Backend Agent Log Stream (`AGENT_LOG`)
```typescript
interface AgentLogPayload {
  type: "AGENT_LOG";
  nodeId?: string;
  agent?: string;
  level: "info" | "success" | "error" | "warning";
  step?: string;
  text?: string;
  message?: string;
  timestamp?: number | string;
}
```

---

## 3. Zustand Implementation Patterns (`canvasStore.ts`)

### A. Dual Node Status Invariant
In React Flow, nodes have top-level properties and nested `data` properties. Custom node components may read either `node.status` or `node.data.status`.
When handling `TASK_STATUS`, always update both:
```typescript
updateNodeData: (id, patch) => {
  set((state) => ({
    nodes: state.nodes.map((node) => {
      if (node.id === id) {
        return {
          ...node,
          // Sync top-level status if present in patch
          ...(patch.status ? { status: patch.status } : {}),
          data: {
            ...node.data,
            ...patch,
          },
        };
      }
      return node;
    }),
  }));
}
```

### B. Dual Text Key Normalization
Different swarm agent backends format message bodies using either `text` or `message`. Always normalize:
```typescript
case "AGENT_LOG": {
  const normalizedLog: AgentLogEntry = {
    id: `log-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
    nodeId: data.nodeId,
    agent: data.agent,
    level: data.level || "info",
    step: data.step,
    text: data.text || data.message || "",
    message: data.message || data.text || "",
    timestamp: data.timestamp || Date.now(),
  };

  set((state) => ({
    activeLogs: [...state.activeLogs.slice(-199), normalizedLog], // Ring-buffer max 200 entries
  }));
  break;
}
```

### C. UserSoul Ingestion
Always inject user context (`userSoul`) into `TASK_EXECUTE` to ground swarm generation without requiring repeated persona prompts:
```typescript
const payload = {
  type: "TASK_EXECUTE",
  nodeId,
  taskType: taskType || targetNode?.type || "generic_agent",
  context: {
    projectId: get().activeProjectId || "default-project",
    prompt: prompt || targetNode?.data?.prompt || "",
    userSoul: get().userSoul,
  },
};
```

---

## 4. UI Streaming Integration (`StitchAgentLog.tsx`)

1. **Reactive Node Filter:** Allow filtering logs by `selectedNodeId` with a fallback toggle to view all logs across the canvas.
2. **Trace ID Badge:** Display `Langfuse trace_id` prominently in the inspector header with a direct link or copy action.
3. **Smooth Auto-Scroll:** Anchor auto-scroll to the bottom of the logs stream via `logsEndRef.current?.scrollIntoView({ behavior: "smooth" })` inside a `useEffect` keyed on `activeLogs.length`.
