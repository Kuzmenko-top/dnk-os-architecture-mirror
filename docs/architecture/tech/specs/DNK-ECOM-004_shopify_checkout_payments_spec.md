# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ECOM-004_shopify_checkout_payments_spec"
# purpose: "TaskDNA, Architecture Specification & Evolutionary DAG for Shopify Checkout Extensions & Payment Gateways"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-ECOM-004"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛍️ DNK-ECOM-004 — Shopify Checkout Extension & Payment Gateway Integration

## 🧬 TaskDNA Evolutionary DAG
```
[Phase 1: Checkout UI Extension & Payment Gateway Configs]
       │
       ▼
[Phase 2: Payment Intent Manager & 3D Secure 2.0 Engine]
       │
       ▼
[Phase 3: Post-Purchase Upsell Engine (AST/Liquid Validation)]
       │
       ▼
[Phase 4: Webhook Event Bus & Real-time Live Streams]
       │
       ▼
[Phase 5: React UI Components, Full E2E & Master Quality Gate]
```

## 📐 Architecture Components
1. **Checkout UI Extension Engine (`shopify_checkout_extension.py`)**:
   - Manages custom checkout fields (shipping instructions, gift messages, B2B PO numbers).
   - Validates extension schema, target placements, and API versioning (`2024-07`).
2. **Multi-Gateway Payment Dispatcher (`shopify_payment_gateway_handler.py`)**:
   - Unified interface for Stripe (Cards, Apple Pay), Shopify Payments (Native), and Crypto (Coinbase Commerce).
   - Dynamic credential encryption and test connectivity validation.
3. **Payment Intent & 3DS 2.0 Manager (`shopify_payment_intent_manager.py`)**:
   - Complete lifecycle: `create` -> `requires_action (3DS)` -> `capture` -> `refund`.
   - Idempotency guarantees and PCI DSS compliance (no raw PAN storage).
4. **Post-Purchase Upsell Engine (`shopify_post_purchase_upsell.py`)**:
   - One-click add-ons, cross-sell recommendation matching, order bumps.
   - Dynamic discount calculations and max usage limits.
5. **Webhook Ingestion & Event Bus (`shopify_webhook_event.py` / Redis Streams)**:
   - Ingests `order/created`, `payment/succeeded`, `payment/failed`, `order/refunded`.
   - Signature verification (`HMAC-SHA256`) and idempotency replay protection.
