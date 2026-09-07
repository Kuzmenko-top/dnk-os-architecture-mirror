<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plans/self_heal/TASK-DNK-SELFHEAL-20260907-143222.md"
# purpose: "Автономна задача самолікування системи (Self-Healing) після сесії 20260907_135735_9d37dc."
# canonical_source: true
# alters_files: ["AGENTS.md"]
# triggers_tasks: []
# status: "Active"
# version: "2.5.0"
# updated_at: "2026-09-07"
# author: "Session Sentinel (Shadow Auditor) & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---
-->

# 🏥 САМОЛІКУВАННЯ СИСТЕМИ: Absolute Path Invariant Violation (/Users/...)

> **Автономна детекція від Session Sentinel (`gerych_auditor`)**
> Під час виконання сесії `20260907_135735_9d37dc` виявлено 1 критичних або алгоритмічних дефектів.
> Ця задача призначена для агента-розробника ядра (`dnk_dev_fullstack`), щоб відновити 100% стабільність системи та запобігти повторенню дефектів.

---

## 🎯 Task Header & Metadata

- **Task ID**: `TASK-DNK-SELFHEAL-20260907-143222`
- **Title**: `[Self-Heal] Absolute Path Invariant Violation (/Users/...)`
- **Domain / Bounded Context**: `core/hermes_agent`
- **Primary Executor**: `dnk_dev_fullstack` (System Doctor & Fullstack Lead)
- **Collaborating Swarm Agents**: `gerych_auditor`, `dnk_scones_memory`
- **Execution Mode**: `MUTATION (Core System & Algorithm Patching)`
- **Estimated Complexity**: `P1 High`
- **Origin Session ID**: `20260907_135735_9d37dc`
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

### ⚠️ 1. Absolute Path Invariant Violation (/Users/...) (`PATH_VIOLATION` - HIGH)
- **Опис**: Agent passed an absolute system path in tool arguments instead of mandatory relative path.
- **Лог / Стек**: ```text
{"content": "---\nid: \"075\"\ntitle: \"Gerych as Chief Developer Agent: Human & Mentor Deep-Dive, Capabilities, and Infrastructure Synergy Audit\"\ndate: 2026-09-07\ntags:\n  - \"#architecture\"\n  - \"#chief-developer\"\n  - \"#hermes-agent\"\n  -
```
- **Пропоноване лікування**: Enforce relative path sanitization (./ or ../) before dispatching tool calls.
- **Цільові файли**: `AGENTS.md`

---

## 🗺️ 2. Targeted File Manifest

| Дія | Відносний шлях | Відповідальність та ключові сутності |
| :--- | :--- | :--- |
| `[MODIFY]` | `AGENTS.md` | Системне виправлення дефекту та підвищення стійкості |

---

## 🧩 3. Mandatory Atomic Slices (MASE)

### 🔹 Slice 1: Core System Patching
- **Ціль**: Усунути кореневу причину помилки в цільових модулях, збільшити ліміти токенів або додати безпечний fallback.
- **Цільові файли**: `AGENTS.md`
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
