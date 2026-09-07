# --- DNK-MRH-HEADER ---
# mrh_id: "skills/assertion_error_shopify_api/test_assertion_error_shopify_api.py"
# purpose: "Unit tests for Shopify API payload sanitation solution."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from skills.assertion_error_shopify_api.solution import sanitize_and_fix_shopify_payload


def test_sanitize_and_fix_shopify_payload():
    raw_payload = {"shop_url": "my-shop.myshopify.com", "token": "shpat_test"}
    fixed = sanitize_and_fix_shopify_payload(raw_payload)
    assert fixed["shop_url"] == "https://my-shop.myshopify.com"
