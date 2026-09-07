# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_checkout_customization_service"
# purpose: "Delivery & Payment Customization Service for Shopify Functions (DNK-ECOM-005 Phase 3)"
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


class ShopifyCheckoutCustomizationService:
    """
    Business service managing Delivery Customization & Payment Customization Shopify Functions.
    """

    def __init__(self, wasm_engine: Optional[ShopifyFunctionsWasmEngine] = None):
        self.wasm_engine = wasm_engine or ShopifyFunctionsWasmEngine()
        self._delivery_rules: Dict[str, List[Dict[str, Any]]] = {}
        self._payment_rules: Dict[str, List[Dict[str, Any]]] = {}

    # Delivery Rules
    def register_delivery_rule(self, workspace_id: str, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Register delivery customization rule."""
        if workspace_id not in self._delivery_rules:
            self._delivery_rules[workspace_id] = []
        rule_id = rule.get("rule_id", f"deliv-{len(self._delivery_rules[workspace_id]) + 1}")
        entry = {**rule, "rule_id": rule_id, "enabled": rule.get("enabled", True)}
        self._delivery_rules[workspace_id].append(entry)
        return entry

    def list_delivery_rules(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List active delivery customization rules for a workspace."""
        return self._delivery_rules.get(workspace_id, [])

    def create_hide_delivery_option_rule(
        self,
        workspace_id: str,
        rule_name: str,
        target_delivery_methods: List[str],
        conditions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create rule to hide specific shipping methods."""
        rule = {
            "rule_name": rule_name,
            "action": "hide",
            "target_delivery_methods": target_delivery_methods,
            "match_conditions": conditions or {},
            "enabled": True,
        }
        return self.register_delivery_rule(workspace_id, rule)

    def create_rename_delivery_option_rule(
        self,
        workspace_id: str,
        rule_name: str,
        target_delivery_method: str,
        rename_to: str,
    ) -> Dict[str, Any]:
        """Create rule to dynamically rename shipping methods."""
        rule = {
            "rule_name": rule_name,
            "action": "rename",
            "target_delivery_methods": [target_delivery_method],
            "parameters": {"rename_to": rename_to},
            "enabled": True,
        }
        return self.register_delivery_rule(workspace_id, rule)

    # Payment Rules
    def register_payment_rule(self, workspace_id: str, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Register payment customization rule."""
        if workspace_id not in self._payment_rules:
            self._payment_rules[workspace_id] = []
        rule_id = rule.get("rule_id", f"pay-{len(self._payment_rules[workspace_id]) + 1}")
        entry = {**rule, "rule_id": rule_id, "enabled": rule.get("enabled", True)}
        self._payment_rules[workspace_id].append(entry)
        return entry

    def list_payment_rules(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List active payment customization rules for a workspace."""
        return self._payment_rules.get(workspace_id, [])

    def create_hide_payment_gateway_rule(
        self,
        workspace_id: str,
        rule_name: str,
        target_payment_methods: List[str],
        conditions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create rule to hide payment gateways conditionally."""
        rule = {
            "rule_name": rule_name,
            "action": "hide",
            "target_payment_methods": target_payment_methods,
            "match_conditions": conditions or {},
            "enabled": True,
        }
        return self.register_payment_rule(workspace_id, rule)

    # Evaluations
    def evaluate_delivery_customization(
        self, workspace_id: str, delivery_input: Dict[str, Any]
    ) -> WasmExecutionResult:
        """Evaluate delivery options against active rules."""
        rules = self.list_delivery_rules(workspace_id)
        return self.wasm_engine.execute_function(
            api_type="delivery_customization",
            input_data=delivery_input,
            function_config={"rules": rules},
        )

    def evaluate_payment_customization(
        self, workspace_id: str, payment_input: Dict[str, Any]
    ) -> WasmExecutionResult:
        """Evaluate payment gateways against active rules."""
        rules = self.list_payment_rules(workspace_id)
        return self.wasm_engine.execute_function(
            api_type="payment_customization",
            input_data=payment_input,
            function_config={"rules": rules},
        )
