---
document_id: DNK-DEV-1921
file_name: AGENT_SHOPIFY_INTEGRATION_GUIDE.md
title: Connecting AI Agents to Shopify (Spring 2026 Editions & Heuristics)
category: DEV
type: Guide
owner: Head of Orchestration
status: Active
version: 1.0.0
created_at: 2026-07-12
updated_at: 2026-07-12
parent_id: DNK-STD-0080
related_ids: []
tags:
  - shopify
  - ai-agents
  - spring-2026
  - integration
storage_type: git
path: services/dnk_shopify/docs/tech/AGENT_SHOPIFY_INTEGRATION_GUIDE.md
access_level: write
checksum: null
changelog_ref: null
---

# 🤖 ЗВІТ: ПІДКЛЮЧЕННЯ ШІ-АГЕНТІВ ДО SHOPIFY (ВІДПОВІДНО ДО SPRING 2026 EDITIONS)

Проведено детальний аналіз матеріалів **Shopify Spring 2026 Editions** (що фокусується на «Agentic E-commerce» та глибокій інтеграції автономних ШІ-агентів) спільно з еталонними архітектурами з нашої бази знань (таких як `shopify-hermes-oauth`, `hermes-agent-shopify` та `bankr-skill-shopify`).

Нижче наведено технічний стандарт підключення нашої агентної системи **DNK OS** до Shopify.

---

## 🌟 1. Ключові технології Agentic E-commerce (Spring 2026)
У релізі **Shopify Spring '26** центральне місце займають два оновлення, спеціально створені для розробників агентних систем:

1. **Shopify Sidekick & AI Toolkit Extensions:** Shopify дозволяє підключати сторонні агентні системи (як наш DNK HUB) безпосередньо до Admin API через спеціальні кастомні розширення з використанням декларативних інструкцій.
2. **GraphQL Admin API "Agentic" Scopes:** Додано нові точкові права доступу для ШІ-агентів (наприклад, `read_agent_analytics`, `write_agent_interactions`), які забезпечують безпечний доступ агента тільки до тих ресурсів магазину, які потрібні для виконання конкретної таски (наприклад, CRO-оптимізації сторінки товару).

---

## 🔌 2. Три еталонні архітектури підключення агента до магазину

Аналізуючи репозиторії з нашої бази, ми маємо 3 перевірених підходи до інтеграції агентів:

### Підхід А: Пряме виконання через Hermes Custom Tool (як у `hermes-agent-shopify`)
Це ідеальний безсерверний (serverless) підхід, коли наш агент (на базі Hermes) використовує кастомний Python-інструмент (MCP Tool) для виконання дій у магазині.

```python
# Приклад інструменту для нашого агента (tools/shopify_tool.py)
from hermes_tools import terminal

def run_agent_action(store: str, action: str, payload: dict, token: str):
    """Канонічний інструмент агента для виклику Shopify API"""
    import requests
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    
    if action == "publish_advertorial":
        # Агент публікує згенерований Liquid-код безпосередньо в тему
        url = f"https://{store}/admin/api/2026-07/themes/{payload['theme_id']}/assets.json"
        data = {
            "asset": {
                "key": f"templates/page.{payload['handle']}.json",
                "value": payload['json_content']
            }
        }
        res = requests.put(url, json=data, headers=headers)
        return res.json()
```

### Підхід Б: OAuth Авторизація для багатокористувацьких систем (як у `shopify-hermes-oauth`)
Використовується, коли ми продаємо нашу систему як SaaS для багатьох сторонніх клієнтів. Агент отримує доступ після того, як клієнт натискає «Встановити додаток» та проходить стандартний OAuth-флоу:

1. Клієнт вводить адресу магазину $\rightarrow$ Агент перенаправляє на:
   `https://{shop}.myshopify.com/admin/oauth/authorize?client_id={api_key}&scope=write_themes,write_products&redirect_uri={redirect_uri}`
2. Агент отримує тимчасовий `code` на свій сервер $\rightarrow$ міняє його на постійний `access_token` за допомогою POST-запиту.
3. Токен надійно зберігається в нашій базі даних PostgreSQL з RLS (Row Level Security).

---

## 🩺 3. Верифікація за допомогою Shopify Theme Check
Для забезпечення стабільності, перед тим як ШІ-агент робить `theme push` на сервер клієнта, він зобов'язаний локально виконати валідацію:
```bash
shopify theme check --environment=default
```
Якщо лінтер повертає помилки синтаксису (наприклад, незакриті теги в кастомних Liquid-секціях Advertorial), агент **автоматично блокує реліз** та відправляє код на доопрацювання.

---

## 📑 План дій для нашого тандему:
1. **Реєстрація Custom App:** Створюємо додаток `DNKShop_OS` в адмінці `m-craft-top` та копіюємо токен `shpat_...` (як описано у попередній інструкції).
2. **Локальна ініціалізація теми:** Виконуємо `shopify theme pull` у нашому Git Worktree.
3. **Автономна публікація карток товарів:** Агенти наповнюють магазин товарами через API.
4. **Реліз висококонверсійного контенту:** Агент публікує готові сторінки-шаблони (Advertorial, Listicle) безпосередньо в тему через інструмент `create_theme_asset`.
