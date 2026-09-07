# DAG Task Graph Persistence Hygiene, Test Isolation & Conversational Intake Guard

## 1. Problem & Root Cause
In dynamic canvas / DAG task graphs with live JSON persistence (`data/node_task_graph.json` via `NodeTaskPersistenceManager`), two major contamination vectors can rapidly bloat the graph (e.g. from 11 baseline nodes to 240+ chaotic nodes):
1. **Unisolated Integration Tests**: Test suites invoking FastAPI endpoints (`TestClient`) or background services directly execute against the singleton instance of `NodeTaskPersistenceManager.get_instance()`, mutating the live production/development JSON file instead of an isolated sandbox.
2. **Naive Conversational Chat Intake**: A natural language intake endpoint (`POST /api/v3/node_tasks/chat_intake`) that unconditionally treats every chat message as a task or epic decomposition will create phantom task nodes (`task-chat-*`) whenever the user asks an exploratory or diagnostic question (e.g., *"Why are there so many nodes?"* or *"What is the status?"*).

---

## 2. Test Persistence Isolation Pattern (Pytest `tmp_path`)
Never let integration tests mutate the active repo data file. In all test modules touching `NodeTaskPersistenceManager`, inject an auto-use or explicit pytest fixture using `tmp_path`:

```python
import pytest
from services.dnk_node_tasks.persistence import NodeTaskPersistenceManager

@pytest.fixture(autouse=True)
def isolate_node_task_persistence(tmp_path):
    """
    Isolates NodeTaskPersistenceManager so tests mutate an ephemeral temp graph,
    preserving the canonical data/node_task_graph.json baseline.
    """
    original_instance = NodeTaskPersistenceManager._instance
    temp_file = tmp_path / "node_task_graph.json"
    
    # Initialize a clean manager pointing to the temporary directory
    isolated_manager = NodeTaskPersistenceManager(storage_path=temp_file)
    NodeTaskPersistenceManager._instance = isolated_manager
    
    yield isolated_manager
    
    # Restore original singleton after test teardown
    NodeTaskPersistenceManager._instance = original_instance
```

### Verification Invariant:
After running test suites (`pytest tests/verification/test_node_tasks_*.py`), verify that `data/node_task_graph.json` has not changed:
```bash
git diff --exit-code data/node_task_graph.json
```

---

## 3. Conversational Intake Guard (Intent Disambiguation)
To prevent conversational chit-chat or questions from spawning junk nodes, implement intent classification before invoking node creation or DAG decomposition:

```python
import re

CONVERSATIONAL_PATTERNS = [
    r"^(привіт|добридень|вітаю|hello|hi|hey)\b",
    r"^(чому|як|що|де|коли|хто|скільки|why|how|what|where|when|who)\b",
    r"\?$",  # Ending with a question mark without task keywords
]

TASK_COMMAND_PATTERNS = [
    r"^(створи|додай|зроби|розбий|декомпозуй|create|add|make|decompose|task:|epic:|ідея:)\b"
]

def is_conversational_inquiry(text: str) -> bool:
    cleaned = text.strip().lower()
    # If explicitly prefixed with task keywords, prioritize as task
    if any(re.search(pat, cleaned) for pat in TASK_COMMAND_PATTERNS):
        return False
    # If matching question words, greetings, or ending in '?', classify as conversation
    return any(re.search(pat, cleaned) for pat in CONVERSATIONAL_PATTERNS)
```

When `is_conversational_inquiry` returns `True`:
- **Do NOT** call `create_task_node()` or `decompose_epic()`.
- Return an informational message (e.g. summary of current nodes, status breakdown, or guidance on task syntax).
- Preserve existing graph topology.
