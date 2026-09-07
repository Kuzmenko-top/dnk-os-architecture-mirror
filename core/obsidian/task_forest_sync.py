# --- DNK-MRH-HEADER ---
# mrh_id: "core/obsidian/task_forest_sync.py"
# purpose: "Bidirectional synchronization between TaskForest graph and Obsidian Vault markdown notes."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from core.task_forest.models import (
    TaskNode,
    NodeType,
    ExecutionStage,
    Priority,
)
from core.task_forest.forest import TaskForest


class ObsidianTaskForestSync:
    """
    Handles bidirectional synchronization between DNK Task Forest nodes
    and Obsidian Vault markdown files with YAML frontmatter and [[wikilinks]].
    """

    def __init__(self, forest: TaskForest, vault_dir: str = "docs/notes/task_forest"):
        self.forest = forest
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, text: str) -> str:
        clean = re.sub(r'[\\/*?:"<>|]', "", text).strip()
        clean = clean.replace(" ", "_")
        return clean or "unnamed_node"

    def export_node_to_markdown(self, node: TaskNode) -> str:
        """
        Generate Obsidian-compatible Markdown note with YAML frontmatter,
        DNK-MRH header, and [[wikilinks]] for dependencies.
        """
        dep_wikilinks = []
        for dep_id in node.dependencies:
            dep_node = self.forest.get_node(dep_id)
            title = dep_node.title if dep_node and dep_node.title else dep_id
            dep_wikilinks.append(f"[[{title}]]")

        frontmatter: Dict[str, Any] = {
            "id": node.id,
            "type": node.type.value if isinstance(node.type, NodeType) else str(node.type),
            "title": node.title,
            "stage": node.stage.value if isinstance(node.stage, ExecutionStage) else str(node.stage),
            "priority": node.priority.value if isinstance(node.priority, Priority) else str(node.priority),
            "tags": list(node.tags),
            "dependencies": list(node.dependencies),
            "created_at": node.created_at.isoformat() if isinstance(node.created_at, datetime) else str(node.created_at),
            "updated_at": node.updated_at.isoformat() if isinstance(node.updated_at, datetime) else str(node.updated_at),
        }
        if node.completed_at:
            frontmatter["completed_at"] = node.completed_at.isoformat() if isinstance(node.completed_at, datetime) else str(node.completed_at)
        if node.metadata:
            frontmatter["metadata"] = dict(node.metadata)

        yaml_str = yaml.dump(frontmatter, sort_keys=False, allow_unicode=True)

        mrh_header = (
            f"<!-- --- DNK-MRH-HEADER ---\n"
            f'# mrh_id: "docs/notes/task_forest/{self._sanitize_filename(node.title or node.id)}.md"\n'
            f'# purpose: "Obsidian representation of Task Forest node {node.id}"\n'
            f'# canonical_source: false\n'
            f"# alters_files: []\n"
            f"# triggers_tasks: []\n"
            f'# status: "Active"\n'
            f'# version: "1.0.0"\n'
            f'# updated_at: "{datetime.now().strftime("%Y-%m-%d")}"\n'
            f'# author: "DNK TaskForest Sync"\n'
            f"--- END DNK-MRH-HEADER -->\n"
        )

        dep_list_md = "\n".join([f"- {link}" for link in dep_wikilinks]) if dep_wikilinks else "- None"

        content = (
            f"---\n"
            f"{yaml_str}"
            f"---\n"
            f"{mrh_header}\n"
            f"# {node.title or 'Untitled Node'}\n\n"
            f"**Type:** `{node.type.value}` | **Stage:** `{node.stage.value}` | **Priority:** `{node.priority.value}`\n\n"
            f"## Description\n\n"
            f"{node.description or '_No description provided._'}\n\n"
            f"## Dependencies\n\n"
            f"{dep_list_md}\n"
        )

        return content

    def export_all(self, vault_path: Optional[str] = None) -> int:
        """
        Export all nodes in the forest into Obsidian markdown files.
        """
        target_dir = Path(vault_path) if vault_path else self.vault_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        exported_count = 0
        for node in self.forest.nodes.values():
            filename = f"{self._sanitize_filename(node.title or node.id)}.md"
            file_path = target_dir / filename
            file_path.write_text(self.export_node_to_markdown(node), encoding="utf-8")
            exported_count += 1

        return exported_count

    def import_node_from_markdown(self, file_path: Path) -> Optional[TaskNode]:
        """
        Parse an Obsidian markdown file into a TaskNode.
        """
        text = file_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return None

        parts = text.split("---", 2)
        if len(parts) < 3:
            return None

        frontmatter_str = parts[1]
        try:
            data = yaml.safe_load(frontmatter_str) or {}
        except Exception:
            return None

        # Clean dependencies from [[Wikilinks]] to raw strings or IDs
        raw_deps = data.get("dependencies", [])
        clean_deps = []
        for dep in raw_deps:
            if isinstance(dep, str):
                match = re.search(r"\[\[(.*?)\]\]", dep)
                clean_deps.append(match.group(1) if match else dep)

        data["dependencies"] = clean_deps

        # Extract description from body after headers
        body = parts[2]
        desc_match = re.search(r"## Description\s*\n\n(.*?)(?=\n\n##|\Z)", body, re.DOTALL)
        if desc_match and not data.get("description"):
            desc_text = desc_match.group(1).strip()
            if desc_text != "_No description provided._":
                data["description"] = desc_text

        return TaskNode.from_dict(data)

    def import_all(self, vault_path: Optional[str] = None) -> int:
        """
        Import all markdown files in vault directory into the TaskForest.
        """
        source_dir = Path(vault_path) if vault_path else self.vault_dir
        if not source_dir.exists():
            return 0

        imported_count = 0
        for md_file in source_dir.glob("*.md"):
            node = self.import_node_from_markdown(md_file)
            if node:
                self.forest.nodes[node.id] = node
                for dep in node.dependencies:
                    self.forest.dependency_graph.add_dependency(node.id, dep)
                imported_count += 1

        self.forest._save()
        return imported_count

    def export_to_obsidian(self, vault_path: Optional[str] = None) -> int:
        """
        Alias for export_all to match DNK Task Forest specification.
        """
        return self.export_all(vault_path)

    def import_from_obsidian(self, vault_path: Optional[str] = None) -> int:
        """
        Alias for import_all to match DNK Task Forest specification.
        """
        return self.import_all(vault_path)

    def export_to_canvas(self, canvas_path: Optional[str] = None) -> Path:
        """
        Export the current TaskForest as an Obsidian JSON Canvas (.canvas) file.
        """
        target_path = Path(canvas_path) if canvas_path else self.vault_dir / "task_forest.canvas"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        stage_colors = {
            ExecutionStage.BACKLOG.value: "1",      # Red / Gray
            ExecutionStage.PLANNED.value: "2",      # Orange
            ExecutionStage.IN_PROGRESS.value: "3",  # Yellow
            ExecutionStage.REVIEW.value: "4",       # Green / Cyan
            ExecutionStage.DONE.value: "5",         # Cyan / Blue
        }

        nodes = []
        edges = []

        for node in self.forest.nodes.values():
            color = stage_colors.get(node.stage.value, "1")
            content = f"### {node.title}\n**Type:** {node.type.value} | **Stage:** {node.stage.value}\n**Priority:** {node.priority.value}\n\n{node.description or ''}"
            nodes.append({
                "id": node.id,
                "type": "text",
                "text": content,
                "x": int(node.position.get("x", 0)),
                "y": int(node.position.get("y", 0)),
                "width": 280,
                "height": 160,
                "color": color,
            })

            for dep_id in node.dependencies:
                if dep_id in self.forest.nodes:
                    edges.append({
                        "id": f"e_{dep_id}_{node.id}",
                        "fromNode": dep_id,
                        "fromSide": "right",
                        "toNode": node.id,
                        "toSide": "left",
                        "toEnd": "arrow",
                    })

        canvas_data = {
            "nodes": nodes,
            "edges": edges,
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(canvas_data, f, indent=2, ensure_ascii=False)

        return target_path

    def sync(self, vault_path: Optional[str] = None) -> Dict[str, int]:
        """
        Bidirectionally sync between TaskForest and Obsidian Vault.
        """
        target_dir = Path(vault_path) if vault_path else self.vault_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Import new/updated nodes from vault
        imported = 0
        for md_file in target_dir.glob("*.md"):
            node = self.import_node_from_markdown(md_file)
            if node:
                existing = self.forest.get_node(node.id)
                if not existing or node.updated_at > existing.updated_at:
                    self.forest.nodes[node.id] = node
                    for dep in node.dependencies:
                        self.forest.dependency_graph.add_dependency(node.id, dep)
                    imported += 1

        # 2. Export forest to vault
        exported = self.export_all(str(target_dir))
        self.export_to_canvas(str(target_dir / "task_forest.canvas"))
        self.forest._save()

        return {"imported": imported, "exported": exported}


# Canonical alias for compatibility
TaskForestSync = ObsidianTaskForestSync

