---
document_id: DNK-GOV-1912
file_name: extension_boundary_rules.md
title: Shopify Extension Boundary Rules
category: GOV
type: Rules
owner: Head of Orchestration
status: Active
version: 1.0.0
created_at: 2026-07-12
updated_at: 2026-07-12
parent_id: DNK-STD-0080
related_ids: []
tags:
  - shopify
  - architecture
  - security
storage_type: git
path: services/dnk_shopify/docs/tech/extension_boundary_rules.md
access_level: write
checksum: null
changelog_ref: null
---

# 🛡️ Shopify Extension Boundary Rules

Цей документ регламентує чіткі межі та ізоляцію між системним кодом теми **DNK Ecom** та шаром **Theme App Extensions** для запобігання деградації структури теми.

## 1. Повна Ізоляція Репозиторіїв та Файлів
- **Правило:** Весь код розширень додатків має зберігатися виключно у директорії `extensions/` на рівні сервісу.
- **Заборона:** Категорично заборонено вручну імпортувати, копіювати або хардкодити JS/CSS скрипти розширень у папку теми `assets/` чи `snippets/`.

## 2. Комунікація через App Blocks / App Embeds
- Розширення мають інтегруватися у тему виключно через механізм **App Blocks** (додаються мерчантом у конкретні секції через Theme Editor) або **App Embed blocks** (глобальні невидимі скрипти, наприклад, для аналітики або попапів).
- Дозволено використовувати стандартні точки входу Shopify (`theme app extensions`), які автоматично інжектують необхідні скрипти без модифікації файлу `theme.liquid`.

## 3. Налаштування та Конфігурація (`shopify.extension.toml`)
- Кожне розширення повинно мати свій незалежний конфігураційний файл `shopify.extension.toml`, що описує метадані та тип розширення.
- Всі схеми налаштувань (`settings`) всередині App Blocks мають валідуватися на сумісність перед релізом.
