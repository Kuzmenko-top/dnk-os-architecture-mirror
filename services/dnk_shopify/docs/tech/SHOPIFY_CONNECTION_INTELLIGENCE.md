---
document_id: DNK-DEV-1920
file_name: SHOPIFY_CONNECTION_INTELLIGENCE.md
title: Shopify Connection & Theme Intelligence Report
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
  - connection
  - cli-api
  - patterns
storage_type: git
path: services/dnk_shopify/docs/tech/SHOPIFY_CONNECTION_INTELLIGENCE.md
access_level: write
checksum: null
changelog_ref: null
---

# 🔌 ДОСЛІДЖЕННЯ: ЗАКРИТИЙ КОНТУР ПІДКЛЮЧЕННЯ ТА РОБОТИ З ТЕМАМИ SHOPIFY

На основі детального аналізу еталонних репозиторіїв з нашої бази знань (зокрема `shopify/themekit`, `shopify/theme-tools`, `uicrooks/shopify-theme-lab` та `bankrbot/bankr-skill-shopify`), ми виділили **два найбільш надійних та швидких методи підключення до тем та API магазину Shopify**.

---

## 🛠️ МЕТОД 1: Офіційне підключення та синхронізація через Shopify CLI
Це найнадійніший індустріальний метод роботи з темами, що підтримує «живий» перезапуск змін (Hot Reloading), лінтинг коду та валідацію схем.

### 🔑 Вимоги для авторизації:
Замість складної веб-авторизації через браузер, Shopify CLI підтримує **Direct Token Authentication** за допомогою сервісних токенів `Theme Access` або `Custom App`.

### 💻 Команди підключення:
1. **Ініціалізація та скачування поточної теми бренду:**
   ```bash
   cd services/dnk_shopify/DNK_Ecom_v1_0_0
   shopify theme pull --store="m-craft-top.myshopify.com" --password="shpat_your_admin_api_token"
   ```
2. **Запуск локального сервера розробки з Hot Reload (зміни миттєво з'являються на копії стору):**
   ```bash
   shopify theme dev --store="m-craft-top.myshopify.com" --environment="default"
   ```
3. **Вивантаження кастомних секцій та контенту на «живий» стор:**
   ```bash
   shopify theme push --store="m-craft-top.myshopify.com" --theme="DNK-Ecom-Prod"
   ```

---

## 🔌 МЕТОД 2: Автономний ШІ-Міст розробника через Python Admin API
Для масової публікації карток товарів (Products, Variants, Metafields) та згенерованих нами JSON-шаблонів сторінок (Advertorials, Listicles), ми використовуємо пряме підключення до **Shopify Admin REST / GraphQL API**.

Це дозволяє уникнути роботи з консоллю та публікувати активи повністю автоматично за допомогою ШІ-команд.

### 🐍 Приклад коду автономної інтеграції (`src/shopify_api_bridge.py`):
```python
import os
import requests

class ShopifyAdminBridge:
    def __init__(self, store_domain: str, admin_token: str):
        self.base_url = f"https://{store_domain}/admin/api/2026-07"
        self.headers = {
            "X-Shopify-Access-Token": admin_token,
            "Content-Type": "application/json"
        }

    def create_product(self, title: str, body_html: str, vendor: str, price: str, image_url: str):
        """Створює картку товару безпосередньо в адмінці магазину"""
        payload = {
            "product": {
                "title": title,
                "body_html": body_html,
                "vendor": vendor,
                "status": "active",
                "variants": [{"price": price, "requires_shipping": True}],
                "images": [{"src": image_url}]
            }
        }
        response = requests.post(f"{self.base_url}/products.json", json=payload, headers=self.headers)
        return response.json()

    def create_theme_asset(self, theme_id: str, key: str, value: str):
        """Завантажує згенерований Liquid або JSON-шаблон прямо в тему"""
        payload = {
            "asset": {
                "key": key,
                "value": value
            }
        }
        response = requests.put(f"{self.base_url}/themes/{theme_id}/assets.json", json=payload, headers=self.headers)
        return response.json()
```

---

## 📈 ПЛАН ЗАПУСКУ МАГАЗИНУ МУДРИЙ КРАФТЯР:
1. **Підключення CLI:** Використовуючи токен `shpat_...` з адмінки `m-craft-top`, ми завантажуємо базову тему у папку `DNK_Ecom_v1_0_0`.
2. **Генерація карток:** Наш автономний скрипт `src/mudriy_craftiar_build.py` автоматично створює картки коптилень, димогенераторів та тріски безпосередньо через Admin API.
3. **Публікація контенту:** Завантаження згенерованих JSON-сторінок (Advertorial, Listicle) у тему за допомогою `requests.put` або `shopify theme push`.
4. **Валідація:** Запуск `shopify theme check` для підтвердження відсутності багів перед фінальним запуском.
