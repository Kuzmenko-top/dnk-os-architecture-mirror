# Live Swarm Node Execution, Visual Pulse & Ring-Buffer Terminal Logs

## 1. Overview
Real-time execution protocol for autonomous Swarm agents on individual DAG task nodes within spatial canvas environments (`@xyflow/react` / ReactFlow). Combines bounded backend ring-buffer logging, live visual node pulsing, and an in-drawer execution terminal.

---

## 2. Backend Ring-Buffer & REST Execution Contract

### A. In-Memory Ring-Buffer Storage
To prevent unbounded memory growth during high-frequency agent thought streams, store logs in a bounded per-node ring-buffer (maximum 100 entries per node):

```python
_task_logs: Dict[str, List[Dict[str, Any]]] = {}
MAX_LOGS_PER_TASK = 100

def append_task_log(node_id: str, level: str, message: str, agent: str = "gerych_builder") -> None:
    if node_id not in _task_logs:
        _task_logs[node_id] = []
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,  # INFO, STEP, DONE, THOUGHT, ERROR
        "agent": agent,
        "message": message,
    }
    _task_logs[node_id].append(entry)
    if len(_task_logs[node_id]) > MAX_LOGS_PER_TASK:
        _task_logs[node_id] = _task_logs[node_id][-MAX_LOGS_PER_TASK:]
```

### B. Execution Endpoint (`POST /api/v3/node_tasks/{node_id}/execute`)
- Updates node stage to `in_progress` / status to `in_progress`.
- Records initial execution stages into `_task_logs`.
- If `auto_complete=True`, finishes execution, marks stage as `done` / status `completed`, and triggers graph dependency propagation to unblock downstream dependent nodes.
- Returns execution status and current log history.

---

## 3. Frontend Canvas Active Agent Pulse (ReactFlow)

### A. Visual State Detection
```typescript
const isRunning = node.stage === 'in_progress' || node.status === 'in_progress';
```

### B. Neon Pulse & Active Runner Badge (`CustomTaskNode.tsx`)
When a node is actively running, wrap the card with an emerald neon pulse and active status indicator:
```tsx
<div
  className={cn(
    "relative rounded-xl border transition-all duration-300",
    isRunning && "ring-2 ring-emerald-400/80 shadow-[0_0_25px_rgba(52,211,153,0.35)] animate-pulse"
  )}
>
  {isRunning && (
    <div className="absolute -top-3 right-3 flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-950/90 border border-emerald-500/50 text-[10px] text-emerald-300 font-mono shadow-sm">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
      </span>
      <span>{node.agent || 'Swarm Runner'}</span>
    </div>
  )}
  {/* Node Header & Content */}
</div>
```

---

## 4. In-Drawer Live Terminal Logs Viewer

### A. Terminal Component Pattern (`NodeTaskDetailDrawer.tsx`)
- Monospace dark aesthetic (`bg-zinc-950/90 font-mono text-xs border border-zinc-800`).
- Color-coded log level badges:
  - `INFO`: Slate / Blue (`bg-blue-900/40 text-blue-400`)
  - `STEP`: Violet / Purple (`bg-purple-900/40 text-purple-400`)
  - `DONE` / `SUCCESS`: Emerald (`bg-emerald-900/40 text-emerald-400`)
  - `THOUGHT`: Amber (`bg-amber-900/40 text-amber-400`)
  - `ERROR`: Rose / Red (`bg-rose-900/40 text-rose-400`)
- Auto-scroll to bottom on incoming entries via `ref.scrollIntoView({ behavior: 'smooth' })`.
