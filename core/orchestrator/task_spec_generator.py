#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/task_spec_generator.py"
# purpose: "Autonomous Task Spec Generator: Automatically transforms unstructured natural language user prompts into rigorous, MASE-compliant Task Specifications v2.5."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

from core.orchestrator.task_triage import dnk_triage_task, TriageResult
from core.orchestrator.evidence_planner import generate_evidence_plan, EpistemicStatus
from core.orchestrator.risk_gate import assess_risk, RiskLevel
from core.orchestrator.github_research import analyze_github_repo, normalize_repo_slug

HUB_ROOT = Path(__file__).resolve().parent.parent.parent


def should_auto_spec(user_query: str) -> bool:
    """
    Detect if user query is an unstructured action task request requiring
    automatic transformation into a structured MASE Task Spec v2.5.
    """
    if not user_query or not user_query.strip():
        return False

    trimmed = user_query.strip()

    # 1. If prompt ALREADY contains a structured Task Spec header/template, do not double-wrap
    if any(marker in trimmed for marker in (
        "# 🎯 СЛАЙС",
        "# 🎯 SLICE",
        "## 📌 ЦІЛЬОВА ДИРЕКТИВА",
        "## 🔒 PRECONDITIONS & BUDGET",
        "## DEFINITION OF DONE",
        "## ✅ DEFINITION OF DONE"
    )):
        return False

    # 2. Keywords indicating actionable task request
    task_keywords = [
        r"\bзроби\b", r"\bствори\b", r"\bзнайди\b", r"\bреалізуй\b",
        r"\bвиконай\b", r"\bпобудуй\b", r"\bнапиши\b", r"\bзгенеруй\b",
        r"\bімплементуй\b", r"\bимплементуй\b", r"\bаудит\b", r"\bпорівняй\b",
        r"\bдосліди\b", r"\bдодай\b", r"\bонови\b", r"\bвиправ\b",
        r"\bрефактор\b", r"\bперевір\b", r"\bналаштуй\b", r"\bінтегруй\b",
        r"\bвидали\b", r"\bвидалити\b", r"\bочисти\b", r"\bочистити\b",
        r"\bbuild\b", r"\bcreate\b", r"\bimplement\b", r"\bfix\b",
        r"\brefactor\b", r"\baudit\b", r"\bgenerate\b", r"\badd\b",
        r"\bupdate\b", r"\boptimize\b", r"\bsetup\b", r"\bintegrate\b",
        r"\btest\b", r"\bverify\b", r"\bdelete\b", r"\bremove\b", r"\bdrop\b", r"\bpurge\b"
    ]

    # 3. Pure conversational questions or queries without actionable commands
    pure_question_starts = [
        r"^(?:привіт|добрий\s+день|hello|hi|hey)\b",
        r"^(?:хто\s+ти|що\s+ти|how\s+are\s+you|who\s+are\s+you)\b",
        r"^(?:що\s+таке|what\s+is|explain\b|поясни\b)",
    ]

    for q_start in pure_question_starts:
        if re.search(q_start, trimmed, re.IGNORECASE) and not any(re.search(kw, trimmed, re.IGNORECASE) for kw in task_keywords[:10]):
            return False

    # Check if any actionable task keyword is matched
    has_task_kw = any(re.search(kw, trimmed, re.IGNORECASE) for kw in task_keywords)
    return has_task_kw


def get_next_slice_number() -> str:
    """
    Determines the next sequential micro-slice number by inspecting git history
    or existing documentation. Default increments last major.minor slice.
    """
    try:
        res = subprocess.run(
            ["git", "log", "-n", "20", "--oneline"],
            cwd=str(HUB_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if res.returncode == 0 and res.stdout:
            # Look for slice patterns in commit messages: slice 13.1, slice 12.5, etc.
            matches = re.findall(r'slice\s+(\d+)\.(\d+)(?:\.(\d+))?', res.stdout, re.IGNORECASE)
            if matches:
                # Find maximum major and minor
                slices = []
                for m in matches:
                    major = int(m[0])
                    minor = int(m[1])
                    patch = int(m[2]) if m[2] else 0
                    slices.append((major, minor, patch))
                slices.sort(key=lambda s: (s[0], s[1], s[2]), reverse=True)
                top = slices[0]
                return f"{top[0]}.{top[1] + 1}"
    except Exception:
        pass

    return "13.2"


def extract_task_title(user_query: str) -> str:
    """
    Extracts a concise, professional task title from the user's natural language request.
    """
    cleaned = user_query.strip()
    # Strip greetings / agent prefixes
    cleaned = re.sub(r'^(?:герич[,\s]+|hermes[,\s]+|antigravity[,\s]+|будь\s+ласка[,\s]+|please[,\s]+)+', '', cleaned, flags=re.IGNORECASE)
    
    # Take the first line or up to first punctuation
    first_sentence = re.split(r'[\n\r\.!\?]', cleaned)[0].strip()
    if not first_sentence:
        first_sentence = cleaned[:60]

    # Limit length
    words = first_sentence.split()
    if len(words) > 10:
        first_sentence = " ".join(words[:10])

    first_sentence = first_sentence.strip(" :-\t")
    return first_sentence[:70] if first_sentence else "Automated Task Execution"


def format_target_files(target_files: List[str], domains: Optional[List[str]] = None) -> str:
    """
    Formats the target file manifest for the Task Spec.
    """
    if not target_files:
        if domains and "knowledge_docs" in domains:
            return "- [NEW] docs/architecture/AUDIT_REPORT.md\n- [NEW] docs/architecture/RECOMMENDATIONS.md"
        if domains and "backend_api" in domains:
            return "- [MODIFY] apps/api/main.py\n- [NEW] tests/unit/test_api_slice.py"
        return "- [MODIFY] core/orchestrator/README.md\n- [NEW] tests/verification/test_execution_slice.py"

    lines = []
    for f in target_files:
        clean = f.lstrip("./")
        cand = HUB_ROOT / clean
        action = "[MODIFY]" if cand.exists() else "[NEW]"
        lines.append(f"- {action} {clean}")
    return "\n".join(lines)


def generate_technical_requirements(user_query: str, triage_result: TriageResult) -> str:
    """
    Generates structured technical requirements based on user intent and domain triage.
    """
    reqs = [
        "1. Суворе дотримання архітектурних інваріантів DNK OS (відносні шляхи `./`, MRH-заголовки `DNK-STD-0075`).",
        "2. Ізоляція контексту: робота виключно в межах зазначених цільових файлів без модифікації сторонніх модулів.",
    ]

    domains = triage_result.domains_detected
    if "backend_api" in domains:
        reqs.append("3. FastAPI / Async: збереження типізації Pydantic v2 та асинхронних патернів без блокуючих операцій.")
    if "frontend_canvas" in domains:
        reqs.append("3. React / Canvas: дотримання стану Zustand, TypeScript типізація та запобігання зайвим ре-рендерам.")
    if "qa_security" in domains:
        reqs.append("3. Тестування: 100% покриття критичних шляхів новими тестами без модифікації існуючих асертів.")
    if "knowledge_docs" in domains:
        reqs.append("3. Документація: створення структурованих Markdown звітів із висновками, доказами та посиланнями.")

    reqs.append(f"4. Специфіка завдання: реалізувати директиву користувача: '{extract_task_title(user_query)}'.")
    return "\n".join(reqs)


def slugify(text: str) -> str:
    cleaned = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '_', cleaned).strip('_')
    return slug[:40] if slug else "task"


def save_task_spec(spec: str, title: str, slice_number: str = "1.0") -> Dict[str, str]:
    """
    Persists the generated Task Spec to:
    1. .hermes/active_task_spec.md (active runtime spec)
    2. docs/plans/TASK_ACTIVE.md (quick workspace reference)
    3. docs/plans/my_task/task_{date}_{slug}.md (canonical historical spec)
    4. docs/notes/tasks_and_ideas/{slug}.md (Obsidian Task Forest note)
    """
    from datetime import datetime

    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M%S")
    slug = slugify(title)

    saved_paths = {}

    # 1. .hermes/active_task_spec.md
    try:
        hermes_dir = HUB_ROOT / ".hermes"
        hermes_dir.mkdir(parents=True, exist_ok=True)
        active_spec_path = hermes_dir / "active_task_spec.md"
        active_spec_path.write_text(spec, encoding="utf-8")
        saved_paths["active_spec"] = str(active_spec_path.relative_to(HUB_ROOT))
    except Exception:
        pass

    # 2. docs/plans/TASK_ACTIVE.md
    try:
        plans_dir = HUB_ROOT / "docs" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        task_active_path = plans_dir / "TASK_ACTIVE.md"
        task_active_path.write_text(spec, encoding="utf-8")
        saved_paths["active_plan"] = str(task_active_path.relative_to(HUB_ROOT))
    except Exception:
        pass

    # 3. docs/plans/my_task/task_{date}_{slug}.md
    try:
        my_tasks_dir = HUB_ROOT / "docs" / "plans" / "my_task"
        my_tasks_dir.mkdir(parents=True, exist_ok=True)
        canonical_task_path = my_tasks_dir / f"task_{date_str}_{slug}.md"
        canonical_task_path.write_text(spec, encoding="utf-8")
        saved_paths["canonical_task"] = str(canonical_task_path.relative_to(HUB_ROOT))
    except Exception:
        pass

    # 4. docs/notes/tasks_and_ideas/{subfolder}/{slug}.md (Obsidian MRH Hygiene: Frontmatter first, muted MRH comment)
    try:
        if slug.startswith("epic-"):
            subfolder = "epics"
        elif slug.startswith("idea-"):
            subfolder = "ideas"
        elif slug.startswith("gate-"):
            subfolder = "gates"
        elif slug.startswith("task-"):
            subfolder = "tasks"
        else:
            subfolder = "tasks"
        obsidian_tasks_dir = HUB_ROOT / "docs" / "notes" / "tasks_and_ideas" / subfolder
        obsidian_tasks_dir.mkdir(parents=True, exist_ok=True)
        obsidian_task_path = obsidian_tasks_dir / f"{slug}.md"

        obsidian_content = f"""---
node_id: "{slug}"
title: "{title}"
node_type: task
stage: ready
status: in_progress
slice_number: "{slice_number}"
created_at: "{now.strftime('%Y-%m-%d %H:%M:%S')}"
tags: [task_spec, zero_touch, mase]
---
<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/notes/tasks_and_ideas/{slug}.md"
# purpose: "Obsidian Task Forest Mirror for {title}"
# canonical_source: false
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "{now.strftime('%Y-%m-%d')}"
# author: "Chief System Architect (Gerych Prime) & DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
-->

{spec}
"""
        obsidian_task_path.write_text(obsidian_content, encoding="utf-8")
        saved_paths["obsidian_note"] = str(obsidian_task_path.relative_to(HUB_ROOT))
    except Exception:
        pass

    return saved_paths


def auto_generate_task_spec(
    user_query: str,
    triage_result: Optional[TriageResult] = None,
    slice_number: Optional[str] = None
) -> str:
    """
    Auto-generates a complete, structured, MASE-compliant Task Spec v2.5 from an unstructured user query.
    """
    if triage_result is None:
        triage_result = dnk_triage_task(user_query)

    if not slice_number:
        slice_number = get_next_slice_number()

    task_title = extract_task_title(user_query)

    # Collect target files from triage execution plan or query
    target_files = []
    for plan_step in triage_result.execution_plan:
        if isinstance(plan_step, dict):
            target_files.extend(plan_step.get("scope_files", []))

    # Deduplicate while preserving order
    deduped_files = []
    for f in target_files:
        if f not in deduped_files:
            deduped_files.append(f)

    files_manifest = format_target_files(deduped_files, triage_result.domains_detected)
    tech_reqs = generate_technical_requirements(user_query, triage_result)

    mode = triage_result.mode
    complexity = triage_result.complexity_score
    assigned_workers = list({s.get("assigned_agent", "gerych_prime") for s in triage_result.execution_plan if isinstance(s, dict)})
    workers_str = ", ".join(assigned_workers) if assigned_workers else "gerych_prime"

    # Select appropriate test verification command
    if "backend_api" in triage_result.domains_detected:
        test_cmd = "./.venv/bin/pytest apps/api/tests/ -v"
    elif "qa_security" in triage_result.domains_detected:
        test_cmd = "./.venv/bin/pytest tests/ -v"
    else:
        test_cmd = "./.venv/bin/pytest tests/unit/ -v 2>/dev/null || ./.venv/bin/pytest tests/ -v"

    # 1. Evaluate Risk Gate
    risk_info = assess_risk(user_query, deduped_files)
    risk_level = risk_info["risk_level"]
    requires_approval = risk_info["requires_approval"]
    safeguards_list = "\n".join(f"- 🛡️ {sg}" for sg in risk_info.get("suggested_safeguards", []))

    # 2. Generate Evidence Plan
    evidence_plan = generate_evidence_plan(user_query, deduped_files)
    evidence_probes_list = "\n".join(
        f"- [{p['epistemic_status']}] `{p['command']}` -> очікувано: `{p['expected']}` ({p['claim'][:60]})"
        for p in evidence_plan.get("probes", [])[:5]
    )

    # 3. Check for GitHub Repository Research
    github_section = ""
    github_match = re.search(r"(?:https?://github\.com/([a-zA-Z0-9_\.-]+/[a-zA-Z0-9_\.-]+)|([a-zA-Z0-9_-]+/[a-zA-Z0-9_\.-]+))", user_query)
    if github_match and any(gh_hint in user_query.lower() for gh_hint in ["github", "repo", "репозиторій", "open-source", "sota"]):
        repo_target = github_match.group(1) or github_match.group(2)
        if repo_target and not repo_target.startswith("core/") and not repo_target.startswith("apps/"):
            gh_res = analyze_github_repo(repo_target)
            github_section = f"""
## 🧬 SOTA GITHUB ДОСЛІДЖЕННЯ & TWO-TRACK ЛІЦЕНЗІЯ
- Цільовий репозиторій: [{gh_res['repo']}]({gh_res['url']})
- Ліцензія: `{gh_res['license']}` -> **{gh_res['legal_track']}**
- Патерни: {', '.join(gh_res['patterns'])}
- Застосовність: {gh_res['applicability']}
- Зірки: {gh_res['activity']['stars']} | Останній коміт: {gh_res['activity']['last_commit']}
"""

    spec = f"""# 🎯 СЛАЙС {slice_number}: {task_title}

## 📌 ЦІЛЬОВА ДИРЕКТИВА
{user_query.strip()}
ВИКОНУЙ НЕГАЙНО.

## 🔒 PRECONDITIONS & BUDGET
- Repository Root: `./`
- Execution Mode: `{mode}` (Complexity Score: {complexity})
- Primary Executor: `{workers_str}`
- Execution Budget: максимум 25 tool calls на слайс
- Read Calls: ≤ 8
- Write Calls: ≤ 8
- Verification Calls: ≤ 4
- Порушення ізоляції: ЗАБОРОНЕНО (лише цільові файли)

## 📁 ЦІЛЬОВІ ФАЙЛИ
{files_manifest}

## 🛡️ ОЦІНКА РИЗИКІВ ТА ЗАПОБІЖНИКИ (RISK GATE)
- Рівень ризику: `{risk_level}` (Оцінка: {risk_info['risk_score']}/100)
- Потребує погодження людини: `{'ТАК' if requires_approval else 'НІ'}`
- Бекап / Відкат: `{'ОБОВ\'ЯЗКОВО' if risk_info['backup_required'] else 'РЕКОМЕНДОВАНО'}`
{safeguards_list}

## 🔬 ПЛАН ЗБОРУ ЕМПІРИЧНИХ ДОКАЗІВ (EVIDENCE PLANNER)
{evidence_probes_list if evidence_probes_list else "- Немає додаткових емпіричних проб"}
{github_section}
## 📋 ТЕХНІЧНІ ВИМОГИ
{tech_reqs}

## ✅ DEFINITION OF DONE (DoD)
- ✅ Всі цільові файли створено або оновлено без побічних ефектів
- ✅ Жодних вигаданих API чи порушень відносних шляхів
- ✅ Модульні тести пройдено (100% Green)
- ✅ `bash scripts/verify_all.sh` або цільовий тестовий набір: 100% Green
- ✅ Відсутність синтаксичних та лінтер-помилок

## 🔍 КОМАНДА ВЕРИФІКАЦІЇ
```bash
# 1. Targeted Unit Tests
{test_cmd}

# 2. Master Verification Gate
bash scripts/verify_all.sh

# 3. Clean Git Diff Check
git diff --check
```

## 🚀 РЕЖИМ ВИКОНАННЯ
Жодних довгих міркувань — одразу код і точкові інструменти. Після верифікації — фінальний YAML-звіт.

## 🛑 BLOCKED RULE
Якщо вимога суперечить реальній архітектурі репозиторію — НЕ вигадуй API, НЕ змінюй файли поза scope. Поверни BLOCKED із чіткою причиною та артефактом.

## 📤 REQUIRED REPORT
```yaml
status: COMPLETED | BLOCKED | FAILED | BUDGET_EXCEEDED
slice: "{slice_number}"
files_changed:
{chr(10).join(f'  - "{line.split()[-1]}"' for line in files_manifest.splitlines() if line.strip())}
verification:
  command: "{test_cmd} && git diff --check"
  exit_code: 0
tests:
  - "Targeted tests passed"
  - "Quality Gate certified"
assumptions: []
remaining_risks: []
```

## 🧠 STEP 0: TRIAGE PROTOCOL (MANDATORY)
1. Triage оцінено: mode = `{mode}`, complexity = {complexity}
2. Якщо mode == "SOLO" (C ≤ 3) → виконуй сам у межах ≤ 15 tool calls
3. Якщо mode == "SWARM_PARALLEL" (C > 3) → негайно виклич `dnk_swarm_parallel` за планом

## ⚠️ CRITICAL: MASE-Compliance
- Ця задача обмежена мікрослайсом {slice_number} для дотримання ліміту MASE (≤ 25 викликів)
- НЕ намагайся виконувати наступні слайси у цій сесії
- Після завершення {slice_number} — зроби git commit і зафіксуй результат
"""

    # Persist the active task spec to active runtime, canonical plans, and Obsidian mirror
    try:
        save_task_spec(spec, task_title, slice_number)
    except Exception:
        pass

    return spec
