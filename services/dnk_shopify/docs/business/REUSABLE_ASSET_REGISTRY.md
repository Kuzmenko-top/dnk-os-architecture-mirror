---
document_id: DNK-BUS-1918
file_name: REUSABLE_ASSET_REGISTRY.md
title: Reusable Asset Registry
category: BUS
type: Registry
owner: Head of Orchestration
status: Active
version: 1.0.0
created_at: 2026-07-12
updated_at: 2026-07-12
parent_id: DNK-STD-0080
related_ids: []
tags:
  - assets
  - registry
  - shopify
  - monetization
storage_type: git
path: services/dnk_shopify/docs/business/REUSABLE_ASSET_REGISTRY.md
access_level: write
checksum: null
checksum_type: sha256
changelog_ref: null
---

# 📦 REUSABLE ASSET REGISTRY: DNK Shopify

Цей реєстр фіксує всі створені, протестовані та валідовані нашими агентами функціональні активи (секції, блоки, шаблони розширень), які готові до повторного використання або пакування у комерційні пропозиції.

---

## 💎 Активні Активи (Active Assets)

| ID Активу | Назва (Asset Name) | Тип компонента | Версія | Сумісність (Shopify compatibility) | Use Case / Опис | Source Reference (Репо-донор) |
| :---: | :--- | :--- | :---: | :---: | :--- | :--- |
| **`AST-001`** | **ReBurn Countdown Timer** | Theme App Extension (App Block) | `1.0.0` | Product, Index, Collection pages | Стимулювання імпульсивних продажів за допомогою дефіциту часу | `skraloupak/theme-quiz` / `uicrooks/shopify-theme-lab` |
| **`AST-002`** | **Trust & Guarantee Badges** | Reusable Liquid Section | `1.1.0` | Any theme section | Зняття занепокоєння клієнта щодо оплати та швидкої доставки | `maxwellt7/advertorial-creation-skill` |
| **`AST-003`** | **Advertorial Page Template** | JSON Page Template | `1.0.0` | Templates (Pages) | Створення висококонверсійних текстових сторінок-оглядів товарів | `florianbruniaux/claude-code-ultimate-guide-landing` |

---

## 🛠️ Як перевикористати актив
Всі активи підготовлені за стандартами Shopify-native та сумісні з візуальним редактором. Для імпорту активу в інший клієнтський магазин достатньо виконати команду:
```bash
python3 main.py asset import --id AST-001 --target /path/to/client_theme
```
