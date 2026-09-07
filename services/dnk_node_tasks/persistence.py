# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_node_tasks/persistence.py"
# purpose: "Dual-Store Persistence for Node Tasks (JSON DB + Obsidian Vault Sync) and Multi-Tenant Project Management"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    NodeItem,
    DependencyEdge,
    NodeTaskGraph,
    EdgeRelation,
    ProjectInfo,
)
from .graph_engine import NodeTaskGraphEngine
from .seed_data import create_initial_dnk_node_task_graph


DEFAULT_PROJECTS: List[ProjectInfo] = [
    ProjectInfo(
        id="dnk_core",
        name="DNK OS Core",
        slug="dnk-core",
        description="DNK OS Core Platform & Swarm Framework",
        color="#06b6d4",
        icon="dna",
        is_active=True,
        created_at="2026-09-01T00:00:00Z",
    ),
    ProjectInfo(
        id="m_craft",
        name="M-Craft Hub",
        slug="m-craft",
        description="M-Craft E-Commerce & Production Hub",
        color="#a855f7",
        icon="hammer",
        is_active=True,
        created_at="2026-09-01T00:00:00Z",
    ),
    ProjectInfo(
        id="brand_alpha",
        name="Brand Alpha",
        slug="brand-alpha",
        description="Brand Alpha Pilot Store",
        color="#10b981",
        icon="rocket",
        is_active=True,
        created_at="2026-09-01T00:00:00Z",
    ),
]


class NodeTaskPersistenceManager:
    """Manages thread-safe JSON persistence and Obsidian Markdown sync."""

    _instance = None
    _lock = threading.Lock()

    def __init__(
        self,
        data_file_path: Optional[str] = None,
        obsidian_dir: Optional[str] = None,
        projects_file_path: Optional[str] = None,
    ):
        self.data_file = Path(data_file_path or "./data/node_task_graph.json")
        self.obsidian_dir = Path(obsidian_dir or "./docs/notes/tasks_and_ideas")
        self.projects_file = Path(projects_file_path or "./data/projects.json")
        self._graph: Optional[NodeTaskGraph] = None
        self._projects: Optional[List[ProjectInfo]] = None
        self._last_loaded_mtime: float = 0.0
        self._last_loaded_mtime_ns: int = 0
        self._last_projects_mtime: float = 0.0
        self._last_projects_mtime_ns: int = 0
        self._file_lock = threading.Lock()

    @property
    def file_path(self) -> Path:
        """Alias for data_file for backward compatibility."""
        return self.data_file

    @classmethod
    def get_instance(
        cls,
        data_file_path: Optional[str] = None,
        obsidian_dir: Optional[str] = None,
        projects_file_path: Optional[str] = None,
    ) -> "NodeTaskPersistenceManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(data_file_path, obsidian_dir, projects_file_path)
            return cls._instance

    def load_graph(self, force_reload: bool = False) -> NodeTaskGraph:
        """Loads graph from JSON file or initializes from seed baseline with mtime invalidation."""
        with self._file_lock:
            current_mtime = 0.0
            current_mtime_ns = 0
            file_exists = self.data_file.exists()
            if file_exists:
                try:
                    stat_res = self.data_file.stat()
                    current_mtime = stat_res.st_mtime
                    current_mtime_ns = stat_res.st_mtime_ns
                except OSError:
                    file_exists = False

            if self._graph is not None and not force_reload:
                # If file exists on disk and its mtime hasn't changed since last load/save, return cached graph
                if file_exists and current_mtime_ns > 0 and current_mtime_ns <= self._last_loaded_mtime_ns:
                    return self._graph
                elif not file_exists:
                    return self._graph

            if file_exists:
                try:
                    with open(self.data_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._graph = NodeTaskGraph.model_validate(data)
                    NodeTaskGraphEngine.recalculate_graph_dependencies(self._graph)
                    self._last_loaded_mtime = current_mtime
                    self._last_loaded_mtime_ns = current_mtime_ns
                    return self._graph
                except Exception as e:
                    print(f"[NodeTaskPersistence] Warning: Failed to load {self.data_file}: {e}. Falling back to baseline.")

            # Initialize with seed data
            self._graph = create_initial_dnk_node_task_graph()
            NodeTaskGraphEngine.recalculate_graph_dependencies(self._graph)
            self._save_graph_unlocked()
            return self._graph

    def save_graph(self, graph: Optional[NodeTaskGraph] = None) -> None:
        """Saves graph to JSON store."""
        with self._file_lock:
            if graph is not None:
                self._graph = graph
            self._save_graph_unlocked()

    def _save_graph_unlocked(self) -> None:
        if self._graph is None:
            return
        self._graph.updated_at = datetime.now(timezone.utc).isoformat()
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            f.write(self._graph.model_dump_json(indent=2))
        try:
            stat_res = self.data_file.stat()
            self._last_loaded_mtime = stat_res.st_mtime
            self._last_loaded_mtime_ns = stat_res.st_mtime_ns
        except OSError:
            pass

    def reset_to_baseline(self) -> NodeTaskGraph:
        """Resets the graph to the rich DNK OS roadmap seed."""
        with self._file_lock:
            self._graph = create_initial_dnk_node_task_graph()
            NodeTaskGraphEngine.recalculate_graph_dependencies(self._graph)
            self._save_graph_unlocked()
            return self._graph

    def get_projects(self, force_reload: bool = False) -> List[ProjectInfo]:
        """Loads projects from JSON file or initializes with default projects with mtime invalidation."""
        with self._file_lock:
            current_mtime = 0.0
            current_mtime_ns = 0
            file_exists = self.projects_file.exists()
            if file_exists:
                try:
                    stat_res = self.projects_file.stat()
                    current_mtime = stat_res.st_mtime
                    current_mtime_ns = stat_res.st_mtime_ns
                except OSError:
                    file_exists = False

            if self._projects is not None and not force_reload:
                if file_exists and current_mtime_ns > 0 and current_mtime_ns <= self._last_projects_mtime_ns:
                    return [p.model_copy() for p in self._projects]
                elif not file_exists:
                    return [p.model_copy() for p in self._projects]

            if file_exists:
                try:
                    with open(self.projects_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        self._projects = [ProjectInfo.model_validate(p) for p in data]
                        self._last_projects_mtime = current_mtime
                        self._last_projects_mtime_ns = current_mtime_ns
                        return [p.model_copy() for p in self._projects]
                except Exception as e:
                    print(f"[NodeTaskPersistence] Warning: Failed to load {self.projects_file}: {e}. Falling back to default projects.")

            # Initialize with default projects
            self._projects = [p.model_copy() for p in DEFAULT_PROJECTS]
            self._save_projects_unlocked()
            return [p.model_copy() for p in self._projects]

    def create_project(self, project: ProjectInfo) -> ProjectInfo:
        """Adds or updates a project and persists to JSON file."""
        with self._file_lock:
            if self._projects is None:
                if self.projects_file.exists():
                    try:
                        with open(self.projects_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if isinstance(data, list):
                            self._projects = [ProjectInfo.model_validate(p) for p in data]
                    except Exception:
                        self._projects = [p.model_copy() for p in DEFAULT_PROJECTS]
                else:
                    self._projects = [p.model_copy() for p in DEFAULT_PROJECTS]

            projects_list = self._projects if self._projects is not None else []
            if not project.created_at:
                project.created_at = datetime.now(timezone.utc).isoformat()

            replaced = False
            for idx, existing in enumerate(projects_list):
                if existing.id == project.id:
                    projects_list[idx] = project
                    replaced = True
                    break
            if not replaced:
                projects_list.append(project)

            self._projects = projects_list
            self._save_projects_unlocked()
            return project

    def _save_projects_unlocked(self) -> None:
        if self._projects is None:
            return
        self.projects_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.projects_file, "w", encoding="utf-8") as f:
            json_data = [p.model_dump() for p in self._projects]
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        try:
            stat_res = self.projects_file.stat()
            self._last_projects_mtime = stat_res.st_mtime
            self._last_projects_mtime_ns = stat_res.st_mtime_ns
        except OSError:
            pass

    def get_node(self, node_id: str, force_reload: bool = False) -> Optional[NodeItem]:
        """Retrieves a single node by ID, ensuring cache is fresh via load_graph."""
        graph = self.load_graph(force_reload=force_reload)
        return graph.nodes.get(node_id)

    def find_node(self, node_id: str, force_reload: bool = False) -> Optional[NodeItem]:
        """Alias for get_node."""
        return self.get_node(node_id, force_reload=force_reload)

    def get_graph(self, project_id: Optional[str] = None, force_reload: bool = False) -> NodeTaskGraph:
        """
        Retrieves graph, optionally filtered by project_id.
        If project_id is provided, only nodes with that project_id (nodes without project_id treated as 'dnk_core')
        and valid internal edges are returned.
        """
        full_graph = self.load_graph(force_reload=force_reload)
        if not project_id:
            return full_graph

        filtered_nodes = {}
        for node_id, node in full_graph.nodes.items():
            node_proj = getattr(node, "project_id", None) or "dnk_core"
            if node_proj == project_id:
                filtered_nodes[node_id] = node.model_copy(deep=True)

        filtered_edges = [
            e.model_copy(deep=True)
            for e in full_graph.edges
            if e.source in filtered_nodes and e.target in filtered_nodes
        ]

        filtered_graph = NodeTaskGraph(
            nodes=filtered_nodes,
            edges=filtered_edges,
            stages=list(full_graph.stages),
            version=full_graph.version,
            updated_at=full_graph.updated_at,
        )
        NodeTaskGraphEngine.recalculate_graph_dependencies(filtered_graph)
        return filtered_graph

    def sync_to_obsidian(self) -> Dict[str, Any]:
        """
        Synchronizes all nodes and dependencies to the Obsidian Vault
        at ./docs/notes/tasks_and_ideas/ with MRH headers and wikilinks.
        """
        graph = self.load_graph()
        target_dir = self.obsidian_dir
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except (FileExistsError, OSError):
            # Broken symlink in container or host path discrepancy; fallback to local dir
            fallback_dir = Path("./docs/local_notes/tasks_and_ideas")
            fallback_dir.mkdir(parents=True, exist_ok=True)
            target_dir = fallback_dir

        synced_files = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Generate Master Index Note
        index_path = target_dir / "000_DNK_TASK_AND_IDEAS_INDEX.md"
        stats = NodeTaskGraphEngine.compute_statistics(graph)

        index_content = [
            "# --- DNK-MRH-HEADER ---",
            '# mrh_id: "docs/notes/tasks_and_ideas/000_DNK_TASK_AND_IDEAS_INDEX.md"',
            '# purpose: "DNK OS Master Node-Based Tasks & Ideas Index & DAG Status"',
            "# canonical_source: true",
            "# alters_files: []",
            "# triggers_tasks: []",
            '# status: "Active"',
            '# version: "1.0.0"',
            f'# updated_at: "{datetime.now(timezone.utc).strftime("%Y-%m-%d")}"',
            '# author: "DNK-e.com Maksym & Gerych Prime"',
            "# --- END DNK-MRH-HEADER ---",
            "",
            "# 🌐 DNK OS Node-Based TASK & Ideas System Index",
            "",
            f"> Last synced: `{now_str}` | Total Nodes: **{stats.total_nodes}** | Progress: **{stats.overall_progress}%**",
            "",
            "## 📊 System Overview",
            f"- 💡 **Ideas**: {stats.ideas_count}",
            f"- 🏆 **Epics**: {stats.epics_count}",
            f"- 📋 **Tasks**: {stats.tasks_count}",
            f"- 🛡️ **Quality Gates**: {stats.gates_count}",
            f"- 🔒 **Blocked Nodes**: {stats.blocked_count} | 🔓 **Ready**: {stats.ready_count} | ⚡ **In Progress**: {stats.in_progress_count} | ✅ **Completed**: {stats.completed_count}",
            "",
            "## 🗺️ Node Registry & Stage Status",
            "| ID | Type | Title | Stage | Status | Progress | Assigned | Blocked By |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for node_id, node in graph.nodes.items():
            blocked_str = ", ".join([f"[[{b}]]" for b in node.blocked_by]) if node.blocked_by else "None"
            badge_type = {
                "idea": "💡 Idea",
                "epic": "🏆 Epic",
                "task": "📋 Task",
                "slice": "⚡ Slice",
                "gate": "🛡️ Gate"
            }.get(node.node_type.value, node.node_type.value)

            row = (
                f"| [[{node.id}]] | {badge_type} | **{node.title}** | `{node.stage.value}` | "
                f"`{node.status.value}` | {node.progress}% | `{node.assigned_agent or 'None'}` | {blocked_str} |"
            )
            index_content.append(row)

        index_content.extend([
            "",
            "## 🔗 Active Swarm Workload Distribution",
        ])
        for agent, count in stats.agent_workload.items():
            index_content.append(f"- **{agent}**: {count} active node(s)")

        index_content.append("")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(index_content))
        synced_files.append(str(index_path))

        # 2. Generate Individual Notes for Every Node
        type_to_sub = {
            "idea": "ideas",
            "epic": "epics",
            "task": "tasks",
            "slice": "tasks",
            "gate": "gates",
        }
        for node_id, node in graph.nodes.items():
            sub_folder_name = type_to_sub.get(node.node_type.value, "tasks")
            sub_dir = target_dir / sub_folder_name
            sub_dir.mkdir(parents=True, exist_ok=True)
            node_file = sub_dir / f"{node.id}.md"

            # Compute upstream and downstream relations
            upstream_deps = []
            downstream_deps = []
            for e in graph.edges:
                if e.target == node.id:
                    upstream_deps.append(f"- **{e.relation.value}** from [[{e.source}]] ({e.description or ''})")
                elif e.source == node.id:
                    downstream_deps.append(f"- **{e.relation.value}** to [[{e.target}]] ({e.description or ''})")

            ac_items = "\n".join([f"- [ ] {ac}" for ac in node.acceptance_criteria]) or "_None defined_"
            target_files = "\n".join([f"- `{tf}`" for tf in node.target_files]) or "_None specified_"
            tags_str = ", ".join(node.tags)

            content = [
                "# --- DNK-MRH-HEADER ---",
                f'# mrh_id: "docs/notes/tasks_and_ideas/{sub_folder_name}/{node.id}.md"',
                f'# purpose: "Task & Idea Node: {node.title}"',
                "# canonical_source: true",
                "# alters_files: []",
                "# triggers_tasks: []",
                '# status: "Active"',
                '# version: "1.0.0"',
                f'# updated_at: "{datetime.now(timezone.utc).strftime("%Y-%m-%d")}"',
                '# author: "DNK-e.com Maksym & Gerych Prime"',
                "# --- END DNK-MRH-HEADER ---",
                "",
                "---",
                f"node_id: {node.id}",
                f"title: \"{node.title}\"",
                f"node_type: {node.node_type.value}",
                f"stage: {node.stage.value}",
                f"status: {node.status.value}",
                f"progress: {node.progress}",
                f"priority: {node.priority}",
                f"assigned_agent: {node.assigned_agent or 'None'}",
                f"target_module: {node.target_module or 'None'}",
                f"is_blocked: {str(node.is_blocked).lower()}",
                f"tags: [{tags_str}]",
                "---",
                "",
                f"# {node.title}",
                "",
                f"**Type**: `{node.node_type.value.upper()}` | **Stage**: `{node.stage.value}` | **Status**: `{node.status.value}` | **Progress**: `{node.progress}%`",
                "",
                "### Description",
                node.description,
                "",
                "### Target Module & Files",
                f"**Module**: `{node.target_module or 'core'}`",
                target_files,
                "",
                "### Acceptance Criteria (Definition of Done)",
                ac_items,
                "",
                "### Upstream Dependencies (Prerequisites)",
                "\n".join(upstream_deps) if upstream_deps else "_No upstream dependencies_",
                "",
                "### Downstream Dependents",
                "\n".join(downstream_deps) if downstream_deps else "_No downstream dependents_",
                "",
                f"> Node Position on Canvas: `x={node.position.x}, y={node.position.y}`",
                f"> Backlink to Master Index: [[000_DNK_TASK_AND_IDEAS_INDEX]]",
                ""
            ]

            with open(node_file, "w", encoding="utf-8") as f:
                f.write("\n".join(content))
            synced_files.append(str(node_file))

        return {
            "status": "success",
            "synced_count": len(synced_files),
            "obsidian_dir": str(target_dir),
            "files": synced_files
        }
