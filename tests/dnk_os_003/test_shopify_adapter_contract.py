# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_os_003_test_shopify_adapter_contract"
# purpose: "Contract tests asserting JSON Schema and Pydantic validation for ShopifyAdapterResult and Domain models"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone
from apps.api.services.shopify_models import (
    NormalizedShopMeta,
    NormalizedTheme,
    NormalizedThemeAsset,
    NormalizedAssetContent,
    ShopifyRateLimitInfo,
    ShopifyAdapterResult
)


def test_normalized_shop_meta_contract():
    model = NormalizedShopMeta(
        id=987654321,
        name="DNK-e.com Official Store",
        email="contact@dnk-e.com",
        domain="dnk-e.com",
        myshopify_domain="dnk-e-com.myshopify.com",
        currency="USD",
        plan_name="shopify_plus"
    )
    dumped = model.model_dump()
    assert dumped["id"] == 987654321
    assert dumped["myshopify_domain"] == "dnk-e-com.myshopify.com"
    assert dumped["plan_name"] == "shopify_plus"


def test_normalized_theme_contract():
    model = NormalizedTheme(
        id=160000001,
        name="Dawn Production 2026",
        role="main",
        created_at="2026-01-15T08:00:00Z",
        updated_at="2026-08-28T09:30:00Z",
        previewable=True,
        processing=False
    )
    dumped = model.model_dump()
    assert dumped["role"] == "main"
    assert dumped["previewable"] is True


def test_normalized_theme_asset_and_content_contract():
    asset = NormalizedThemeAsset(
        key="layout/theme.liquid",
        content_type="text/x-liquid",
        size=12450,
        created_at="2026-01-15T08:00:00Z",
        updated_at="2026-08-28T09:30:00Z",
        public_url=None
    )
    assert asset.key == "layout/theme.liquid"
    assert asset.content_type == "text/x-liquid"

    content = NormalizedAssetContent(
        key="layout/theme.liquid",
        theme_id=160000001,
        content_type="text/x-liquid",
        value="<html><body>{{ content_for_layout }}</body></html>",
        attachment=None,
        public_url=None,
        size=52
    )
    assert content.theme_id == 160000001
    assert "{{ content_for_layout }}" in (content.value or "")


def test_shopify_adapter_result_envelope():
    now_iso = datetime.now(timezone.utc).isoformat()
    res = ShopifyAdapterResult(
        data={"name": "DNK-e.com Official Store"},
        data_source="live",
        stale=False,
        fetched_at=now_iso,
        expires_at=now_iso,
        error_code=None,
        rate_limit_info=ShopifyRateLimitInfo(call_limit="1/40", cost_limit="50/1000", retry_after=None)
    )
    dumped = res.model_dump()
    assert dumped["data_source"] == "live"
    assert dumped["stale"] is False
    assert dumped["error_code"] is None
    assert dumped["rate_limit_info"]["call_limit"] == "1/40"
