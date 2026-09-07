# 🌸 Flower_01_security_decorator.md: Посилені Гейти Затвердження та Декоратор Безпеки (Phased Gate Lifecycle)

## 📋 Метадані
---
mrh_id: "docs/tasks/Sector_01_Core/Tree_03_Security/Bush_02_Gates/Flower_01_security_decorator.md"
author: "Maxim"
license: "DNK-INTERNAL"
source_type: "competitor_observation"
source_reference: "crewai/002-crewai-approval-gate.png"
derivative_status: "adapted"
status: "GO_PHASED"
version: "1.0.0"
created_at: "2026-08-11"
---

## 🎯 Мета (Purpose)
Впровадити надійну двофазну систему безпеки Supervisor Approval Gates:
1. **Developer API:** Python-декоратор `@security_gate` для інтеграції розробниками.
2. **Security Authority (Служба Політик):** Центральний сервіс верифікації та життєвого циклу гейтів.
3. **Audit Timeline:** Незмінний лог виконання для фіксації кожної дії.

## 📝 Критерії Приймання (Acceptance Criteria) - Definition of Done (DoD)
- [ ] **Fail-Closed за замовчуванням:** Будь-яка помилка валідації, виняток або відсутність відповіді мережі автоматично розглядається як відхилення дії (викидається `PermissionError`).
- [ ] **Approval Binding:** Запит на затвердження унікально прив'язується до:
  * `run_id` (ідентифікатор поточного запуску)
  * `action_name` (назва дії/функції)
  * `arguments_hash` (криптографічний SHA-256 хеш переданих аргументів функції для захисту від підміни параметрів під час очікування)
- [ ] **No Auto-Approve on Timeout:** Додано обов'язковий таймаут очікування (`expiry` / `timeout`, наприклад, 600 секунд). Після закінчення часу запит автоматично маркується як `timeout_rejected` та виконання блокується. Авто-апрув заборонений!
- [ ] **Idempotency (Захист від повторних деструктивних дій):** Кожна дія має унікальний ключ ідемпотентності. Якщо дія вже була затверджена для даного `run_id` та `arguments_hash`, повторний виклик не повинен ініціювати деструктивну операцію знову.
- [ ] **Audit Trail Log:** Всі події життєвого циклу (`approved`, `rejected`, `timeout_rejected`, `denied`) записуються в захищений лог аудиту безпеки з позначкою часу, ID користувача та деталями підпису.
- [ ] **Developer API (Декоратор):** Створено декоратор `@security_gate(level="high")` в `core/security/gates.py`, який слугує зручним фасадом для взаємодії розробників з `GateService`.
- [ ] **Policy Failure Tests:** Написано окрему групу тестів для перевірки поведінки системи при порушенні політик безпеки, таймаутах та симуляції збоїв у самому сервісі гейтів.

## 💡 Джерело Ідеї (Idea Source)
Адаптовано з механізму CrewAI Human-in-the-loop (HITL).
* Докладний аналіз: `docs/research/competitors/crewai_analysis.md` (screen_002)
* Продуктовий інсайт: `docs/research/competitors/insights/INSIGHT_002_approval_gate.md`

## ⚡ Ризики та Запобігання (Risks & Mitigations)
- **Ризик:** Зловмисник змінює аргументи функції після створення запиту на затвердження.
  - *Запобігання:* Хешувати аргументи (`arguments_hash`) під час створення запиту і повторно звіряти хеш під час розблокування гейту.
- **Ризик:** Помилка в базі даних або сервісі гейтів пропускає виконання чутливої дії.
  - *Запобігання:* Реалізувати логіку "fail-closed" через конструкцію `try-except`, де будь-яка помилка за замовчуванням блокує виконання (`allow = False`).

## 🔍 Метод Перевірки (Verification Method)
1. Написати юніт-тести в `tests/test_security_gates.py`, що симулюють:
   - Успішне схвалення у межах встановленого часу (expiry).
   - Автоматичне відхилення через таймаут (no auto-approve).
   - Блокування при спробі змінити аргументи під час очікування (binding check).
   - Викидання винятку при збої бази даних (fail-closed check).
2. Запустити тестову матрицю через `pytest tests/test_security_gates.py`.
