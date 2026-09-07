---
document_id: DNK-BUS-1919
file_name: COMMERCIAL_OPERATING_PLAN.md
title: DNK Shopify Commercial Operating Plan v1
category: BUS
type: Framework
owner: Head of Orchestration
status: Active
version: 1.0.0
created_at: 2026-07-12
updated_at: 2026-07-12
parent_id: DNK-STD-0080
related_ids: []
tags:
  - business
  - operations
  - shopify
  - client-success
storage_type: git
path: services/dnk_shopify/docs/business/operations/COMMERCIAL_OPERATING_PLAN.md
access_level: write
checksum: null
changelog_ref: null
---

# 🔱 COMMERCIAL OPERATING PLAN: DNK Shopify v1

Цей документ регламентує повний операційний цикл ведення клієнтів та продуктізації активів для сервісу **DNK Shopify**.

---

## 🔄 1. Операційний Цикл Клієнта (Operational Flow)

Кожен клієнтський проєкт проходить через 6 жорстких детермінованих етапів:

```
[1. Client Intake] ──> [2. Theme Scan & Audit] ──> [3. Research Patterns]
                                                               │
                                                               ▼
[6. Asset Registry] <── [5. Quality Gate & Release] <── [4. Agentic Build]
```

### 📋 Етап 1: Client Onboarding & Intake
* **Вхідний потік:** Клієнт заповнює `CLIENT_INTAKE_FORM.md`.
* **Завдання:** ШІ-оркестратор зчитує нішу, біль клієнта та наявний стек додатків для побудови бізнес-профілю.

### 🔍 Етап 2: Theme Scan & Audit
* **Дія:** Запуск команди `theme analyze` через наш `ThemeIntelligence` інструмент.
* **Результат:** Оцінка наявної теми, виявлення дублікатів, застарілих тегів та зон ризику.

### 🔎 Етап 3: Research Patterns
* **Дія:** Запит через `GitResearchAdapter` до нашої бази знань PostgreSQL pgvector.
* **Результат:** Добірка еталонних рішень з нашої бібліотеки 125+ репозиторіїв.

### 🛠️ Етап 4: Agentic Build
* **Дія:** Оркестратор розподіляє підзадачі на спеціалізованих агентів.
* **Результат:** Збірка секцій (`Section Agent`), контентних сторінок (`Content Agent`) або розширень (`App Agent`).

### 🩺 Етап 5: Quality Gate & Release (DoD)
* **Дія:** Перевірка згенерованих артефактів через лінтер `shopify theme check` у нашому ізольованому робочому просторі `Git Worktree`.

### 📦 Етап 6: Asset Registry & Knowledge Flywheel
* **Дія:** Успішно зданий проєкт маркується версійним тегом та додається до `REUSABLE_ASSET_REGISTRY.md` як **Reusable Asset** для миттєвого копіювання чи перевикористання в майбутніх проєктах.

---

## 📈 2. Продуктовий План (Product Scaling Framework)

Те, що довело свою конверсійну цінність на наших внутрішніх брендах (наприклад, ReBurn), ми негайно упаковуємо у продукти:

* **Theme Blocks Pack:** Пакет готових до завантаження розширень теми (таймери, кастомні квізи).
* **Funnel Templates:** Готові воронки продажів (Landing Page + Advertorial + Listicle) у Shopify-native JSON-форматі сторінок.
