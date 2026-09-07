<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plans/self_heal/TASK-DNK-SELFHEAL-20260907-001046.md"
# purpose: "Автономна задача самолікування системи (Self-Healing) після сесії bg_181029_83211a."
# canonical_source: true
# alters_files: ["AGENTS.md", "core/hermes_agent/agent/title_generator.py", "core/hermes_agent/plugins/model-providers/vertex/__init__.py", "core/hermes_agent/tools/dnk_swarm_tool.py", "core/orchestrator/session_sentinel.py", "core/orchestrator/swarm_coordinator.py", "docs/plans/self_heal/TASK-DNK-SELFHEAL-20260906-171819.md"]
# triggers_tasks: []
# status: "Active"
# version: "2.5.0"
# updated_at: "2026-09-07"
# author: "Session Sentinel (Shadow Auditor) & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---
-->

# 🏥 САМОЛІКУВАННЯ СИСТЕМИ: Tool Execution or Test Failure in [read_file]

> **Автономна детекція від Session Sentinel (`gerych_auditor`)**
> Під час виконання сесії `bg_181029_83211a` виявлено 16 критичних або алгоритмічних дефектів.
> Ця задача призначена для агента-розробника ядра (`dnk_dev_fullstack`), щоб відновити 100% стабільність системи та запобігти повторенню дефектів.

---

## 🎯 Task Header & Metadata

- **Task ID**: `TASK-DNK-SELFHEAL-20260907-001046`
- **Title**: `[Self-Heal] Tool Execution or Test Failure in [read_file]`
- **Domain / Bounded Context**: `core/hermes_agent`
- **Primary Executor**: `dnk_dev_fullstack` (System Doctor & Fullstack Lead)
- **Collaborating Swarm Agents**: `gerych_auditor`, `dnk_scones_memory`
- **Execution Mode**: `MUTATION (Core System & Algorithm Patching)`
- **Estimated Complexity**: `P1 High`
- **Origin Session ID**: `bg_181029_83211a`
- **Recursion Depth**: `2`

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
{"content": "1|<!--\n2|# --- DNK-MRH-HEADER ---\n3|# mrh_id: \"docs/plans/self_heal/TASK-DNK-SELFHEAL-20260906-171819.md\"\n4|# purpose: \"Автономна задача самолікування системи (Self-Healing) після сесії 20260906_170225_84c16b.\"\n5|# canonical_source: true\n6|# alters_files: [\"AGENTS.md\", \"apps
```
- **Пропоноване лікування**: Diagnose test failure via error distiller and apply atomic code fix.
- **Цільові файли**: N/A

### ⚠️ 2. Tool Execution or Test Failure in [session_search] (`TEST_FAILURE` - HIGH)
- **Опис**: A verification command or test suite failed during execution.
- **Лог / Стек**: ```text
{"success": true, "mode": "read", "session_id": "20260906_164224_3bb3fd", "link": "@session:default/20260906_164224_3bb3fd", "session_meta": {"when": "September 06, 2026 at 04:44 PM", "source": "cli", "model": "gemini-3.8-flash", "title": "Архітектор та аудит системи DNK_HUB"}, "message_count": 87,
```
- **Пропоноване лікування**: Diagnose test failure via error distiller and apply atomic code fix.
- **Цільові файли**: N/A

### ⚠️ 3. Read Loop Detected on: session_sentinel.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File core/orchestrator/session_sentinel.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: core/orchestrator/session_sentinel.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `core/orchestrator/session_sentinel.py`

### ⚠️ 4. Read Loop Detected on: swarm_coordinator.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File core/orchestrator/swarm_coordinator.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: core/orchestrator/swarm_coordinator.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `core/orchestrator/swarm_coordinator.py`

### ⚠️ 5. Read Loop Detected on: TASK-DNK-SELFHEAL-20260906-171819.md (`TOOL_LOOP` - MEDIUM)
- **Опис**: File docs/plans/self_heal/TASK-DNK-SELFHEAL-20260906-171819.md was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: docs/plans/self_heal/TASK-DNK-SELFHEAL-20260906-171819.md (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `docs/plans/self_heal/TASK-DNK-SELFHEAL-20260906-171819.md`

### ⚠️ 6. Read Loop Detected on: dnk_swarm_tool.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File core/hermes_agent/tools/dnk_swarm_tool.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: core/hermes_agent/tools/dnk_swarm_tool.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `core/hermes_agent/tools/dnk_swarm_tool.py`

### ⚠️ 7. Tool Execution or Test Failure in [terminal] (`TEST_FAILURE` - HIGH)
- **Опис**: A verification command or test suite failed during execution.
- **Лог / Стек**: ```text
[terminal] ran `./.venv/bin/python3 -c "from core.hermes_agent.tools.dnk_swarm_tool import dn...` -> exit 1, 1 lines output
```
- **Пропоноване лікування**: Diagnose test failure via error distiller and apply atomic code fix.
- **Цільові файли**: N/A

### ⚠️ 8. Error Loop: Repeated 'ValueError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'ValueError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"total_count": 40, "matches_format": "path-grouped: each file path on its own line, followed by indented '<line>: <content>' rows for matches in that file", "matches_text": "core/orchestrator/session_sentinel.py\n  1: # --- DNK-MRH-HEADER ---\n  2:
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='ValueError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 9. Unverified File Modification Churn: session_sentinel.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File core/orchestrator/session_sentinel.py was modified 3 times consecutively without running verification tests.
- **Лог / Стек**: ```text
File: core/orchestrator/session_sentinel.py (Unverified edits: 3)
```
- **Пропоноване лікування**: Plan complete changes in advance or run verification tests between modifications.
- **Цільові файли**: `core/orchestrator/session_sentinel.py`

### ⚠️ 10. Error Loop: Repeated 'OSError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'OSError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"total_count": 51, "matches_format": "path-grouped: each file path on its own line, followed by indented '<line>: <content>' rows for matches in that file", "matches_text": "scripts/system/session_sentinel.py\n  17: import signal\n  18: import argpa
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='OSError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 11. API Authentication Failure (HTTP 401 / Invalid Credentials) (`AUTH_ERROR` - CRITICAL)
- **Опис**: The agent encountered an authentication failure when invoking auxiliary or primary models.
- **Лог / Стек**: ```text
{"content": "1|# --- DNK-MRH-HEADER ---\n2|# mrh_id: \"tests/verification/test_session_sentinel.py\"\n3|# purpose: \"Verification test suite for Session Sentinel (Shadow Observer & Self-Healing Loop).\"\n4|# canonical_source: true\n5|# alters_files: []\n6|# triggers_tasks: []\n7|# status: \"Active\"
```
- **Пропоноване лікування**: Rotate or re-authenticate credentials in ~/.hermes/config.yaml or refresh environment token.
- **Цільові файли**: `core/hermes_agent/plugins/model-providers/vertex/__init__.py`, `~/.hermes/config.yaml`

### ⚠️ 12. Auxiliary Model Output Exhaustion / NoneType Attribute Error (`MODEL_REASONING` - HIGH)
- **Опис**: Auxiliary call failed or returned empty content because reasoning model thought tokens exhausted max_tokens budget.
- **Лог / Стек**: ```text
{"content": "1|# --- DNK-MRH-HEADER ---\n2|# mrh_id: \"tests/verification/test_session_sentinel.py\"\n3|# purpose: \"Verification test suite for Session Sentinel (Shadow Observer & Self-Healing Loop).\"\n4|# canonical_source: true\n5|# alters_files: []\n6|# triggers_tasks: []\n7|# status: \"Active\"
```
- **Пропоноване лікування**: Increase max_tokens (e.g. to 1024) for reasoning models and use getattr(choice.message, 'content') fallback.
- **Цільові файли**: `core/hermes_agent/agent/title_generator.py`

### ⚠️ 13. Absolute Path Invariant Violation (/Users/...) (`PATH_VIOLATION` - HIGH)
- **Опис**: Agent passed an absolute system path in tool arguments instead of mandatory relative path.
- **Лог / Стек**: ```text
{"mode": "replace", "new_string": "        # Construct markdown content adhering to GERYCH_TASK_TEMPLATE.md v2.5\n        anomalies_summary = \"\\n\\n\".join([\n            f\"### ⚠️ {i+1}. {a.title} (`{a.category.value}` - {a.severity.value})\\n\"\n
```
- **Пропоноване лікування**: Enforce relative path sanitization (./ or ../) before dispatching tool calls.
- **Цільові файли**: `AGENTS.md`

### ⚠️ 14. Error Loop: Repeated 'AssertionError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'AssertionError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"output": "============================= test session starts ==============================\nplatform darwin -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0 -- $HOME/Kuzmenko/MY_LIFE_WORK/DNK_HUB/.venv/bin/python3\ncachedir: .pytest_cache
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='AssertionError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 15. MASE Tool Budget Breached (332 > 25 calls) (`BUDGET_BREACH` - HIGH)
- **Опис**: Task executed with 332 tool calls, exceeding the atomic slice limit of 25 calls.
- **Лог / Стек**: ```text
Total tool calls: 332
```
- **Пропоноване лікування**: Decompose task into smaller atomic slices using task_spec_generator or zero_waste_slicer.
- **Цільові файли**: `AGENTS.md`

### ⚠️ 16. Missing AST Fast-Path: Repeated search_files instead of dnk_resolve_symbol (`TOOL_LOOP` - MEDIUM)
- **Опис**: Agent performed 163 search_files calls without utilizing dnk_resolve_symbol (<20ms pre-indexed AST cache).
- **Лог / Стек**: ```text
Total search_files calls: 163, dnk_resolve_symbol calls: 0
```
- **Пропоноване лікування**: Invoke dnk_resolve_symbol(symbol=...) for sub-20ms AST symbol resolution instead of scanning files on disk.
- **Цільові файли**: N/A

---

## 🗺️ 2. Targeted File Manifest

| Дія | Відносний шлях | Відповідальність та ключові сутності |
| :--- | :--- | :--- |
| `[MODIFY]` | `AGENTS.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/hermes_agent/agent/title_generator.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/hermes_agent/plugins/model-providers/vertex/__init__.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/hermes_agent/tools/dnk_swarm_tool.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/orchestrator/session_sentinel.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/orchestrator/swarm_coordinator.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `docs/plans/self_heal/TASK-DNK-SELFHEAL-20260906-171819.md` | Системне виправлення дефекту та підвищення стійкості |

---

## 🧩 3. Mandatory Atomic Slices (MASE)

### 🔹 Slice 1: Core System Patching
- **Ціль**: Усунути кореневу причину помилки в цільових модулях, збільшити ліміти токенів або додати безпечний fallback.
- **Цільові файли**: `AGENTS.md, core/hermes_agent/agent/title_generator.py, core/hermes_agent/plugins/model-providers/vertex/__init__.py, core/hermes_agent/tools/dnk_swarm_tool.py, core/orchestrator/session_sentinel.py, core/orchestrator/swarm_coordinator.py, docs/plans/self_heal/TASK-DNK-SELFHEAL-20260906-171819.md`
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
