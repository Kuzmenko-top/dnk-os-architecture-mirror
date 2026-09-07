# 🌸 Flower_01_implement_timeline_db.md: Реалізація таблиці та логера Timeline-моделі (PostgreSQL-First)

## 📋 Метадані
---
mrh_id: "docs/tasks/Sector_03_UI/Tree_01_Timeline/Bush_01_Logger/Flower_01_implement_timeline_db.md"
author: "Maxim"
license: "DNK-INTERNAL"
source_type: "competitor_observation"
source_reference: "crewai/001-crewai-dashboard.png"
derivative_status: "adapted"
status: "GO"
version: "1.0.0"
created_at: "2026-08-11"
---

## 🎯 Мета (Purpose)
Створити централізовану структуру даних та логер для побудови єдиного таймлайну подій роботи всіх субагентів у системі DNK OS на базі PostgreSQL (з підтримкою SQLite виключно як локального тест-адаптера).

## 📝 Критерії Приймання (Acceptance Criteria) - Definition of Done (DoD)
- [ ] **PostgreSQL Migration:** Створено SQL-міграцію для таблиці `agent_timeline` зі структурою:
  * `id` (UUID, primary key)
  * `run_id` (UUID, indexed) - унікальний ідентифікатор запуску
  * `agent_id` (VARCHAR, indexed) - назва субагента
  * `event_type` (VARCHAR) - тип події (наприклад, `task_start`, `task_end`, `error`, `approval_request`)
  * `status` (VARCHAR) - стан виконання (`pending`, `running`, `completed`, `failed`)
  * `payload_json` (JSONB) - метадані події з обов'язковим очищенням від секретів та API-ключів
  * `idempotency_key` (VARCHAR, unique) - ключ ідемпотентності для уникнення дублів
  * `timestamp` (TIMESTAMP WITH TIME ZONE, default NOW(), indexed)
- [ ] **Repository Interface:** Створено інтерфейс-абстракцію `ITimelineRepository` та його конкретну PostgreSQL-реалізацію (а також SQLite-реалізацію виключно для ручного тестування/development-режиму).
- [ ] **Timeline Logger:** Клас `TimelineLogger` у файлі `core/utils/timeline_logger.py` з методами `log_action_start` та `log_action_end`.
- [ ] **Sanitization:** Вбудовано автоматичне очищення/маскування паролів, токенів та секретів всередині `payload_json` перед записом у БД.
- [ ] **Concurrency Tests:** Написано тести паралельного запису (`concurrent-write tests`) та автоматичного ретраю при тимчасових втратах зв'язку з базою (retry logic).

## 💡 Джерело Ідеї (Idea Source)
Адаптовано з CrewAI Enterprise Dashboard (детальні лог-трейси виконання кроків).
* Докладний аналіз: `docs/research/competitors/crewai_analysis.md` (screen_001)
* Продуктовий інсайт: `docs/research/competitors/insights/INSIGHT_001_timeline.md`

## ⚡ Ризики та Запобігання (Risks & Mitigations)
- **Ризик:** Запис конфіденційних даних (API-ключі, токени користувача) в базу даних подій.
  - *Запобігання:* Реалізувати фільтр-санітайзер в `payload_json` за паттернами регулярних виразів (`key`, `token`, `secret`, `password`).
- **Ризик:** Конкуренція записів при високому навантаженні паралельних агентів.
  - *Запобігання:* Використовувати PostgreSQL пул підключень та оптимістичне блокування, супроводжуване ретраями з експоненціальним бекоффом.

## 🔍 Метод Перевірки (Verification Method)
1. Запустити симуляційний скрипт паралельної роботи трьох агентів.
2. Виконати SQL-запит до таблиці `agent_timeline` у PostgreSQL та переконатися, що всі події збережено хронологічно, а конфіденційні дані замасковані (`***`).
3. Запустити тест `pytest tests/test_timeline_logger.py`.
