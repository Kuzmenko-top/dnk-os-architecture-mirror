# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_cart_transform_service"
# purpose: "Cart Transform Service for bundle expansion, component splitting & price overrides (DNK-ECOM-005 Phase 3)"
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


class ShopifyCartTransformService:
    """
    Business service managing Cart Transform Shopify Functions and bundle transformations.
    """

    def __init__(self, wasm_engine: Optional[ShopifyFunctionsWasmEngine] = None):
        self.wasm_engine = wasm_engine or ShopifyFunctionsWasmEngine()
        self._rules_store: Dict[str, List[Dict[str, Any]]] = {}

    def register_rule(self, workspace_id: str, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Store or update a cart transform rule for a given workspace."""
        if workspace_id not in self._rules_store:
            self._rules_store[workspace_id] = []
        
        rule_id = rule.get("rule_id", f"rule-{len(self._rules_store[workspace_id]) + 1}")
        rule_entry = {**rule, "rule_id": rule_id, "enabled": rule.get("enabled", True)}
        self._rules_store[workspace_id].append(rule_entry)
        return rule_entry

    def list_rules(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List active transform rules for a workspace."""
        return self._rules_store.get(workspace_id, [])

    def create_bundle_expansion_rule(
        self,
        workspace_id: str,
        rule_name: str,
        parent_variant_id: str,
        components: List[Dict[str, Any]],
        min_quantity: int = 1,
    ) -> Dict[str, Any]:
        """
        Create a bundle expansion rule: automatically splits a bundle parent item into component variants.
        """
        operations = []
        for comp in components:
            operations.append({
                "merchandise_id": comp["variant_id"],
                "quantity": comp.get("quantity", 1),
                "price_override": comp.get("price_override"),
            })

        rule = {
            "rule_name": rule_name,
            "transform_type": "bundle_expand",
            "trigger_criteria": {
                "parent_variant_id": parent_variant_id,
                "min_quantity": min_quantity,
            },
            "operations": operations,
            "enabled": True,
        }
        return self.register_rule(workspace_id, rule)

    def create_price_override_rule(
        self,
        workspace_id: str,
        rule_name: str,
        target_variant_id: str,
        fixed_price: float,
        currency_code: str = "USD",
    ) -> Dict[str, Any]:
        """
        Create a dynamic price override rule for a specific product variant line.
        """
        rule = {
            "rule_name": rule_name,
            "transform_type": "price_override",
            "trigger_criteria": {
                "parent_variant_id": target_variant_id,
                "min_quantity": 1,
            },
            "operations": [
                {
                    "price_override": {
                        "fixedPricePerUnit": {
                            "amount": f"{fixed_price:.2f}",
                            "currencyCode": currency_code,
                        }
                    }
                }
            ],
            "enabled": True,
        }
        return self.register_rule(workspace_id, rule)

    def evaluate_cart_transformation(
        self, workspace_id: str, cart_input: Dict[str, Any]
    ) -> WasmExecutionResult:
        """
        Evaluate full cart payload against all active workspace transform rules via Wasm engine.
        """
        rules = self.list_rules(workspace_id)
        config = {"rules": rules}
        return self.wasm_engine.execute_function(
            api_type="cart_transform",
            input_data=cart_input,
            function_config=config,
        )

    def generate_function_manifest(self, workspace_id: str, function_id: str) -> Dict[str, Any]:
        """
        Generate Shopify Function GraphQL Manifest & Schema definition for Cart Transform API.
        """
        return {
            "api_version": "2024-07",
            "title": f"Cart Transform Function ({workspace_id})",
            "description": "Auto bundle expansion and dynamic price overrides by DNK OS",
            "app_key": "dnk_shopify_functions_cart_transform",
            "targets": [
                {
                    "target": "purchase.cart-transform.run",
                    "input_query": """
                    query CartTransformInput {
                      cart {
                        lines {
                          id
                          quantity
                          cost {
                            totalAmount {
                              amount
                              currencyCode
                            }
                          }
                          merchandise {
                            __typename
                            ... on ProductVariant {
                              id
                              title
                              product {
                                id
                                handle
                              }
                            }
                          }
                        }
                      }
                    }
                    """.strip(),
                    "export": "run",
                }
            ],
            "active_rules_count": len(self.list_rules(workspace_id)),
        }
