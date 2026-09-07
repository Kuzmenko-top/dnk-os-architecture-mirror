# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/software-development/sota-repository-assimilation/references/graphify_ast_knowledge_graph_and_obsidian_canvas_assimilation.md"
# purpose: "Assimilation notes and architectural recipes for Graphify (Graphify-Labs/graphify): deterministic Tree-sitter AST, NetworkX Leiden clustering, Obsidian Canvas export, and zero-vector code graph traversal."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🕸️ Graphify Architecture & Assimilation Blueprint

- **Repository**: `Graphify-Labs/graphify` (115k+ stars, YC S26)
- **License**: Apache 2.0 (Track 1 Permissive - Direct Template & Component Assimilation)
- **Core Philosophy**: Zero-vector code knowledge graph. Local deterministic Tree-sitter AST parsing; no embeddings, no LLM cost for code graph construction, graph traversal instead of grepping/vector search.

---

## 1. Pipeline Architecture

```
detect() ➔ extract() ➔ build() ➔ cluster() ➔ analyze() ➔ report() ➔ export()
```

- **Clean Functional Decoupling**: Each stage is an isolated function communicating via plain Python dicts and NetworkX `nx.Graph` instances without global mutable state.
- **Node & Edge Schema**:
  ```json
  {
    "nodes": [
      {"id": "routing:APIRouter", "label": "APIRouter", "source_file": "routing.py", "source_location": "L2210"}
    ],
    "edges": [
      {"source": "id_a", "target": "id_b", "relation": "calls|imports|uses|method", "confidence": "EXTRACTED|INFERRED|AMBIGUOUS"}
    ]
  }
  ```
- **Confidence Taxonomy**:
  - `EXTRACTED`: Explicit AST syntax (imports, inheritance, declarations, function calls).
  - `INFERRED`: Derived via call-graph second pass, resolution tables, or co-occurrence.
  - `AMBIGUOUS`: Flagged for human/auditor review.

---

## 2. Key Modules & Reusable Patterns

### A. Clustering & Community Detection (`graphify/cluster.py`)
- Employs `graspologic_native.leiden` (compiled Rust) for ultra-fast community detection, falling back to NetworkX Louvain.
- Native Rust bypass avoids heavy `numba`/`umap` JIT overhead (saving 7-19s per run).
- Splits oversized communities to keep graph clusters readable and bounded.

### B. Obsidian Canvas Export Layout Engine (`graphify/export.py:to_canvas`)
- Direct export into Obsidian `.canvas` JSON format (`nodes: [...]`, `edges: [...]`).
- **Grid Layout Algorithm**:
  - Calculates grid dimensions: `cols = ceil(sqrt(num_communities))`, `rows = ceil(num_communities / cols)`.
  - Places community groups as colored enclosing frames (`CANVAS_COLORS = ["1".."6"]`).
  - Arranges member nodes inside each community card in structured internal rows and columns.
  - Adds typed directed edges connecting nodes across and within communities.

### C. Graph Analysis & God Nodes (`graphify/analyze.py`)
- Computes degree centrality, betweenness, and cohesion to detect:
  - `god_nodes(G)`: High-degree architectural bottlenecks.
  - `surprising_connections(G)`: Cross-community bridge edges violating layering.
  - `find_import_cycles(G)`: Circular dependency chains for CI gates.

---

## 3. DNK OS Assimilation & Integration Map

1. **Obsidian Canvas Bridge (`apps/api/routers/obsidian_canvas_bridge.py`)**:
   - Assimilate `export.to_canvas` community grid layout math to auto-generate `.canvas` views from Swarm TaskDNA DAGs and code symbol graphs.
2. **Deterministic Code Discovery (`scripts/system/repo_map.py` & `dnk_resolve_symbol`)**:
   - Augment `repo_map.py` with Graphify's two-tier `EXTRACTED`/`INFERRED` relationship extraction and shortest-path query (`get_call_path(from_sym, to_sym)`).
3. **Auditor Quality Gates (`core/orchestrator/agents/gerych_auditor/`)**:
   - Utilize Graphify's `find_import_cycles` and `god_nodes` detection in pre-commit adversarial reviews (`dnk_run_adversarial_review`).
4. **Hybrid Knowledge Graph (LightRAG + Graphify)**:
   - Combine LightRAG's semantic concept extraction with Graphify's deterministic AST graph for 100% grounded architectural exploration.

---

## 4. Live Verification Recipes & Operational Pitfalls (from DNK_HUB Benchmark)

### A. Non-LLM Extraction & Clustering Commands
For large codebases (>7k files, >100k nodes) without consuming LLM tokens:
```bash
# 1. Deterministic code-only AST extraction (allow >=300s timeout)
graphify extract . --code-only

# 2. Local Leiden/Louvain community clustering without LLM labeling
graphify cluster-only . --no-label

# 3. Interactive D3 tree visualization
graphify tree --graph graphify-out/graph.json --output graphify-out/GRAPH_TREE.html
```

### B. Agent Instant Query CLI Tools (<50ms AST queries)
- **Blast Radius Analysis**: `graphify affected "<Symbol>"` — reveals all upstream dependents before refactoring.
- **Shortest Call Path**: `graphify path "<SymbolA>" "<SymbolB>"` — traces exact hop sequence (`A <--imports-- file <--imports-- B`).
- **Architectural Hubs**: `graphify god-nodes` — lists components with excessive degree centrality.
- **Symbol Inspection**: `graphify explain "<Symbol>"` — gives file, line number, community ID, and immediate AST edges.

### C. Large Monorepo Subgraph Canvas Export Recipe
Because a full monorepo graph (>100k nodes) exceeds Obsidian Canvas rendering capacity, filter to a high-degree subgraph or domain before exporting:
```python
import json, networkx as nx
import graphify.export as exp

with open("graphify-out/graph.json") as f:
    data = json.load(f)

# Schema note: node objects use 'source_file' and edges reside in 'links'
core_nodes = {n["id"]: n for n in data["nodes"] if "core/" in n.get("source_file", "")}
core_ids = set(core_nodes.keys())

G = nx.Graph()
for nid, ndata in core_nodes.items():
    G.add_node(nid, label=ndata.get("label", nid), source_file=ndata.get("source_file", ""))
for edge in data.get("links", []):
    u, v = edge.get("source"), edge.get("target")
    if u in core_ids and v in core_ids:
        G.add_edge(u, v, relation=edge.get("relation", ""), confidence=edge.get("confidence", "EXTRACTED"))

# Top N degree nodes for clean canvas rendering
degrees = dict(G.degree())
top_nodes = sorted(degrees.keys(), key=lambda n: degrees[n], reverse=True)[:100]
sub_G = G.subgraph(top_nodes).copy()

communities = {1: [n for n in sub_G.nodes()]}
exp.to_canvas(sub_G, communities, "docs/notes/architecture.canvas")
```

### D. Repository Hygiene Invariant
Always ensure `graphify-out/` and `.graphify*` are added to `.gitignore` — full graph outputs generate 100MB+ of artifacts.

### E. Monorepo Multi-Tier AST Pitfall: Phantom Inferred Connections
- **The Pitfall**: In monorepos containing both primary root modules (`apps/web`, `core/`) and nested/vendored R&D subprojects (`visual_shell/open_design`), heuristic AST engines generate false-positive `[INFERRED]` cross-community calls. For example, a standard `catch (err)` block in `apps/web` can be falsely linked to `export const err = ...` in a nested daemon package.
- **Resolution**:
  1. Scope AST extraction using ignore rules for nested/vendored trees (`--ignore "visual_shell/*"`).
  2. Avoid bare identifier collisions in client code by using typed `catch (error: unknown)` with explicit `instanceof Error` normalization.
  3. Formalize a canonical client-side `apiProtocol.ts` exporting explicit `ApiError` and `Result<T, E>` types.
  4. Enforce strict layer purity with automated AST/regex boundary tests (`tests/test_web_layer_isolation.py`) ensuring zero cross-tier imports for Tier-2 packaging.

### F. Resolving Circular Import Cycles (Dependency Inversion & Type Decoupling)
- **The Pitfall**: `graphify find_import_cycles` or compiler AST passes reveal circular dependency chains (e.g. `anthropic.ts <-> openai-compatible.ts`, `updater.ts <-> scheduler.ts`). These cycles degrade tree-shaking, cause undefined runtime evaluation order, and introduce subtle initialization bugs.
- **Root Cause Taxonomy**:
  1. *Concrete Sibling as Type Hub*: One concrete driver (e.g. `anthropic.ts`) defines shared interfaces (e.g. `StreamHandlers`) imported by 9 sibling drivers, while the first driver dynamically aggregates or proxies those siblings.
  2. *Utility Layer Inversion*: A pure utility/protocol module (`utils/apiProtocol.ts`) imports domain predicates (`isOpenAICompatible`) from a concrete driver, while drivers import protocol types from the utility.
  3. *Parent-Child Bidirectional Coupling*: A subsystem facade (`updater.ts`) imports execution runners from submodules (`updater/payload.ts`, `updater/scheduler.ts`), while submodules import facade types (`DesktopUpdater`, `DesktopUpdaterLogger`) from the parent file.
- **Resolution Recipe**:
  1. **Leaf Type Extraction**: Extract shared contracts into dedicated leaf type modules (`providers/types.ts`, `updater/types.ts`). Leaf type modules have zero runtime imports.
  2. **Predicate Relocation**: Move protocol predicates directly into the protocol/utility layer (`utils/apiProtocol.ts`), ensuring dependencies flow strictly downwards (Drivers -> Utilities -> Types).
  3. **Facade Re-export**: In the parent facade, import types from the leaf module and re-export them (`export type { DesktopUpdater } from "./updater/types.js"`) to maintain backwards compatibility without cyclic coupling.
  4. **AST Pre-Commit Gate**: Add an automated import cycle test (`tests/test_import_cycles.py`) to the verification gate (`verify_all.sh`) to detect new circular chains immediately.

### G. Decomposing Monolithic God Components (The 12,000-Line Accretion Disk Pattern)
- **The God Node Symptom**: High-centrality UI components (e.g. `ProjectView.tsx` with 12,148 LOC and 31+ external connections flagged by `graphify god-nodes`) accumulate state management, event streaming buffers, file artifact recovery, and panel layout calculations alongside DOM rendering. External consumers (`useConversationChat.ts`, unit tests) become coupled to the God Node just to reuse pure domain algorithms.
- **Modular Domain Package Extraction Recipe**:
  1. **Dedicated Domain Subdirectory**: Create `src/components/<component-name>/` (e.g. `components/project-view/`) to isolate sub-concerns into focused, single-responsibility files:
     - `layoutUtils.ts`: Dimensions, clamping, CSS variable injection, storage persistence, panel collapse logic.
     - `conversationUtils.ts`: Turn order normalization (`normalizeConversationMessageOrder`), server/local message merging, run status transitions, and buffered streaming text updates (`createBufferedTextUpdates` with `hasPendingText`, `visibilitychange`, and `pagehide` teardown safety).
     - `artifactRecoveryUtils.ts`: Touched file path extraction from agent events, primary file heuristics, artifact comparison normalization.
     - `index.ts`: Barrel export unifying the domain package.
  2. **Zero-Downtime Decoupling & Backward Compatibility**:
     - Re-export all extracted utilities from the legacy God Component to ensure 100% backward compatibility for existing consumers and third-party imports.
     - Decouple active consumers (`useConversationChat.ts`, component tests) by repointing imports directly to the modular package (`../project-view`).
  3. **Automated Architecture Gate**:
     - Author a dedicated regression test (`tests/test_project_view_decomposition.py`) asserting that modular files exist, export required symbols, and critical consumers do not import extracted utilities from the God Component.
