---
document_id: DNK-BUS-1916
file_name: REBURN_CRO_EXPERIMENT_BRIEF.md
title: ReBurn CRO Experiment Brief
category: BUS
type: Brief
owner: Head of Orchestration
status: Active
version: 1.0.0
created_at: 2026-07-12
updated_at: 2026-07-12
parent_id: DNK-STD-0080
related_ids: []
tags:
  - reburn
  - cro
  - brief
  - a-b-test
storage_type: git
path: services/dnk_shopify/docs/business/REBURN_CRO_EXPERIMENT_BRIEF.md
access_level: write
checksum: null
changelog_ref: null
---

# 🔬 CRO EXPERIMENT BRIEF: ReBurn PDP Uplift (Case 01)

## 1. Гіпотеза (Hypothesis)
**ЯКЩО** ми інтегруємо висококонверсійний блок дефіциту часу (Countdown Timer) прямо під кнопкою додавання в кошик (Add to Cart CTA) та додамо блоки довіри (Trust & Guarantee Badges) біля секції опису продукту коптильного обладнання ReBurn,
**ТОДІ** ми зменшимо психологічне тертя клієнта на етапі ухвалення рішення та стимулюємо імпульсивну покупку,
**ЩО ПРИЗВЕДЕ** до зростання показника **Add-to-Cart (ATC) Rate на +15%** та загального доходу магазину без залучення сторонніх важких Shopify-додатків, які уповільнюють швидкість завантаження теми.

---

## 2. Елементи Експерименту (Experiment Elements)

| Елемент (Element) | Тип інтеграції | Цільовий Use Case | Конфігурація (Settings) |
| :--- | :--- | :--- | :--- |
| **ReBurn Countdown Timer** | Theme App Extension Block | Створення дефіциту часу (Urgency) | `title`, `end_date` (налаштування в Theme Editor) |
| **Trust Badges Block** | Custom Liquid Section | Зняття занепокоєння (Security & Shipping) | 3 іконки: "Швидка доставка", "100% Гарантія Луцького заводу", "Безпечна оплата" |

---

## 3. Метрики та Налаштування Аналітики (Measurement & Tracking)
- **Primary Metric:** Add-to-Cart (ATC) Rate (кількість кліків на кнопку "Додати в кошик" / унікальні сесії на PDP).
- **Secondary Metrics:**
  - Bounce Rate на PDP.
  - Середній час перебування користувача на сторінці товару.
  - Conversion Rate замовлень.
- **Аналітичні інструменти:** Google Analytics 4 (GA4) + GTM для відстеження кастомних подій кліку.

---

## 4. План Дій щодо Запуску (Execution Pipeline)
1. **Крок 1 (Baseline):** Фіксація поточного ATC Rate за останні 14 днів.
2. **Крок 2 (Deploy):** Увімкнення App Block `countdown-timer` та розміщення секції `trust-badges` у Shopify Theme Editor.
3. **Крок 3 (Validation):** Перевірка швидкості завантаження сторінки через Lighthouse (базовий показник не повинен просісти більш ніж на 2%).
4. **Крок 4 (A/B Test):** Проведення тестування протягом 14 днів (або до досягнення статистичної значущості у 95%).
