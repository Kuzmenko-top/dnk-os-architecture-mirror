---
document_id: DNK-BUS-1914
file_name: REBURN_EXECUTION_PLAN.md
title: ReBurn Shopify Execution Plan v1
category: BUS
type: Plan
owner: Head of Orchestration
status: Active
version: 1.0.0
created_at: 2026-07-12
updated_at: 2026-07-12
parent_id: DNK-STD-0080
related_ids: []
tags:
  - reburn
  - execution
  - shopify
  - cro
  - experiments
storage_type: git
path: services/dnk_shopify/docs/business/REBURN_EXECUTION_PLAN.md
access_level: write
checksum: null
changelog_ref: null
---

# 🛍️ REBURN SHOPIFY EXECUTION PLAN: Case 01 (CRO & Conversion Booster)

Цей план є еталонним запуском (Case 01) першого комерційного бізнес-експерименту на реальному магазині нашого власного бренду **ReBurn** з виготовлення коптильного обладнання.

---

## 🎯 1. Головна Мета & Метрики Успіху (Success Metrics)

* **Ціль:** Підвищити конверсію сторінки товару (Product Detail Page - PDP) коптильні ReBurn за рахунок усунення психологічного тертя покупця, додавання соціального доказу (Trust/Proof) та стимулювання швидкої покупки (Scarcity).
* **Метрика успіху (Primary Metric):** Зростання показника **Add-to-Cart (ATC) Rate на +15%** та загальної конверсії замовлень.
* **Базовий показник (Baseline):** Вимірюється перед активацією експерименту на живому трафіку.

---

## 🔬 2. Експеримент: "Scarcity & Trust Stack" (CRO Experiment Blueprint)

Ми впроваджуємо два висококонверсійних модуля за допомогою нашої ШІ-агентної системи:

### ⏱️ Модуль А: ReBurn Countdown Timer (App Block)
* *Тип:* Theme App Extension (ізольований блок).
* *Задача:* Стимулювання швидкої покупки за рахунок таймера зворотного відліку акційної пропозиції.
* *Локація:* Блок рендериться під кнопкою "Додати в кошик" (Add to Cart).

### 🛡️ Модуль Б: Trust & Guarantee Badges (Custom Section)
* *Тип:* Liquid Section з налаштуваннями.
* *Задача:* Зняття занепокоєння щодо доставки, гарантії на обладнання та безпеки оплати.

---

## 📅 3. Покроковий План Реалізації (Execution Timeline)

### 🗓️ Етап 1: Scan & Audit (День 1)
* Запуск `ThemeIntelligence` для аналізу поточної теми магазину ReBurn. Побудова точної мапи секцій для виявлення конфліктів скриптів.

### 🗓️ Етап 2: Generation & Sandbox Build (День 2-3)
* **Section Agent** генерує блок довіри `trust-badges.liquid`.
* **App Agent** готує та пакує `countdown-timer` у папці `extensions/`.

### 🗓️ Етап 3: Sandbox Validation (День 4)
* Тестування та перевірка сумісності з Shopify Theme Editor. Схеми JSON повинні проходити лінтинг без помилок.

### 🗓️ Етап 4: Live Launch & Monitoring (День 5-14)
* Запуск експерименту на живому трафіку. Відстеження ATC Rate, показників залученості та швидкості завантаження сторінки.

### 🗓️ Етап 5: Knowledge Capture (День 15)
* Збереження напрацьованих секцій та конфігурацій розширення у нашу базу знань PostgreSQL pgvector як **Reusable Asset** з версійним тегом `1.0.0-case1`.
