# Shopify Checkout Extensions & Payment Gateways Reference

This reference provides schemas, placement targets, payment intent lifecycles, and multi-gateway patterns for building Shopify Checkout UI Extensions, managing payment integrations, post-purchase upsells, and webhook event processing (DNK-ECOM-004).

## 1. Shopify Checkout UI Extension Placements & Field Types

### Target Placements
- `purchase.checkout.shipping-option-list.render-after` (Shipping instructions, delivery notes)
- `purchase.checkout.payment-method.render-before` (VIP access code, custom tax/VAT numbers)
- `purchase.checkout.order-summary.render-after` (Gift messages, donation checkboxes)
- `purchase.checkout.cart-line-item.render-after` (Line-item custom engraving/options)
- `purchase.checkout.information-form.render-before` (B2B PO numbers, enterprise billing)
- `purchase.post-purchase.render-primary` (Post-purchase one-click upsells)

### Field Definition Schema
```json
{
  "key": "shipping_notes",
  "label": "Delivery Instructions",
  "field_type": "textarea",
  "required": false,
  "default_value": "",
  "validation_regex": "^[a-zA-Z0-9 .,!?-]*$",
  "help_text": "Enter gate code or specific porch instructions (max 250 chars)."
}
```

### Validation Invariants
- `required`: Non-empty string, non-null value, or boolean `True` for required checkboxes.
- `validation_regex`: Pattern matching against string values using `re.match`.
- `max_length` / `min_value` / `max_value`: Enforced per field type (`text`, `textarea`, `number`).
- `options`: For `select` fields, submitted value must exist in declared options.

---

## 2. Multi-Gateway Payment Integration & Credential Hygiene

### Supported Gateway Adapters
1. **Stripe Payments (`stripe`)**:
   - Capabilities: `card`, `apple_pay`, `google_pay`.
   - Credentials: `secret_key` (`sk_test_*` or `sk_live_*`), `publishable_key` (`pk_test_*` or `pk_live_*`), `webhook_secret` (`whsec_*`).
   - Latency & Handshake: Ping `https://api.stripe.com/v1` or perform test validation.

2. **Shopify Payments (`shopify_payments`)**:
   - Capabilities: `native_shopify`, `apple_pay`, `google_pay`.
   - Credentials: `shopify_store_domain` (`*.myshopify.com`), `access_token` (`shpat_*`).

3. **Coinbase Commerce (`coinbase`)**:
   - Capabilities: `crypto` (`BTC`, `ETH`, `USDC`, `SOL`, `MATIC`).
   - Credentials: `api_key`, `webhook_secret`.

### Security & Redaction Invariant
- Never expose raw secret keys or tokens in API responses, logs, or UI state.
- Redact credentials to `[REDACTED]` or partial masks (`sk_live_...` -> `sk_live_...abcd`).
- Return sanitized configuration models (`sanitized_dict()`) to external callers.

---

## 3. Payment Intent Lifecycle & 3D Secure 2.0 (SCA)

### Intent Status Flow
```
[ PENDING ] ── (3DS Required) ──> [ REQUIRES_ACTION ] ── (Challenge Success) ──> [ SUCCEEDED ]
    │                                     │ (Challenge Failed)
    │ (Direct Confirm)                    └──> [ FAILED ]
    ▼
[ SUCCEEDED ] ── (Capture) ──> Captured Balance
    │
    ├── (Partial Refund) ──> [ PARTIALLY_REFUNDED ]
    └── (Full Refund)    ──> [ REFUNDED ]

[ PENDING / REQUIRES_ACTION ] ── (Cancel) ──> [ CANCELLED ]
```

### Invariants for Payment Processing
- **Idempotency**: Store index of `idempotency_key -> payment_intent_id` to guarantee zero duplicate charges upon network retries.
- **3D Secure 2.0**: When `require_3ds=True`, initial state is `REQUIRES_ACTION`, containing `challenge_url` and transaction IDs for the browser/extension iframe.
- **Refund Validation**: Refunds are only permitted on `SUCCEEDED` or `PARTIALLY_REFUNDED` intents. Cumulative refunds cannot exceed `amount_captured_cents`.
- **Cancellation**: Settled payments (`SUCCEEDED`, `REFUNDED`) cannot be cancelled; they must be refunded instead.

---

## 4. Post-Purchase Upsell Engine & Liquid AST Validation

### Offer Matching & Discount Calculation
- **Trigger Matching**: Evaluate cart / checkout items against `trigger_product_ids`.
- **Discount Types**:
  - `PERCENTAGE`: `final_price = original_price * (1 - discount_value / 100)`
  - `FIXED_AMOUNT`: `final_price = max(0, original_price - discount_value_cents)`
  - `FREE_SHIPPING`: Applies 100% shipping waiver while maintaining item base price.

### Liquid AST Validation Invariants
- **XSS Sanitization**: Disallow raw inline scripts (`<script>`), `javascript:` hrefs, and malicious event handlers (`onload`, `onerror`).
- **Tag Balance**: Ensure all Liquid control structures (`{% if %}` ➔ `{% endif %}`, `{% for %}` ➔ `{% endfor %}`, `{% form %}` ➔ `{% endform %}`) are strictly balanced.
- **Variable Whitelist**: Restrict available context variables to safe checkout scope (`customer`, `order`, `upsell_offer`, `shop`).

---

## 5. 1-Click Post-Purchase Funnel Engine & Margin Optimization (DNK-ECOM-006)

### Margin & COGS Dynamic Pricing
- **Margin Score Formula**: `margin_score = (offer_price - cogs) / offer_price` (normalized to `0.0 - 1.0`).
- **Dynamic Prioritization**: Rank eligible post-purchase offers by `(priority, margin_score)` descending to maximize store profit while delivering competitive discounts.
- **Signed Expiration Tokens**: Generate HMAC-SHA256 signed tokens (`{expires_at}.{signature}`) tying `order_id` and `offer_id` with a strict countdown timer (e.g., 300s TTL) to prevent tampering or replay.
- **Downsell Fallback Chain**: If a customer declines the primary upsell, automatically route to a secondary downsell offer with a steeper percentage discount or lower price point.

---

## 6. Real-Time Conversion Analytics & AOV Lift

### Core Funnel Metrics
- **CTR**: `(clicks / impressions) * 100%`
- **Conversion Rate (CR)**: `(accepts / impressions) * 100%`
- **Acceptance Rate**: `(accepts / (accepts + declines)) * 100%`
- **AOV Lift**: `total_incremental_revenue / completed_orders`
- **Multi-Channel Attribution**: Separate reporting by channel source (`checkout_ui`, `post_purchase`, `thank_you`).
- **Time-Series Aggregation**: Daily / hourly breakdown of impressions, accepts, and incremental revenue.

---

## 7. HMAC-Verified Webhook Event Bus & Ingress

### Signature Verification Patterns
- **Shopify Webhooks**:
  - Header: `X-Shopify-Hmac-SHA256`
  - Algorithm: Base64-encoded HMAC-SHA256 of raw request payload using `webhook_secret`.
  - Timing-Safe Comparison: `hmac.compare_digest(calculated, header_signature)`.
- **Stripe Webhooks**:
  - Header: `Stripe-Signature` (`t=timestamp,v1=signature`)
  - Algorithm: Hex-encoded HMAC-SHA256 of `timestamp.raw_body` using `webhook_secret`.
  - Timestamp Tolerance: Enforce 300s window to prevent replay attacks.

### Ingress & Event Bus Lifecycle
- **Deduplication**: Hash `(source, event_id, event_topic)` with 24-hour TTL in cache.
- **Idempotent Ingestion**: Repeated webhooks return HTTP 200 with status `DUPLICATE` without triggering downstream side-effects.
- **Dead-Letter Queue (DLQ)**: Failed handler executions increment retry counter (up to 3 attempts with exponential backoff) before routing event payload to DLQ for manual inspection.
- **ORM Model Polymorphic Compatibility**: Webhook data persistence models (e.g., `ShopifyWebhookEventModel`) must support bidirectional alias mapping (`event_type` ↔ `topic`, `processing_status` ↔ `status`) and UUID/string type coercion in `__init__` to ensure backward compatibility across payment gateway tests and new checkout analytics pipelines.
