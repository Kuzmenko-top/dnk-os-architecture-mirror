---
mrh_id: "docs/notes/014 Auto-Task-Spec Generation Protocol.md"
title: "014 Auto-Task-Spec Generation Protocol & MASE Interceptor"
date: "2026-09-05"
author: "DNK-e.com Maksym & Gerych Prime"
tags:
  - architecture
  - orchestrator
  - gerych-prime
  - mase
  - zero-waste
  - hooks
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/014 Auto-Task-Spec Generation Protocol.md"
purpose: "Documentation of the Auto-Task-Spec Generation Engine and Pre-Tool Hook Interceptor for DNK OS v2.5."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🎯 014 Auto-Task-Spec Generation Protocol & MASE Interceptor

## 📌 Огляд та Проблема
Раніше при отриманні вільних запитів природною мовою (наприклад: *"Герич, зроби аудит архітектури та знайди кращі open-source рішення..."*) виникали наступні ризики:
- ❌ Відсутність чіткого переліку цільових файлів (scope drift)
- ❌ Відсутність ліміту викликів інструментів (budget exhaustion 90/90)
- ❌ Відсутність зафіксованого Definition of Done (DoD)
- ❌ Ризик порушення правила [[012 Mandatory Atomic Slice Execution (MASE)]]

## 🏗️ Архітектура Рішення

```
┌─────────────────────────────────────────────────────────────┐
│                    User Natural Query                       │
│  "Герич, зроби аудит архітектури..."                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│          core/orchestrator/task_spec_generator.py           │
│                                                             │
│  1. should_auto_spec(query) -> bool                         │
│     - Фільтрація чистого діалогу та вже валідних спек      │
│     - Детектування дієслів дії (ua/en)                      │
│                                                             │
│  2. dnk_triage_task(query)                                  │
│     - Розрахунок C = F + 2D + 3S                            │
│     - Визначення режиму: SOLO vs SWARM_PARALLEL            │
│     - Витягування або синтез цільових файлів               │
│                                                             │
│  3. auto_generate_task_spec(...)                            │
│     - Авто-інкремент мікрослайсу (напр. 13.2)               │
│     - Формування специфікації за GERYCH_TASK_TEMPLATE v2.5  │
│     - Збереження у .hermes/active_task_spec.md              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              scripts/system/hermes_pre_tool_hook.py         │
│  - Інтеграція з хуками виклику інструментів                 │
│  - Кешування у трекері сесії active_task_spec               │
│  - Контроль за дотриманням Strict Dispatch Law              │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Компоненти Системи

1. **`core/orchestrator/task_spec_generator.py`**:
   - `should_auto_spec(user_query: str) -> bool`: Перевіряє, чи запит потребує структурування (виключає чисті запитання/привітання та вже оформлені спеки).
   - `get_next_slice_number() -> str`: Автоматично визначає наступний номер слайсу на основі останніх git комітів репозиторію.
   - `extract_task_title(user_query: str) -> str`: Витягує лаконічний заголовок задачі, очищуючи звернення.
   - `auto_generate_task_spec(...)`: Формує повний Markdown Task Spec v2.5 з усіма обов'язковими блоками.

2. **`scripts/system/auto_task_spec.py`**:
   - Автономна CLI-утиліта для розробників, агентів та зовнішніх пайплайнів.
   - Підтримує прапорці `--check`, `--json`, `--slice <id>`, `--output <path>`.

3. **`scripts/system/hermes_pre_tool_hook.py`**:
   - При виклику `dnk_triage_task` автоматично генерує та кешує специфікацію в активному трекері сесії.

## 🔍 Валідація
Покриття тестами:
- `tests/core/test_task_spec_generator.py` (7/7 passed)
- `tests/core/test_task_triage.py` (10/10 passed)
- `tests/verification/test_swarm_delegation_guard.py` (5/5 passed)
- `tests/verification/test_completion_gate_hook.py` (8/8 passed)
Разом 30/30 тестів (100% Green).
