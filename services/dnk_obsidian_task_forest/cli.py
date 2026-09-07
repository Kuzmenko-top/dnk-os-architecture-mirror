# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_obsidian_task_forest/cli.py"
# purpose: "CLI runner for Obsidian Task Forest Engine: scans vault notes, recalculates Bottom-Up Rollup progress, and updates Markdown reports."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import sys
import argparse
from services.dnk_obsidian_task_forest.src.obsidian_task_forest import ObsidianTaskForestParser


def main() -> None:
    parser = argparse.ArgumentParser(description="DNK OS Obsidian Task Forest CLI Engine")
    parser.add_argument("--vault", type=str, default="docs/tasks", help="Path to Obsidian Vault tasks directory")
    parser.add_argument("--sync", action="store_true", help="Sync and recalculate progress for all plant nodes")
    args = parser.parse_args()

    print("=================================================================")
    print("🌻 DNK OS: Obsidian Task Forest CLI Engine")
    print("=================================================================")

    tf_parser = ObsidianTaskForestParser(args.vault)
    nodes = tf_parser.scan_vault()

    print(f"✅ Знайдено нод у Vault ({args.vault}): {len(nodes)}")

    fields = [n for n in nodes.values() if n.plant_scale == "field"]
    if not fields:
        print("ℹ️ Жодного Корневого Поля (Project Field) поки не знайдено.")
    else:
        for f in fields:
            pct = f.get_completion_percentage()
            print(f"🌾 Поле `{f.title}` -> Загальний Прогрес: {pct}%")
            print("-----------------------------------------------------------------")
            print(f.to_mermaid(direction="BT"))
            print("-----------------------------------------------------------------")


if __name__ == "__main__":
    main()
