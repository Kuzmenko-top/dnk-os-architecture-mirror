# --- DNK-MRH-HEADER ---
# mrh_id: "core_orchestrator_zero_waste_slicer"
# purpose: "Zero-Waste Task Slicing & Autonomous Atomic Execution DAG Engine (Phase 3 Mentor Protocol)"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-04"
# alters_files: []
# triggers_tasks: []
# --- END DNK-MRH-HEADER ---

import re
import os
import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("DNKZeroWasteSlicer")


@dataclass
class ExecutionBudget:
    max_tool_calls: int = 25
    max_read_calls: int = 8
    max_write_calls: int = 8
    max_verification_calls: int = 4


@dataclass
class TaskSlice:
    id: str
    index: int
    title: str
    description: str
    target_files: List[str] = field(default_factory=list)
    budget: ExecutionBudget = field(default_factory=ExecutionBudget)
    tool_calls_budget: int = 25
    max_iterations: int = 25
    dod: List[str] = field(default_factory=list)
    verification_cmd: Optional[str] = None
    preconditions: List[str] = field(default_factory=list)
    status: str = "pending"  # "pending", "in_progress", "awaiting_verification", "completed", "failed", "blocked", "budget_exceeded"
    blocked_reason: Optional[str] = None
    result_summary: Optional[str] = None


class ZeroWasteSlicer:
    """
    Decomposes monolithic goals or multi-step specifications into focused,
    atomic execution slices bounded by <=25 tool iterations per turn.
    Guarantees 100% execution fidelity without context rot or budget exhaustion.
    """

    DEFAULT_PLAN_FILE = ".dnk_active_slices.json"

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or Path.cwd()

    def decompose(self, goal: str, raw_subtasks: Optional[List[Dict[str, Any]]] = None) -> List[TaskSlice]:
        """
        Extracts structured atomic slices from raw goal text, markdown lists,
        tables, or explicit subtask payloads.
        """
        slices: List[TaskSlice] = []

        if raw_subtasks:
            for idx, item in enumerate(raw_subtasks):
                s_id = item.get("id") or f"slice-{idx + 1}"
                slices.append(
                    TaskSlice(
                        id=s_id,
                        index=idx + 1,
                        title=item.get("title") or f"Subtask {idx + 1}",
                        description=item.get("description") or "",
                        target_files=item.get("target_files") or [],
                        max_iterations=item.get("max_iterations") or 25,
                        dod=item.get("dod") or [],
                        verification_cmd=item.get("verification_cmd"),
                        status="pending"
                    )
                )
            return slices

        # 1. Parse canonical DNK-STD-0080 markdown slices (# СЛАЙС N.M: ...)
        canonical_slices = self._parse_canonical_markdown_slices(goal)
        if canonical_slices:
            return canonical_slices

        # 2. Parse markdown tables robustly (columns: №, Task, Files, ETA, DoD)
        table_slices = self._parse_markdown_table_slices(goal)
        if table_slices:
            return table_slices

        # 3. Parse numbered lists (e.g. "1.1 Task name", "1. Task name", "- [ ] Task name")
        list_patterns = [
            r"(?:^|\n)\s*(?:[-*]\s+)?(?:\*\*)?(?:Завдання\s+|Task\s+)?([0-9]+(?:\.[0-9]+)?)[.:\s\-]+([^\n]+)",
            r"(?:^|\n)\s*[-*]\s*\[[ xX]\]\s*([0-9]+(?:\.[0-9]+)?|[A-Za-z0-9_-]+)[.:\s\-]+([^\n]+)"
        ]

        for pat in list_patterns:
            matches = re.findall(pat, goal)
            if matches:
                for idx, match in enumerate(matches):
                    step_raw, text = match[0].strip(), match[1].strip()
                    clean_step = step_raw.replace("*", "").strip()
                    extracted_files = self._extract_file_paths(text)
                    verif_cmd = self._derive_verification_cmd(extracted_files)

                    slices.append(
                        TaskSlice(
                            id=f"slice-{clean_step.replace('.', '-')}",
                            index=idx + 1,
                            title=f"Subtask {clean_step}: {text[:80]}",
                            description=text,
                            target_files=extracted_files,
                            max_iterations=25,
                            dod=[f"Complete and verify: {text}"],
                            verification_cmd=verif_cmd,
                            status="pending"
                        )
                    )
                if slices:
                    return slices

        # 3. Fallback: single high-focus slice
        extracted_files = self._extract_file_paths(goal)
        verif_cmd = self._derive_verification_cmd(extracted_files)
        slices.append(
            TaskSlice(
                id="slice-1",
                index=1,
                title=goal[:80].strip() or "Execute primary goal",
                description=goal,
                target_files=extracted_files,
                max_iterations=30,
                dod=["Execute goal and pass Master Quality Gate"],
                verification_cmd=verif_cmd,
                status="pending"
            )
        )
        return slices

    def _parse_canonical_markdown_slices(self, text: str) -> List[TaskSlice]:
        """
        Parses Markdown structured per DNK-STD-0080 / GERYCH_TASK_TEMPLATE:
        Matches '# 🎯 СЛАЙС [N].[M]: [Title]' or '### СЛАЙС [N].[M]: [Title]'
        """
        pattern = r"(?:^|\n)#{1,4}\s*(?:🎯\s*)?(?:СЛАЙС|SLICE|TASK)\s*([0-9]+(?:\.[0-9]+)?)[.:\s\-]+([^\n]+)"
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if not matches:
            return []

        slices = []
        for idx, match in enumerate(matches):
            step_raw = match.group(1).strip()
            title_raw = match.group(2).strip()
            start_pos = match.end()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            body = text[start_pos:end_pos].strip()

            clean_step = step_raw.replace(".", "-")
            extracted_files = self._extract_file_paths(body)

            # Extract bash verification command if present
            cmd_match = re.search(r"```(?:bash|sh)\n(.*?)\n```", body, re.DOTALL)
            verif_cmd = cmd_match.group(1).strip() if cmd_match else self._derive_verification_cmd(extracted_files)

            # Extract DoD items
            dod_items = []
            for line in body.splitlines():
                clean_line = line.strip()
                if clean_line.startswith(("- ✅", "- [ ]", "* ✅", "* [ ]", "- [x]")):
                    dod_items.append(re.sub(r"^[-*]\s*(?:✅|\[[ xX]\])\s*", "", clean_line).strip())

            slices.append(
                TaskSlice(
                    id=f"slice-{clean_step}",
                    index=idx + 1,
                    title=f"{step_raw}: {title_raw}",
                    description=body,
                    target_files=extracted_files,
                    max_iterations=25,
                    dod=dod_items or [f"Complete and verify slice {step_raw}"],
                    verification_cmd=verif_cmd,
                    status="pending"
                )
            )
        return slices

    def _parse_markdown_table_slices(self, text: str) -> List[TaskSlice]:
        lines = [l.strip() for l in text.strip().splitlines() if l.strip().startswith("|")]
        if not lines:
            return []

        header = None
        rows = []
        for line in lines:
            cols = [c.strip() for c in line.strip("|").split("|")]
            # Ignore separator lines (e.g. |---|---|---|)
            if any(set(c) <= set("-: ") for c in cols):
                continue
            if not header:
                header = [c.lower() for c in cols]
            else:
                rows.append(cols)

        if not rows:
            return []

        slices = []
        for idx, row in enumerate(rows):
            if len(row) < 2:
                continue

            step_raw = row[0]
            clean_step = step_raw.replace("*", "").replace("`", "").strip()
            task_title = row[1].replace("*", "").replace("`", "").strip()
            file_col = row[2] if len(row) > 2 else ""
            dod_col = row[4] if len(row) > 4 else (row[3] if len(row) > 3 else "")

            combined_scope = f"{task_title} {file_col} {dod_col}"
            extracted_files = self._extract_file_paths(combined_scope)
            verif_cmd = self._derive_verification_cmd(extracted_files)

            dod_items = [d.strip() for d in dod_col.split(";") if d.strip()] or [dod_col or task_title]

            slices.append(
                TaskSlice(
                    id=f"slice-{clean_step.replace('.', '-')}",
                    index=idx + 1,
                    title=f"{clean_step}: {task_title}",
                    description=f"Task: {task_title}. Files: {file_col}. DoD: {dod_col}",
                    target_files=extracted_files,
                    max_iterations=25,
                    dod=dod_items,
                    verification_cmd=verif_cmd,
                    status="pending"
                )
            )
        return slices

    def save_plan(self, slices: List[TaskSlice], filename: Optional[str] = None) -> Path:
        target = self.workspace_root / (filename or self.DEFAULT_PLAN_FILE)
        data = {
            "version": "1.0.0",
            "total_slices": len(slices),
            "slices": [asdict(s) for s in slices]
        }
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return target

    def load_plan(self, filename: Optional[str] = None) -> List[TaskSlice]:
        target = self.workspace_root / (filename or self.DEFAULT_PLAN_FILE)
        if not target.exists():
            return []
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            loaded = []
            for item in data.get("slices", []):
                if isinstance(item.get("budget"), dict):
                    item["budget"] = ExecutionBudget(**item["budget"])
                loaded.append(TaskSlice(**item))
            return loaded
        except Exception as e:
            logger.warning(f"Failed to load task plan: {e}")
            return []

    def get_next_pending_slice(self, filename: Optional[str] = None) -> Optional[TaskSlice]:
        slices = self.load_plan(filename)
        for s in slices:
            if s.status in ("pending", "in_progress"):
                return s
        return None

    def update_slice_status(
        self,
        slice_id: str,
        status: str,
        summary: Optional[str] = None,
        filename: Optional[str] = None
    ) -> bool:
        slices = self.load_plan(filename)
        updated = False
        for s in slices:
            if s.id == slice_id:
                s.status = status
                if summary:
                    s.result_summary = summary
                updated = True
                break
        if updated:
            self.save_plan(slices, filename)
        return updated

    def generate_slice_prompt(self, slice_item: TaskSlice, total_count: int) -> str:
        """
        Builds an ultra-focused atomic prompt for Gerych for this specific slice (v1.1 standard).
        """
        targets_str = "\n".join(f"- `{f}`" for f in slice_item.target_files) or "- Specified in requirements"
        dod_str = "\n".join(f"- ✅ {d}" for d in slice_item.dod) or "- ✅ Fully functional, verified implementation"
        verif_str = slice_item.verification_cmd or "bash scripts/verify_all.sh"
        budget = slice_item.budget

        preconditions_str = "\n".join(f"- {p}" for p in slice_item.preconditions) or f"- Repository root: `./`\n- Allowed scope: тільки перелічені target files\n- Forbidden: git commit, push, merge, зміни файлів поза scope"

        return f"""# 🎯 ZERO-WASTE SLICE [{slice_item.index}/{total_count}]: {slice_item.title}

## 📌 DIRECTIVE
Виконай цей слайс негайно. Не створюй окремий план і не запитуй підтвердження. Працюй суворо в межах цільових файлів.

## 🔒 PRECONDITIONS
{preconditions_str}
- Execution Budget: максимум {budget.max_tool_calls} tool calls (read: {budget.max_read_calls}, write: {budget.max_write_calls}, verif: {budget.max_verification_calls})

## 📁 TARGET FILES
{targets_str}

## 📋 REQUIREMENTS
{slice_item.description}

## 🧪 VERIFICATION
```bash
{verif_str}
```

## ✅ DoD (Критерії успіху)
{dod_str}
- ✅ Фактичний diff перевірено
- ✅ Відсутні невиконані TODO або mock-заглушки у scope

## 🛑 BLOCKED RULE
Якщо вимога суперечить реальному коду репозиторію, API не відповідає ТЗ або потрібна зміна файлів поза scope:
НЕ вигадуй API і не модифікуй зайві файли.
Зупинись та поверни статус `BLOCKED` із зазначенням точної причини та доказу.

## 📤 REQUIRED REPORT
Поверни строго структурований YAML-звіт:
```yaml
status: COMPLETED # або BLOCKED, FAILED, BUDGET_EXCEEDED
files_changed: []
verification:
  command: "{verif_str}"
  exit_code: 0
tests: []
assumptions: []
remaining_risks: []
```

## 🚀 EXECUTION MODE
Одразу редагуй target files через `write_to_file` або `patch`.
Після першої успішної верифікації заверши слайс і надай фінальний звіт.
"""

    def _extract_file_paths(self, text: str) -> List[str]:
        candidates = re.findall(
            r"(?:apps|services|core|tests|scripts|config|docs)/[A-Za-z0-9_\-./]+\.[a-zA-Z0-9]+",
            text
        )
        clean = []
        for c in candidates:
            p = c.strip("`'\",:;")
            if p not in clean:
                clean.append(p)
        return clean

    def _derive_verification_cmd(self, target_files: List[str]) -> str:
        if not target_files:
            return "bash scripts/verify_all.sh"

        has_py = any(f.endswith(".py") for f in target_files)
        has_ts = any(f.endswith((".ts", ".tsx", ".js", ".jsx")) for f in target_files)
        has_tests = any("/tests/" in f or f.startswith("tests/") for f in target_files)

        if has_tests:
            test_files = [f for f in target_files if "/tests/" in f or f.startswith("tests/")]
            return f"uv run pytest {' '.join(test_files)}"
        elif has_ts and not has_py:
            return "npx --prefix apps/web tsc --project apps/web/tsconfig.json --noEmit"
        elif has_py and not has_ts:
            return "bash scripts/verify_all.sh"
        return "bash scripts/verify_all.sh"
