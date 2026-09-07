#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/repo_map.py"
# purpose: "High-speed zero-waste repository architecture map, symbol resolver, and discovery index for agents."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

HUB_ROOT = Path(__file__).resolve().parent.parent.parent

STRUCTURE_INDEX = {
    "apps": {
        "api": {
            "path": "apps/api",
            "type": "FastAPI Micro-framework Backend",
            "key_files": ["apps/api/main.py", "apps/api/routers", "apps/api/services", "apps/api/middleware"],
            "description": "Core REST and WebSocket API gateway with dynamic router auto-discovery."
        },
        "web": {
            "path": "apps/web",
            "type": "Next.js 14 Web Frontend",
            "key_files": ["apps/web/app/page.tsx", "apps/web/app/layout.tsx", "apps/web/components"],
            "description": "DNK OS Command Center, Analytics Dashboard, and unified UI."
        },
        "visual_shell": {
            "path": "visual_shell/open_design",
            "type": "Open Design Visual Shell & Desktop Daemon",
            "key_files": ["visual_shell/open_design/apps/web", "visual_shell/open_design/apps/daemon"],
            "description": "Visual Shell spatial canvas, asset studio, and folder import engine."
        }
    },
    "services": {
        "dnk_shopify_builder": "E-Commerce Liquid AST & Shopify Vite Bundler (services/dnk_shopify_builder)",
        "dnk_video_ai_creator": "Multi-agent automated video generation pipeline (services/dnk_video_ai_creator)",
        "dnk_obsidian_task_forest": "Obsidian graph task sync & forest visualization (services/dnk_obsidian_task_forest)",
        "dnk_audit_security": "Fail-closed security controls & token hygiene (services/dnk_audit_security)",
    },
    "core": {
        "orchestrator": "Swarm dispatch, Gerych Prime configs & SOULs (core/orchestrator)",
        "security": "Adversarial review engine & probe library (core/security)",
        "scones_memory": "SCONES evolutionary knowledge memory engine (core/scones_memory.py)",
        "task_engine": "TaskDNA evolutionary graph decomposer (core/task_engine.py)",
        "hermes_agent": "Autonomous Hermes subprocess runtime (core/hermes_agent)"
    },
    "scripts": {
        "verify_all": "scripts/verify_all.sh — Master 100% Quality Gate (1350+ tests)",
        "preflight_sync": "scripts/system/preflight_sync.py — Monorepo bidirectional sync & invariant check",
        "secret_scanner": "scripts/system/secret_scanner.py — SSOT Secret scanner & evidence generator",
        "adversarial_gate": "scripts/system/adversarial_gate_runner.py — Fail-closed adversarial gate",
        "generate_evidence": "scripts/system/generate_evidence.py — Automated evidence & 1-Click PR creation"
    }
}

IGNORE_DIRS = {
    ".venv", "venv", "node_modules", ".next", "__pycache__", ".git",
    "dist", "build", ".turbo", ".pytest-cache", ".pytest_cache"
}

TARGET_DIRECTORIES = ["apps", "services", "core", "scripts", "skills"]


def find_symbol(query: str, root: Path = HUB_ROOT) -> List[Dict[str, Any]]:
    """Fast symbol resolver across monorepo source files.
    Matches classes, functions, interfaces, types, and constants.
    """
    rg_bin = shutil.which("rg") or "/opt/homebrew/bin/rg"
    results: List[Dict[str, Any]] = []

    pattern = rf"\b(class|def|async\s+def|interface|type|const)\s+([A-Za-z0-9_]*{re.escape(query)}[A-Za-z0-9_]*)"

    if os.path.exists(rg_bin):
        cmd = [
            rg_bin,
            "-g", "!{.venv,node_modules,.next,__pycache__,.git,dist,build}/**",
            "-n",
            "-e", pattern,
            *[d for d in TARGET_DIRECTORIES if (root / d).exists()]
        ]
        try:
            proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=10)
            for line in proc.stdout.splitlines():
                parts = line.split(":", 2)
                if len(parts) == 3:
                    rel_file, line_no_str, content = parts
                    try:
                        line_no = int(line_no_str)
                    except ValueError:
                        continue
                    m = re.search(pattern, content)
                    kind = m.group(1).strip() if m else "symbol"
                    name = m.group(2).strip() if m else query
                    results.append({
                        "file": rel_file,
                        "line": line_no,
                        "kind": kind,
                        "name": name,
                        "snippet": content.strip()
                    })
            return results
        except Exception:
            pass

    # Pure Python fallback
    regex = re.compile(pattern)
    for target_dir in TARGET_DIRECTORIES:
        base_dir = root / target_dir
        if not base_dir.exists():
            continue
        for current_root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for file in files:
                if not file.endswith((".py", ".ts", ".tsx", ".js", ".md")):
                    continue
                file_path = Path(current_root) / file
                try:
                    rel_path = str(file_path.relative_to(root))
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        for idx, line_text in enumerate(f, start=1):
                            m = regex.search(line_text)
                            if m:
                                results.append({
                                    "file": rel_path,
                                    "line": idx,
                                    "kind": m.group(1).strip(),
                                    "name": m.group(2).strip(),
                                    "snippet": line_text.strip()
                                })
                except Exception:
                    continue

    return results


def find_callers(query: str, root: Path = HUB_ROOT, limit: int = 50) -> List[Dict[str, Any]]:
    """Fast symbol call and reference resolver across monorepo source files.
    Finds where a symbol is invoked or referenced, excluding definition lines.
    """
    rg_bin = shutil.which("rg") or "/opt/homebrew/bin/rg"
    results: List[Dict[str, Any]] = []
    call_pattern = rf"\b{re.escape(query)}\b"
    def_pattern = rf"\b(class|def|async\s+def|interface|type)\s+{re.escape(query)}\b"

    if os.path.exists(rg_bin):
        cmd = [
            rg_bin,
            "-g", "!{.venv,node_modules,.next,__pycache__,.git,dist,build}/**",
            "-n",
            "-e", call_pattern,
            *[d for d in TARGET_DIRECTORIES if (root / d).exists()]
        ]
        try:
            proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=10)
            def_re = re.compile(def_pattern)
            for line in proc.stdout.splitlines():
                if len(results) >= limit:
                    break
                parts = line.split(":", 2)
                if len(parts) == 3:
                    rel_file, line_no_str, content = parts
                    if def_re.search(content):
                        continue
                    try:
                        line_no = int(line_no_str)
                    except ValueError:
                        continue
                    results.append({
                        "file": rel_file,
                        "line": line_no,
                        "snippet": content.strip()
                    })
            return results
        except Exception:
            pass

    # Pure Python fallback
    ref_re = re.compile(call_pattern)
    def_re = re.compile(def_pattern)
    for target_dir in TARGET_DIRECTORIES:
        base_dir = root / target_dir
        if not base_dir.exists():
            continue
        for current_root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for file in files:
                if not file.endswith((".py", ".ts", ".tsx", ".js")):
                    continue
                file_path = Path(current_root) / file
                try:
                    rel_path = str(file_path.relative_to(root))
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        for idx, line_text in enumerate(f, start=1):
                            if len(results) >= limit:
                                return results
                            if ref_re.search(line_text) and not def_re.search(line_text):
                                results.append({
                                    "file": rel_path,
                                    "line": idx,
                                    "snippet": line_text.strip()
                                })
                except Exception:
                    continue

    return results


def resolve_symbol_graph(query: str, root: Path = HUB_ROOT) -> Dict[str, Any]:
    """Builds a dependency and call graph around a symbol: definitions + references."""
    defs = find_symbol(query, root=root)
    calls = find_callers(query, root=root)
    callers_by_file: Dict[str, int] = {}
    for c in calls:
        f = c["file"]
        callers_by_file[f] = callers_by_file.get(f, 0) + 1

    return {
        "symbol": query,
        "definition_count": len(defs),
        "definitions": defs,
        "call_count": len(calls),
        "callers_by_file": callers_by_file,
        "calls": calls
    }


def find_files(pattern: str, root: Path = HUB_ROOT) -> List[str]:
    """Fast file resolver matching path fragments."""
    matched = []
    clean_pat = pattern.lower()
    for target_dir in TARGET_DIRECTORIES:
        base_dir = root / target_dir
        if not base_dir.exists():
            continue
        for current_root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for file in files:
                file_path = Path(current_root) / file
                rel_path = str(file_path.relative_to(root))
                if clean_pat in rel_path.lower():
                    matched.append(rel_path)
    return matched


def main():
    parser = argparse.ArgumentParser(description="DNK OS Architecture & Symbol Map")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--symbol", type=str, help="Fast search for symbols (classes, functions, types)")
    parser.add_argument("--calls", type=str, help="Fast search for symbol calls/references")
    parser.add_argument("--graph", type=str, help="Build symbol definition and call graph")
    parser.add_argument("--find", type=str, help="Fast search for file path fragments")
    args = parser.parse_args()

    if args.graph:
        graph = resolve_symbol_graph(args.graph)
        if args.json:
            print(json.dumps(graph, indent=2))
        else:
            print(f"📊 Symbol Graph for '{args.graph}':")
            print(f"  • Definitions ({graph['definition_count']}):")
            for d in graph["definitions"]:
                print(f"    [{d['kind']}] {d['name']} -> {d['file']}:{d['line']}")
            print(f"  • Call sites & references ({graph['call_count']}):")
            for f, count in graph["callers_by_file"].items():
                print(f"    - {f}: {count} references")
        return

    if args.calls:
        calls = find_callers(args.calls)
        if args.json:
            print(json.dumps({"symbol": args.calls, "count": len(calls), "calls": calls}, indent=2))
        else:
            print(f"📞 Found {len(calls)} references/calls for '{args.calls}':\n")
            for c in calls:
                print(f"  📍 {c['file']}:{c['line']}")
                print(f"    💻 {c['snippet']}\n")
        return

    if args.symbol:
        symbols = find_symbol(args.symbol)
        if args.json:
            print(json.dumps({"symbol": args.symbol, "count": len(symbols), "results": symbols}, indent=2))
        else:
            print(f"🔍 Found {len(symbols)} symbol matches for '{args.symbol}':\n")
            for s in symbols:
                print(f"  [{s['kind']}] {s['name']}")
                print(f"    📍 {s['file']}:{s['line']}")
                print(f"    💻 {s['snippet']}")
                print()
        return

    if args.find:
        matched = find_files(args.find)
        if args.json:
            print(json.dumps({"pattern": args.find, "count": len(matched), "files": matched}, indent=2))
        else:
            print(f"📁 Found {len(matched)} matching files for '{args.find}':\n")
            for f in matched:
                print(f"  • {f}")
        return

    if args.json:
        print(json.dumps(STRUCTURE_INDEX, indent=2))
        return

    print("================================================================================")
    print("🗺️  DNK OS ZERO-WASTE REPOSITORY ARCHITECTURE MAP (SSOT)")
    print("================================================================================")
    for section, items in STRUCTURE_INDEX.items():
        print(f"\n📁 [{section.upper()}]:")
        if isinstance(items, dict):
            for k, v in items.items():
                if isinstance(v, dict):
                    print(f"  • {k}: {v.get('type')} ({v.get('path')})")
                    print(f"    - Purpose: {v.get('description')}")
                    print(f"    - Key Files: {', '.join(v.get('key_files', []))}")
                else:
                    print(f"  • {k}: {v}")
    print("\n================================================================================")


if __name__ == "__main__":
    main()
