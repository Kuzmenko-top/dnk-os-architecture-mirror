# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_obsidian_task_forest/src/obsidian_task_forest.py"
# purpose: "Standalone Obsidian Task Forest Engine parsing Markdown vault notes, building Plant Hierarchy Scale (Field -> Sector -> Tree -> Bush -> Flower), and calculating Bottom-Up Rollup progress."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


PLANT_ICONS = {
    "field": "🌾",
    "sector": "🏞️",
    "tree": "🌳",
    "bush": "🌿",
    "flower": "🌱",
    "seed": "💎",
    "sprout": "⚡",
}


@dataclass
class PlantNode:
    """
    Represents a task plant node in the Obsidian Task Forest.
    plant_scale options: 'field', 'sector', 'tree', 'bush', 'flower'
    """
    id: str
    title: str
    plant_scale: str = "flower"
    status: str = "pending"  # "pending", "in_progress", "completed", "cancelled"
    progress: float = 0.0
    parent_id: Optional[str] = None
    project_id: Optional[str] = None
    sector_id: Optional[str] = None
    assigned_agent: Optional[str] = None
    weight: float = 1.0
    children: List["PlantNode"] = field(default_factory=list)
    filepath: Optional[str] = None

    def add_child(self, child: "PlantNode") -> "PlantNode":
        child.parent_id = self.id
        self.children.append(child)
        return child

    def get_completion_percentage(self) -> float:
        """
        Calculates completion percentage using Bottom-Up Rollup.
        If node has children: average of children's completion.
        If node is leaf:
          - completed -> 100.0
          - cancelled -> 0.0
          - in_progress / pending -> progress value (0.0 .. 100.0)
        """
        if self.children:
            percentages = [child.get_completion_percentage() for child in self.children]
            return round(sum(percentages) / len(percentages), 2) if percentages else 0.0

        if self.status == "completed":
            return 100.0
        if self.status == "cancelled":
            return 0.0
        return round(max(0.0, min(100.0, float(self.progress))), 2)

    def to_mermaid(self, direction: str = "BT") -> str:
        """
        Generates a Mermaid graph with direction 'BT' (Bottom to Top growth).
        """
        lines = [f"graph {direction}"]

        def _build(node: PlantNode) -> None:
            pct = node.get_completion_percentage()
            if pct >= 100.0 or node.status == "completed":
                icon = "✅"
            elif node.status == "in_progress" or pct > 0:
                icon = "⏳"
            else:
                icon = PLANT_ICONS.get(node.plant_scale, "📌")

            safe_title = node.title.replace('"', "'")
            label = f"{icon} {safe_title} ({pct:.1f}%)"
            lines.append(f'    {node.id}["{label}"]')

            for child in node.children:
                _build(child)
                lines.append(f"    {node.id} --> {child.id}")

        _build(self)
        return "\n".join(lines)


class ObsidianTaskForestParser:
    """
    Parses Markdown notes in an Obsidian Vault folder and constructs the Task Forest.
    """
    def __init__(self, vault_path: str) -> None:
        self.vault_path = vault_path
        self.nodes: Dict[str, PlantNode] = {}

    def scan_vault(self) -> Dict[str, PlantNode]:
        """
        Scans all .md files in vault_path for YAML frontmatter with tags 'dnk-task-forest'.
        """
        if not os.path.exists(self.vault_path):
            return self.nodes

        for root_dir, _, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith(".md"):
                    filepath = os.path.join(root_dir, file)
                    node = self._parse_file(filepath)
                    if node:
                        self.nodes[node.id] = node

        # Link children to parents
        for node in list(self.nodes.values()):
            if node.parent_id and node.parent_id in self.nodes:
                parent = self.nodes[node.parent_id]
                if node not in parent.children:
                    parent.children.append(node)

        return self.nodes

    def _parse_file(self, filepath: str) -> Optional[PlantNode]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
            mrh_match = re.match(r"^# --- DNK-MRH-HEADER ---\s*\n(.*?)\n# --- END DNK-MRH-HEADER ---\s*\n", content, re.DOTALL)
            
            fm_text = ""
            if fm_match:
                fm_text = fm_match.group(1)
            elif mrh_match:
                fm_text = mrh_match.group(1)
                # Strip leading '# ' if present
                fm_text = "\n".join([line.lstrip("# ").strip() for line in fm_text.splitlines()])
            else:
                return None

            node_id = self._extract_yaml_val(fm_text, "id") or os.path.splitext(os.path.basename(filepath))[0]
            title = self._extract_yaml_val(fm_text, "title") or node_id
            plant_scale = self._extract_yaml_val(fm_text, "plant_scale") or "flower"
            status = self._extract_yaml_val(fm_text, "status") or "pending"
            progress_str = self._extract_yaml_val(fm_text, "progress") or "0"
            parent_id = self._extract_yaml_val(fm_text, "parent_id")
            project_id = self._extract_yaml_val(fm_text, "project_id")
            assigned_agent = self._extract_yaml_val(fm_text, "assigned_agent")

            return PlantNode(
                id=node_id,
                title=title,
                plant_scale=plant_scale,
                status=status,
                progress=float(progress_str) if progress_str.replace(".", "", 1).isdigit() else 0.0,
                parent_id=parent_id,
                project_id=project_id,
                assigned_agent=assigned_agent,
                filepath=filepath,
            )
        except Exception:
            return None

    def _extract_yaml_val(self, fm_text: str, key: str) -> Optional[str]:
        match = re.search(r"^" + re.escape(key) + r":\s*[\"']?(.*?)[\"']?\s*$", fm_text, re.MULTILINE)
        return match.group(1).strip() if match else None
