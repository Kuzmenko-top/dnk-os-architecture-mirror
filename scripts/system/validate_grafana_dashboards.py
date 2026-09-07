# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/validate_grafana_dashboards.py"
# purpose: "Validates Grafana dashboard JSON schema integrity, panel structure, and metric targets for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def validate_dashboard_file(file_path: Path) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]
    except Exception as e:
        return False, [f"Cannot read file: {e}"]

    # Support both wrapped {"dashboard": {...}} and raw dashboard JSON
    dashboard = data.get("dashboard", data) if isinstance(data, dict) else None
    if not isinstance(dashboard, dict):
        return False, ["Root must be a JSON object containing dashboard definition"]

    if "title" not in dashboard:
        errors.append("Missing required field 'title'")

    panels = dashboard.get("panels")
    if panels is None:
        errors.append("Missing required field 'panels'")
    elif not isinstance(panels, list):
        errors.append("'panels' must be an array")
    elif len(panels) == 0:
        errors.append("'panels' array is empty")
    else:
        for idx, panel in enumerate(panels):
            if not isinstance(panel, dict):
                errors.append(f"Panel #{idx} is not an object")
                continue
            if "title" not in panel and "id" not in panel:
                errors.append(f"Panel #{idx} missing both 'title' and 'id'")
            
            targets = panel.get("targets", [])
            if isinstance(targets, list):
                for t_idx, target in enumerate(targets):
                    if isinstance(target, dict):
                        expr = target.get("expr", "")
                        if expr == "" and "rawSql" not in target:
                            errors.append(f"Panel #{idx} target #{t_idx} has empty query expression")

    return len(errors) == 0, errors


def main() -> int:
    search_dirs = [
        Path("monitoring/grafana_dashboards"),
        Path("monitoring/grafana/dashboards"),
    ]

    dashboard_files: List[Path] = []
    for d in search_dirs:
        if d.exists():
            dashboard_files.extend(d.glob("*.json"))

    if not dashboard_files:
        print("⚠️ No Grafana dashboard JSON files found to validate.")
        return 0

    print(f"🔍 Validating {len(dashboard_files)} Grafana dashboard(s)...")
    total_errors = 0

    for file_path in dashboard_files:
        valid, errors = validate_dashboard_file(file_path)
        rel_path = file_path.as_posix()
        if valid:
            print(f"  ✅ {rel_path}: OK")
        else:
            print(f"  ❌ {rel_path}: {len(errors)} error(s)")
            for err in errors:
                print(f"     - {err}")
            total_errors += len(errors)

    if total_errors == 0:
        print(f"\n🎉 All {len(dashboard_files)} Grafana dashboards passed schema validation!")
        return 0
    else:
        print(f"\n💥 Grafana dashboard validation failed with {total_errors} error(s).")
        return 1


if __name__ == "__main__":
    sys.exit(main())
