---
id: flower_15_gerych_memory_system_transplant
title: "🌸 Квітка 15: Gerych Memory System Transplant & Integration"
type: task_flower
plant_scale: flower
parent_id: bush_self_improving_swarm_engine
status: completed
verification_status: completed
tags:
  - dnk-task-forest
  - dnk-task-flower
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_15_Gerych_Memory_System_Transplant.md"
# purpose: "Task Flower for transplanting Gerych's Memory System into DNK OS core"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# plant_scale: "flower"
# --- END DNK-MRH-HEADER ---

# 🌸 Квітка 15: Трансплантація та інтеграція системи пам'яті Герича в DNK OS MVP

## 📋 Опис завдання
Перенесення перевіреної системи пам'яті Герича (`MemoryManager`, `MemoryProvider` та плагінів) з робочого середовища `DNK_HUB/core/hermes_agent/agent/` у ядро `core/memory/` та її повна інтеграція з базою даних PostgreSQL (pgvector) та шаром SCONES.

Ця інтеграція вирішить проблему накопичення логів трасування та деградації RAG-контексту, забезпечуючи періодичну консолідацію знань під час циклів сну (Sleep Cycles) у чисті структуровані Chronicles (хроніки), що індексуються вектором у LTM (довготривалу пам'ять).

## 🏁 Чек-лист реалізації (Checklist)
- [x] **Копіювання архітектурних файлів**: Перенести `MemoryManager` та `MemoryProvider` з `DNK_HUB/core/hermes_agent/agent/` у `core/memory/` з коригуванням імпортів під архітектуру MVP.
- [x] **Портування плагінів пам'яті**: Перенести базові плагіни (наприклад, `mem0`, `honcho`, `hindsight`) з `DNK_HUB/core/hermes_agent/plugins/memory/` у `core/memory/plugins/`.
- [x] **Інтеграція з SCONES & pgvector**: Забезпечити зв'язок між `MemoryManager` та створеним раніше шаром `SCONESMemoryEngine` для автоматичного збереження та пошуку векторних ембеддінгів Chronicles через PostgreSQL.
- [x] **Автоматичний Sleep Cycle контур**: Написати/адаптувати фоновий скрипт стиснення логів трасування (`sleep_cycle_consolidation.py`) в `scripts/` для автоматичного очищення `agent_traces` кожні 24 години.
- [x] **Розробка модульних тестів**: Додати тести у `tests/` (наприклад, `test_memory_transplant.py`) для верифікації ініціалізації менеджеру, вибору провайдера та збереження Chronicles.
- [x] **TDD Верифікація**: Успішно запустити всі тести в ізольованому Docker-оточенні та переконатись у відсутності регресії ядра.
