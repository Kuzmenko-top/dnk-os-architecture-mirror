# --- DNK-MRH-HEADER ---
# mrh_id: "core/playbooks/scripts/legacy_relevance_auditor.py"
# purpose: "Script-First Execution utility auditing 6-month legacy R&D assets and 1000+ repository clones to evaluate current relevance and promote valuable gems to DNK OS."
# canonical_source: true
# alters_files: ["docs/tasks/06_Discoveries/*"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import sys
import re
import argparse
from typing import Dict, List, Any


class LegacyRelevanceAuditor:
    """
    Audits legacy R&D files and repositories against DNK OS canonical standards.
    Calculates Relevance Score (0-100%) and recommends action: PROMOTE, REFRACTOR, DEPRECATE.
    """
    def __init__(self, target_workspace: str = "DNK OS") -> None:
        self.target_workspace = target_workspace

    def audit_directory(self, dir_path: str) -> Dict[str, Any]:
        if not os.path.exists(dir_path):
            return {"status": "error", "message": f"Path `{dir_path}` does not exist."}

        audited_files = []
        promoted_count = 0
        refactor_count = 0
        deprecate_count = 0

        categories = {
            "gems_core_code": 0,
            "knowledge_schemas": 0,
            "infra_tools": 0,
            "deprecated_legacy": 0
        }

        for root, _, files in os.walk(dir_path):
            if ".git" in root or ".venv" in root or "__pycache__" in root or "node_modules" in root:
                continue
            for file in files:
                if file.endswith((".py", ".md", ".json", ".yaml")):
                    filepath = os.path.join(root, file)
                    res = self._evaluate_file(filepath)
                    audited_files.append(res)

                    cat = res.get("category", "infra_tools")
                    categories[cat] += 1

                    if res["recommendation"] == "PROMOTE":
                        promoted_count += 1
                        self._create_discovery_seed_if_gem(res)
                    elif res["recommendation"] == "REFRACTOR":
                        refactor_count += 1
                    else:
                        deprecate_count += 1

        return {
            "status": "success",
            "scanned_path": dir_path,
            "total_files_audited": len(audited_files),
            "categories": categories,
            "promoted_gems_count": promoted_count,
            "refactor_needed_count": refactor_count,
            "deprecated_count": deprecate_count,
            "audited_files": audited_files[:20]
        }

    def _evaluate_file(self, filepath: str) -> Dict[str, Any]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            score = 100
            reasons = []
            category = "infra_tools"

            # Categorize based on path and contents
            if "hermes_agent" in filepath or "orchestrator" in filepath:
                category = "gems_core_code"
            elif "knowledge" in filepath or "schemas" in filepath or "prompts" in filepath or "docs" in filepath:
                category = "knowledge_schemas"
            elif "legacy" in filepath or "deprecated" in filepath:
                category = "deprecated_legacy"

            # Check relative paths
            if "/Users/" in content:
                score -= 30
                reasons.append("Contains hardcoded absolute path")

            if "mrh_id" in content or "dnk-task-forest" in content:
                score += 10
                reasons.append("Uses DNK OS Machine-Readable Header")

            final_score = max(0, min(100, score))
            if final_score >= 80 and category == "gems_core_code":
                rec = "PROMOTE"
            elif final_score >= 40:
                rec = "REFRACTOR"
            else:
                rec = "DEPRECATE"

            return {
                "filepath": filepath,
                "score": final_score,
                "category": category,
                "recommendation": rec,
                "reasons": reasons
            }
        except Exception as e:
            return {"filepath": filepath, "score": 0, "recommendation": "DEPRECATE", "reasons": [str(e)]}

    def _create_discovery_seed_if_gem(self, file_res: Dict[str, Any]) -> None:
        filename = os.path.basename(file_res["filepath"])
        if file_res["score"] >= 90 and filename.endswith(".py"):
            safe_name = filename.replace(".", "_")
            seed_dir = os.path.join(self.target_workspace, "docs", "tasks", "06_Discoveries")
            os.makedirs(seed_dir, exist_ok=True)
            seed_path = os.path.join(seed_dir, f"Seed_Gem_{safe_name}.md")
            if not os.path.exists(seed_path):
                with open(seed_path, "w", encoding="utf-8") as f:
                    f.write(f"""---
id: seed_gem_{safe_name}
title: 💎 Legacy R&D Gem: {filename}
type: discovery_seed
plant_scale: seed
icon: 💎
category: "Legacy R&D Promotion"
impact_level: "High ({file_res['score']}%)"
created_at: 2026-08-07
tags:
  - dnk-task-forest
  - dnk-discovery-seed
---

# 💎 Зернятко Відкриття: Legacy R&D Gem {filename}

**Шлях У Спадщині**: `{file_res['filepath']}`  
**Relevance Score**: `{file_res['score']}%` | **Рекомендація**: `PROMOTE ✅`

---

## 🎯 Чому Це Двоподібне Дійсне Відкриття:
- {", ".join(file_res['reasons'])}
""")


def main() -> None:
    parser = argparse.ArgumentParser(description="DNK OS Legacy Relevance Auditor Engine")
    parser.add_argument("--scan", type=str, default="core", help="Directory path to audit relevance")
    args = parser.parse_args()

    auditor = LegacyRelevanceAuditor()
    print("=================================================================")
    print(f"🔍 DNK OS Legacy Relevance Auditor Scanning: `{args.scan}`")
    print("=================================================================")
    res = auditor.audit_directory(args.scan)

    print(f"✅ Проскановано файлів: {res.get('total_files_audited', 0)}")
    print(f"💎 Виявлено діамантів для перенесення (PROMOTE 80-100%): {res.get('promoted_gems_count', 0)}")
    print(f"🛠️ Потребують рефакторингу під нові стандарти (REFRACTOR 40-79%): {res.get('refactor_needed_count', 0)}")
    print(f"⚠️ Застарілі (DEPRECATE 0-39%): {res.get('deprecated_count', 0)}")


if __name__ == "__main__":
    main()
