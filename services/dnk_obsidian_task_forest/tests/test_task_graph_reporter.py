# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_obsidian_task_forest/tests/test_task_graph_reporter.py"
# purpose: "Unit tests for TaskGraphReporter detecting 100% completed execution cycles and writing cycle reports."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import tempfile
import pytest
from services.dnk_obsidian_task_forest.src.task_graph_reporter import TaskGraphReporter


def test_task_graph_reporter_generates_report():
    with tempfile.TemporaryDirectory() as tmp_vault, tempfile.TemporaryDirectory() as tmp_reports:
        # Create a completed bush and completed flower
        bush_file = os.path.join(tmp_vault, "Bush_Completed.md")
        flower_file = os.path.join(tmp_vault, "Flower_Completed.md")

        with open(bush_file, "w", encoding="utf-8") as f:
            f.write("""---
id: bush_auth_module
title: Auth Module Feature
plant_scale: bush
status: completed
tags:
  - dnk-task-forest
---
# Auth Module Feature
""")

        with open(flower_file, "w", encoding="utf-8") as f:
            f.write("""---
id: flower_token_func
title: Token Generator Func
plant_scale: flower
status: completed
parent_id: bush_auth_module
tags:
  - dnk-task-forest
---
# Token Generator Func
""")

        reporter = TaskGraphReporter(vault_path=tmp_vault, reports_dir=tmp_reports)
        reports = reporter.check_and_generate_cycle_reports()

        assert len(reports) >= 1
        assert os.path.exists(reports[0])

        with open(reports[0], "r", encoding="utf-8") as f:
            report_text = f.read()

        assert "CYC_BUSH_AUTH_MODULE" in report_text
        assert "Auth Module Feature" in report_text
        assert "100% COMPLETED ✅" in report_text
