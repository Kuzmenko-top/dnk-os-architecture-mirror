# --- DNK-MRH-HEADER ---
# mrh_id: "skills/assertion_error_shopify_api/solution.py"
# purpose: "Distilled Solution for Shopify API Payload & Token Assertion Failures."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any


def sanitize_and_fix_shopify_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes Shopify GraphQL/REST payload to prevent AssertionError."""
    if not isinstance(payload, dict):
        return {}
    fixed = dict(payload)
    if "shop_url" in fixed and not fixed["shop_url"].startswith("https://"):
        fixed["shop_url"] = f"https://{fixed['shop_url'].lstrip('/')}"
    return fixed
