# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_dynamic_discount_service"
# purpose: "Dynamic Discount Service for Tiered, Volume, B2B & VIP Shopify Functions (DNK-ECOM-005 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Dict, Any, List, Optional
from apps.api.services.shopify_functions_wasm_engine import ShopifyFunctionsWasmEngine, WasmExecutionResult

logger = logging.getLogger(__name__)


class ShopifyDynamicDiscountService:
    """
    Business service managing Shopify Product & Order Discount Functions (Tiered, B2B, VIP, BXGY).
    """

    def __init__(self, wasm_engine: Optional[ShopifyFunctionsWasmEngine] = None):
        self.wasm_engine = wasm_engine or ShopifyFunctionsWasmEngine()
        self._discount_rules: Dict[str, List[Dict[str, Any]]] = {}

    def register_rule(self, workspace_id: str, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Register a dynamic discount rule for a workspace."""
        if workspace_id not in self._discount_rules:
            self._discount_rules[workspace_id] = []
        
        rule_id = rule.get("rule_id", f"disc-{len(self._discount_rules[workspace_id]) + 1}")
        rule_entry = {**rule, "rule_id": rule_id, "enabled": rule.get("enabled", True)}
        self._discount_rules[workspace_id].append(rule_entry)
        return rule_entry

    def list_rules(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List active discount rules for a workspace."""
        return self._discount_rules.get(workspace_id, [])

    def create_volume_tier_discount(
        self,
        workspace_id: str,
        discount_title: str,
        min_quantity: int,
        percentage_off: float,
    ) -> Dict[str, Any]:
        """Create volume/quantity tiered discount rule."""
        rule = {
            "discount_title": discount_title,
            "discount_type": "tiered_volume",
            "conditions": {"min_quantity": min_quantity},
            "discount_value_type": "percentage",
            "discount_value": percentage_off,
            "enabled": True,
        }
        return self.register_rule(workspace_id, rule)

    def create_b2b_wholesale_discount(
        self,
        workspace_id: str,
        discount_title: str,
        percentage_off: float,
        customer_tags: Optional[List[str]] = None,
        min_cart_total: float = 0.0,
    ) -> Dict[str, Any]:
        """Create B2B/Wholesale account discount rule."""
        tags = customer_tags or ["b2b", "wholesale", "partner"]
        rule = {
            "discount_title": discount_title,
            "discount_type": "b2b_wholesale",
            "conditions": {
                "customer_tags": tags,
                "min_cart_total": min_cart_total,
            },
            "discount_value_type": "percentage",
            "discount_value": percentage_off,
            "enabled": True,
        }
        return self.register_rule(workspace_id, rule)

    def create_vip_fixed_discount(
        self,
        workspace_id: str,
        discount_title: str,
        fixed_amount: float,
        customer_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create VIP customer fixed-amount loyalty discount."""
        tags = customer_tags or ["vip", "gold_tier", "platinum"]
        rule = {
            "discount_title": discount_title,
            "discount_type": "vip_customer",
            "conditions": {"customer_tags": tags},
            "discount_value_type": "fixed_amount",
            "discount_value": fixed_amount,
            "enabled": True,
        }
        return self.register_rule(workspace_id, rule)

    def evaluate_discounts(
        self, workspace_id: str, discount_input: Dict[str, Any]
    ) -> WasmExecutionResult:
        """
        Evaluate full discount payload against all workspace rules via Wasm engine.
        """
        rules = self.list_rules(workspace_id)
        config = {"rules": rules}
        return self.wasm_engine.execute_function(
            api_type="product_discounts",
            input_data=discount_input,
            function_config=config,
        )

    def generate_function_manifest(self, workspace_id: str, function_id: str) -> Dict[str, Any]:
        """
        Generate Shopify Function GraphQL Manifest & Schema for Product Discounts API.
        """
        return {
            "api_version": "2024-07",
            "title": f"Dynamic Discounts Function ({workspace_id})",
            "description": "Tiered Volume, B2B & VIP Discounts Engine by DNK OS",
            "app_key": "dnk_shopify_functions_discounts",
            "targets": [
                {
                    "target": "purchase.product-discount.run",
                    "input_query": """
                    query ProductDiscountsInput {
                      cart {
                        lines {
                          id
                          quantity
                          merchandise {
                            __typename
                            ... on ProductVariant {
                              id
                            }
                          }
                        }
                      }
                      customer {
                        id
                        tags
                      }
                    }
                    """.strip(),
                    "export": "run",
                }
            ],
            "active_rules_count": len(self.list_rules(workspace_id)),
        }
