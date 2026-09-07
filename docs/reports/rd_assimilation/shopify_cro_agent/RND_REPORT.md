# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/shopify_cro_agent/RND_REPORT.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 📊 R&D Report: Shopify CRO Agent (2026 Admin API & Funnel Insights)

## Секція 1: Executive & Commercial Summary
`shopify-cro-agent` фокусується на оптимізації воронки конверсії інтернет-магазинів на платформі Shopify через Admin API та GraphQL. Головна комерційна цінність полягає в автоматизованому виявленні відхилень у ключових показниках воронки (AOV, PDP->ATC, ATC->Checkout, Checkout->Purchase) та наданні рекомендацій на основі бенчмарків у реальному часі.

## Секція 2: Core Architectural Patterns & Code Blueprints
### 1. 2026 OAuth Client Credentials Grant
Для нових Custom Apps токен авторизації отримується через коротку сесію POST запитів:
```http
POST https://{domain}/admin/oauth/access_token
Content-Type: application/json

{
  "client_id": "SHOPIFY_CLIENT_ID",
  "client_secret": "SHOPIFY_CLIENT_SECRET",
  "grant_type": "client_credentials"
}
```
Це видає короткоживучий токен доступу (~24 години), замінюючи застарілі `shpat_` токени.

### 2. Funnel GraphQL Queries
Приклад GraphQL запиту для збору даних воронки та залучених UTM-міток:
```graphql
query {
  orders(first: 50) {
    edges {
      node {
        id
        totalPriceSet {
          shopMoney {
            amount
          }
        }
        customerJourneySummary {
          firstVisit {
            utmCampaign
            utmSource
            utmMedium
          }
        }
      }
    }
  }
}
```

## Секція 3: DNK OS Mapping Matrix
- **Модуль у DNK OS:** `services/dnk_shopify/src/shopify_cro_funnel.py`
- **Інтеграція:** Отримані дані конвертуються в маржинальні звіти та відображаються на Canvas-інтерфейсі.

## Секція 4: Executable Skills & Verification
- **Згенеровані навички:** `shopify-cro-automation`, `shopify_cro_theme_engineering`
- **Верифікація:** Тест `services/dnk_shopify/tests/test_shopify_security.py` перевіряє безпеку вебхуків та HMAC валідацію.