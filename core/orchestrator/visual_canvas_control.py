# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/visual_canvas_control.py"
# purpose: "Visual Control Panel for Swarm Orchestration: TaskDNA DAG to Obsidian Canvas (.canvas) JSON graph synchronization, real-time stage transitions, HUD telemetry card, and bidirectional TaskForest sync."
# canonical_source: true
# alters_files: ["docs/notes/017_Swarm_TaskDNA_Control_Panel.canvas"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import re
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Set

# Canvas v1.0 standard palette mapping:
# 1 = Red (Blocked / Error)
# 2 = Orange (Warning / High Risk)
# 3 = Yellow (Backlog / Planned)
# 4 = Green (Done / Verified)
# 5 = Cyan / Blue (In Progress / Active Worker)
# 6 = Purple (Review / Audit Gate)
STAGE_CANVAS_COLORS = {
    "backlog": "3",
    "planned": "3",
    "pending": "3",
    "in_progress": "5",
    "running": "5",
    "review": "6",
    "audit": "6",
    "done": "4",
    "completed": "4",
    "blocked": "1",
    "failed": "1",
}

STAGE_STATUS_ICONS = {
    "backlog": "⏳ [BACKLOG]",
    "planned": "📋 [PLANNED]",
    "pending": "⏳ [PENDING]",
    "in_progress": "⚡ [IN_PROGRESS]",
    "running": "⚡ [RUNNING]",
    "review": "🔍 [REVIEW / AUDIT]",
    "audit": "🛡️ [AUDIT_GATE]",
    "done": "✅ [DONE]",
    "completed": "✅ [COMPLETED]",
    "blocked": "🚫 [BLOCKED]",
    "failed": "❌ [FAILED]",
}

AGENT_BADGES = {
    "gerych_prime": "👑 Gerych Prime",
    "antigravity_mentor": "🧠 Antigravity (Architect)",
    "gerych_builder": "🛠️ Gerych Builder",
    "gerych_auditor": "🛡️ Gerych Auditor",
    "dnk_dev_fullstack": "⚡ DNK Dev Fullstack",
    "dnk_video_ai_creator": "🎬 DNK Video AI Creator",
    "dnk_shopify": "🛍️ DNK Shopify Engine",
    "dnk_security_guard": "🔒 DNK Security Guard",
    "herich_librarian": "📚 Herich Librarian",
}
REVERSE_AGENT_BADGES = {v: k for k, v in AGENT_BADGES.items()}

# Swarm Worker Canvas & UI Color Palette (SSOT for Live Swarm HUD)
SWARM_WORKER_COLORS = {
    "gerych_prime": {"canvas_color": "6", "hex": "#8B5CF6", "badge": "👑 Gerych Prime"},
    "antigravity_mentor": {"canvas_color": "6", "hex": "#A78BFA", "badge": "🧠 Antigravity (Architect)"},
    "gerych_builder": {"canvas_color": "5", "hex": "#3B82F6", "badge": "🛠️ Gerych Builder"},
    "dnk_dev_fullstack": {"canvas_color": "5", "hex": "#06B6D4", "badge": "⚡ DNK Dev Fullstack"},
    "dnk_shopify": {"canvas_color": "4", "hex": "#10B981", "badge": "🛍️ DNK Shopify Engine"},
    "dnk_video_ai_creator": {"canvas_color": "2", "hex": "#F59E0B", "badge": "🎬 DNK Video AI Creator"},
    "gerych_auditor": {"canvas_color": "1", "hex": "#EF4444", "badge": "🛡️ Gerych Auditor"},
    "dnk_security_guard": {"canvas_color": "1", "hex": "#DC2626", "badge": "🔒 DNK Security Guard"},
    "herich_librarian": {"canvas_color": "3", "hex": "#EAB308", "badge": "📚 Herich Librarian"},
}

DEFAULT_CONTROL_PANEL_PATH = Path("docs/notes/017_Swarm_TaskDNA_Control_Panel.canvas")
HUB_ROOT = Path(__file__).resolve().parent.parent.parent


class VisualCanvasControlEngine:
    """
    Visual Control Panel Engine for Obsidian Canvas (.canvas) and TaskDNA DAGs.
    Provides topological graph layout, HUD summary node synthesis, stage color-coding,
    real-time node state transitions, and bidirectional TaskForest synchronization.
    """

    def __init__(self, default_output_path: Optional[Union[str, Path]] = None):
        self.output_path = Path(default_output_path or DEFAULT_CONTROL_PANEL_PATH)

    def render_progress_bar(self, completed: int, total: int, length: int = 10) -> str:
        """Renders ASCII visual progress bar: e.g. [██████░░░░] 60%."""
        if total <= 0:
            return "[░░░░░░░░░░] 0%"
        pct = min(1.0, max(0.0, completed / total))
        filled = int(round(length * pct))
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}] {int(pct * 100)}%"

    def compute_topological_layout(
        self, tasks: List[Dict[str, Any]], base_x: float = 380.0, base_y: float = 80.0
    ) -> Tuple[Dict[str, Tuple[float, float]], Dict[str, int]]:
        """
        Computes spatial coordinates (x, y) and topological depths for DAG task nodes.
        Places nodes in horizontal depth tiers with vertical spacing.
        """
        dep_map: Dict[str, List[str]] = {}
        for t in tasks:
            tid = str(t.get("id") or t.get("task_id", ""))
            dep_map[tid] = [str(d) for d in t.get("dependencies", [])]

        depth_map: Dict[str, int] = {}

        def get_depth(node_id: str, visited: Optional[Set[str]] = None) -> int:
            if visited is None:
                visited = set()
            if node_id in depth_map:
                return depth_map[node_id]
            if node_id in visited:
                return 0
            visited.add(node_id)
            deps = dep_map.get(node_id, [])
            if not deps:
                depth_map[node_id] = 0
                return 0
            max_d = max((get_depth(d, visited.copy()) for d in deps if d in dep_map), default=-1)
            depth_map[node_id] = max_d + 1
            return depth_map[node_id]

        for tid in dep_map:
            get_depth(tid)

        coords_map: Dict[str, Tuple[float, float]] = {}
        tier_counts: Dict[int, int] = {}

        for t in tasks:
            tid = str(t.get("id") or t.get("task_id", ""))
            depth = depth_map.get(tid, 0)
            row = tier_counts.get(depth, 0)
            tier_counts[depth] = row + 1

            # Node card dimensions: width=360, height=220
            # Horizontal column spacing = 420, vertical row spacing = 260
            x = base_x + (depth * 420.0)
            y = base_y + (row * 260.0)
            coords_map[tid] = (x, y)

        return coords_map, depth_map

    def build_node_markdown(self, task: Dict[str, Any]) -> str:
        """Builds structured Obsidian Markdown content for a TaskDNA node."""
        title = task.get("title", "Untitled Task")
        stage = str(task.get("stage", "backlog")).lower()
        agent = str(task.get("assigned_agent") or task.get("agent") or "unassigned")
        agent_badge = AGENT_BADGES.get(agent, f"🤖 `{agent}`")
        risk = str(task.get("risk_level", "medium")).capitalize()
        status_icon = STAGE_STATUS_ICONS.get(stage, f"[{stage.upper()}]")
        deps = task.get("dependencies", [])
        deps_str = ", ".join(f"`{d}`" for d in deps) if deps else "*None (Root)*"
        mase_budget = task.get("tool_budget", "<= 25 tools")

        desc = task.get("description") or task.get("rationale") or ""
        checklist = task.get("checklist") or [
            "Specification & contract validation",
            "Targeted code / template execution",
            "Verification & quality gate pass",
        ]

        lines = [
            f"### {title}",
            "",
            f"**Status**: {status_icon} | **Risk**: `{risk}`",
            f"**Worker**: {agent_badge}",
            f"**MASE Budget**: `{mase_budget}`",
            f"**Dependencies**: {deps_str}",
            "",
        ]

        if desc:
            lines.append(f"> {desc.strip()}")
            lines.append("")

        lines.append("#### Subtask Execution:")
        for idx, item in enumerate(checklist):
            checked = "x" if stage in ("done", "completed") else " "
            lines.append(f"- [{checked}] {item}")

        return "\n".join(lines)

    def build_hud_markdown(
        self,
        goal: str,
        total_tasks: int,
        completed_tasks: int,
        in_progress_tasks: int,
        active_agents: List[str],
        updated_at: Optional[str] = None,
        tools_executed: Optional[int] = None,
    ) -> str:
        """Builds Master HUD Summary card content for Obsidian Canvas."""
        progress_bar = self.render_progress_bar(completed_tasks, total_tasks)
        pct = int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)
        timestamp = updated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        gate_status = "🟢 100% PASS" if pct == 100 else ("🔵 RUNNING" if in_progress_tasks > 0 else "🟡 READY")
        agent_pills = ", ".join(f"`{a}`" for a in set(active_agents)) if active_agents else "*None*"
        tools_line = f"\n- **Tools Executed**: `{tools_executed}` calls" if tools_executed is not None else ""

        return f"""# 🎛️ DNK OS Swarm Control Panel
**Goal**: {goal}
___
### 📊 Live Telemetry
- **Progress**: {progress_bar}
- **Milestones**: **{completed_tasks}** / **{total_tasks}** completed
- **In-Flight Tasks**: **{in_progress_tasks}** active{tools_line}
- **Quality Gate**: {gate_status} (Zero-Waste MASE <= 25 tools)
- **Active Swarm**: {agent_pills}
- **Last Sync**: `{timestamp}`
___
*Interactive Obsidian Canvas • Double-click cards to inspect details.*
"""

    def generate_canvas_from_task_dna(
        self,
        dna_data: Dict[str, Any],
        canvas_path: Optional[Union[str, Path]] = None,
        include_groups: bool = True,
    ) -> Dict[str, Any]:
        """
        Converts TaskDNA DAG into an interactive Obsidian Canvas v1.0 JSON format
        and saves it to disk at canvas_path.
        """
        target_path = Path(canvas_path or self.output_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        goal = dna_data.get("goal", "DNK OS Swarm Autonomous Execution")
        raw_tasks = dna_data.get("dag_tree") or dna_data.get("tasks") or []
        if not raw_tasks:
            raw_tasks = [
                {
                    "id": "task_1",
                    "title": goal,
                    "stage": "backlog",
                    "assigned_agent": "gerych_prime",
                    "dependencies": [],
                    "risk_level": "low",
                }
            ]

        coords_map, depth_map = self.compute_topological_layout(raw_tasks, base_x=420.0, base_y=80.0)

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        total_tasks = len(raw_tasks)
        completed_count = 0
        in_progress_count = 0
        active_agents: List[str] = []

        task_map = {str(t.get("id") or t.get("task_id", "")): t for t in raw_tasks}

        # 1. Create Task Nodes
        for task in raw_tasks:
            tid = str(task.get("id") or task.get("task_id", ""))
            stage = str(task.get("stage", "backlog")).lower()
            agent = task.get("assigned_agent") or task.get("agent")
            if agent:
                active_agents.append(str(agent))

            if stage in ("done", "completed"):
                completed_count += 1
            elif stage in ("in_progress", "running", "review", "audit"):
                in_progress_count += 1

            x, y = coords_map.get(tid, (420.0, 80.0))
            color = STAGE_CANVAS_COLORS.get(stage, "3")
            text_content = self.build_node_markdown(task)

            node_obj = {
                "id": tid,
                "x": int(x),
                "y": int(y),
                "width": 360,
                "height": 220,
                "type": "text",
                "text": text_content,
                "color": color,
            }
            nodes.append(node_obj)

            # Build dependency edges based on dependency resolution status
            for dep in task.get("dependencies", []):
                dep_id = str(dep)
                from_task = task_map.get(dep_id)
                from_stage = str(from_task.get("stage", "backlog")).lower() if from_task else "backlog"
                edge_color = "4" if from_stage in ("done", "completed") else ("5" if from_stage in ("in_progress", "running") else "3")
                edge_obj = {
                    "id": f"edge_{dep_id}_to_{tid}",
                    "fromNode": dep_id,
                    "fromSide": "right",
                    "toNode": tid,
                    "toSide": "left",
                    "label": "depends_on",
                    "color": edge_color,
                }
                edges.append(edge_obj)

        # 2. Create Master HUD Summary Node
        hud_text = self.build_hud_markdown(
            goal=goal,
            total_tasks=total_tasks,
            completed_tasks=completed_count,
            in_progress_tasks=in_progress_count,
            active_agents=active_agents,
        )
        hud_color = "4" if completed_count == total_tasks else ("5" if in_progress_count > 0 else "6")
        hud_node = {
            "id": "control_panel_hud",
            "x": 40,
            "y": 80,
            "width": 340,
            "height": 380,
            "type": "text",
            "text": hud_text,
            "color": hud_color,
        }
        nodes.insert(0, hud_node)

        # 3. Create Canvas Stage Groups (Optional Visual Sectioning)
        if include_groups and depth_map:
            max_depth = max(depth_map.values()) if depth_map else 0
            for d in range(max_depth + 1):
                tier_tasks = [t for t in raw_tasks if depth_map.get(str(t.get("id") or t.get("task_id")), 0) == d]
                if not tier_tasks:
                    continue
                group_x = int(400 + (d * 420.0))
                group_y = 40
                group_w = 400
                group_h = max(300, len(tier_tasks) * 270 + 80)
                group_node = {
                    "id": f"group_phase_{d + 1}",
                    "x": group_x,
                    "y": group_y,
                    "width": group_w,
                    "height": group_h,
                    "type": "group",
                    "label": f"Phase {d + 1}: Topological Layer {d + 1}",
                    "color": "6" if d == 0 else "5",
                }
                nodes.append(group_node)

        canvas_doc = {
            "nodes": nodes,
            "edges": edges,
        }

        # Write safely to target file
        target_path.write_text(json.dumps(canvas_doc, indent=2, ensure_ascii=False), encoding="utf-8")
        return canvas_doc

    def update_node_stage(
        self,
        node_id: str,
        new_stage: str,
        canvas_path: Optional[Union[str, Path]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates an existing node's execution stage, status icon, color, and updates
        the master HUD telemetry card in real time.
        """
        target_path = Path(canvas_path or self.output_path)
        if not target_path.exists():
            raise FileNotFoundError(f"Canvas file not found: {target_path}")

        canvas_doc = json.loads(target_path.read_text(encoding="utf-8"))
        nodes = canvas_doc.get("nodes", [])
        norm_stage = new_stage.lower()
        new_color = STAGE_CANVAS_COLORS.get(norm_stage, "3")

        node_found = False
        completed_count = 0
        in_progress_count = 0
        total_tasks = 0
        active_agents: List[str] = []
        hud_node: Optional[Dict[str, Any]] = None
        extracted_goal = "DNK OS Swarm Pipeline"

        for n in nodes:
            nid = str(n.get("id"))
            if nid == "control_panel_hud":
                hud_node = n
                text = n.get("text", "")
                m = re.search(r"\*\*Goal\*\*:\s*([^\n_]+)", text)
                if m:
                    extracted_goal = m.group(1).strip()
                continue
            if n.get("type") == "group":
                continue

            total_tasks += 1
            if nid == node_id:
                node_found = True
                n["color"] = new_color
                orig_text = n.get("text", "")

                # Update Status line in markdown text
                new_status_icon = STAGE_STATUS_ICONS.get(norm_stage, f"[{norm_stage.upper()}]")
                updated_text = re.sub(
                    r"\*\*Status\*\*:\s*[^|\n]+",
                    f"**Status**: {new_status_icon} ",
                    orig_text,
                )

                # Update Checkboxes if DONE
                if norm_stage in ("done", "completed"):
                    updated_text = re.sub(r"- \[ \]", "- [x]", updated_text)
                elif norm_stage in ("backlog", "planned", "pending"):
                    updated_text = re.sub(r"- \[x\]", "- [ ]", updated_text)

                if notes:
                    updated_text += f"\n\n*Note ({datetime.now().strftime('%H:%M:%S')}):* {notes}"

                n["text"] = updated_text

            # Check agent and stage for telemetry
            cur_color = n.get("color")
            if cur_color == "4":
                completed_count += 1
            elif cur_color in ("5", "6"):
                in_progress_count += 1

            # Extract agent from text
            m_agent = re.search(r"\*\*Worker\*\*:\s*([^\n]+)", n.get("text", ""))
            if m_agent:
                worker_str = m_agent.group(1).strip()
                active_agents.append(worker_str)

        if not node_found:
            raise KeyError(f"Node '{node_id}' not found in canvas: {target_path}")

        # Update Master HUD Node
        if hud_node is not None:
            hud_node["text"] = self.build_hud_markdown(
                goal=extracted_goal,
                total_tasks=total_tasks,
                completed_tasks=completed_count,
                in_progress_tasks=in_progress_count,
                active_agents=active_agents,
            )
            hud_node["color"] = "4" if completed_count == total_tasks else ("5" if in_progress_count > 0 else "6")

        # Update connected edges colors
        for edge in canvas_doc.get("edges", []):
            if edge.get("fromNode") == node_id:
                edge["color"] = "4" if norm_stage in ("done", "completed") else ("5" if norm_stage == "in_progress" else "3")

        target_path.write_text(json.dumps(canvas_doc, indent=2, ensure_ascii=False), encoding="utf-8")
        return {
            "status": "success",
            "node_id": node_id,
            "new_stage": norm_stage,
            "completed_tasks": completed_count,
            "total_tasks": total_tasks,
            "canvas_path": str(target_path),
        }

    def sync_forest_to_canvas(
        self,
        forest: Any,
        canvas_path: Optional[Union[str, Path]] = None,
        goal: str = "DNK OS Task Forest Orchestration",
    ) -> Path:
        """
        Exports all nodes and edges from a TaskForest instance directly to Obsidian Canvas.
        """
        target_path = Path(canvas_path or self.output_path)
        tasks = []
        for n in forest.nodes.values():
            stage_str = n.stage.value if hasattr(n.stage, "value") else str(n.stage)
            priority_str = n.priority.value if hasattr(n.priority, "value") else str(n.priority)
            tasks.append({
                "id": n.id,
                "title": n.title,
                "description": n.description,
                "stage": stage_str,
                "assigned_agent": n.assigned_agent,
                "risk_level": priority_str,
                "dependencies": list(n.dependencies),
            })

        dna_data = {
            "goal": goal,
            "dag_tree": tasks,
        }
        self.generate_canvas_from_task_dna(dna_data, canvas_path=target_path)
        return target_path

    def sync_canvas_to_forest(
        self,
        canvas_path: Optional[Union[str, Path]] = None,
        forest: Any = None,
    ) -> List[str]:
        """
        Parses Obsidian Canvas file and updates TaskForest nodes with spatial coordinates,
        user-completed checklists, and stage transitions.
        """
        target_path = Path(canvas_path or self.output_path)
        if not target_path.exists():
            return []

        canvas_doc = json.loads(target_path.read_text(encoding="utf-8"))
        updated_node_ids: List[str] = []

        for node_data in canvas_doc.get("nodes", []):
            nid = str(node_data.get("id"))
            if nid in ("control_panel_hud",) or node_data.get("type") == "group":
                continue

            if forest is not None and nid in forest.nodes:
                f_node = forest.nodes[nid]
                # Sync spatial position
                f_node.position = {"x": float(node_data.get("x", 0)), "y": float(node_data.get("y", 0))}

                # Sync color / stage
                color = node_data.get("color")
                if color == "4":
                    from core.task_forest.models import ExecutionStage
                    f_node.stage = ExecutionStage.DONE
                elif color in ("5", "6"):
                    from core.task_forest.models import ExecutionStage
                    f_node.stage = ExecutionStage.IN_PROGRESS

                # Check if all checkboxes in text are checked
                text = node_data.get("text", "")
                if "- [ ]" not in text and "- [x]" in text:
                    from core.task_forest.models import ExecutionStage
                    f_node.stage = ExecutionStage.DONE

                f_node.updated_at = datetime.now()
                updated_node_ids.append(nid)

        if forest is not None and updated_node_ids:
            forest._save()

        return updated_node_ids

    def record_live_tool_execution(
        self,
        tool_name: str,
        tool_input: Optional[Dict[str, Any]] = None,
        status: str = "success",
        result_text: str = "",
        canvas_path: Optional[Union[str, Path]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Invoked by hermes_post_tool_hook.py on each tool completion.
        Updates tool count, node stages (in_progress on edit, done on passing tests, failed on errors),
        and refreshes the HUD in the active Obsidian Canvas.
        """
        target_path = Path(canvas_path or os.environ.get("DNK_ACTIVE_CANVAS_PATH") or self.output_path)
        if not target_path.exists():
            return None

        try:
            canvas_doc = json.loads(target_path.read_text(encoding="utf-8"))
        except Exception:
            return None

        nodes = canvas_doc.get("nodes", [])
        hud_node = None
        extracted_goal = "DNK OS Swarm Pipeline"
        total_tasks = 0
        completed_count = 0
        in_progress_count = 0
        active_agents: List[str] = []
        tools_count = 0

        for n in nodes:
            nid = str(n.get("id"))
            if nid == "control_panel_hud":
                hud_node = n
                text = n.get("text", "")
                m_goal = re.search(r"\*\*Goal\*\*:\s*([^\n_]+)", text)
                if m_goal:
                    extracted_goal = m_goal.group(1).strip()
                m_tools = re.search(r"\*\*Tools Executed\*\*:\s*`?(\d+)`?", text)
                if m_tools:
                    tools_count = int(m_tools.group(1))
                continue

            if n.get("type") == "group":
                continue

            total_tasks += 1
            cur_color = n.get("color")
            if cur_color == "4":
                completed_count += 1
            elif cur_color in ("5", "6"):
                in_progress_count += 1

            m_agent = re.search(r"\*\*Worker\*\*:\s*([^\n]+)", n.get("text", ""))
            if m_agent:
                active_agents.append(m_agent.group(1).strip())

        if hud_node is None:
            return None

        tools_count += 1
        tool_input_data = tool_input or {}

        # Determine state updates based on tool action
        node_to_update = None
        new_stage = None
        note_text = None

        if tool_name in ("write_file", "patch"):
            path_arg = tool_input_data.get("path", "")
            for n in nodes:
                if n.get("type") == "group" or n.get("id") == "control_panel_hud":
                    continue
                if path_arg and path_arg in n.get("text", ""):
                    node_to_update = n
                    break
            if not node_to_update:
                for n in nodes:
                    if n.get("type") == "group" or n.get("id") == "control_panel_hud":
                        continue
                    if n.get("color") in ("3", "5"):
                        node_to_update = n
                        break
            if node_to_update:
                new_stage = "in_progress"
                note_text = f"Modifying {path_arg} via {tool_name}"

        elif tool_name == "terminal":
            cmd = tool_input_data.get("command", "")
            is_test = any(k in cmd for k in ("pytest", "verify_all.sh", "npm test", "vitest", "jest"))
            if is_test:
                is_failed = (status == "error") or ("FAILED" in result_text and "passed" not in result_text) or ("exit code: 1" in result_text) or ("exit code: 2" in result_text)
                for n in nodes:
                    if n.get("type") == "group" or n.get("id") == "control_panel_hud":
                        continue
                    if n.get("color") in ("5", "6", "3"):
                        node_to_update = n
                        break
                if node_to_update:
                    if is_failed:
                        new_stage = "failed"
                        note_text = f"Test failed: {cmd[:40]}"
                    else:
                        new_stage = "done"
                        note_text = f"Test passed: {cmd[:40]}"

        # Apply node update if identified
        if node_to_update and new_stage:
            node_id = str(node_to_update.get("id"))
            try:
                res = self.update_node_stage(
                    node_id=node_id,
                    new_stage=new_stage,
                    canvas_path=target_path,
                    notes=note_text,
                )
                # Ensure tools_executed count is synced in HUD
                refreshed = json.loads(target_path.read_text(encoding="utf-8"))
                for rn in refreshed.get("nodes", []):
                    if rn.get("id") == "control_panel_hud":
                        hud_text = rn.get("text", "")
                        if "Tools Executed" in hud_text:
                            rn["text"] = re.sub(r"\*\*Tools Executed\*\*:\s*`?\d+`?\s*calls?", f"**Tools Executed**: `{tools_count}` calls", hud_text)
                        else:
                            rn["text"] = hud_text.replace("- **In-Flight Tasks**:", f"- **Tools Executed**: `{tools_count}` calls\n- **In-Flight Tasks**:")
                        break
                target_path.write_text(json.dumps(refreshed, indent=2, ensure_ascii=False), encoding="utf-8")
                res["tools_executed"] = tools_count
                return res
            except Exception:
                pass

        # If no specific node transitioned, still update HUD tools count
        hud_node["text"] = self.build_hud_markdown(
            goal=extracted_goal,
            total_tasks=total_tasks,
            completed_tasks=completed_count,
            in_progress_tasks=in_progress_count,
            active_agents=active_agents,
            tools_executed=tools_count,
        )
        target_path.write_text(json.dumps(canvas_doc, indent=2, ensure_ascii=False), encoding="utf-8")
        return {
            "status": "updated_hud",
            "tools_executed": tools_count,
            "canvas_path": str(target_path),
        }

    def poll_and_execute_canvas_triggers(
        self,
        canvas_path: Optional[Union[str, Path]] = None,
        auto_execute: bool = True,
        test_command: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Two-Way Interactive Canvas -> Swarm Trigger Engine (Vector 3).
        Detects checked action boxes in cards:
          - [x] Run Tests / Verify All -> executes verification suite, updates HUD and card.
          - [x] Dispatch Worker / Run Worker -> invokes dnk_swarm_dispatch for card's assigned worker.
        """
        target_path = Path(canvas_path or os.environ.get("DNK_ACTIVE_CANVAS_PATH") or self.output_path)
        if not target_path.exists():
            return []

        try:
            canvas_doc = json.loads(target_path.read_text(encoding="utf-8"))
        except Exception:
            return []

        executed_actions: List[Dict[str, Any]] = []
        doc_modified = False

        for node in canvas_doc.get("nodes", []):
            if node.get("type") == "group" or node.get("id") == "control_panel_hud":
                continue

            text = node.get("text", "")
            node_id = str(node.get("id"))

            # 1. Check for interactive Test Trigger: "- [x] Run Tests" or "- [x] Verify All"
            test_patterns = [
                r"- \[x\]\s+(?:Run Tests|Verify All|Run verification)",
                r"- \[x\]\s+Execute Test Suite",
            ]
            triggered_test = any(re.search(pat, text, re.IGNORECASE) for pat in test_patterns)

            if triggered_test:
                action_info = {
                    "node_id": node_id,
                    "action": "run_tests",
                    "status": "triggered"
                }
                if auto_execute:
                    import subprocess
                    cmd = test_command or ["./.venv/bin/pytest", "-q", "--tb=short", "tests/verification/test_visual_canvas_control.py"]
                    p = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd=str(HUB_ROOT)
                    )
                    test_success = (p.returncode == 0)
                    action_info["exit_code"] = str(p.returncode)
                    action_info["output"] = p.stdout[-300:] if p.stdout else p.stderr[-300:]
                    status_badge = "✅ [Tests Passed]" if test_success else "❌ [Tests Failed]"
                    new_text = re.sub(
                        r"- \[x\]\s+(?:Run Tests|Verify All|Run verification|Execute Test Suite)",
                        f"- [ ] Run Tests\n  > {status_badge} ({datetime.now().strftime('%H:%M:%S')})",
                        text,
                        flags=re.IGNORECASE
                    )
                    node["text"] = new_text
                    if test_success:
                        node["color"] = "4"
                    else:
                        node["color"] = "1"
                    doc_modified = True
                executed_actions.append(action_info)

            # 2. Check for Worker Dispatch Trigger: "- [x] Dispatch Worker" or "- [x] Run Worker"
            worker_patterns = [
                r"- \[x\]\s+(?:Dispatch Worker|Run Worker|Execute Task)",
            ]
            triggered_worker = any(re.search(pat, text, re.IGNORECASE) for pat in worker_patterns)

            if triggered_worker:
                m_agent = re.search(r"\*\*Worker\*\*:\s*([^\n]+)", text)
                raw_agent = m_agent.group(1).strip() if m_agent else "dnk_dev_fullstack"
                assigned_agent = REVERSE_AGENT_BADGES.get(raw_agent, raw_agent)
                action_info = {
                    "node_id": node_id,
                    "action": "dispatch_worker",
                    "agent": assigned_agent,
                    "status": "triggered"
                }
                if auto_execute:
                    try:
                        from core.hermes_agent.tools.dnk_swarm_tool import dnk_swarm_dispatch
                        disp_res = dnk_swarm_dispatch(
                            agent=assigned_agent,
                            task_description=f"Executed from Obsidian Canvas card {node_id}: {text[:100]}",
                            workspace_id="ws-alpha-001"
                        )
                        action_info["dispatch_result"] = disp_res
                    except Exception as e:
                        action_info["dispatch_result"] = str(e)

                    new_text = re.sub(
                        r"- \[x\]\s+(?:Dispatch Worker|Run Worker|Execute Task)",
                        f"- [ ] Dispatch Worker\n  > 🚀 [Dispatched to `{assigned_agent}`] ({datetime.now().strftime('%H:%M:%S')})",
                        text,
                        flags=re.IGNORECASE
                    )
                    node["text"] = new_text
                    node["color"] = "5"
                    doc_modified = True
                executed_actions.append(action_info)

        if doc_modified:
            target_path.write_text(json.dumps(canvas_doc, indent=2, ensure_ascii=False), encoding="utf-8")

        return executed_actions

    def canvas_to_react_flow(self, canvas_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        SSOT Bridge (Vector 4): Converts Obsidian Canvas document into React Flow schema.
        Maps spatial coordinates, node dimensions, markdown content, and edge connections.
        """
        rf_nodes = []
        rf_edges = []

        for node in canvas_doc.get("nodes", []):
            nid = str(node.get("id"))
            ntype = node.get("type", "text")
            pos = {
                "x": float(node.get("x", 0.0)),
                "y": float(node.get("y", 0.0))
            }
            dim = {
                "width": float(node.get("width", 380.0)),
                "height": float(node.get("height", 240.0))
            }

            text = node.get("text", "")
            title_m = re.search(r"##\s*([^\n]+)", text) or re.search(r"#\s*([^\n]+)", text)
            title = title_m.group(1).strip() if title_m else nid

            m_agent = re.search(r"\*\*Worker\*\*:\s*([^\n]+)", text)
            raw_agent = m_agent.group(1).strip().strip("`") if m_agent else "gerych_builder"
            agent = REVERSE_AGENT_BADGES.get(raw_agent, raw_agent)

            data = {
                "id": nid,
                "label": title,
                "title": title,
                "content": text,
                "color": node.get("color", "3"),
                "worker": agent,
                "obsidian_type": ntype,
            }

            rf_nodes.append({
                "id": nid,
                "type": "group_node" if ntype == "group" else "task_node",
                "position": pos,
                "dimensions": dim,
                "data": data
            })

        for edge in canvas_doc.get("edges", []):
            eid = str(edge.get("id"))
            rf_edges.append({
                "id": eid,
                "source": str(edge.get("fromNode")),
                "target": str(edge.get("toNode")),
                "sourceHandle": edge.get("fromSide", "right"),
                "targetHandle": edge.get("toSide", "left"),
                "animated": True,
            })

        return {
            "nodes": rf_nodes,
            "edges": rf_edges,
            "viewport": {"x": 0.0, "y": 0.0, "zoom": 1.0}
        }

    def react_flow_to_canvas(self, rf_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        SSOT Bridge (Vector 4): Converts React Flow document into Obsidian Canvas schema.
        Maps spatial coordinates, dimensions, metadata, and handles.
        """
        canvas_nodes = []
        canvas_edges = []

        for node in rf_doc.get("nodes", []):
            nid = str(node.get("id"))
            pos = node.get("position", {})
            dim = node.get("dimensions", {})
            data = node.get("data", {})
            is_group = (node.get("type") == "group_node" or data.get("obsidian_type") == "group")

            c_node: Dict[str, Any] = {
                "id": nid,
                "type": "group" if is_group else "text",
                "x": float(pos.get("x", 0.0)),
                "y": float(pos.get("y", 0.0)),
                "width": float(dim.get("width", 380.0)),
                "height": float(dim.get("height", 240.0)),
            }

            if is_group:
                c_node["label"] = data.get("label", nid)
            else:
                c_node["text"] = data.get("content") or f"## {data.get('title', nid)}\n{data.get('label', '')}"
                c_node["color"] = str(data.get("color", "3"))

            canvas_nodes.append(c_node)

        for edge in rf_doc.get("edges", []):
            eid = str(edge.get("id"))
            canvas_edges.append({
                "id": eid,
                "fromNode": str(edge.get("source")),
                "toNode": str(edge.get("target")),
                "fromSide": edge.get("sourceHandle", "right"),
                "toSide": edge.get("targetHandle", "left"),
            })

        return {
            "nodes": canvas_nodes,
            "edges": canvas_edges
        }

