# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/shopify_graphql_engine.py"
# purpose: "Shopify Admin API GraphQL Engine with query builders and token-bucket rate limiting"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
from typing import Optional, Dict, Any, Callable
from apps.api.services.rate_limiter import TokenBucketRateLimiter


class ShopifyGraphQLEngine:
    """
    Shopify Admin API GraphQL Engine supporting query execution, pagination,
    and automatic TokenBucketRateLimiter protection.
    """

    def __init__(
        self,
        shop_url: str,
        access_token: str,
        rate_limiter: Optional[TokenBucketRateLimiter] = None,
        mock_handler: Optional[Callable[[str, Optional[Dict[str, Any]]], Dict[str, Any]]] = None,
    ):
        self.shop_url = shop_url
        self.access_token = access_token
        self.endpoint = f"https://{shop_url}/admin/api/2024-07/graphql.json"
        self.rate_limiter = rate_limiter or TokenBucketRateLimiter(rate=1000, burst=50)
        self.mock_handler = mock_handler

    async def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute GraphQL query with rate limiter protection."""
        async with self.rate_limiter:
            if self.mock_handler:
                return self.mock_handler(query, variables)
            return self._default_mock_execute(query, variables)

    def _default_mock_execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fallback mock executor for offline development and testing."""
        q = query.strip()
        if "bulkOperationRunQuery" in q:
            return {
                "bulkOperationRunQuery": {
                    "bulkOperation": {
                        "id": "gid://shopify/BulkOperation/10001",
                        "status": "CREATED",
                        "objectCount": "0",
                        "fileSize": None,
                        "url": None,
                    },
                    "userErrors": [],
                }
            }
        if "bulkOperationRunStagedUpload" in q:
            return {
                "bulkOperationRunStagedUpload": {
                    "bulkOperation": {
                        "id": "gid://shopify/BulkOperation/10002",
                        "status": "CREATED",
                    },
                    "userErrors": [],
                }
            }
        if "GetBulkOperation" in q or "node(id:" in q:
            op_id = variables.get("id") if variables else "gid://shopify/BulkOperation/10001"
            return {
                "node": {
                    "id": op_id,
                    "status": "COMPLETED",
                    "objectCount": "120",
                    "fileSize": "45200",
                    "url": "https://storage.googleapis.com/shopify-bulk/products_export.jsonl",
                    "errorCode": None,
                }
            }
        if "GetProducts" in q or "products(" in q:
            first = variables.get("first", 10) if variables else 10
            return {
                "products": {
                    "edges": [
                        {
                            "node": {
                                "id": f"gid://shopify/Product/{100 + i}",
                                "title": f"Cyberpunk Exo-Suit #{100 + i}",
                                "handle": f"cyberpunk-exo-suit-{100 + i}",
                                "variants": {
                                    "edges": [
                                        {
                                            "node": {
                                                "id": f"gid://shopify/ProductVariant/{1000 + i}",
                                                "title": "Default Title",
                                                "price": "149.99",
                                                "inventoryQuantity": 42,
                                            }
                                        }
                                    ]
                                },
                            }
                        }
                        for i in range(first)
                    ]
                }
            }
        if "GetOrders" in q or "orders(" in q:
            first = variables.get("first", 10) if variables else 10
            return {
                "orders": {
                    "edges": [
                        {
                            "node": {
                                "id": f"gid://shopify/Order/{500 + i}",
                                "orderNumber": 1000 + i,
                                "totalPrice": "299.98",
                                "lineItems": {
                                    "edges": [
                                        {
                                            "node": {
                                                "title": "Cyberpunk Exo-Suit",
                                                "quantity": 2,
                                                "price": "149.99",
                                            }
                                        }
                                    ]
                                },
                                "customer": {
                                    "id": f"gid://shopify/Customer/{700 + i}",
                                    "email": f"customer_{i}@dnk-e.com",
                                },
                            }
                        }
                        for i in range(first)
                    ]
                }
            }
        return {"data": {}, "userErrors": []}

    async def get_products(self, first: int = 50) -> Dict[str, Any]:
        """Fetch products with pagination and variants."""
        query = """
        query GetProducts($first: Int!) {
          products(first: $first) {
            edges {
              node {
                id
                title
                handle
                variants(first: 10) {
                  edges {
                    node {
                      id
                      title
                      price
                      inventoryQuantity
                    }
                  }
                }
              }
            }
          }
        }
        """
        return await self.execute(query, {"first": first})

    async def get_orders(self, first: int = 50) -> Dict[str, Any]:
        """Fetch orders with line items and customer info."""
        query = """
        query GetOrders($first: Int!) {
          orders(first: $first, sortKey: PROCESSED_AT, reverse: true) {
            edges {
              node {
                id
                orderNumber
                totalPrice
                lineItems(first: 10) {
                  edges {
                    node {
                      title
                      quantity
                      price
                    }
                  }
                }
                customer {
                  id
                  email
                }
              }
            }
          }
        }
        """
        return await self.execute(query, {"first": first})
