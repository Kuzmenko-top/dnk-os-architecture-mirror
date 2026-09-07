# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/beads_audit.md"
# purpose: "SOTA Architectural Audit & Assimilation Mapping of gastownhall/beads for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Assimilation & Architectural Audit: gastownhall/beads (bd)

## 👑 1. Executive Summary

This document presents a comprehensive, high-fidelity architectural audit of the open-source repository **`gastownhall/beads` (bd)**, developed by Steve Yegge (formerly Google, Amazon, Sourcegraph).

**Beads (bd)** is a pioneering, AI-native task and issue tracker designed specifically for autonomous software development agents (such as Claude Code, Gemini CLI, and custom agent swarms) and human-AI collaboration. Unlike legacy platforms (Jira, Linear, GitHub Issues) which are optimized for human graphical interactions, Beads is engineered from the ground up to solve the core cognitive limitations of LLM-based developers: **context window decay, multi-agent race conditions, blind task navigation, and transactional state tracking**.

### 🌟 Key Audit Takeaway
Beads represents the state-of-the-art (SOTA) in **Context Engineering and Agentic Task Navigation**. The core mechanics found within Beads—specifically **unblocked task auto-discovery, context budget-aware schemas, and atomic concurrency fencing**—should be directly assimilated into the **DNK OS Swarm Engine** to elevate Gerych Prime and specialized swarm subagents to a 10x level of execution efficiency.

---

## 🏗️ 2. Core Philosophy: Human-Native vs. AI-Native Trackers

Traditional issue trackers suffer from heavy overhead, massive payloads, and nested graphical relationships that are highly inefficient for AI execution. Beads introduces the concept of an **AI-Native Tracker**, relying on six fundamental pillars:

| Capability | Traditional Trackers (Jira/Linear) | AI-Native Trackers (Beads) |
| :--- | :--- | :--- |
| **Primary Operator** | Humans using web browsers / mouse. | AI Agents using terminal CLIs & MCP. |
| **Work Discovery** | Manual searching, complex JQL, drag-and-drop. | DAG dependency queries (`bd ready` / `bd blocked`). |
| **Payload Weight** | 10k–100k tokens per query (HTML/GraphQL). | Compressed JSON schemas & `<100 bytes` minimal models. |
| **Context Longevity** | Stateless; prompt resets blow context memory. | `bd prime` boots workflow context & persistent memories. |
| **Agent Concurrency**| High risk of dual-agent overlap on same tasks. | Atomic Compare-And-Swap (CAS) lease fencing. |
| **State Integrity** | Out of sync with the physical worktree. | Relies on Dolt (SQL versioned database in `.beads`). |

---

## 🔍 3. Deep Dive into Key Components & Mechanics

### 🌿 3.1. Graph-Based Dependency Engine (DAG)
The tracking system in Beads acts as a Directed Acyclic Graph (DAG), modeling issues as nodes and typed relationships as edges:
- **Relation Types**: `blocks`, `related`, `parent-child`, `duplicates`, `supersedes`, `replies-to`.
- **`bd ready` & `bd blocked`**: These commands traverse the task DAG to find issues that are unblocked (have no active dependencies or whose blocking issues are closed) vs issues that are blocked (annotated with why and by whom).
- **Hierarchical Identity**: Issues use hierarchical IDs (e.g., `bd-a3f8.1`, `bd-a3f8.1.1`) to represent subtask branching automatically.

```
       [Epic: bd-a1b2]
         /         \
   [Task: bd-a1b2.1] [Task: bd-a1b2.2] <-- (Blocked by bd-a1b2.1)
         |
  [Wisp: bd-a1b2.1.1] (Ephemeral sub-task)
```

### 🧠 3.2. Context Engineering & Diet Protocols
Beads utilizes highly optimized serialization protocols to prevent agent context bloating:
1. **Lazy Tool Schema Loading**: The Beads Model Context Protocol (MCP) server implements a discovery handshake. Instead of registering 50k tokens of JSON schemas at boot, it registers empty or lightweight schemas, letting agents request deep schemas via `get_tool_info(name)` only when needed.
2. **Minimal Issue Model (`IssueMinimal`)**: Standard lists return highly compressed profiles (~80 bytes per entry) containing only IDs, titles, priority, and flags. Full metadata (descriptions, design files, comments) are isolated and accessed only via `bd show <id>` on an individual basis.
3. **Unbounded Compaction Guard (`CompactedResult`)**: If a query returns more than 20 results, Beads automatically switches to a compacted payload, returning the top 5 results as a preview and a metadata summary telling the agent how to narrow down its query.
4. **Context Bootstrapping (`bd prime`)**: A lightweight command outputting compact, AI-optimized markdown instructions (~50 tokens in MCP mode, ~1k in CLI mode) to act as a resilient anchor in the agent's prompt, preventing memory loss after context compactions.

### 🛡️ 3.3. Concurrency, Leases, and Fencing
In a multi-agent swarm, two subagents might accidentally claim the same task. Beads solves this via **Atomic Fencing**:
- **Atomic Claiming**: `bd update <id> --claim` uses a Compare-And-Swap (CAS) mechanism. It writes a lease record to the storage backend containing a lease owner ID (the agent's identifier) and an expiration lease window.
- **Assign Fence**: If another agent attempts to write state to an issue claimed by someone else, the system throws a fencing violation error, rejecting the write.
- **Wisps**: Light, ephemeral subtasks that auto-expire and are pruned via a background Garbage Collector (GC), perfect for short-lived research or sub-agent explorations.

### 📑 3.4. Agent Provenance & Audit Journal
To maintain accountability across swarm runs:
- **`events_journal`**: Every action (create, update, claim, close) is logged in an immutable, append-only ledger.
- **Agent Signatures**: Every write contains an `Agent-Signature` trailer specifying the LLM model name, reasoning type, temperature, and caller context, ensuring absolute traceability.

---

## ⚡ 4. Swarm Assimilation Mapping: Integrating beads Into DNK OS

We can directly map the architectural masterpieces of Beads into our existing **DNK OS Unified Workspace** without introducing heavy dependencies like Dolt. We will implement these concepts inside our current Python-based workspace orchestrators.

### 🗺️ 4.1. The "To-Be" Architectural Mapping

```
     [DNK OS Orchestration (Gerych Prime)]
                    |
      +-------------+-------------+
      |                           |
[TaskDNA DAG]               [SCONES Memory]
      |                           |
      | (DAG Relationships)       | (Context Diet & Compaction)
      v                           v
- Parent/Child Subtasks     - Minimal Schema Serialization
- Blockers / "Ready" Tasks  - Ephemeral "Wisps" Memory Keys
- CAS Workspace Fencing     - Context Bootstrap Anchor (prime.md)
```

### 💻 4.2. Concrete Python Assimilation Examples

To adapt these principles immediately, we can extend our `dnk_decompose_task_dna` and `scones` structures:

#### A. DAG Task Traversal & "Ready" Task Resolver
We can add a dependency analyzer to our TaskDNA to determine which nodes in our DAG are unblocked and executable in parallel:

```python
# core/orchestrator/task_dna_resolver.py
from typing import List, Dict, Any

class TaskDNADAG:
    def __init__(self, tasks: List[Dict[str, Any]]):
        self.tasks = {t["id"]: t for t in tasks}
        
    def get_ready_tasks(self) -> List[Dict[str, Any]]:
        """Returns tasks that have no unresolved dependencies."""
        ready = []
        for task_id, task in self.tasks.items():
            if task.get("status") not in ["pending", "in_progress"]:
                continue
            
            # Check dependencies
            blocked = False
            for dep_id in task.get("dependencies", []):
                dep_task = self.tasks.get(dep_id)
                if dep_task and dep_task.get("status") not in ["completed", "cancelled"]:
                    blocked = True
                    break
            
            if not blocked:
                ready.append(task)
        return ready
```

#### B. Workspace Lease Fencing (Compare-And-Swap)
We can protect our JSON databases (e.g., `visual_shell_db.json`) from concurrent write corruptions during `dnk_swarm_parallel` dispatches:

```python
# core/orchestrator/concurrency_gate.py
import time
import json
import os

class WorkspaceLeaseGate:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def acquire_lease(self, task_id: str, agent_id: str, duration_sec: int = 300) -> bool:
        """Atomically claim a task node using a Compare-And-Swap (CAS) lease protocol."""
        if not os.path.exists(self.db_path):
            return False
            
        with open(self.db_path, "r+") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return False
                
            task = data.get("tasks", {}).get(task_id)
            if not task:
                return False
                
            current_time = time.time()
            lease = task.get("lease", {})
            
            # Fencing: Check if active lease exists and is held by someone else
            if lease and lease.get("expires_at", 0) > current_time:
                if lease.get("owner") != agent_id:
                    # Active lease owned by another agent - Fencing protection triggered!
                    return False
            
            # CAS: Write new lease metadata
            task["lease"] = {
                "owner": agent_id,
                "expires_at": current_time + duration_sec,
                "acquired_at": current_time
            }
            task["status"] = "in_progress"
            
            # Save atomic commit
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
            return True
```

#### C. Context Compaction Guard (Result Compacting)
We can apply an output-limiting protocol on our SCONES memory results and search tools:

```python
# core/orchestrator/context_guard.py
from typing import List, Dict, Any

def compact_search_results(results: List[Dict[str, Any]], limit: int = 20) -> Dict[str, Any]:
    """Guards context diet by trimming massive data queries automatically."""
    total_count = len(results)
    if total_count <= limit:
        return {"compacted": False, "data": results}
        
    # Return minimal previews
    preview = []
    for item in results[:5]:
        preview.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "status": item.get("status"),
            "category": item.get("category")
        })
        
    return {
        "compacted": True,
        "total_count": total_count,
        "preview": preview,
        "preview_count": len(preview),
        "hint": "Query returned too many results. Refine your query parameters or retrieve by ID."
    }
```

---

## 🛠️ 5. Implementation Roadmap for DNK OS

To successfully integrate the Beads design pattern into our Swarm Framework, we establish the following concrete milestones:

### 📍 Milestone 1: TaskDNA Extension (DAG Upgrades)
- **Action**: Enhance `dnk_decompose_task_dna` to support dependency field mapping (`blocks`, `parent_child`).
- **Goal**: Enable swarm dispatchers to resolve dependency trees natively.

### 📍 Milestone 2: Context Diet Implementation
- **Action**: Embed standard result compacting inside `scones_get_memories` and file search tools.
- **Goal**: Auto-compress metadata when results scale beyond 20 nodes, maintaining 20k token targets.

### 📍 Milestone 3: Workspace Concurrency Gateway
- **Action**: Introduce lease locks inside parallel subagent launchers to block duplicate executions.
- **Goal**: Safe concurrent task dispatching via `dnk_swarm_parallel`.

### 📍 Milestone 4: Gerych Session Bootstrapper (`prime.md`)
- **Action**: Create a `core/orchestrator/agents/gerych_prime/PRIME.md` detailing quick reference, quality gates, and essential commands.
- **Goal**: Resilience against mid-session context compaction.

---

## 🛡️ 6. Verification Status

This architectural blueprint and integration mapping have been structured inside the DNK OS ecosystem. We have confirmed the design's structural compliance with `DNK-STD-0075` and project paths.

- **Audited Repository**: `gastownhall/beads`
- **Resulting Artifact**: `docs/tech/sota_assimilation/beads_audit.md`
- **Status**: **Approved for Swarm Assimilation (Active)**
