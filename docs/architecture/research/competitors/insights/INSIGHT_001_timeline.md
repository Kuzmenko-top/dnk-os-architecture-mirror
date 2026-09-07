# 💡 ІНСАЙТ ТА ПРОДУКТОВА ІДЕЯ: Модель Єдиного Таймлайну (Timeline-Model)

## 📋 Метадані
---
mrh_id: "docs/research/competitors/insights/INSIGHT_001_timeline.md"
author: "Maxim"
license: "DNK-INTERNAL"
source_type: "competitor_observation"
source_reference: "crewai/001-crewai-dashboard.png"
derivative_status: "adapted"
created_at: "2026-08-11"
status: "Approved"
---

## 🔍 Спостереження (Observation)
В інтерфейсі CrewAI Enterprise (screen_001) логи виконання виводяться окремо для кожної групи ("Crew"). Це виглядає як послідовний набір текстових рядків, через що важко зрозуміти загальний контекст системи, якщо працюють кілька різних груп одночасно.

## 🩹 Біль, що вирішується (Pain Point)
Користувачеві важко відслідковувати паралельні робочі потоки. Коли один агент очікує на іншого, у логах виникає інформаційний вакуум, і незрозуміло, чи система зависла, чи просто чекає на завершення суміжної операції.

## 🚀 Продуктова ідея для DNK OS
Ми адаптуємо цю ідею у формі **Єдиної синхронізованої Timeline-моделі** для нашого Web UI. Всі субагенти (такі як `dnk_koder`, `dnk-dev-01`) реєструють свої дії в єдиному журналі у форматі таймлайну. Користувач може візуально бачити часову шкалу: хто, коли і яке завдання виконував, а також взаємозв'язки між ними.

---

## 🛡️ Zero-Regression Gate (Обов'язковий бар'єр)
1. **Концепція Прототипу (Prototype Specification):**
   * Створити легкий логер в `core/utils/timeline_logger.py`, який записує події виконання від різних субагентів у спільну таблицю PostgreSQL `agent_timeline` з полями `run_id`, `agent_id`, `event_type`, `status`, `timestamp`.
2. **Сценарій Тестування (Test Scenario):**
   * Запустити два субагенти паралельно через `delegate_task` і перевірити, що в базі даних події записані хронологічно без блокувань та втрати даних.
3. **Обґрунтування Цінності (Value Justification / ROI):**
   * Скорочує час розробника на відлагодження паралельних процесів на 40% та дає 100% розуміння стану системи в будь-який момент часу.

---

## 🌸 Трансляція у Flower (Тільки після затвердження "Adopt" або "Adapt")
* **Посилання на Flower Task:** `docs/tasks/Sector_03_UI/Tree_01_Timeline/Bush_01_Logger/Flower_01_implement_timeline_db.md`
* **Критерії Приймання (Acceptance Criteria):**
  - [ ] Реалізовано PostgreSQL-схему та міграцію для таблиці `agent_timeline`.
  - [ ] Створено клас `TimelineLogger` з методами `log_action_start` та `log_action_end`.
  - [ ] Записи мають чіткі позначки часу з точністю до мілісекунд.
* **Ризики (Risks & Mitigations):**
  - Блокування при великій кількості паралельних записів ➔ Створити індекси на `run_id`, `agent_id` та `timestamp`.
* **Метод Перевірки (Verification Method):**
  - Запуск інтеграційного тесту `pytest tests/test_timeline_concurrency.py`.
