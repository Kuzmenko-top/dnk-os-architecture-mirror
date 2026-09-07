<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plans/self_heal/TASK-DNK-SELFHEAL-20260907-001043.md"
# purpose: "Автономна задача самолікування системи (Self-Healing) після сесії 20260906_172052_5dcd93."
# canonical_source: true
# alters_files: ["AGENTS.md", "core/hermes_agent/plugins/model-providers/vertex/__init__.py", "services/dnk_node_tasks/conversational_intake.py", "tests/verification/test_node_tasks_router.py"]
# triggers_tasks: []
# status: "Active"
# version: "2.5.0"
# updated_at: "2026-09-07"
# author: "Session Sentinel (Shadow Auditor) & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---
-->

# 🏥 САМОЛІКУВАННЯ СИСТЕМИ: Read Loop Detected on: test_node_tasks_router.py

> **Автономна детекція від Session Sentinel (`gerych_auditor`)**
> Під час виконання сесії `20260906_172052_5dcd93` виявлено 6 критичних або алгоритмічних дефектів.
> Ця задача призначена для агента-розробника ядра (`dnk_dev_fullstack`), щоб відновити 100% стабільність системи та запобігти повторенню дефектів.

---

## 🎯 Task Header & Metadata

- **Task ID**: `TASK-DNK-SELFHEAL-20260907-001043`
- **Title**: `[Self-Heal] Read Loop Detected on: test_node_tasks_router.py`
- **Domain / Bounded Context**: `apps/api`
- **Primary Executor**: `dnk_dev_fullstack` (System Doctor & Fullstack Lead)
- **Collaborating Swarm Agents**: `gerych_auditor`, `dnk_scones_memory`
- **Execution Mode**: `MUTATION (Core System & Algorithm Patching)`
- **Estimated Complexity**: `P1 High`
- **Origin Session ID**: `20260906_172052_5dcd93`
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

### ⚠️ 1. Read Loop Detected on: test_node_tasks_router.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File tests/verification/test_node_tasks_router.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: tests/verification/test_node_tasks_router.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `tests/verification/test_node_tasks_router.py`

### ⚠️ 2. API Authentication Failure (HTTP 401 / Invalid Credentials) (`AUTH_ERROR` - CRITICAL)
- **Опис**: The agent encountered an authentication failure when invoking auxiliary or primary models.
- **Лог / Стек**: ```text
{"content": "240|    assert task_file.exists()\n241|\n242|    content = task_file.read_text(encoding=\"utf-8\")\n243|    assert \"DNK-MRH-HEADER\" in content\n244|    assert \"dnk_dev_fullstack\" in content\n245|    assert \"HTTP 401\" in content\n246|\n247|    # Test Canvas Enqueueing\n248|    node
```
- **Пропоноване лікування**: Rotate or re-authenticate credentials in ~/.hermes/config.yaml or refresh environment token.
- **Цільові файли**: `core/hermes_agent/plugins/model-providers/vertex/__init__.py`, `~/.hermes/config.yaml`

### ⚠️ 3. Read Loop Detected on: conversational_intake.py (`TOOL_LOOP` - MEDIUM)
- **Опис**: File services/dnk_node_tasks/conversational_intake.py was read 3 times consecutively without modifications.
- **Лог / Стек**: ```text
File: services/dnk_node_tasks/conversational_intake.py (Consecutive read count: 3)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `services/dnk_node_tasks/conversational_intake.py`

### ⚠️ 4. Error Loop: Repeated 'nConnectionResetError' Without Distillation (`ERROR_LOOP` - HIGH)
- **Опис**: Error pattern 'nConnectionResetError' occurred consecutively without querying error solutions database.
- **Лог / Стек**: ```text
{"output": "Traceback (most recent call last):\n  File \"<string>\", line 7, in <module>\n    resp = urllib.request.urlopen(req)\n  File \"$HOME/.local/share/uv/python/cpython-3.14.4-macos-aarch64-none/lib/python3.14/urllib/request.py\"
```
- **Пропоноване лікування**: Query dnk_query_error_solutions(error_text='nConnectionResetError') immediately instead of repeated trial-and-error.
- **Цільові файли**: N/A

### ⚠️ 5. MASE Tool Budget Breached (166 > 25 calls) (`BUDGET_BREACH` - HIGH)
- **Опис**: Task executed with 166 tool calls, exceeding the atomic slice limit of 25 calls.
- **Лог / Стек**: ```text
Total tool calls: 166
```
- **Пропоноване лікування**: Decompose task into smaller atomic slices using task_spec_generator or zero_waste_slicer.
- **Цільові файли**: `AGENTS.md`

### ⚠️ 6. Missing AST Fast-Path: Repeated search_files instead of dnk_resolve_symbol (`TOOL_LOOP` - MEDIUM)
- **Опис**: Agent performed 34 search_files calls without utilizing dnk_resolve_symbol (<20ms pre-indexed AST cache).
- **Лог / Стек**: ```text
Total search_files calls: 34, dnk_resolve_symbol calls: 0
```
- **Пропоноване лікування**: Invoke dnk_resolve_symbol(symbol=...) for sub-20ms AST symbol resolution instead of scanning files on disk.
- **Цільові файли**: N/A

---

## 🗺️ 2. Targeted File Manifest

| Дія | Відносний шлях | Відповідальність та ключові сутності |
| :--- | :--- | :--- |
| `[MODIFY]` | `AGENTS.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `core/hermes_agent/plugins/model-providers/vertex/__init__.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `services/dnk_node_tasks/conversational_intake.py` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `tests/verification/test_node_tasks_router.py` | Системне виправлення дефекту та підвищення стійкості |

---

## 🧩 3. Mandatory Atomic Slices (MASE)

### 🔹 Slice 1: Core System Patching
- **Ціль**: Усунути кореневу причину помилки в цільових модулях, збільшити ліміти токенів або додати безпечний fallback.
- **Цільові файли**: `AGENTS.md, core/hermes_agent/plugins/model-providers/vertex/__init__.py, services/dnk_node_tasks/conversational_intake.py, tests/verification/test_node_tasks_router.py`
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
