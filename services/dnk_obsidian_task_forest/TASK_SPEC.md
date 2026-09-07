---
task_id: DNK-TASK-OBSIDIAN-FOREST-01
file_name: TASK_SPEC.md
title: 🌻 Завдання для Герича: Реалізація Open-Source Сервісу `dnk_obsidian_task_forest`
assignee: Hermes (Gerych Executable Subagent)
supervisor: Antigravity (Lead Architect & Mentor)
status: Ready for Execution
created_at: 2026-08-07
---

# 🌻 Специфікація Завдання: Open-Source Сервіс `dnk_obsidian_task_forest`

## 📋 Опис Завдання
Створити новий автономний сервіс `dnk_obsidian_task_forest` у каталозі `services/dnk_obsidian_task_forest`.

Сервіс надає можливість користувачам Obsidian вести свої проєкти у вигляді метафори "Саду та Лісу":
1. **🌾 Поле (Project Field)** — корінь проєкту.
2. **🏞️ Сектори (Sector Zones)** — напрямки розробки (Design, Core, Marketing).
3. **🌳 Дерева (Epic Trees)** — масштабні епічні задачі.
4. **🌿 Кущі (Feature Bushes)** — задачі фіч.
5. **🌱 Квіточки (Task Flowers)** — атомарні мікро-підзадачі (1-4 години).

---

## 🎯 Кроки Виконання для Герича

1. **Створення папочної структури**:
   - `services/dnk_obsidian_task_forest/templates/`
   - `services/dnk_obsidian_task_forest/src/`
   - `services/dnk_obsidian_task_forest/tests/`

2. **Створення шаблонів Obsidian**:
   - `Project_Field_Template.md`
   - `Sector_Zone_Template.md`
   - `Epic_Tree_Template.md`
   - `Feature_Bush_Template.md`
   - `Task_Flower_Template.md`

3. **Створення модуля `src/obsidian_task_forest.py`**:
   - Сканування нотаток Obsidian з YAML-фронтматером.
   - Побудова графа та розрахунок прогресу % знизу вгору (Bottom-Up Rollup).
   - Метод `to_mermaid(direction="BT")` з іконками рослин (`🌾`, `🏞️`, `🌳`, `🌿`, `🌱`, `✅`).

4. **Створення юніт-тестів `tests/test_obsidian_task_forest.py`**:
   - Покрити 100% тестів на сканування, зв'язування нод та обчислення %.

5. **Тестування та перевірка**:
   - `uv run pytest services/dnk_obsidian_task_forest/tests/ -v`
