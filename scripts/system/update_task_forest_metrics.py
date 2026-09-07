#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/update_task_forest_metrics.py"
# purpose: "Autonomous DAG and Metric Calculator for Obsidian Task Forest (docs/notes/tasks_and_ideas)"
# canonical_source: true
# alters_files: ["docs/notes/tasks_and_ideas/000_DNK_TASK_AND_IDEAS_INDEX.md"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "Gerych Prime & DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None


HUB_ROOT = Path(__file__).resolve().parent.parent.parent
TASKS_DIR = HUB_ROOT / "docs" / "notes" / "tasks_and_ideas"
INDEX_FILE = TASKS_DIR / "000_DNK_TASK_AND_IDEAS_INDEX.md"
IGNORED_DIRS = {"archive", "trash", ".obsidian", "templates"}


def parse_node_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Parse YAML frontmatter and MRH header from a task forest markdown note."""
    if file_path.name.startswith("000_"):
        return None

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    # Match YAML frontmatter between ^--- and ^---
    fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL | re.MULTILINE)
    data: Dict[str, Any] = {}

    if fm_match and yaml:
        try:
            parsed = yaml.safe_load(fm_match.group(1))
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            data = {}

    # Fallback regex parsing if yaml is unavailable or failed
    if not data:
        for line in content.splitlines()[:50]:
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key in ["node_id", "title", "node_type", "stage", "status", "progress", "assigned_agent", "blocked_by"]:
                    data[key] = val

    node_id = data.get("node_id") or file_path.stem
    title = data.get("title") or file_path.stem.replace("-", " ").replace("_", " ").title()

    # Determine node type from frontmatter or filename prefix
    node_type = str(data.get("node_type", "")).lower()
    if not node_type or node_type == "none":
        if file_path.name.startswith("epic-"):
            node_type = "epic"
        elif file_path.name.startswith("idea-"):
            node_type = "idea"
        elif file_path.name.startswith("gate-"):
            node_type = "gate"
        else:
            node_type = "task"

    # Progress parsing
    progress_val = data.get("progress", 0.0)
    try:
        if isinstance(progress_val, str):
            progress_val = float(progress_val.replace("%", "").strip())
        else:
            progress_val = float(progress_val)
    except Exception:
        progress_val = 0.0

    stage = str(data.get("stage", "ready")).lower()
    status = str(data.get("status", "draft")).lower()

    if status == "completed":
        progress_val = 100.0

    # Assigned agent
    assigned = data.get("assigned_agent") or data.get("assignee") or data.get("assigned") or "unassigned"

    # Priority
    priority = str(data.get("priority", "medium")).lower()

    # Target module
    target_module = str(data.get("target_module", "core"))

    # Is blocked
    is_blocked = data.get("is_blocked", False)
    if isinstance(is_blocked, str):
        is_blocked = is_blocked.lower() in ("true", "1", "yes")
    elif not isinstance(is_blocked, bool):
        is_blocked = False

    # Dependencies / Blocked By
    blocked_by = data.get("blocked_by") or data.get("dependencies") or []
    if isinstance(blocked_by, str):
        if blocked_by.lower() in ["none", "null", "[]", ""]:
            blocked_by = []
        else:
            blocked_by = [b.strip() for b in blocked_by.split(",") if b.strip()]

    # Rel path for indexing
    rel_path = file_path.relative_to(TASKS_DIR)

    return {
        "node_id": node_id,
        "title": title,
        "node_type": node_type,
        "stage": stage,
        "status": status,
        "progress": progress_val,
        "assigned": assigned,
        "priority": priority,
        "target_module": target_module,
        "is_blocked": is_blocked,
        "blocked_by": blocked_by,
        "rel_path": str(rel_path),
        "file_name": file_path.name,
    }


def collect_nodes() -> List[Dict[str, Any]]:
    """Scan TASKS_DIR recursively and collect all active nodes."""
    nodes = []
    if not TASKS_DIR.exists():
        return nodes

    for fpath in TASKS_DIR.rglob("*.md"):
        if any(ignored in fpath.parts for ignored in IGNORED_DIRS):
            continue
        parsed = parse_node_file(fpath)
        if parsed:
            nodes.append(parsed)

    return nodes


def calculate_metrics(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate DAG metrics, epics, and distributions."""
    total = len(nodes)
    if total == 0:
        return {
            "total": 0,
            "avg_progress": 0.0,
            "completion_rate": 0.0,
            "by_type": {},
            "by_status": {},
            "by_priority": {},
            "by_module": {},
            "by_agent": {},
            "epics_summary": [],
            "blocked_nodes": [],
        }

    by_type: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}
    by_module: Dict[str, int] = {}
    by_agent: Dict[str, int] = {}
    blocked_nodes: List[Dict[str, Any]] = []
    epics_summary: List[Dict[str, Any]] = []

    total_progress = 0.0

    for n in nodes:
        ntype = n["node_type"]
        by_type[ntype] = by_type.get(ntype, 0) + 1

        nstatus = n["status"]
        by_status[nstatus] = by_status.get(nstatus, 0) + 1

        priority = n.get("priority", "medium")
        by_priority[priority] = by_priority.get(priority, 0) + 1

        module = n.get("target_module", "core")
        by_module[module] = by_module.get(module, 0) + 1

        agent = n["assigned"]
        by_agent[agent] = by_agent.get(agent, 0) + 1

        total_progress += n["progress"]

        if ntype == "epic":
            epics_summary.append({
                "node_id": n["node_id"],
                "title": n["title"],
                "status": n["status"],
                "progress": n["progress"],
                "assigned": n["assigned"],
                "module": module,
            })

        if n["status"] == "blocked" or n.get("is_blocked") or (n["blocked_by"] and n["status"] != "completed"):
            blocked_nodes.append(n)

    avg_progress = round(total_progress / total, 1)
    completed_count = by_status.get("completed", 0)
    completion_rate = round(completed_count / total * 100, 1) if total else 0.0

    return {
        "total": total,
        "avg_progress": avg_progress,
        "completion_rate": completion_rate,
        "by_type": by_type,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_module": by_module,
        "by_agent": by_agent,
        "epics_summary": epics_summary,
        "blocked_nodes": blocked_nodes,
    }


def render_markdown_index(nodes: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
    """Render 000_DNK_TASK_AND_IDEAS_INDEX.md content."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Order types
    type_icons = {
        "idea": "💡 Idea",
        "epic": "🏆 Epic",
        "task": "📋 Task",
        "gate": "🛡️ Gate",
    }

    type_counts = metrics["by_type"]
    status_counts = metrics["by_status"]

    md = []
    md.append("<!-- --- DNK-MRH-HEADER ---")
    md.append('mrh_id: "docs/notes/tasks_and_ideas/000_DNK_TASK_AND_IDEAS_INDEX.md"')
    md.append('purpose: "DNK OS Master Node-Based Tasks & Ideas Index & DAG Status"')
    md.append("canonical_source: true")
    md.append("alters_files: []")
    md.append("triggers_tasks: []")
    md.append('status: "Active"')
    md.append('version: "2.0.0"')
    md.append(f'updated_at: "{datetime.now(timezone.utc).strftime("%Y-%m-%d")}"')
    md.append('author: "Gerych Prime & DNK-e.com Maksym"')
    md.append("--- END DNK-MRH-HEADER -->\n")

    md.append("# 🌐 DNK OS Node-Based TASK & Ideas System Index\n")
    md.append(f"> Last synced: `{now_str}` | Total Nodes: **{metrics['total']}** | Progress: **{metrics['avg_progress']}%** | Completion Rate: **{metrics.get('completion_rate', 0.0)}%**\n")

    md.append("## 📊 System Overview")
    md.append(f"- 💡 **Ideas**: {type_counts.get('idea', 0)}")
    md.append(f"- 🏆 **Epics**: {type_counts.get('epic', 0)}")
    md.append(f"- 📋 **Tasks**: {type_counts.get('task', 0)}")
    md.append(f"- 🛡️ **Quality Gates**: {type_counts.get('gate', 0)}")
    md.append(
        f"- 🔒 **Blocked**: {len(metrics['blocked_nodes'])} | "
        f"🔓 **Ready**: {status_counts.get('ready', 0)} | "
        f"⚡ **In Progress**: {status_counts.get('in_progress', 0)} | "
        f"📝 **Draft**: {status_counts.get('draft', 0)} | "
        f"✅ **Completed**: {status_counts.get('completed', 0)}"
    )

    if metrics.get("epics_summary"):
        md.append("\n## 🏆 Active Epics & Objectives")
        md.append("| Epic ID | Title | Module | Progress | Status | Assigned Agent |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for ep in metrics["epics_summary"]:
            md.append(
                f"| [[{ep['node_id']}]] | {ep['title']} | `{ep['module']}` | {ep['progress']}% | `{ep['status']}` | `{ep['assigned']}` |"
            )

    if metrics["blocked_nodes"]:
        md.append("## ⚠️ Bottlenecks & Blocked Nodes")
        md.append("| Node | Blocked By | Assigned Agent |")
        md.append("| :--- | :--- | :--- |")
        for bn in metrics["blocked_nodes"]:
            blockers = ", ".join(f"[[{b}]]" for b in bn["blocked_by"]) if bn["blocked_by"] else "`flagged blocked`"
            md.append(f"| [[{bn['node_id']}]] | {blockers} | `{bn['assigned']}` |")
        md.append("")

    md.append("## 🗺️ Master Node Registry")
    md.append("| ID | Type | Title | Stage | Status | Progress | Assigned | Blocked By |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    # Sort nodes: Epics first, then Gates, then Ideas, then Tasks, then alphabetically by node_id
    type_priority = {"epic": 1, "gate": 2, "idea": 3, "task": 4}
    sorted_nodes = sorted(nodes, key=lambda x: (type_priority.get(x["node_type"], 5), x["node_id"]))

    for n in sorted_nodes:
        icon = type_icons.get(n["node_type"], "📋 " + n["node_type"].title())
        blockers = ", ".join(f"[[{b}]]" for b in n["blocked_by"]) if n["blocked_by"] else "None"
        title_escaped = n["title"].replace("|", "\\|")
        md.append(
            f"| [[{n['node_id']}]] | {icon} | **{title_escaped}** | "
            f"`{n['stage']}` | `{n['status']}` | {n['progress']:.1f}% | "
            f"`{n['assigned']}` | {blockers} |"
        )

    md.append("\n## 🔗 Active Swarm Workload Distribution")
    for agent, count in sorted(metrics["by_agent"].items(), key=lambda x: -x[1]):
        md.append(f"- **{agent}**: {count} node(s)")

    md.append("")
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Update Task Forest DAG metrics and index.")
    parser.add_argument("--dry-run", action="store_true", help="Print metrics without writing file")
    parser.add_argument("--json", action="store_true", help="Output JSON metrics to stdout")
    parser.add_argument("--verify", action="store_true", help="Verify index file is up to date (exit 1 if out of sync)")
    args = parser.parse_args()

    nodes = collect_nodes()
    metrics = calculate_metrics(nodes)

    if args.json:
        print(json.dumps(metrics, indent=2))
        return

    content = render_markdown_index(nodes, metrics)

    if args.dry_run:
        print(f"[DRY-RUN] Collected {metrics['total']} nodes across subfolders:")
        for t, c in metrics["by_type"].items():
            print(f"  - {t}: {c}")
        print(f"Average Progress: {metrics['avg_progress']}%")
        print(f"Completion Rate: {metrics.get('completion_rate', 0.0)}%")
        print(f"Blocked Nodes: {len(metrics['blocked_nodes'])}")
        return

    if args.verify:
        if not INDEX_FILE.exists():
            print(f"❌ Verification failed: {INDEX_FILE} does not exist.")
            sys.exit(1)
        existing = INDEX_FILE.read_text(encoding="utf-8")
        norm_existing = re.sub(r"> Last synced: `[^`]+`", "> Last synced: `NORM`", existing)
        norm_generated = re.sub(r"> Last synced: `[^`]+`", "> Last synced: `NORM`", content)
        if norm_existing.strip() != norm_generated.strip():
            print(f"❌ Verification failed: {INDEX_FILE} is out of sync with task files on disk.")
            sys.exit(1)
        print(f"✅ Verification passed: {INDEX_FILE} is synchronized.")
        return

    INDEX_FILE.write_text(content, encoding="utf-8")
    print(f"✅ Successfully updated {INDEX_FILE} ({metrics['total']} nodes indexed, {metrics['avg_progress']}% avg progress, {metrics['completion_rate']}% completed).")


if __name__ == "__main__":
    main()
