#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/visual_canvas_control_runner.py"
# purpose: "CLI runner for Visual Control Panel on Canvas: TaskDNA DAG generation, real-time stage updates, and bidirectional Obsidian Canvas synchronization."
# canonical_source: true
# alters_files: ["docs/notes/017_Swarm_TaskDNA_Control_Panel.canvas"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import argparse
import json
import sys
import time
from pathlib import Path

# SSOT Root Execution Path
HUB_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HUB_ROOT))

from core.orchestrator.visual_canvas_control import (
    VisualCanvasControlEngine,
    DEFAULT_CONTROL_PANEL_PATH,
)
from core.task_forest.forest import TaskForest


def main():
    parser = argparse.ArgumentParser(
        description="Visual Control Panel on Canvas Runner (TaskDNA & Swarm Orchestration)"
    )
    parser.add_argument("--goal", type=str, help="High-level goal to decompose and render onto Canvas")
    parser.add_argument("--task-dna", type=str, help="Path to TaskDNA JSON file to import into Canvas")
    parser.add_argument("--canvas-path", "--output", "-o", dest="canvas_path", type=str, default=str(DEFAULT_CONTROL_PANEL_PATH), help="Target .canvas path")
    parser.add_argument("--update-node", type=str, help="Node ID to transition stage")
    parser.add_argument("--stage", type=str, help="New stage (backlog, in_progress, review, done, blocked)")
    parser.add_argument("--notes", type=str, help="Optional progress notes to append to the node")
    parser.add_argument("--sync-forest", action="store_true", help="Sync TaskForest nodes directly to Obsidian Canvas")
    parser.add_argument("--status", action="store_true", help="Display telemetry from current Canvas control panel")
    parser.add_argument("--poll-triggers", action="store_true", help="Scan canvas cards for interactive triggers (- [x] Run Tests, - [x] Dispatch Worker) and execute them")
    parser.add_argument("--watch", action="store_true", help="Run continuous reactive watchdog daemon tracking canvas triggers")
    parser.add_argument("--interval", type=float, default=2.0, help="Watchdog poll interval in seconds (default: 2.0)")
    parser.add_argument("--export-react-flow", type=str, help="Export active Canvas to React Flow JSON format")
    parser.add_argument("--import-react-flow", type=str, help="Import React Flow JSON into Obsidian Canvas format")

    args = parser.parse_args()
    engine = VisualCanvasControlEngine(default_output_path=args.canvas_path)

    # 1. Update Node Stage
    if args.update_node:
        if not args.stage:
            print("[ERROR] --stage is required when using --update-node", file=sys.stderr)
            sys.exit(1)
        res = engine.update_node_stage(
            node_id=args.update_node,
            new_stage=args.stage,
            canvas_path=args.canvas_path,
            notes=args.notes,
        )
        print(f"[SUCCESS] Node '{args.update_node}' transitioned to '{args.stage}'.")
        print(f"Telemetery: {res['completed_tasks']}/{res['total_tasks']} completed. Canvas: {res['canvas_path']}")
        return

    # 2. Sync TaskForest
    if args.sync_forest:
        forest = TaskForest()
        canvas_file = engine.sync_forest_to_canvas(forest=forest, canvas_path=args.canvas_path)
        print(f"[SUCCESS] Synchronized TaskForest to Obsidian Canvas: {canvas_file}")
        return

    # 3. Import TaskDNA File
    if args.task_dna:
        p = Path(args.task_dna)
        if not p.exists():
            print(f"[ERROR] TaskDNA file not found: {p}", file=sys.stderr)
            sys.exit(1)
        dna_data = json.loads(p.read_text(encoding="utf-8"))
        res = engine.generate_canvas_from_task_dna(dna_data, canvas_path=args.canvas_path)
        print(f"[SUCCESS] Rendered TaskDNA to Canvas: {args.canvas_path} ({len(res['nodes'])} nodes, {len(res['edges'])} edges)")
        return

    # 4. Decompose Goal & Render
    if args.goal:
        # High-velocity deterministic decomposition
        subtasks = [
            {
                "id": "slice_1_arch",
                "title": "Architecture & Interface Contract Specification",
                "stage": "in_progress",
                "assigned_agent": "antigravity_mentor",
                "risk_level": "low",
                "tool_budget": "<= 25 tools",
                "dependencies": [],
                "rationale": "Define contracts, data models, and topological layout algorithms.",
            },
            {
                "id": "slice_2_impl",
                "title": f"Implementation of Core Modules for '{args.goal[:40]}'",
                "stage": "backlog",
                "assigned_agent": "gerych_builder",
                "risk_level": "medium",
                "tool_budget": "<= 25 tools",
                "dependencies": ["slice_1_arch"],
                "rationale": "Construct modules, converters, and CLI runners.",
            },
            {
                "id": "slice_3_audit",
                "title": "Adversarial Quality Gate & Green Test Pass",
                "stage": "backlog",
                "assigned_agent": "gerych_auditor",
                "risk_level": "low",
                "tool_budget": "<= 25 tools",
                "dependencies": ["slice_2_impl"],
                "rationale": "Fail-closed adversarial security and regression tests.",
            },
        ]
        dna_data = {
            "goal": args.goal,
            "status": "active",
            "dag_tree": subtasks,
        }
        res = engine.generate_canvas_from_task_dna(dna_data, canvas_path=args.canvas_path)
        print(f"[SUCCESS] Decomposed Goal & Generated Visual Control Panel: {args.canvas_path}")
        print(f"Nodes: {len(res['nodes'])}, Edges: {len(res['edges'])}")
        return

    # 5. Status / Telemetry
    if args.status:
        p = Path(args.canvas_path)
        if not p.exists():
            print(f"[INFO] Control Panel canvas does not exist yet at: {p}")
            return
        data = json.loads(p.read_text(encoding="utf-8"))
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        hud = next((n for n in nodes if n.get("id") == "control_panel_hud"), None)
        print(f"=== Visual Control Panel Telemetry ({p}) ===")
        print(f"Total Nodes: {len(nodes)}, Edges: {len(edges)}")
        if hud:
            print("\n--- HUD Summary ---")
            print(hud.get("text", "").strip())
        return

    # 6. Single-shot Poll Triggers (Vector 3 Interactive Trigger)
    if args.poll_triggers:
        actions = engine.poll_and_execute_canvas_triggers(canvas_path=args.canvas_path)
        if actions:
            print(f"⚡ [TRIGGER DETECTED] Executed {len(actions)} actions from Obsidian Canvas:")
            for a in actions:
                print(f"   • Node '{a['node_id']}': Action '{a['action']}' -> {a.get('status')}")
        else:
            print("[INFO] No interactive triggers detected in Canvas.")
        return

    # 7. Continuous Reactive Watchdog Daemon (Vector 3 Watchdog)
    if args.watch:
        print(f"👁️  Starting Reactive Canvas Watchdog on: {args.canvas_path}")
        print(f"⏱️  Interval: {args.interval}s | Press Ctrl+C to terminate.")
        try:
            while True:
                actions = engine.poll_and_execute_canvas_triggers(canvas_path=args.canvas_path)
                if actions:
                    for a in actions:
                        print(f"⚡ [TRIGGER FIRED] Node '{a['node_id']}': {a['action']} -> {a.get('status')}")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n🛑 Watchdog stopped by user.")
            return

    # 8. Export to React Flow
    if args.export_react_flow:
        p = Path(args.canvas_path)
        if not p.exists():
            print(f"[ERROR] Canvas file does not exist: {p}", file=sys.stderr)
            sys.exit(1)
        canvas_doc = json.loads(p.read_text(encoding="utf-8"))
        rf_doc = engine.canvas_to_react_flow(canvas_doc)
        out_p = Path(args.export_react_flow)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(rf_doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[SUCCESS] Exported Obsidian Canvas to React Flow JSON: {out_p}")
        print(f"Nodes: {len(rf_doc['nodes'])}, Edges: {len(rf_doc['edges'])}")
        return

    # 9. Import from React Flow
    if args.import_react_flow:
        in_p = Path(args.import_react_flow)
        if not in_p.exists():
            print(f"[ERROR] React Flow file does not exist: {in_p}", file=sys.stderr)
            sys.exit(1)
        rf_doc = json.loads(in_p.read_text(encoding="utf-8"))
        c_doc = engine.react_flow_to_canvas(rf_doc)
        out_p = Path(args.canvas_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(c_doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[SUCCESS] Imported React Flow JSON into Obsidian Canvas: {out_p}")
        print(f"Nodes: {len(c_doc['nodes'])}, Edges: {len(c_doc['edges'])}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
