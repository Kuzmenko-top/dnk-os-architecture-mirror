<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plans/self_heal/TASK-DNK-SELFHEAL-20260906-171819.md"
# purpose: "Автономна задача самолікування системи (Self-Healing) після сесії 20260906_170225_84c16b."
# canonical_source: true
# alters_files: ["AGENTS.md", "apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx"]
# triggers_tasks: []
# status: "Active"
# version: "2.5.0"
# updated_at: "2026-09-06"
# author: "Session Sentinel (Shadow Auditor) & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---
-->

# 🏥 САМОЛІКУВАННЯ СИСТЕМИ: Read Loop Detected on: NodeTaskMarketingVideoViewer.tsx

> **Автономна детекція від Session Sentinel (`gerych_auditor`)**
> Під час виконання сесії `20260906_170225_84c16b` виявлено 3 критичних або алгоритмічних дефектів.
> Ця задача призначена для агента-розробника ядра (`dnk_dev_fullstack`), щоб відновити 100% стабільність системи та запобігти повторенню дефектів.

---

## 🎯 Task Header & Metadata

- **Task ID**: `TASK-DNK-SELFHEAL-20260906-171819`
- **Title**: `[Self-Heal] Read Loop Detected on: NodeTaskMarketingVideoViewer.tsx`
- **Domain / Bounded Context**: `apps/web`
- **Primary Executor**: `dnk_dev_fullstack` (System Doctor & Fullstack Lead)
- **Collaborating Swarm Agents**: `gerych_auditor`, `dnk_scones_memory`
- **Execution Mode**: `MUTATION (Core System & Algorithm Patching)`
- **Estimated Complexity**: `P1 High`
- **Origin Session ID**: `20260906_170225_84c16b`

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

### ⚠️ 1. Read Loop Detected on: NodeTaskMarketingVideoViewer.tsx (`TOOL_LOOP` - MEDIUM)
- **Опис**: File apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx was read 4 times consecutively without modifications.
- **Лог / Стек**: ```text
File: apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx (Consecutive read count: 4)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx`

### ⚠️ 2. Tool Execution or Test Failure in [terminal] (`TEST_FAILURE` - HIGH)
- **Опис**: A verification command or test suite failed during execution.
- **Лог / Стек**: ```text
[terminal] ran `./apps/web/node_modules/.bin/tsc --noEmit --project apps/web/tsconfig.json` -> exit 2, 1 lines output
```
- **Пропоноване лікування**: Diagnose test failure via error distiller and apply atomic code fix.
- **Цільові файли**: N/A

### ⚠️ 3. MASE Tool Budget Breached (178 > 25 calls) (`BUDGET_BREACH` - HIGH)
- **Опис**: Task executed with 178 tool calls, exceeding the atomic slice limit of 25 calls.
- **Лог / Стек**: ```text
Total tool calls: 178
```
- **Пропоноване лікування**: Decompose task into smaller atomic slices using task_spec_generator or zero_waste_slicer.
- **Цільові файли**: `AGENTS.md`

---

## 🗺️ 2. Targeted File Manifest

| Дія | Відносний шлях | Відповідальність та ключові сутності |
| :--- | :--- | :--- |
| `[MODIFY]` | `AGENTS.md` | Системне виправлення дефекту та підвищення стійкості |
| `[MODIFY]` | `apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx` | Системне виправлення дефекту та підвищення стійкості |

---

## 🧩 3. Mandatory Atomic Slices (MASE)

### 🔹 Slice 1: Core System Patching
- **Ціль**: Усунути кореневу причину помилки в цільових модулях, збільшити ліміти токенів або додати безпечний fallback.
- **Цільові файли**: `AGENTS.md, apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx`
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
