---
title: "068 Session Sentinel Phase 3: Autonomous Closed-Loop Self-Healing & Recursion Control"
aliases: ["Session Sentinel Phase 3", "Self-Healing Auto-Dispatch"]
tags: ["#architecture", "#sentinel", "#self-healing", "#swarm", "#circuit-breaker"]
created: "2026-09-06"
updated: "2026-09-06"
status: "Active"
author: "DNK-e.com Maksym & Gerych Prime"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/068_session_sentinel_phase3_autonomous_closed_loop.md"
purpose: "Architectural specification and design decisions for Session Sentinel Phase 3 Autonomous Closed-Loop Self-Healing with Swarm Auto-Dispatch and Recursion Control."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

F8 Session Sentinel Phase 3: Autonomous Closed-Loop Self-Healing & Recursion Control

## 📌 Огляд та мета

**Фаза 3** розширює систему моніторингу та діагностики сесій **Session Sentinel** (`core/orchestrator/session_sentinel.py` та `scripts/system/session_sentinel.py`), перетворюючи її з пасивного спостерігача (Shadow Observer) на **активний замкнений контур автономного самозцілення (Autonomous Closed-Loop Self-Healing)**.

У попередніх фазах (Фаза 1 та Фаза 2) Sentinel навчився:
1. Виявляти аномалії в режимі реального часу (`in-flight`) та пост-сесійно (помилки автентифікації, цикли читання, вичерпання лімітів інструментів, порушення абсолютних шляхів).
2. Синтезувати канонічні специфікації задач лікування (`docs/plans/self_heal/TASK-DNK-SELFHEAL-*.md` за стандартом v2.5).
3. Публікувати діагностичні вершини у візуальний DAG Canvas (`NodeTaskPersistenceManager`).

**Фаза 3** додає повністю автономний запуск виправлень без очікування ручного втручання людини, із залізним захистом від нескінченних рекурсивних циклів (Recursion Circuit Breaker).

---

## ⚙️ Архітектурні компоненти Фази 3

### 1. Прапорець `--auto-dispatch` та конфігурація
- Додано CLI-аргумент `--auto-dispatch` у `scripts/system/session_sentinel.py`.
- Додано прапорець глибини `--max-recursion-depth` (за замовчуванням `2`).
- Додано підтримку змінної оточення `DNK_SENTINEL_AUTO_DISPATCH=1` для безперервної фонової роботи у скриптах запуску.

### 2. Відстеження глибини рекурсії (`Lineage Tracking`)
Щоб запобігти каскадному самовідтворенню сесій у разі неможливості автоматичного виправлення дефекту:
- Створено механізм `get_session_recursion_depth(session_id)`:
  1. Перевіряє реєстр ліній сесій `data/self_heal_lineage.json`.
  2. Сканує вхідний промпт сесії на наявність маркерів: `[Self-Heal Autopilot Depth X/Y]` або `Recursion Depth: X`.
  3. Для кореневих сесій повертає `0`.
- Метод `record_lineage` атомарно зберігає зв'язки `parent_session_id -> task_id -> dispatched_depth -> agent` у `data/self_heal_lineage.json`.

### 3. Захисний автомат (Recursion Circuit Breaker)
- Якщо `current_depth >= max_recursion_depth`:
  - Автоматичний діспатч блокується (`status: blocked`, `dispatch_status: recursion_depth_exceeded`).
  - Генерується критична аномалія `AnomalyCategory.ERROR_LOOP` (`CRITICAL`), яка записується у `data/sentinel_alerts.json`.
  - Завдання ескалюється на людину або ментора Antigravity для ручного розбору першопричини дефекту.

### 4. Автономний запуск через Swarm (`dnk_swarm_dispatch`)
- Якщо ліміт не вичерпано (`current_depth < max_recursion_depth`):
  - Обчислюється `next_depth = current_depth + 1`.
  - Формується інструкція для виконавця `dnk_dev_fullstack` (System Doctor & Fullstack Lead).
  - Викликається `dnk_swarm_dispatch(agent="dnk_dev_fullstack", task_description=..., parameters=...)`.
  - У результаті аудиту фіксуються атрибути `dispatched_agent` та `dispatch_status`.

---

## 🧪 Верифікація та тестове покриття

Створено та верифіковано повний набір юніт-тестів у `tests/verification/test_session_sentinel.py`:
1. `test_recursion_depth_tracking`: перевірка розпізнавання глибини для кореневих сесій, сесій з текстовими маркерами та записів у lineage.
2. `test_auto_dispatch_self_healing_and_circuit_breaker`:
   - Успішний діспатч на глибині 0 -> перехід у глибину 1 із фіксацією у `self_heal_lineage.json`.
   - Спрацьовування Circuit Breaker при спробі виклику з `depth >= max_recursion_depth`.
   - Запис критичного алерту у `sentinel_alerts.json`.

Всі 13 тестів у `tests/verification/test_session_sentinel.py` виконуються зеленими за 0.25с.
Adversarial Review Gate та Preflight Sanitizer пройдені на 100%.

---

## 🔗 Пов'язані нотатки
- [[023 NodeTask Cabinet Architecture and Improvement Roadmap]]
- [[000 DNK HUB Index]]
- [[docs/templates/GERYCH_TASK_TEMPLATE.md]]
