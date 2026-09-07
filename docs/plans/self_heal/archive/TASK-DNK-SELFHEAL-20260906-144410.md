<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plans/self_heal/TASK-DNK-SELFHEAL-20260906-144410.md"
# purpose: "Автономна задача самолікування системи (Self-Healing) після сесії 22cb06b2-4776-4218-b14d-893b74faaa36."
# canonical_source: true
# alters_files: ["smokehouse-hero-banner.html"]
# triggers_tasks: []
# status: "Active"
# version: "2.5.0"
# updated_at: "2026-09-06"
# author: "Session Sentinel (Shadow Auditor) & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---
-->

# 🏥 САМОЛІКУВАННЯ СИСТЕМИ: Read Loop Detected on: smokehouse-hero-banner.html

> **Автономна детекція від Session Sentinel (`gerych_auditor`)**
> Під час виконання сесії `22cb06b2-4776-4218-b14d-893b74faaa36` виявлено 1 критичних або алгоритмічних дефектів.
> Ця задача призначена для агента-розробника ядра (`dnk_dev_fullstack`), щоб відновити 100% стабільність системи та запобігти повторенню дефектів.

---

## 🎯 Task Header & Metadata

- **Task ID**: `TASK-DNK-SELFHEAL-20260906-144410`
- **Title**: `[Self-Heal] Read Loop Detected on: smokehouse-hero-banner.html`
- **Domain / Bounded Context**: `core/hermes_agent`
- **Primary Executor**: `dnk_dev_fullstack` (System Doctor & Fullstack Lead)
- **Collaborating Swarm Agents**: `gerych_auditor`, `dnk_scones_memory`
- **Execution Mode**: `MUTATION (Core System & Algorithm Patching)`
- **Estimated Complexity**: `P1 High`
- **Origin Session ID**: `22cb06b2-4776-4218-b14d-893b74faaa36`

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

### ⚠️ 1. Read Loop Detected on: smokehouse-hero-banner.html (`TOOL_LOOP` - MEDIUM)
- **Опис**: File smokehouse-hero-banner.html was read 4 times consecutively without modifications.
- **Лог / Стек**: ```text
File: smokehouse-hero-banner.html (Consecutive read count: 4)
```
- **Пропоноване лікування**: Cache file content in working memory or force test/action slice instead of repeated reads.
- **Цільові файли**: `smokehouse-hero-banner.html`

---

## 🗺️ 2. Targeted File Manifest

| Дія | Відносний шлях | Відповідальність та ключові сутності |
| :--- | :--- | :--- |
| `[MODIFY]` | `smokehouse-hero-banner.html` | Системне виправлення дефекту та підвищення стійкості |

---

## 🧩 3. Mandatory Atomic Slices (MASE)

### 🔹 Slice 1: Core System Patching
- **Ціль**: Усунути кореневу причину помилки в цільових модулях, збільшити ліміти токенів або додати безпечний fallback.
- **Цільові файли**: `smokehouse-hero-banner.html`
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
