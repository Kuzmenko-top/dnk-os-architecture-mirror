# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/conversational_task_intake_and_capcut_stitch_protocol.md"
# purpose: "Protocol specification for Conversational Task Intake, DAG mutation, and CapCut/Google Stitch workspace integration."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎬 Conversational Task Intake & CapCut / Google Stitch Visual Cabinet Protocol

## 1. Architectural Overview
This protocol defines how user natural language prompts (in Ukrainian or English) delivered via chat or a floating command dock are autonomously transformed into typed DAG nodes, assigned to specialized swarm agents, linked by dependency edges, and synchronized to dual persistence (JSON DB + Obsidian Vault).

## 2. Core Components

1. **Conversational Task Extractor (`services/dnk_node_tasks/conversational_intake.py`)**:
   - Analyzes intent, keywords, and patterns to extract:
     - **Node Types**: `idea` (концепт, гіпотеза), `task` (виконавча дія), `epic` (великий рефакторинг/проєкт), `gate` (перевірка якості, тест).
     - **Priorities**: `critical` (терміново, негайно), `high` (важливо), `medium`, `low`.
     - **Swarm Agent Routing**: `dnk_dev_fullstack`, `gerych_builder`, `dnk_shopify`, `dnk_video_ai_creator`, `gerych_auditor`.
     - **DAG Decomposition**: Multi-action prompts are parsed into sequential subtasks linked with `depends_on` edges.

2. **Backend API Endpoint (`POST /api/v3/node_tasks/chat_intake`)**:
   - Receives `{ "prompt": string, "workspace_id": string, "default_agent": string }`.
   - Mutates `NodeTaskGraph` in memory, saves to `node_task_graph.json`, and triggers `manager.sync_to_obsidian()`.
   - Returns structured feedback with created nodes, edges, and formatted assistant confirmation.

3. **CapCut & Google Stitch Visual Layer (`apps/web/`)**:
   - **Google Stitch Floating Command Dock (`GerychTaskPromptDock.tsx`)**: Bottom-centered input dock with prompt chips (`💡 Ідея`, `🎯 Задача`, `⚡ Декомпозиція`) and pulse indicator.
   - **Slide-out Chat Drawer (`GerychTaskChatDrawer.tsx`)**: Dark-glass panel for extended dialogues with Gerych, rendering task pills with direct canvas focus.
   - **Status Pill (`NodeTaskGraphCanvas.tsx`)**: Bottom-left real-time status beacon (`🟢 Gerych Prime | Task Intake Ready`).

## 3. Containerized Filesystem & Vault Symlink Invariant
When running under Docker / Linux containers where host paths (e.g. `/Users/.../Documents/...`) are not mounted:
- Symlinks like `./docs/notes` become broken symlinks.
- A naive `Path(dir).mkdir(parents=True, exist_ok=True)` raises `FileExistsError: [Errno 17] File exists`.
- **Mandatory Pattern**:
  ```python
  target_dir = self.obsidian_dir
  try:
      target_dir.mkdir(parents=True, exist_ok=True)
  except (FileExistsError, OSError):
      fallback_dir = Path("./docs/local_notes/tasks_and_ideas")
      fallback_dir.mkdir(parents=True, exist_ok=True)
      target_dir = fallback_dir
  ```
