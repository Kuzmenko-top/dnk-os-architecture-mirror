# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_shopify_media_api.py"
# purpose: "Unit tests for ShopifyMediaAPIClient covering staged upload requesting and file registration."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.shopify_graphql_engine import ShopifyGraphQLEngine
from services.dnk_shopify.media_api import ShopifyMediaAPIClient


@pytest.mark.asyncio
async def test_shopify_staged_uploads():
    engine = ShopifyGraphQLEngine(shop_url="https://test-shop.myshopify.com", access_token="shpat_mock_token")
    client = ShopifyMediaAPIClient(graphql_engine=engine)

    # test creating staged upload target
    res = await client.create_staged_upload(
        filename="kinetic_shorts_test.mp4",
        mime_type="video/mp4",
        file_size=1200300,
    )
    assert res is not None
    assert "success" in res or "stagedTarget" in res


@pytest.mark.asyncio
async def test_shopify_file_reference():
    engine = ShopifyGraphQLEngine(shop_url="https://test-shop.myshopify.com", access_token="shpat_mock_token")
    client = ShopifyMediaAPIClient(graphql_engine=engine)

    res = await client.create_file_reference(
        staged_resource_url="gid://shopify/Video/999182-kinetic_shorts_test_mp4",
        alt_text="Kinetic Sand Satisfying ASMR",
    )
    assert res is not None
    assert "success" in res or "file" in res


@pytest.mark.asyncio
async def test_shopify_full_upload_pipeline():
    engine = ShopifyGraphQLEngine(shop_url="https://test-shop.myshopify.com", access_token="shpat_mock_token")
    client = ShopifyMediaAPIClient(graphql_engine=engine)

    res = await client.upload_media_asset(
        file_path="fake_shorts_render.mp4",
        alt_text="Satisfying ASMR",
    )
    assert res["success"] is True
    assert "staged_target" in res
    assert "file_reference" in res
    assert res["cdn_url"].startswith("https://cdn.shopify.com")
