# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tech_specs_DNK-ECOM-006_checkout_postpurchase_engine_spec"
# purpose: "TaskDNA Specification for Shopify Checkout UI Extensions, Post-Purchase Engine, Webhook Ingestion & Conversion Analytics (DNK-ECOM-006)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

# 🛍️ DNK-ECOM-006: Shopify Checkout UI Extensions & Post-Purchase Engine Specification

## 1. Executive Summary & Objectives
The **DNK-ECOM-006** track expands the DNK E-Commerce stack with an intelligent Checkout UI Extensions framework, an automated AI-driven Post-Purchase Upsell Engine, high-throughput Shopify Webhook ingestion with HMAC verification, and end-to-end Conversion Analytics.

Key capabilities:
1. **Checkout UI Extensions**: Pre-purchase cross-sells, delivery custom banners, custom order notes, trust badges, and dynamic checkout validation rules.
2. **Post-Purchase Upsell Engine**: 1-click upsell/downsell funnel generator, inventory reservation checks, margin-optimised discount pricing, and dynamic acceptance tokens.
3. **Webhook Ingestion & Idempotency**: Shopify HMAC SHA256 signature verification, webhook deduplication (idempotency key cache), event replay, and async event dispatcher.
4. **Conversion & AOV Analytics**: Real-time tracking of checkout extension impressions, CTR, conversion lift, AOV incrementality, and revenue attribution.

---

## 2. Architecture & DAG Phases

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DNK-ECOM-006 DAG PHASES                         │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 1: TaskDNA Specification & Core ORM Models                       │
│   ├── CheckoutExtensionModel, PostPurchaseOfferModel, UpsellRuleModel   │
│   └── CheckoutConversionEventModel, ShopifyWebhookEventModel           │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 2: Checkout Extension Engine & Post-Purchase Funnel Engine       │
│   ├── Dynamic extension placement & condition evaluation               │
│   └── 1-Click Post-Purchase Funnel, margin scoring & discount builder  │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 3: Shopify Webhook Ingestor & Real-Time Conversion Analytics     │
│   ├── HMAC-SHA256 verification & idempotency cache                     │
│   └── Multi-touch revenue attribution & AOV lift calculator            │
├────────────────────────────────────────────────────────────────────────┤
│ Phase 4: FastAPI REST Endpoints, Webhook Listeners & Evidence Gate     │
│   ├── /api/v1/ecom/checkout/*, /api/v1/ecom/post-purchase/*, webhooks  │
│   └── Integration tests, Evidence JSON, Handoff report & PR creation   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Models
- `CheckoutExtensionModel`: target placement (`purchase.checkout.block.render`, `purchase.checkout.cart-line-item.render-after`), status, config, rules.
- `PostPurchaseOfferModel`: offer title, trigger product IDs, upsell product IDs, discount percent, expiration seconds, priority.
- `UpsellRuleModel`: rule conditions (min cart total, tag matching, customer tier), action type, dynamic pricing tier.
- `CheckoutConversionEventModel`: event type (`IMPRESSION`, `CLICK`, `CONVERSION`, `DECLINE`), offer ID, order ID, revenue, currency.
- `ShopifyWebhookEventModel`: topic, shop domain, payload JSON, HMAC verified status, processed at, idempotency key.
