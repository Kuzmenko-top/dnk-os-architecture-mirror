# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_canvas_api/obsidian_sync_engine.py"
# purpose: "Bidirectional Synchronization Engine between Obsidian Vault Markdown Notes and DAG Task Graph"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

from services.dnk_node_tasks.graph_engine import NodeTaskGraphEngine
from services.dnk_node_tasks.models import (
    DependencyEdge,
    EdgeRelation,
    ExecutionStage,
    NodeItem,
    NodePosition,
    NodeStatus,
    NodeTaskGraph,
    NodeType,
)
from services.dnk_node_tasks.persistence import NodeTaskPersistenceManager

logger = logging.getLogger("dnk.canvas.obsidian_sync")


class ObsidianSyncEngine:
    """
    Engine for bidirectional synchronization between Obsidian Vault markdown notes
    and the DAG Node Task graph. Supports parsing YAML Frontmatter, [[wikilinks]],
    acceptance criteria checkboxes, and edge reconciliation.
    """

    @staticmethod
    def _extract_frontmatter_and_body(content: str) -> Tuple[Dict[str, Any], str]:
        """
        Extracts YAML frontmatter and the remaining Markdown body from a note.
        Ignores leading DNK-MRH headers (comment or HTML format).
        """
        lines = content.splitlines()
        clean_lines = []
        in_mrh = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# --- DNK-MRH-HEADER ---") or stripped.startswith("<!-- --- DNK-MRH-HEADER ---"):
                in_mrh = True
                continue
            if in_mrh:
                if stripped.endswith("--- END DNK-MRH-HEADER ---") or stripped.endswith("--- END DNK-MRH-HEADER -->"):
                    in_mrh = False
                continue
            clean_lines.append(line)

        # Look for YAML frontmatter block delimited by '---'
        start_idx = None
        end_idx = None

        for idx, line in enumerate(clean_lines):
            if line.strip() == "---":
                if start_idx is None:
                    start_idx = idx
                elif end_idx is None:
                    end_idx = idx
                    break

        if start_idx is not None and end_idx is not None and end_idx > start_idx:
            yaml_content = "\n".join(clean_lines[start_idx + 1 : end_idx])
            body_content = "\n".join(clean_lines[end_idx + 1 :])
            try:
                data = yaml.safe_load(yaml_content) or {}
                if isinstance(data, dict):
                    return data, body_content
            except Exception as e:
                logger.warning(
                    "Soup Resilient Fallback: Failed to parse standard YAML frontmatter: %s. Attempting heuristic recovery.",
                    e,
                )
                # Soup Data Hygiene: resilient line-by-line key-value recovery
                recovered: Dict[str, Any] = {}
                for yline in yaml_content.splitlines():
                    kv_match = re.match(r"^([a-zA-Z0-9_-]+)\s*:\s*(.*)$", yline.strip())
                    if kv_match:
                        k, v = kv_match.group(1), kv_match.group(2).strip()
                        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                            v = v[1:-1]
                        recovered[k] = v
                if recovered:
                    return recovered, body_content

        return {}, "\n".join(clean_lines)

    @staticmethod
    def normalize_wikilinks(raw_links: Any) -> List[str]:
        """
        Normalizes Obsidian wikilinks and strings into pure target node IDs.
        Handles:
        - "[[node-id]]" -> "node-id"
        - "[[node-id|Alias]]" -> "node-id"
        - "node-id" -> "node-id"
        - List of nested values or comma-separated lists.
        """
        result: List[str] = []
        if raw_links is None:
            return result

        if isinstance(raw_links, (list, tuple, set)):
            for item in raw_links:
                result.extend(ObsidianSyncEngine.normalize_wikilinks(item))
            # Deduplicate preserving order
            seen: Set[str] = set()
            return [x for x in result if not (x in seen or seen.add(x))]

        val = str(raw_links).strip()
        if not val or val.lower() == "none":
            return result

        # Check for [[wikilink]] patterns
        wiki_matches = re.findall(r"\[\[(.*?)\]\]", val)
        if wiki_matches:
            for match in wiki_matches:
                cleaned = match.split("|")[0].split("#")[0].strip()
                if cleaned:
                    result.append(cleaned)
        else:
            # Handle comma-separated IDs
            parts = [p.strip() for p in val.split(",") if p.strip()]
            for p in parts:
                cleaned = p.strip("[]'\" ")
                if cleaned and cleaned.lower() != "none":
                    result.append(cleaned)

        seen = set()
        return [x for x in result if not (x in seen or seen.add(x))]

    @classmethod
    def parse_markdown_note(cls, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parses an Obsidian markdown note:
        - Extracts YAML Frontmatter (id, title, stage, status, type, priority, project_id, assigned_agent, dependencies)
        - Normalizes [[wikilinks]] in dependencies
        - Extracts acceptance criteria checkboxes from markdown body (- [ ] ..., - [x] ...)
        - Extracts description and canvas coordinates if present
        Returns None for index notes or unparseable files.
        """
        file_path = Path(file_path)
        if not file_path.is_file() or file_path.suffix.lower() != ".md":
            return None

        # Ignore master index and readme notes
        name = file_path.name
        if name.startswith("000_") or name.lower() in ("readme.md", "index.md"):
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error("Error reading file %s: %s", file_path, e)
            return None

        fm, body = cls._extract_frontmatter_and_body(content)

        # 1. Node ID
        node_id = fm.get("id") or fm.get("node_id") or file_path.stem
        node_id = str(node_id).strip()
        if not node_id:
            return None

        # 2. Title
        title = fm.get("title")
        if not title:
            # Look for H1 in body
            h1_match = re.search(r"^#\s+(.+)$", body, flags=re.MULTILINE)
            if h1_match:
                title = h1_match.group(1).strip()
            else:
                title = node_id.replace("-", " ").replace("_", " ").title()
        title = str(title).strip()

        # 3. Node Type
        raw_type = fm.get("node_type") or fm.get("type") or "task"
        try:
            node_type = NodeType(str(raw_type).strip().lower())
        except ValueError:
            node_type = NodeType.TASK

        # 4. Stage
        raw_stage = fm.get("stage") or "ready"
        try:
            stage = ExecutionStage(str(raw_stage).strip().lower())
        except ValueError:
            stage = ExecutionStage.READY

        # 5. Status
        raw_status = fm.get("status") or "ready"
        try:
            status = NodeStatus(str(raw_status).strip().lower())
        except ValueError:
            status = NodeStatus.READY

        # 6. Priority & Progress
        priority = str(fm.get("priority", "medium")).strip().lower()
        if priority not in ("low", "medium", "high", "critical"):
            priority = "medium"

        try:
            progress = float(fm.get("progress", 0.0))
            progress = max(0.0, min(100.0, progress))
        except (ValueError, TypeError):
            progress = 0.0

        # 7. Project & Agent & Subsystems
        project_id = str(fm.get("project_id", "dnk_core")).strip()
        assigned_agent = fm.get("assigned_agent")
        if assigned_agent:
            assigned_agent = str(assigned_agent).strip()
            if assigned_agent.lower() in ("none", "null", ""):
                assigned_agent = None

        target_module = fm.get("target_module")
        if target_module:
            target_module = str(target_module).strip()
            if target_module.lower() in ("none", "null", ""):
                target_module = "core"
        else:
            target_module = "core"

        # 8. Tags
        tags_raw = fm.get("tags", [])
        if isinstance(tags_raw, str):
            tags = [t.strip().lstrip("#") for t in tags_raw.split(",") if t.strip()]
        elif isinstance(tags_raw, list):
            tags = [str(t).strip().lstrip("#") for t in tags_raw if str(t).strip()]
        else:
            tags = []

        # 9. Acceptance Criteria (parsed from markdown checkboxes)
        checkbox_matches = re.findall(r"^-\s*\[([ xX])\]\s*(.+)$", body, flags=re.MULTILINE)
        acceptance_criteria: List[str] = [c[1].strip() for c in checkbox_matches]

        # If acceptance_criteria also specified in frontmatter, merge
        fm_ac = fm.get("acceptance_criteria")
        if fm_ac and isinstance(fm_ac, list):
            for item in fm_ac:
                text_item = str(item).strip()
                if text_item and text_item not in acceptance_criteria:
                    acceptance_criteria.append(text_item)

        # 10. Dependencies (Frontmatter + Markdown Upstream Dependencies section)
        dependencies: List[str] = []
        raw_deps = fm.get("dependencies") or fm.get("depends_on") or fm.get("upstream_dependencies")
        if raw_deps:
            dependencies.extend(cls.normalize_wikilinks(raw_deps))

        # Scan body for upstream dependency wikilinks
        # e.g.: - **depends_on** from [[task-node-system]]
        body_upstream_deps = re.findall(r"from\s+\[\[(.*?)\]\]", body, flags=re.IGNORECASE)
        for dep in body_upstream_deps:
            cleaned = dep.split("|")[0].split("#")[0].strip()
            if cleaned and cleaned not in dependencies:
                dependencies.append(cleaned)

        # 11. Description extraction
        description = ""
        desc_match = re.search(r"###?\s+(?:Description|Опис)\s*\n+(.*?)(?=\n###?|\Z)", body, flags=re.DOTALL | re.IGNORECASE)
        if desc_match:
            description = desc_match.group(1).strip()
        else:
            desc_fm = fm.get("description")
            if desc_fm:
                description = str(desc_fm).strip()

        # 12. Position extraction
        pos_x = 0.0
        pos_y = 0.0
        pos_fm = fm.get("position")
        if isinstance(pos_fm, dict):
            pos_x = float(pos_fm.get("x", 0.0))
            pos_y = float(pos_fm.get("y", 0.0))
        else:
            pos_match = re.search(r">\s*Node Position on Canvas:\s*`x=([0-9.-]+),\s*y=([0-9.-]+)`", body)
            if pos_match:
                try:
                    pos_x = float(pos_match.group(1))
                    pos_y = float(pos_match.group(2))
                except (ValueError, TypeError):
                    pass

        # 13. Target Files extraction
        target_files: List[str] = []
        tf_fm = fm.get("target_files")
        if isinstance(tf_fm, list):
            target_files = [str(f).strip() for f in tf_fm if str(f).strip()]
        else:
            tf_match = re.search(r"###?\s+Target Module & Files\s*\n+(.*?)(?=\n###?|\Z)", body, flags=re.DOTALL | re.IGNORECASE)
            if tf_match:
                for line in tf_match.group(1).splitlines():
                    f_match = re.search(r"-\s*`([^`]+)`", line)
                    if f_match:
                        target_files.append(f_match.group(1).strip())

        return {
            "id": node_id,
            "title": title,
            "description": description,
            "node_type": node_type,
            "stage": stage,
            "status": status,
            "progress": progress,
            "priority": priority,
            "project_id": project_id,
            "assigned_agent": assigned_agent,
            "target_module": target_module,
            "target_files": target_files,
            "tags": tags,
            "acceptance_criteria": acceptance_criteria,
            "dependencies": dependencies,
            "position": NodePosition(x=pos_x, y=pos_y),
            "file_path": str(file_path),
        }

    @classmethod
    def sync_from_obsidian_vault(
        cls,
        vault_dir: Optional[Path] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Scans obsidian markdown notes, updates or creates graph nodes in NodeTaskPersistenceManager,
        reconciles edge dependencies based on parsed wikilinks, recalculates DAG state, and saves graph.
        """
        manager = NodeTaskPersistenceManager.get_instance()
        target_dir = Path(vault_dir) if vault_dir else manager.obsidian_dir

        if not target_dir.exists():
            return {
                "status": "success",
                "scanned": 0,
                "imported": 0,
                "updated": 0,
                "edges_synced": 0,
                "nodes_synced": 0,
                "message": f"Vault directory does not exist: {target_dir}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        graph = manager.load_graph(force_reload=True)
        ignored_patterns = {"archive", "trash", ".obsidian", "templates"}
        md_files = sorted([
            f for f in target_dir.rglob("*.md")
            if not any(part.lower() in ignored_patterns for part in f.parts)
        ])

        scanned = 0
        imported = 0
        updated = 0
        edges_synced = 0
        node_dependencies_map: Dict[str, List[str]] = {}

        now_iso = datetime.now(timezone.utc).isoformat()

        for fpath in md_files:
            parsed = cls.parse_markdown_note(fpath)
            if not parsed:
                continue

            # Project filtering if specified
            if project_id and parsed["project_id"] != project_id:
                continue

            scanned += 1
            node_id = parsed["id"]
            node_dependencies_map[node_id] = parsed["dependencies"]

            if node_id in graph.nodes:
                # Update existing node fields from Obsidian
                node = graph.nodes[node_id]
                node.title = parsed["title"]
                if parsed["description"]:
                    node.description = parsed["description"]
                node.node_type = parsed["node_type"]
                node.stage = parsed["stage"]
                node.status = parsed["status"]
                node.progress = parsed["progress"]
                node.priority = parsed["priority"]
                if parsed["assigned_agent"]:
                    node.assigned_agent = parsed["assigned_agent"]
                if parsed["target_module"]:
                    node.target_module = parsed["target_module"]
                if parsed["target_files"]:
                    node.target_files = parsed["target_files"]
                if parsed["acceptance_criteria"]:
                    # Soup Criteria Merge: union while preserving existing items
                    existing_set = set(node.acceptance_criteria or [])
                    merged_criteria = list(node.acceptance_criteria or [])
                    for crit in parsed["acceptance_criteria"]:
                        if crit not in existing_set:
                            merged_criteria.append(crit)
                            existing_set.add(crit)
                    node.acceptance_criteria = merged_criteria
                if parsed["tags"]:
                    node.tags = parsed["tags"]
                if parsed["position"].x != 0.0 or parsed["position"].y != 0.0:
                    node.position = parsed["position"]
                node.updated_at = now_iso
                updated += 1
            else:
                # Import new node from Obsidian note
                new_node = NodeItem(
                    id=node_id,
                    title=parsed["title"],
                    description=parsed["description"],
                    node_type=parsed["node_type"],
                    stage=parsed["stage"],
                    status=parsed["status"],
                    progress=parsed["progress"],
                    priority=parsed["priority"],
                    project_id=parsed["project_id"],
                    assigned_agent=parsed["assigned_agent"] or "gerych_builder",
                    target_module=parsed["target_module"] or "core",
                    target_files=parsed["target_files"],
                    acceptance_criteria=parsed["acceptance_criteria"],
                    tags=parsed["tags"],
                    position=parsed["position"],
                    created_at=now_iso,
                    updated_at=now_iso,
                )
                graph.nodes[node_id] = new_node
                imported += 1

        # Reconcile dependency edges from parsed wikilinks
        # Format: prerequisite (source) -> dependent task (target)
        for target_id, prereqs in node_dependencies_map.items():
            for source_id in prereqs:
                if source_id == target_id:
                    continue

                # Soup Anti-Dangling Wikilink Guard:
                # If prerequisite does not exist in graph, auto-stub an idea node
                if source_id not in graph.nodes:
                    target_node = graph.nodes.get(target_id)
                    stub_node = NodeItem(
                        id=source_id,
                        title=f"Unresolved Prerequisite: {source_id}",
                        description=f"Auto-generated stub placeholder from dangling Obsidian wikilink in [[{target_id}]].",
                        node_type=NodeType.IDEA,
                        stage=ExecutionStage.IDEATION,
                        status=NodeStatus.BACKLOG,
                        progress=0.0,
                        priority="low",
                        project_id=target_node.project_id if target_node else "dnk_core",
                        assigned_agent="herich_librarian",
                        target_module="core",
                        tags=["unresolved_prerequisite", "obsidian_stub"],
                        position=NodePosition(
                            x=target_node.position.x - 280.0 if target_node else 0.0,
                            y=target_node.position.y if target_node else 0.0,
                        ),
                        created_at=now_iso,
                        updated_at=now_iso,
                    )
                    graph.nodes[source_id] = stub_node
                    imported += 1
                    logger.info("Soup Anti-Dangling Guard: created stub node %s for wikilink in %s", source_id, target_id)

                # Check if edge already exists
                exists = any(
                    e.source == source_id and e.target == target_id and e.relation == EdgeRelation.DEPENDS_ON
                    for e in graph.edges
                )
                if not exists:
                    # Prevent cycle creation
                    has_cycle, _ = NodeTaskGraphEngine.detect_cycle_with_new_edge(
                        graph.edges, source_id, target_id, EdgeRelation.DEPENDS_ON
                    )
                    if not has_cycle:
                        edge_id = f"edge-{source_id}-{target_id}"
                        new_edge = DependencyEdge(
                            id=edge_id,
                            source=source_id,
                            target=target_id,
                            relation=EdgeRelation.DEPENDS_ON,
                            description="Synced from Obsidian wikilinks",
                        )
                        graph.edges.append(new_edge)
                        edges_synced += 1

        # Recalculate DAG dynamic dependencies (is_blocked, blocked_by)
        NodeTaskGraphEngine.recalculate_graph_dependencies(graph)

        # Persist updated graph
        manager.save_graph(graph)

        return {
            "status": "success",
            "scanned": scanned,
            "imported": imported,
            "updated": updated,
            "edges_synced": edges_synced,
            "nodes_synced": imported + updated,
            "total_graph_nodes": len(graph.nodes),
            "timestamp": now_iso,
        }

    @classmethod
    def sync_bidirectional(
        cls,
        vault_dir: Optional[Path] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full 2-way cycle:
        1. Ingests all Markdown updates & new notes from Obsidian into DAG graph.
        2. Exports updated DAG graph back to Obsidian to ensure Markdown notes stay in sync.
        """
        manager = NodeTaskPersistenceManager.get_instance()
        if vault_dir:
            manager.obsidian_dir = Path(vault_dir)

        # 1. Sync from Obsidian -> Graph
        from_obsidian = cls.sync_from_obsidian_vault(vault_dir=vault_dir, project_id=project_id)

        # 2. Export Graph -> Obsidian
        to_obsidian = manager.sync_to_obsidian()

        return {
            "status": "success",
            "scanned": from_obsidian["scanned"],
            "imported": from_obsidian["imported"],
            "updated": from_obsidian["updated"],
            "edges_synced": from_obsidian["edges_synced"],
            "nodes_synced": from_obsidian["nodes_synced"],
            "exported": to_obsidian.get("synced_count", 0),
            "obsidian_dir": to_obsidian.get("obsidian_dir", str(vault_dir or manager.obsidian_dir)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
