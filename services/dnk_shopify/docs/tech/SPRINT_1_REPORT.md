---
document_id: DNK-PLN-1909
file_name: SPRINT_1_REPORT.md
title: DNK Shopify Sprint 1 Report & Implementation Tasks
category: PLN
type: Plan
owner: Head of Orchestration
status: Active
version: 1.0.0
created_at: 2026-07-12
updated_at: 2026-07-12
parent_id: DNK-STD-0080
related_ids: []
tags:
  - sprint-1
  - shopify
  - roadmap
storage_type: git
path: services/dnk_shopify/docs/tech/SPRINT_1_REPORT.md
access_level: write
checksum: null
changelog_ref: null
---

# 🏁 SPRINT 1: Foundation (Theme Map, Agents & Drift Policy)

## 1. DNK Ecom Theme Map Standard

Карта теми **DNK Ecom** сканується модулем `ThemeIntelligence` та містить:
- **Sections Index:** Реєстр наявних Liquid-файлів у `sections/`, наявність блоку `{% schema %}`, кількість `settings` та `blocks`.
- **Templates Registry:** Аналіз JSON-шаблонів (`templates/*.json`) для перевірки, які секції використовуються на головній, сторінках товарів та колекцій.
- **Dependency Graph:** Аналіз підключення фрагментів коду `{% render %}`.

---

## 2. Agent Registry (Реєстр Агентів)

Для версії v1 сервісу `dnk_shopify` зареєстровано такі ролі агентів:

1. **Theme Agent (`src/agents/theme.py`):**
   * *Задача:* Робота з глобальною структурою теми, розширення `theme.liquid`.
2. **Section Agent (`src/agents/section.py`):**
   * *Задача:* Створення гнучких Liquid-секцій з адаптивними схемами (Single File Components).
3. **Content Agent (`src/agents/content.py`):**
   * *Задача:* Генерація структурованого контенту для секцій, квізів, розробка сторінок-шаблонів (Lading Pages, Listicles, PDP) у форматі Shopify-ready JSON templates.
4. **CRO Agent (`src/agents/cro.py`):**
   * *Задача:* Створення Liquid-коду для проведення А/Б-тестів на рівні клієнта.
5. **QA Agent (`src/agents/qa.py`):**
   * *Задача:* Валідація схем та семантики Liquid-тегів.
6. **Versioning Agent (`src/agents/versioning.py`):**
   * *Задача:* Контроль версійності та логування змін.

---

## 3. Validation Checklist & Anti-Drift Policy (Захист від дрейфу коду)

Кожна зміна або нова секція повинна пройти автоматизовану та ручну перевірку:

- [ ] **Liquid Syntax Valid:** Відсутність незакритих тегів `{% if %}`, `{% schema %}` тощо.
- [ ] **JSON Schema Syntax Valid:** Валідність структури метаданих всередині `{% schema %}`.
- [ ] **Zero Duplication Check:** Перевірка по карті теми, чи немає схожої секції.
- [ ] **Source Reference Tagged:** Кожна генерація повинна мати тег `source_reference` (наприклад, посилання на репозиторій-донор з нашої бази 125+ репо).
- [ ] **Version Tagged:** Надання унікальної версії за стандартом Semantic Versioning (наприклад, `1.1.0`).

---

## 4. Перші 10 Завдань до Імплементації (Top 10 Implementation Tasks)

Ці завдання реєструються в базі даних та виконуються послідовно:

1. **`[TECH-001]`** Ініціалізувати парсер `ThemeIntelligence` для аналізу `DNK_Ecom_v1_0_0` (збережено у `src/theme_intel.py`).
2. **`[TECH-002]`** Створити модуль автоматичного сканування схем секцій та генерації JSON-карти теми.
3. **`[TECH-003]`** Розробити адаптер `GitResearchAdapter` для завантаження паттернів з PostgreSQL pgvector.
4. **`[TECH-004]`** Створити базовий клас `ShopifyBaseAgent` з підтримкою ведення логів та контролю контексту.
5. **`[TECH-005]`** Написати інструмент валідації Liquid-схем (`src/validator.py`) для автоматичного лінтингу JSON-блоків перед збереженням.
6. **`[TECH-006]`** Налаштувати `Section Agent` для генерації Single File Component секцій (Liquid + CSS + Schema).
7. **`[TECH-007]`** Налаштувати `Content Agent` для генерації Shopify-ready JSON templates для Landing Pages, Listicles, Advertorials та Product Cards.
8. **`[TECH-008]`** Реалізувати інтеграційні тести для перевірки роутингу в `Orchestrator`.
9. **`[TECH-009]`** Створити скрипт автоматичної ініціалізації та нормалізації 125+ Shopify репозиторіїв у базу даних PostgreSQL з додаванням векторних ембеддінгів.
10. **`[TECH-010]`** Створити фінальний CLI-інтерфейс для запуску аналізу, генерації та валідації (`main.py` у сервісі).
