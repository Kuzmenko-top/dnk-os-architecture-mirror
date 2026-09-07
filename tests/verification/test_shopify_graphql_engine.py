# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-VERIFY-SHOPIFY-GRAPHQL-001"
# purpose: "Comprehensive Unit and Integration Tests for Shopify Admin API GraphQL Engine & Bulk Operations"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import time
import pytest
from apps.api.services.rate_limiter import TokenBucketRateLimiter
from apps.api.services.shopify_graphql_engine import ShopifyGraphQLEngine
from apps.api.services.shopify_bulk_operations import ShopifyBulkOperations
from apps.api.services.shopify_sync_engine import ShopifySyncEngine


class TestTokenBucketRateLimiter:
    @pytest.mark.asyncio
    async def test_burst_and_wait(self):
        # 600 req/min = 10 req/sec, burst = 5
        limiter = TokenBucketRateLimiter(rate=600, burst=5)

        # Acquire 5 burst tokens instantaneously
        for _ in range(5):
            await limiter.acquire(cost=1.0)

        # 6th token must trigger wait
        start = time.monotonic()
        await limiter.acquire(cost=1.0)
        elapsed = time.monotonic() - start

        assert elapsed >= 0.05

    @pytest.mark.asyncio
    async def test_context_manager(self):
        limiter = TokenBucketRateLimiter(rate=6000, burst=10)
        async with limiter:
            pass
        assert limiter.tokens <= 10.0


class TestShopifyGraphQLEngine:
    @pytest.mark.asyncio
    async def test_get_products(self):
        engine = ShopifyGraphQLEngine("test-shop.myshopify.com", "test-token")
        result = await engine.get_products(first=5)
        assert "products" in result
        edges = result["products"]["edges"]
        assert len(edges) == 5
        assert "title" in edges[0]["node"]
        assert "variants" in edges[0]["node"]

    @pytest.mark.asyncio
    async def test_get_orders(self):
        engine = ShopifyGraphQLEngine("test-shop.myshopify.com", "test-token")
        result = await engine.get_orders(first=3)
        assert "orders" in result
        edges = result["orders"]["edges"]
        assert len(edges) == 3
        assert "orderNumber" in edges[0]["node"]
        assert "customer" in edges[0]["node"]

    @pytest.mark.asyncio
    async def test_custom_mock_handler(self):
        def custom_handler(query, vars):
            return {"custom": "ok", "vars": vars}

        engine = ShopifyGraphQLEngine("test-shop.myshopify.com", "test-token", mock_handler=custom_handler)
        res = await engine.execute("query Test { test }", {"var1": "val1"})
        assert res == {"custom": "ok", "vars": {"var1": "val1"}}


class TestShopifyBulkOperations:
    @pytest.mark.asyncio
    async def test_bulk_export_products(self):
        engine = ShopifyGraphQLEngine("test-shop.myshopify.com", "test-token")
        bulk = ShopifyBulkOperations(engine)
        op_id = await bulk.bulk_export_products()
        assert op_id.startswith("gid://shopify/BulkOperation/")

    @pytest.mark.asyncio
    async def test_bulk_import_products(self):
        engine = ShopifyGraphQLEngine("test-shop.myshopify.com", "test-token")
        bulk = ShopifyBulkOperations(engine)
        op_id = await bulk.bulk_import_products("https://storage.googleapis.com/csv/products.csv")
        assert op_id.startswith("gid://shopify/BulkOperation/")

    @pytest.mark.asyncio
    async def test_get_bulk_operation_status_and_wait(self):
        engine = ShopifyGraphQLEngine("test-shop.myshopify.com", "test-token")
        bulk = ShopifyBulkOperations(engine)
        status = await bulk.wait_for_completion("gid://shopify/BulkOperation/10001", poll_interval=0.01)
        assert status.get("status") == "COMPLETED"
        assert "url" in status


class TestShopifySyncEngine:
    @pytest.mark.asyncio
    async def test_sync_products_to_local(self):
        engine = ShopifyGraphQLEngine("test-shop.myshopify.com", "test-token")
        sync_engine = ShopifySyncEngine(engine)
        report = await sync_engine.sync_products_to_local()
        assert report["status"] == "success"
        assert report["products_synced"] == 2
        assert len(sync_engine._local_products) == 2

    @pytest.mark.asyncio
    async def test_sync_orders_to_local(self):
        engine = ShopifyGraphQLEngine("test-shop.myshopify.com", "test-token")
        sync_engine = ShopifySyncEngine(engine)
        report = await sync_engine.sync_orders_to_local(limit=4)
        assert report["status"] == "success"
        assert report["orders_synced"] == 4
        assert len(sync_engine._local_orders) == 4

    @pytest.mark.asyncio
    async def test_sync_local_to_shopify(self):
        engine = ShopifyGraphQLEngine("test-shop.myshopify.com", "test-token")
        sync_engine = ShopifySyncEngine(engine)
        products = [
            {"title": "Neural Implant V1", "price": 499.00},
            {"title": "Cybernetic Arm T-800", "price": 1299.00},
        ]
        report = await sync_engine.sync_local_to_shopify(products)
        assert report["status"] == "COMPLETED"
        assert report["products_imported"] == 2
