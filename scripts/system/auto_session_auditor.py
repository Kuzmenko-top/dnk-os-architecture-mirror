#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/auto_session_auditor.py"
# purpose: "Autonomous Post-Session Auditor & Distiller: Analyzes Gerych session trajectories from state.db, extracts anti-patterns, and persists self-improving lessons into SCONES memory."
# canonical_source: true
# alters_files: [".scones/session_lessons.json", "docs/audit/sessions/"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import os
import sys
import json
import sqlite3
import datetime
import argparse
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
SCONES_DIR = HUB_ROOT / ".scones"
LESSONS_FILE = SCONES_DIR / "session_lessons.json"
AUDIT_REPORTS_DIR = HUB_ROOT / "docs" / "audit" / "sessions"


def get_agent_db(agent_name: str = "gerych_prime") -> Path:
    """Locates the SQLite state database for the agent."""
    primary = HUB_ROOT / "core" / "orchestrator" / "agents" / agent_name / "state.db"
    if primary.exists():
        return primary
    fallback = Path.home() / ".hermes" / "state.db"
    return fallback


def fetch_session_data(db_path: Path, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Loads session record and full message trajectory from state.db."""
    if not db_path.exists():
        return None

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if session_id:
        cur.execute(
            "SELECT id, model, started_at, ended_at, title FROM sessions WHERE id = ? OR id LIKE ?",
            (session_id, f"%{session_id}%")
        )
    else:
        cur.execute(
            "SELECT id, model, started_at, ended_at, title FROM sessions ORDER BY started_at DESC LIMIT 1"
        )

    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    sid, model, start_ts, end_ts, title = row

    cur.execute(
        "SELECT id, role, content, tool_name, tool_calls, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC",
        (sid,)
    )
    raw_messages = cur.fetchall()
    conn.close()

    return {
        "session_id": sid,
        "model": model,
        "started_at": start_ts,
        "ended_at": end_ts,
        "title": title or "Untitled Session",
        "messages": raw_messages
    }


def analyze_trajectory(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyzes message trajectory to detect waste, errors, and efficiency."""
    messages = session_data["messages"]
    tool_counts: Dict[str, int] = {}
    failed_calls: List[Dict[str, Any]] = []
    wasted_nav_calls: List[Dict[str, Any]] = []
    total_tool_calls = 0
    user_prompt = ""
    assistant_final = ""

    for mid, role, content, tool_name, tool_calls, ts in messages:
        if role == "user" and not user_prompt:
            user_prompt = content or ""
        elif role == "assistant" and not tool_calls:
            assistant_final = content or ""
        elif role == "assistant" and tool_calls:
            try:
                tcs = json.loads(tool_calls)
            except Exception:
                tcs = []
            for tc in tcs:
                total_tool_calls += 1
                fn = tc.get("function", {})
                name = fn.get("name", "unknown")
                args = fn.get("arguments", "{}")
                tool_counts[name] = tool_counts.get(name, 0) + 1

                # Detect navigation / exploration waste
                if name == "terminal":
                    for cmd in ("pwd", "cd ", "ls -la core/", "ls -la"):
                        if cmd in args and not any(k in args for k in ("pytest", "git", "python", "npm", "tsc")):
                            wasted_nav_calls.append({"id": mid, "tool": name, "args": args})
                            break
                elif name == "read_file" and "error" in args.lower():
                    wasted_nav_calls.append({"id": mid, "tool": name, "args": args})

        elif role == "tool":
            if content and any(err in content for err in ("exit 1", "exit 2", "FileNotFoundError", "error:", "False")):
                failed_calls.append({"tool": tool_name, "preview": content[:150].replace("\n", " ")})

    duration_sec = (session_data["ended_at"] or session_data["started_at"]) - session_data["started_at"]
    if duration_sec < 0:
        duration_sec = 0

    useful_calls = max(total_tool_calls - len(failed_calls) - len(wasted_nav_calls), 0)
    efficiency_pct = round((useful_calls / max(total_tool_calls, 1)) * 100, 1)

    # Distill specific actionable lessons
    lessons: List[Dict[str, str]] = []

    if wasted_nav_calls:
        lessons.append({
            "category": "PATH_HYGIENE",
            "observation": f"Encountered {len(wasted_nav_calls)} exploratory navigation commands (pwd/cd/ls).",
            "rule": "Execution CWD is always $HUB_ROOT. Target files via canonical relative paths (e.g. core/..., apps/web/...). Do not invoke terminal('pwd') or cd."
        })

    for fc in failed_calls:
        if "pytest" in fc.get("preview", ""):
            lessons.append({
                "category": "TEST_EXECUTION",
                "observation": "Global pytest returned error.",
                "rule": "Always invoke pytest directly with venv context (e.g. ./.venv/bin/pytest or ensured PATH)."
            })
            break

    if total_tool_calls <= 25 and not failed_calls:
        lessons.append({
            "category": "ZERO_WASTE_EFFICIENCY",
            "observation": f"Executed cleanly within atomic budget ({total_tool_calls} tool calls).",
            "rule": "Keep single-slice atomic focus: 1 turn = 1 focused slice."
        })

    return {
        "session_id": session_data["session_id"],
        "model": session_data["model"],
        "title": session_data["title"],
        "duration_sec": round(duration_sec, 1),
        "total_messages": len(messages),
        "total_tool_calls": total_tool_calls,
        "tool_breakdown": tool_counts,
        "failed_calls_count": len(failed_calls),
        "failed_calls": failed_calls[:5],
        "wasted_nav_count": len(wasted_nav_calls),
        "efficiency_pct": efficiency_pct,
        "lessons": lessons,
        "user_prompt_preview": user_prompt[:300],
        "assistant_final_preview": assistant_final[:300]
    }


def persist_lessons(lessons: List[Dict[str, str]], session_id: str):
    """Appends distilled lessons to SCONES memory store."""
    SCONES_DIR.mkdir(parents=True, exist_ok=True)
    all_lessons = []
    if LESSONS_FILE.exists():
        try:
            all_lessons = json.loads(LESSONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            all_lessons = []

    existing_rules = {item.get("rule") for item in all_lessons}
    now_iso = datetime.datetime.now().isoformat()

    added = 0
    for l in lessons:
        rule_text = l.get("rule", "")
        if rule_text and rule_text not in existing_rules:
            all_lessons.append({
                "session_id": session_id,
                "created_at": now_iso,
                "category": l.get("category", "GENERAL"),
                "observation": l.get("observation", ""),
                "rule": rule_text
            })
            existing_rules.add(rule_text)
            added += 1

    # Keep only most recent 30 high-impact lessons
    if len(all_lessons) > 30:
        all_lessons = all_lessons[-30:]

    LESSONS_FILE.write_text(json.dumps(all_lessons, indent=2, ensure_ascii=False), encoding="utf-8")
    return added


TASK_CATALOG_FILE = SCONES_DIR / "task_evolution_catalog.json"


def sync_to_l1_memory(agent_name: str = "gerych_prime") -> bool:
    """Hot-syncs the latest 5 high-impact distilled lessons directly into agent's L1 MEMORY.md."""
    if not LESSONS_FILE.exists():
        return False
    try:
        all_lessons = json.loads(LESSONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not all_lessons:
        return False

    recent_lessons = all_lessons[-5:]
    memory_path = HUB_ROOT / "core" / "orchestrator" / "agents" / agent_name / "memories" / "MEMORY.md"
    if not memory_path.exists():
        return False

    try:
        content = memory_path.read_text(encoding="utf-8")
    except Exception:
        return False

    section_header = "## 💡 5. Active Dynamic Lessons (Distilled from Recent Sessions)"
    lessons_lines = [f"- **[{item.get('category', 'GENERAL')}]**: {item.get('rule', '')}" for item in recent_lessons if item.get("rule")]
    new_section = f"{section_header}\n" + "\n".join(lessons_lines) + "\n"

    if section_header in content:
        parts = content.split(section_header)
        prefix = parts[0]
        rest = parts[1]
        suffix = "\n## " + rest.split("\n## ", 1)[1] if "\n## " in rest else ""
        updated_content = prefix.rstrip() + "\n\n" + new_section + suffix.lstrip()
    else:
        updated_content = content.rstrip() + "\n\n" + new_section

    memory_path.write_text(updated_content, encoding="utf-8")
    return True


def normalize_canonical_path(raw_path: str, hub_root: Path = HUB_ROOT) -> Optional[str]:
    """Ensures paths stored in memory/catalogs strictly adhere to DNK relative invariants."""
    raw = str(raw_path).strip()
    if not raw or raw in (".", "./", "..", "/", "~"):
        return None

    # Handle external Obsidian Vault note references
    if "DNK_HUB My Notes" in raw:
        note_sub = raw.split("DNK_HUB My Notes")[-1].lstrip("/\\")
        if note_sub.startswith("DNK_HUB My Notes/"):
            note_sub = note_sub[len("DNK_HUB My Notes/"):]
        return f"vault:{note_sub}" if note_sub else None

    # Handle user-expanded or absolute workstation paths
    if "/Users/" in raw or raw.startswith("~"):
        expanded = os.path.expanduser(raw)
        try:
            p = Path(expanded).resolve()
            if str(p).startswith(str(hub_root.resolve())):
                return str(p.relative_to(hub_root.resolve()))
        except Exception:
            pass

    clean = raw.replace("\\", "/")
    # Extract workspace relative path if it contains canonical roots
    for root_prefix in ("core/", "apps/", "services/", "docs/", "tests/", "scripts/", "packages/", "visual_shell/", "nginx/"):
        if root_prefix in clean:
            extracted = root_prefix + clean.split(root_prefix, 1)[1]
            extracted = extracted.rstrip("/")
            return extracted if extracted else root_prefix.rstrip("/")

    if clean.startswith("obsidian/") and (hub_root / "core" / clean).exists():
        return f"core/{clean}"

    # Clean local relative prefixes (./, ../)
    clean = os.path.normpath(clean)
    while clean.startswith("./"):
        clean = clean[2:]
    if clean.startswith(".."):
        try:
            resolved = (hub_root / clean).resolve()
            if str(resolved).startswith(str(hub_root.resolve())):
                return str(resolved.relative_to(hub_root.resolve()))
        except Exception:
            pass
        base = clean.split("/")[-1]
        return f"external/{base}"

    clean = clean.rstrip("/")
    if not clean or clean in (".", "/", "~"):
        return None

    return clean


def record_task_milestone(session_data: Dict[str, Any], metrics: Dict[str, Any], overwrite: bool = False) -> bool:
    """Records the task implementation milestone with strictly canonical relative paths (preventing catastrophic forgetting)."""
    SCONES_DIR.mkdir(parents=True, exist_ok=True)
    catalog = []
    if TASK_CATALOG_FILE.exists():
        try:
            catalog = json.loads(TASK_CATALOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            catalog = []

    sid = metrics["session_id"]
    existing_idx = next((i for i, item in enumerate(catalog) if item.get("session_id") == sid), None)
    if existing_idx is not None and not overwrite:
        # If existing record has fewer tool calls or empty affected files, allow auto-refresh
        if catalog[existing_idx].get("total_tool_calls", 0) >= metrics["total_tool_calls"] and catalog[existing_idx].get("affected_files"):
            return False

    affected_files = set()
    for _, role, content, tool_name, tool_calls, _ in session_data["messages"]:
        if tool_calls:
            try:
                tcs = json.loads(tool_calls)
                for tc in tcs:
                    fn = tc.get("function", {})
                    args_raw = fn.get("arguments", "{}")
                    try:
                        args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                        for k in ("path", "file_path", "target_file", "file"):
                            if k in args and isinstance(args[k], str):
                                norm = normalize_canonical_path(args[k])
                                if norm:
                                    affected_files.add(norm)
                    except Exception:
                        pass
            except Exception:
                pass

    milestone = {
        "session_id": sid,
        "timestamp": datetime.datetime.now().isoformat(),
        "title": metrics["title"],
        "user_prompt": metrics["user_prompt_preview"],
        "model": metrics["model"],
        "duration_sec": metrics["duration_sec"],
        "total_tool_calls": metrics["total_tool_calls"],
        "affected_files": sorted(list(affected_files))[:25],
        "efficiency_pct": metrics["efficiency_pct"]
    }

    if existing_idx is not None:
        catalog[existing_idx] = milestone
    else:
        catalog.append(milestone)

    TASK_CATALOG_FILE.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def generate_markdown_audit_report(metrics: Dict[str, Any]) -> Path:
    """Generates an enterprise-grade DNK-MRH audit markdown report."""
    AUDIT_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    sid = metrics["session_id"]
    report_path = AUDIT_REPORTS_DIR / f"AUDIT_{sid}.md"

    lessons_md = "\n".join(
        [f"- **[{l['category']}]**: {l['rule']} *(Observed: {l['observation']})*" for l in metrics["lessons"]]
    ) or "None (Clean execution)."

    tool_breakdown_md = "\n".join(
        [f"  - `{k}`: {v}" for k, v in metrics["tool_breakdown"].items()]
    ) or "  - None"

    content = f"""<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/audit/sessions/AUDIT_{sid}.md"
purpose: "Autonomous Post-Session Audit for Session {sid} by Gerych Auditor."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "{datetime.datetime.now().strftime('%Y-%m-%d')}"
author: "DNK-e.com Maksym & Gerych Auditor"
--- END DNK-MRH-HEADER --- -->

# 🛡️ Gerych Auditor: Post-Session Audit Report

- **Session ID**: `{sid}`
- **Task Title**: {metrics['title']}
- **Model**: `{metrics['model']}`
- **Duration**: {metrics['duration_sec']}s
- **Tool Efficiency Score**: **{metrics['efficiency_pct']}%**

---

## 📊 1. Execution Telemetry

| Metric | Value |
|--------|-------|
| **Total Messages** | {metrics['total_messages']} |
| **Total Tool Calls** | {metrics['total_tool_calls']} |
| **Failed / Retry Calls** | {metrics['failed_calls_count']} |
| **Navigation Churn Steps** | {metrics['wasted_nav_count']} |
| **Tool Efficiency** | {metrics['efficiency_pct']}% |

### Tool Call Distribution:
{tool_breakdown_md}

---

## 🧬 2. Distilled Evolutionary Lessons (Saved to SCONES)

{lessons_md}

---

## 🔍 3. Auditor Verdict & Next Steps

{"✅ **PASSED**: Execution completed cleanly within atomic budget." if metrics['efficiency_pct'] >= 70 else "⚠️ **OPTIMIZATION REQUIRED**: Excessive navigation or retries detected. Lessons injected into pre-flight briefing."}
"""

    report_path.write_text(content, encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser(description="DNK OS Autonomous Post-Session Auditor & Distiller")
    parser.add_argument("--latest", action="store_true", help="Audit the most recent session")
    parser.add_argument("--session", "-s", type=str, help="Audit specific session ID")
    parser.add_argument("--agent", "-a", type=str, default="gerych_prime", help="Agent name (default: gerych_prime)")
    parser.add_argument("--force", "-f", action="store_true", help="Force overwrite milestone in catalog")
    parser.add_argument("--json", action="store_true", help="Output raw metrics JSON")

    args = parser.parse_args()

    db_path = get_agent_db(args.agent)
    session_data = fetch_session_data(db_path, args.session)

    if not session_data:
        print(f"ℹ️ No matching session found in {db_path}.")
        return

    metrics = analyze_trajectory(session_data)
    new_lessons = persist_lessons(metrics["lessons"], metrics["session_id"])
    l1_synced = sync_to_l1_memory(args.agent)
    milestone_recorded = record_task_milestone(session_data, metrics, overwrite=args.force)
    report_file = generate_markdown_audit_report(metrics)

    if args.json:
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
        return

    print("\n========================================================")
    print(f"⚔️  GERYCH AUDITOR: POST-SESSION AUDIT COMPLETE")
    print("========================================================")
    print(f"🆔 Session: {metrics['session_id']}")
    print(f"⏱️  Duration: {metrics['duration_sec']}s | Tools: {metrics['total_tool_calls']} calls")
    print(f"📈 Efficiency Score: {metrics['efficiency_pct']}%")
    print(f"💡 Lessons Distilled: {len(metrics['lessons'])} ({new_lessons} new saved to SCONES)")
    print(f"🧠 L1 Memory Sync: {'ACTIVE ✅ (MEMORY.md updated)' if l1_synced else 'SKIPPED'}")
    print(f"🏛️ Task Evolution Catalog: {'RECORDED ✅' if milestone_recorded else 'ALREADY LOGGED'}")
    print(f"📄 Audit Report: {report_file.relative_to(HUB_ROOT)}")
    print("========================================================\n")


if __name__ == "__main__":
    main()
