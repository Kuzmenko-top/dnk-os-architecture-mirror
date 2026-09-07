# Shopify Admin API GraphQL Engine, Rate Limiting & Bulk Operations

This reference documents the architecture, patterns, and integration workflows for Shopify Admin API GraphQL Engine, Token-Bucket Rate Limiting, Async Bulk Operations Pipeline, and Two-Way Catalog Synchronization.

---

## 1. Token-Bucket Rate Limiter Pattern

Shopify Admin API imposes strict rate limits (typically up to 1000 requests per minute with burst capacity):

```python
import asyncio
import time
from typing import Optional

class TokenBucketRateLimiter:
    """
    Asynchronous Token-Bucket Rate Limiter with burst capacity.
    Default: 1000 requests/minute (16.66 tokens/sec) with burst capacity of 50.
    """
    def __init__(self, rate_per_minute: float = 1000.0, burst_capacity: int = 50):
        self.rate_per_second = rate_per_minute / 60.0
        self.capacity = float(burst_capacity)
        self.tokens = float(burst_capacity)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.last_refill = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_second)

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

                # Calculate sleep duration needed for required tokens
                deficit = tokens - self.tokens
                wait_time = deficit / self.rate_per_second
                await asyncio.sleep(wait_time)

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
```

---

## 2. Admin API GraphQL Engine (`2024-07`)

GraphQL requests should always be routed through the rate limiter:

- Endpoint: `https://{shop_domain}/admin/api/{api_version}/graphql.json`
- Headers:
  - `X-Shopify-Access-Token: {access_token}`
  - `Content-Type: application/json`

### Key Queries

1. **`GetProducts` with Variants and Inventory**:
```graphql
query GetProducts($first: Int!, $after: String) {
  products(first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      cursor
      node {
        id
        title
        handle
        status
        variants(first: 20) {
          edges {
            node {
              id
              title
              sku
              price
              inventoryQuantity
            }
          }
        }
      }
    }
  }
}
```

2. **`GetOrders` with Financial/Fulfillment Status**:
```graphql
query GetOrders($first: Int!, $after: String) {
  orders(first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      cursor
      node {
        id
        name
        createdAt
        financialStatus
        fulfillmentStatus
        totalPriceSet {
          shopMoney {
            amount
            currencyCode
          }
        }
        lineItems(first: 20) {
          edges {
            node {
              id
              title
              quantity
            }
          }
        }
      }
    }
  }
}
```

---

## 3. Bulk Operations Pipeline (Async Export/Import)

For high-volume synchronization (10k+ items), querying the standard GraphQL API sequentially triggers throttle limits. Use `bulkOperationRunQuery`:

```graphql
mutation CreateBulkExport($query: String!) {
  bulkOperationRunQuery(
    query: $query
  ) {
    bulkOperation {
      id
      status
    }
    userErrors {
      field
      message
    }
  }
}
```

### Polling & Processing JSONL:
1. Query current status via `currentBulkOperation`:
```graphql
query CurrentBulkOperation {
  currentBulkOperation {
    id
    status
    errorCode
    createdAt
    completedAt
    objectCount
    fileSize
    url
  }
}
```
2. Once status is `COMPLETED`, stream the `.jsonl` file line-by-line to avoid high memory spikes.
3. Parse each JSON line into local models (`Product`, `Variant`, `Order`).

---

## 4. Two-Way Catalog Synchronization Pattern

- **Shopify ➔ Local**:
  1. Trigger `bulk_export_products()` / `bulk_export_orders()`.
  2. Poll until `COMPLETED`.
  3. Stream download JSONL lines and batch upsert to local DB.
- **Local ➔ Shopify**:
  1. Generate JSONL/CSV payload in staged format.
  2. Call `stagedUploadsCreate` mutation.
  3. POST file to Google Cloud Storage staged URL.
  4. Call `bulkOperationRunMutation` with staged upload key.

---

## 5. Testing Pitfall: TestClient & Global Rate Limiting

When running large regression suites (400+ tests) against FastAPI apps containing security middleware:
- Ensure rate-limiting middleware bypasses requests originating from `testclient` IP or when `os.getenv("PYTEST_CURRENT_TEST")` is set.
- Otherwise, running all test suites sequentially triggers HTTP 429 `RateLimitExceeded`.
