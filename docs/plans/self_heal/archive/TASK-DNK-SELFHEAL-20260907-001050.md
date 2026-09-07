<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plans/self_heal/TASK-DNK-SELFHEAL-20260907-001050.md"
# purpose: "Автономна задача самолікування системи (Self-Healing) після сесії bg_173628_6d18c2."
# canonical_source: true
# alters_files: ["AGENTS.md", "core/orchestrator/session_sentinel.py", "scripts/system/gerych.sh", "scripts/system/hermes_pre_tool_hook.py"]
# triggers_tasks: []
# status: "Active"
# version: "2.5.0"
# updated_at: "2026-09-07"
# author: "Session Sentinel (Shadow Auditor) & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---
-->

# 🏥 САМОЛІКУВАННЯ СИСТЕМИ: Tool Execution or Test Failure in [read_file]

> **Автономна детекція від Session Sentinel (`gerych_auditor`)**
> Під час виконання сесії `bg_173628_6d18c2` виявлено 8 критичних або алгоритмічних дефектів.
> Ця задача призначена для агента-розробника ядра (`dnk_dev_fullstack`), щоб відновити 100% стабільність системи та запобігти повторенню дефектів.

---

## 🎯 Task Header & Metadata

- **Task ID**: `TASK-DNK-SELFHEAL-20260907-001050`
- **Title**: `[Self-Heal] Tool Execution or Test Failure in [read_file]`
- **Domain / Bounded Context**: `core/hermes_agent`
- **Primary Executor**: `dnk_dev_fullstack` (System Doctor & Fullstack Lead)
- **Collaborating Swarm Agents**: `gerych_auditor`, `dnk_scones_memory`
- **Execution Mode**: `MUTATION (Core System & Algorithm Patching)`
- **Estimated Complexity**: `P1 High`
- **Origin Session ID**: `bg_173628_6d18c2`
- **Recursion Depth**: `1`

---

## ⚡ Zero-Waste Execution Contract

| Параметр | Вимога | Призначення |
| :--- | :--- | :--- |
| **Max Tool Calls** | **≤ 15 tool calls** | Швидкий точковий патч без зайвої розвідки. |
| **Virtualenv SSOT** | `.venv/bin/python3` та `.venv/bin/pytest` | Жодних системних інтерпретаторів. |
| **Path Invariant** | **Тільки відносні шляхи (`./`, `../`)** | 0 абсолютних шляхів `/Users/...`. |
| **MRH Invariant** | Обов'язковий MRH заголовок | `DNK-STD-0075` комплаєнс. |
| **Quality Gate** | **100% Green Pytest Suite** | Регресійне тестування перед фіксацією. |

---

## 💡 1. Problem Statement & Raw Evidence

### ⚠️ 1. Tool Execution or Test Failure in [read_file] (`TEST_FAILURE` - HIGH)
- **Опис**: A verification command or test suite failed during execution.
- **Лог / Стек**: ```text
{"content": "1|#!/bin/bash\n2|# --- DNK-MRH-HEADER ---\n3|# mrh_id: \"scripts/system/gerych.sh\"\n4|# purpose: \"Canonical launcher for Gerych Hermes Agent runtime with Process Lock, Proactive Auth, and Path Hygiene.\"\n5|# canonical_source: true\n6|# alters_files: []\n7|# triggers_tasks: []\n8|# st
```
- **Пропоноване лікування**: Diagnose test failure via error distiller and apply atomic code fix.
- **Цільові файли**: N/A

### ⚠️ 2. Read Loop Detected on: gerych.sh (`TOOL_LOOP` - MEDIUM)
- **Опис**: File scripts/system/gerych.sh was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: scripts/system/gerych.sh (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `scripts/system/gerych.sh`

### ⚠️ 3. Read Loop Detected on: session_sentinel.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File core/orchestrator/session_sentinel.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: core/orchestrator/session_sentinel.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `core/orchestrator/session_sentinel.py`

### ⚠️ 4. Read Loop Detected on: hermes_pre_tool_hook.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File scripts/system/hermes_pre_tool_hook.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: scripts/system/hermes_pre_tool_hook.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `scripts/system/hermes_pre_tool_hook.py`

### ⚠️ 5. Unverified File Modification Churn: gerych.sh (`TOOL_LOOP` - MEDIUM)
- **Опис**: File scripts/system/gerych.sh was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: scripts/system/gerych.sh (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `scripts/system/gerych.sh`

### ⚠️ 6. Tool Execution or Test Failure in [terminal] (`TEST_FAILURE` - HIGH)
- **Опис**: A verification command or test suite failed during execution.
- **Лог / Стек**: ```text
{"output": "diff --git a/scripts/system/gerych.sh b/scripts/system/gerych.sh\nindex c8b2a32c56..26f5c5ca2d 100755\n--- a/scripts/system/gerych.sh\n+++ b/scripts/system/gerych.sh\n@@ -6,8 +6,8 @@\n # alters_files: []\n # triggers_tasks: []\n # status: \"Active\"\n-# version: \"2.0.1\"\n-# updated_at:
```
- **Пропоноване лікування**: Diagnose test failure via error distiller and apply atomic code fix.
- **Цільові файли**: N/A

### ⚠️ 7. MASE Tool Budget Breached (56 > 25 calls) (`BUDGET_BREACH` - HIGH)
- **Опис**: Task executed with 56 tool calls, exceeding the atomic slice limit of 25 calls.
- **Лог / Стек**: ```text
Total tool calls: 56
```
- **Пропоноване лікування**: Decompose task into smaller atomic slices using task_spec_generator or zero_waste_slicer.
- **Цільові файли**: `AGENTS.md`

### ⚠️ 8. Missing AST Fast-Path: Repeated search_files instead of dnk_resolve_symbol (`TOOL_LOOP` - MEDIUM)
- **Опис**: Agent performed 21 search_files calls without utilizing dnk_resolve_symbol (<20ms pre-indexed AST cache).
- **Лог / Стек**: ```text
Total search_files calls: 21, dnk_resolve_symbol calls: 0
```
- **Пропоноване лікування**: Invoke dnk_resolve_symbol(symbol=...) for sub-20ms AST symbol resolution instead of scanning files on disk.
- **Цільові файли**: N/A

---

## 🗺️ 2. Targeted File Manifest

| Дія | Відносний шлях | Відповідальність та ключові сутності |
| :--- | :--- | :--- |
| `[MODIFY]` | `AGENTS.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/orchestrator/session_sentinel.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `scripts/system/gerych.sh` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `scripts/system/hermes_pre_tool_hook.py` | Системне виправлення дефекту та підвищення стійкості |

---

## 🧩 3. Mandatory Atomic Slices (MASE)

### 🔹 Slice 1: Core System Patching
- **Ціль**: Усунути кореневу причину помилки в цільових модулях, збільшити ліміти токенів або додати безпечний fallback.
- **Цільові файли**: `AGENTS.md, core/orchestrator/session_sentinel.py, scripts/system/gerych.sh, scripts/system/hermes_pre_tool_hook.py`
- **Команда перевірки**:
  ```bash
  .venv/bin/pytest tests/verification/test_*.py -v
  ```
- **Бюджет**: ≤ 12 tool calls.

### 🔹 Slice 2: Evidence & SCONES Memory Confirmation
- **Ціль**: Перевірити відсутність регресій та оновити базу уроків.
- **Команда перевірки**:
  ```bash
  python3 scripts/system/session_sentinel.py --audit-latest
  ```
- **Бюджет**: ≤ 5 tool calls.

---

## ✅ 4. Definition of Done (DoD)

- [ ] Всі виявлені аномалії усунуто в коді цільових файлів.
- [ ] 0 абсолютних шляхів у змінених файлах.
- [ ] Тести проходять на 100% Green.
- [ ] Звіт передано ментору Antigravity та зафіксовано в git.
