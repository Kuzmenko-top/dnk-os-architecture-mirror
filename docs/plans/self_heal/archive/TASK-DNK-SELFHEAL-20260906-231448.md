<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plans/self_heal/TASK-DNK-SELFHEAL-20260906-231448.md"
# purpose: "Автономна задача самолікування системи (Self-Healing) після сесії 20260905_225623_4eddbc."
# canonical_source: true
# alters_files: ["AGENTS.md", "core/orchestrator/tools/stealth_browser_tool.py"]
# triggers_tasks: []
# status: "Completed"
# version: "2.5.0"
# updated_at: "2026-09-06"
# author: "Session Sentinel (Shadow Auditor) & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---
-->

# 🏥 САМОЛІКУВАННЯ СИСТЕМИ: Error Loop: Repeated 'RuntimeError' Without Distillation

> **Автономна детекція від Session Sentinel (`gerych_auditor`)**
> Під час виконання сесії `20260905_225623_4eddbc` виявлено 4 критичних або алгоритмічних дефектів.
> Ця задача призначена для агента-розробника ядра (`dnk_dev_fullstack`), щоб відновити 100% стабільність системи та запобігти повторенню дефектів.

---

## 🎯 Task Header & Metadata

- **Task ID**: `TASK-DNK-SELFHEAL-20260906-231448`
- **Title**: `[Self-Heal] Error Loop: Repeated 'RuntimeError' Without Distillation`
- **Domain / Bounded Context**: `core/hermes_agent`
- **Primary Executor**: `dnk_dev_fullstack` (System Doctor & Fullstack Lead)
- **Collaborating Swarm Agents**: `gerych_auditor`, `dnk_scones_memory`
- **Execution Mode**: `MUTATION (Core System & Algorithm Patching)`
- **Estimated Complexity**: `P1 High`
- **Origin Session ID**: `20260905_225623_4eddbc`
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

### ⚠️ 1. Error Loop: Repeated 'RuntimeError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'RuntimeError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"content": "121|        # Simulates zero-CDP globalThis evaluation without Runtime.enable\n122|        if expression == \"navigator.webdriver\":\n123|            return False\n124|        return f\"Evaluated: {expression}\"\n125|\n126|    def extrac
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='RuntimeError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 2. Unverified File Modification Churn: stealth_browser_tool.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File core/orchestrator/tools/stealth_browser_tool.py was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: core/orchestrator/tools/stealth_browser_tool.py (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `core/orchestrator/tools/stealth_browser_tool.py`

### ⚠️ 3. MASE Tool Budget Breached (91 > 25 calls) (`BUDGET_BREACH` - HIGH)
- **Опис**: Task executed with 91 tool calls, exceeding the atomic slice limit of 25 calls.
- **Лог / Стек**: ```text
Total tool calls: 91
```
- **Пропоноване лікування**: Decompose task into smaller atomic slices using task_spec_generator or zero_waste_slicer.
- **Цільові файли**: `AGENTS.md`

### ⚠️ 4. Missing AST Fast-Path: Repeated search_files instead of dnk_resolve_symbol (`TOOL_LOOP` - MEDIUM)
- **Опис**: Agent performed 10 search_files calls without utilizing dnk_resolve_symbol (<20ms pre-indexed AST cache).
- **Лог / Стек**: ```text
Total search_files calls: 10, dnk_resolve_symbol calls: 0
```
- **Пропоноване лікування**: Invoke dnk_resolve_symbol(symbol=...) for sub-20ms AST symbol resolution instead of scanning files on disk.
- **Цільові файли**: N/A

---

## 🗺️ 2. Targeted File Manifest

| Дія | Відносний шлях | Відповідальність та ключові сутності |
| :--- | :--- | :--- |
| `[MODIFY]` | `AGENTS.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/orchestrator/tools/stealth_browser_tool.py` | Системне виправлення дефекту та підвищення стійкості |

---

## 🧩 3. Mandatory Atomic Slices (MASE)

### 🔹 Slice 1: Core System Patching
- **Ціль**: Усунути кореневу причину помилки в цільових модулях, збільшити ліміти токенів або додати безпечний fallback.
- **Цільові файли**: `AGENTS.md, core/orchestrator/tools/stealth_browser_tool.py`
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

- [x] Всі виявлені аномалії усунуто в коді цільових файлів.
- [x] 0 абсолютних шляхів у змінених файлах.
- [x] Тести проходять на 100% Green (`tests/stealth/test_patchright_adapter.py` — 7 passed).
- [x] Рішення дистильовано в базу помилок (`dnk_record_error_solution`) та SCONES (`SCONES-MEM-1788725996593`).
- [x] Звіт передано ментору Antigravity та зафіксовано в git.
