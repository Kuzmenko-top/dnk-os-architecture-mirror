# Architecture Guard & Blast Radius Algorithms

This reference details the core algorithms for cycle detection, layer isolation, and reverse dependency mapping used in high-velocity pre-commit gates.

## 1. Cycle Detection via DFS / Strongly Connected Components

To identify circular imports across TypeScript or Python modules without running a heavy compiler:

```python
import re
from pathlib import Path
from typing import Dict, List, Set

def parse_ts_imports(file_path: Path) -> List[str]:
    content = file_path.read_text(encoding="utf-8")
    # Matches relative imports: from './foo' or from '../bar'
    pattern = r'(?:import|from)\s+[\'"](\.[^\'"]+)[\'"]'
    matches = re.findall(pattern, content)
    resolved = []
    for rel in matches:
        target = (file_path.parent / rel).resolve()
        for ext in [".ts", ".tsx", "/index.ts", "/index.tsx"]:
            candidate = Path(str(target) + ext)
            if candidate.exists() and candidate.is_file():
                resolved.append(str(candidate))
                break
    return resolved

def find_cycles(graph: Dict[str, List[str]]) -> List[List[str]]:
    visited: Set[str] = set()
    rec_stack: List[str] = []
    cycles: List[List[str]] = []

    def dfs(node: str):
        visited.add(node)
        rec_stack.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                idx = rec_stack.index(neighbor)
                cycles.append(rec_stack[idx:] + [neighbor])
        rec_stack.pop()

    for node in graph:
        if node not in visited:
            dfs(node)
    return cycles
```

## 2. Reverse Dependency Graph for Blast Radius

To map touched files to all affected dependents:

```python
from collections import defaultdict, deque
from typing import Dict, List, Set

def build_reverse_dependency_graph(forward_graph: Dict[str, List[str]]) -> Dict[str, Set[str]]:
    reverse_graph = defaultdict(set)
    for source, targets in forward_graph.items():
        for target in targets:
            reverse_graph[target].add(source)
    return reverse_graph

def calculate_blast_radius(changed_files: List[str], reverse_graph: Dict[str, Set[str]]) -> Set[str]:
    affected: Set[str] = set(changed_files)
    queue = deque(changed_files)
    while queue:
        current = queue.popleft()
        for dependent in reverse_graph.get(current, set()):
            if dependent not in affected:
                affected.add(dependent)
                queue.append(dependent)
    return affected
```
