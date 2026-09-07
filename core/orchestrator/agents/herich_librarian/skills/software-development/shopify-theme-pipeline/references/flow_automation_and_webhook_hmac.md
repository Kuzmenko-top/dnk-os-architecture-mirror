# Shopify Flow Automation & Webhook HMAC-SHA256 Bridge Reference

## Overview
This document outlines best practices, cryptographic verification standards, and architecture patterns for integrating Shopify Flow automation workflows and handling inbound Shopify Webhooks securely.

---

## 1. Shopify Webhook HMAC-SHA256 Verification

Shopify signs all webhook payloads with the store's shared webhook secret using HMAC-SHA256. The signature is transmitted via the HTTP header `X-Shopify-Hmac-SHA256`.

### Verification Logic (Base64 & Hex Comparison)

```python
import hmac
import hashlib
import base64
from typing import Optional

def verify_shopify_hmac(body_bytes: bytes, hmac_header: Optional[str], secret: str) -> bool:
    if not hmac_header:
        return False
    
    secret_bytes = secret.encode("utf-8")
    
    # Standard Shopify format: Base64-encoded binary SHA256 digest
    calculated_digest = hmac.new(secret_bytes, body_bytes, hashlib.sha256).digest()
    calculated_base64 = base64.b64encode(calculated_digest).decode("utf-8")
    if hmac.compare_digest(hmac_header, calculated_base64):
        return True
    
    # Alternative format: Hexadecimal digest
    calculated_hex = hmac.new(secret_bytes, body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(hmac_header, calculated_hex)
```

### Key Security Invariants
- **Raw Body Required**: Calculate HMAC strictly on raw incoming body bytes before JSON deserialization to prevent whitespace/key reordering mismatches.
- **Constant Time Comparison**: Always use `hmac.compare_digest` to prevent timing attacks.
- **Fail-Closed Execution**: If header is missing or signature verification fails, immediately return HTTP 401 Unauthorized.

---

## 2. Webhook Event Routing & Dispatch

| Topic | Handler Purpose | Actions Triggered |
|---|---|---|
| `orders/create` | Process new orders | Persist order, trigger Flow auto-fulfillment, emit merchant notification |
| `products/update` | Catalog sync | Update local DB, invalidate product/collection cache |
| `app/uninstalled` | GDPR/Store Lifecycle | Purge store credentials, schedule data cleanup |
| Custom/Other | Generic ingest | Log event, dispatch to event bus |

---

## 3. Shopify Flow API Automation

Shopify Flow allows merchants and apps to trigger automated GraphQL mutations when specific triggers occur.

### Standard Order Fulfillment Flow Mutation
```graphql
mutation FlowCreate {
  flowCreate(
    flow: {
      title: "DNK Auto Fulfillment"
      trigger: { flowTrigger: { __typename: "OrderCreate" } }
      actions: [
        {
          flowAction: {
            __typename: "SendEmail"
            recipient: "merchant@example.com"
            subject: "New Order {{ order.orderNumber }}"
            body: "Order {{ order.id }} requires fulfillment"
          }
        },
        {
          flowAction: {
            __typename: "FulfillOrder"
            notifyCustomer: true
          }
        }
      ]
    }
  ) {
    flow { id title }
    userErrors { field message }
  }
}
```

### Low Inventory Alert Flow Mutation
```graphql
mutation FlowCreate {
  flowCreate(
    flow: {
      title: "DNK Low Inventory Alert"
      trigger: { flowTrigger: { __typename: "InventoryLevelUpdate" } }
      conditions: [
        {
          flowCondition: {
            __typename: "InventoryQuantityLessThan"
            value: 10
          }
        }
      ]
      actions: [
        {
          flowAction: {
            __typename: "SendEmail"
            recipient: "merchant@example.com"
            subject: "Low Inventory Alert"
            body: "Product inventory below threshold."
          }
        }
      ]
    }
  ) {
    flow { id title }
    userErrors { field message }
  }
}
```
