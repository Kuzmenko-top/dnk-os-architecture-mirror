# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/software-development/sota-repository-assimilation/references/beads_ai_native_tracker_and_context_engineering.md"
# purpose: "SOTA Reference: beads AI-Native Tracker & Context Engineering."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧠 Steve Yegge's Beads (bd): AI-Native Tracker & Context Engineering Patterns

## 👑 1. Traditional vs. AI-Native Trackers
Traditional issue trackers (Jira, Linear, GitHub Issues) are designed for human consumption via rich web browsers. When applied to AI-agent workflows, they create massive **context window pollution**, suffer from a lack of concurrency fencing (multiple agents picking the same task), and lack programmatic DAG-navigation tools.

Beads (`bd`) solves this by defining tasks and contexts specifically designed for programmatic AI consumption.

---

## ⚡ 2. Core Technological & Architectural Patterns

### A. Graph-Based Dependency Engine (DAG Task Representation)
Tasks in Beads are nodes in a directed acyclic graph (DAG) connected by typed edges:
- `blocks` / `is_blocked_by`
- `parent-child` (Working Set Isolation)
- `related_to`
- `supersedes`

#### Gerych Adaptability Recipe:
- **Autonomous Ready Queue**: Instead of asking humans "what to do next," agents query `bd ready` which returns only leaves of the DAG whose dependencies are 100% resolved (`status = OPEN` and `is_blocked = FALSE`).
- **Blocked Path Exposure**: `bd blocked` lists tasks that cannot be processed, mapping out exactly what blocks them, allowing agents to systematically unblock upstream tasks first.

---

### B. Context Engineering & Diet Invariants
To maximize model reasoning capacity and avoid token bloating, Beads enforces strict diet patterns:

1. **Bootstrap Session Anchors (`bd prime`)**:
   - A dedicated command designed to run during Session Start or after a context compaction.
   - Outputs a highly concentrated prompt payload (~50 tokens for MCP, 1-2k for CLI) summarizing:
     - Project constraints and absolute rules.
     - Currently claimed tasks.
     - Unblocked task backlog.
     - Target quality gates.

2. **Compacted Result Rendering (`IssueMinimal`)**:
   - Listing large issue databases can quickly consume 30k+ tokens.
   - Beads defines a lightweight DTO: `IssueMinimal` (ID, Status, Assignee, Title) representing ~80 bytes of text.
   - If an operation returns >20 results, the system automatically prints a `CompactedResult` preview and prompts the agent to paginate or narrow the query using explicit filters.

3. **Lazy Tool Schema Discovery**:
   - Traditional MCP servers register all tool JSON schemas upon startup, injecting up to 50k tokens of JSON schemas into every turn.
   - Beads-MCP registers light-weight schemas or discovers tools on demand (`discover_tools()`, `get_tool_info()`), reducing prompt overhead by 90%.

---

### C. Concurrency Fencing & Atomic Task Claiming
When multi-agent swarms operate concurrently on the same workspace, they run into race conditions (e.g. two subagents writing to the same database or selecting the same task).

- **Compare-And-Swap (CAS) Lease Locks**:
  - `bd update <issue_id> --claim` performs an atomic update to lock the task to the current session.
  - If another agent attempts to edit or work on that task, the operation is blocked by a fencing check.
  - Claims have automatic TTL (leases) that expire unless renewed, preventing tasks from being permanently stranded if an agent crashes.

---

### D. Audit Trails & AI Provenance
Beads automatically logs metadata of the agent that performed the task:
- Model signature (`model_name`, `provider`, `temperature`).
- Execution transcript / seed.
- Appended as Git Commit Trailers to track provenance:
  ```git
  Agent-Signature: Gerych-Prime; model=gemini-3.5-flash; context_hash=sha256:7f9a...
  ```

---

### E. Local-First / Git-Integrated Persistence (Dolt & SQLite)
Beads supports storing task databases directly in `.beads/` within the git repository:
- **SQLite**: Local relational storage for zero-dependency operation.
- **Dolt Integration**: "Git for data." Allows branching, merging, and time-travel querying of relational issue tables. Task updates are checked in and pushed/pulled alongside standard source code commits.

---

## 🛠️ Gerych Swarm Implementation Guide

To implement these patterns inside our custom Python tools in `DNK_HUB`:

```python
# Example: Compacted Result Pattern for high-volume file searches or SCONES memory results
def render_compacted_results(results: list[dict], threshold: int = 20) -> str:
    if len(results) <= threshold:
        return "\n".join(f"- [{r['id']}] {r['title']} ({r['status']})" for r in results)
    
    compacted = results[:threshold]
    omitted_count = len(results) - threshold
    
    output = "\n".join(f"- [{r['id']}] {r['title']} ({r['status']})" for r in compacted)
    output += f"\n\n⚠️ CONTEXT DIET WARNING: Truncated {omitted_count} items to save context tokens."
    output += f"\nUse `get_details(ids=[...])` or narrow your query to see more."
    return output
```

Use these patterns during any scale operations to keep the token diet strictly controlled and execution speed maximized.
