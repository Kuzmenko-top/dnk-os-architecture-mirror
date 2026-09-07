---
id: flower_18_langgraph_runtime_adapter
title: "🌸 Квітка 18: LangGraph Runtime Adapter"
type: task_flower
plant_scale: flower
parent_id: bush_self_improving_swarm_engine
status: completed
verification_status: passed
tags:
  - dnk-task-forest
  - dnk-task-flower
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_18_LangGraph_Runtime_Adapter.md"
# purpose: "Task Flower tracking LangGraph adapter, checkpointers and self-healing loop implementation"
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# plant_scale: "flower"
# --- END DNK-MRH-HEADER ---

# 🌸 Квітка 18: LangGraph Runtime Adapter & Multi-Agent Checkpointer

## 📋 Опис завдання
Розробка та інтеграція адаптера для запуску стейтфул-графів LangGraph з підтримкою версіонування станів (Checkpointers), людино-оркестрованих переривань (Human Interrupts) та самовідновлювальних контурів (Adaptive Self-Healing) на базі вивчення workarounds.

## 🏁 Чек-лист реалізації (Checklist)
- [x] **GraphRuntimeProtocol**: Описано стабільну схему життєвого циклу графа (`start`, `checkpoint`, `interrupt`, `resume`, `success`, `failure`) та контракт `DNKGraphState`.
- [x] **LangGraphAdapter**: Створено гнучкий `DNKLangGraphAdapter` в `core/adapters/dnk_langgraph_adapter.py`.
- [x] **CheckpointerPort**: Спроектовано абстрактний порт checkpointer з вбудованими перевірками ізоляції воркспейсів.
- [x] **InMemory & File Checkpointer**: Створено `InMemoryCheckpointer` для ізольованого тестування та `FileCheckpointer` для персистентного зберігання.
- [x] **Adaptive Recoveries**: Інтегровано контур людино-оркестрованого переривання (`before_` та `after_` вузли) та повного відновлення через `resume`.
- [x] **Error Distillation Injection**: У разі падіння будь-якої ноди адаптер викликає `ErrorDistiller` (з Квітки 17), класифікує збій та вбудовує інструменти самолікування у наступні спроби запуску.
- [x] **Unit & E2E Testing**: Розроблено 12 тестів (включаючи E2E контур збоїв та самовідновлення) у `tests/verification/test_langgraph_adapter.py` (100% успіху).
- [x] **Task Forest & Docs**: Оновлено документи квіток, кущів та секторів.
