# Shopify Functions & Wasm Custom Checkout Logic Reference

This reference specifies architecture, schemas, and invariants for building, compiling, and executing Shopify Functions via WebAssembly (Wasm) for custom checkout logic, cart transformations, order routing, and dynamic discounts (DNK-ECOM-005 / DNK-SHOPIFY-002).

## 1. Shopify Functions API Targets & Lifecycle

Shopify Functions execute server-side in a WebAssembly sandbox (under 5ms execution budget) replacing legacy Shopify Scripts.

### Primary Function Targets
- `cart_transform`: Expand bundles into component items, merge identical line items, override component pricing.
- `order_routing_location_rule`: Rank and select fulfillment locations based on stock distance, rules, and priority.
- `product_discount` / `order_discount`: Compute dynamic discounts (tiered volume, customer tags, B2B VIP pricing).
- `delivery_customization`: Hide, reorder, or rename shipping methods dynamically.
- `payment_customization`: Filter, hide, or reorder payment gateways dynamically (e.g. hide COD for high-risk orders).

## 2. Input/Output Schemas & GraphQL Query Contract

### Input Query Pattern (`run.graphql`)
```graphql
query RunInput {
  cart {
    lines {
      id
      quantity
      cost {
        amountPerQuantity {
          amount
          currencyCode
        }
      }
      merchandise {
        ... on ProductVariant {
          id
          title
          product {
            hasAnyTag(tags: ["bundle", "vip", "b2b"])
          }
        }
      }
    }
  }
}
```

### Output Mutation Schema (`FunctionResult`)
```json
{
  "operations": [
    {
      "expand": {
        "cartLineId": "gid://shopify/CartLine/123",
        "expandedCartItems": [
          {
            "merchandiseId": "gid://shopify/ProductVariant/456",
            "quantity": 1,
            "price": {
              "adjustment": {
                "fixedPricePerUnit": {
                  "amount": "49.99"
                }
              }
            }
          }
        ]
      }
    }
  ]
}
```

## 3. Input Normalization & Payload Invariants

Payload structures in Shopify Functions can arrive in either root GraphQL fields or nested customization objects depending on the API target and client version:
- **Delivery Customization**: Normalize from `deliveryGroups[].deliveryOptions[]`, `deliveryCustomization.deliveryOptions[]`, or direct `deliveryOptions[]`.
- **Payment Customization**: Normalize from `paymentMethods[]` or nested `paymentCustomization.paymentMethods[]`.
- **Cart Transform**: Extract from `cart.lines[]` with optional `merchandise.product.tags` evaluation.

## 4. Wasm Sandbox Execution & Invariants

1. **Deterministic Execution**:
   - Zero network I/O, filesystem access, or non-deterministic clock calls inside Wasm runtime.
2. **Execution Latency Budget**:
   - Hard execution timeout capped at 5ms per invocation; memory consumption under 10MB.
3. **Fail-Safe Fallback**:
   - If a Function execution throws or exceeds resource budget, checkout proceeds gracefully with empty operations (zero checkout disruption).
   - When executing sandbox evaluation for delivery/payment customizations in local Python runtime test suites, default simulation handlers (`_default_delivery_customization_handler`, `_default_payment_customization_handler`) should be provided so evaluation endpoints return valid result structures without requiring compiled native C/Rust `.wasm` binaries.
4. **Multi-Tenant Rule Storage & ORM Models**:
   - Rule configurations stored with `tenant_id` and `workspace_id` in PostgreSQL ORM models:
     - `ShopifyFunctionManifestModel`: Stores function_id, api_type, wasm_binary_hash, wasm_source_type, status.
     - `ShopifyCartTransformRuleModel`: Bundle expand/merge, component split, price overrides.
     - `ShopifyDynamicDiscountRuleModel`: Tiered volume, B2B wholesale, VIP discounts.
     - `ShopifyDeliveryCustomizationRuleModel`: Geo/weight rules for shipping method hide/rename/reorder.
     - `ShopifyPaymentCustomizationRuleModel`: B2B status/risk rules for payment gateway hide/reorder.
     - `ShopifyFunctionExecutionLogModel`: Stores execution latency, memory usage, invocation traces for performance audits.

## 5. FastAPI REST API & Admin UI Components

- **FastAPI Endpoints** (`/api/v1/shopify/functions`):
  - `POST /cart-transform/rules/bundle` & `/rules/price-override` — Register bundle expansion and price override rules.
  - `GET /cart-transform/rules` & `/cart-transform/manifest` — List rules and generate GraphQL Function targets.
  - `POST /cart-transform/evaluate` — Run Wasm sandbox transformation on cart input.
  - `POST /discounts/rules` & `POST /discounts/evaluate` — Manage and evaluate dynamic discount tiers.
  - `POST /delivery/rules` & `POST /delivery/evaluate` — Delivery customization rules (hide, rename).
  - `POST /payment/rules` & `POST /payment/evaluate` — Payment gateway customization rules (hide, block).
  - `POST /evaluate` — Generic function executor returning execution latency, memory, and operations.
- **Admin UI Components**:
  - `CartTransformRulesCard.tsx` — Visual rule builder for bundle expansion and price adjustments.
  - `DynamicDiscountsCard.tsx` — Tiered and wholesale discount configuration panel.
  - `FunctionsEvaluationSandbox.tsx` — Interactive sandbox simulator tracking <5ms latency and <10MB memory ceilings.
