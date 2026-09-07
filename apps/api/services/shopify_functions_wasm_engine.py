# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_functions_wasm_engine"
# purpose: "Wasm Execution & Sandbox Engine for Shopify Functions (DNK-ECOM-005 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import time
import uuid
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

import os

# Execution Limits per Shopify Function Specifications
MAX_MEMORY_BYTES = 10 * 1024 * 1024  # 10 MB limit
MAX_EXECUTION_TIME_MS = float(os.getenv("SHOPIFY_WASM_MAX_TIME_MS", "50.0"))          # Execution target limit (50ms for emulation, 5ms for Wasm native)


@dataclass
class WasmExecutionResult:
    invocation_id: str
    api_type: str
    status: str  # 'success', 'error', 'timeout', 'memory_exceeded'
    output: Dict[str, Any]
    execution_time_ms: float
    memory_usage_bytes: int
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "invocation_id": self.invocation_id,
            "api_type": self.api_type,
            "status": self.status,
            "output": self.output,
            "execution_time_ms": round(self.execution_time_ms, 4),
            "memory_usage_bytes": self.memory_usage_bytes,
            "error_message": self.error_message,
        }


class ShopifyFunctionsWasmEngine:
    """
    High-Performance Wasm & Sandbox Engine for executing Shopify Functions.
    Supports Cart Transform, Discounts, Delivery Customization, Payment Customization, and Order Routing.
    """

    def __init__(self):
        self._handlers: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = {
            "cart_transform": self._default_cart_transform_handler,
            "product_discounts": self._default_discount_handler,
            "order_discounts": self._default_discount_handler,
            "delivery_customization": self._default_delivery_customization_handler,
            "payment_customization": self._default_payment_customization_handler,
            "order_routing": self._default_order_routing_handler,
        }

    def register_custom_handler(
        self,
        api_type: str,
        handler: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """Register custom execution sandbox handler for a specific Function API target."""
        self._handlers[api_type] = handler

    def execute_function(
        self,
        api_type: str,
        input_data: Dict[str, Any],
        function_config: Optional[Dict[str, Any]] = None,
        timeout_ms: float = MAX_EXECUTION_TIME_MS,
        max_memory_bytes: int = MAX_MEMORY_BYTES,
    ) -> WasmExecutionResult:
        """
        Execute Shopify Function within the Wasm sandbox runner with CPU and memory telemetry.
        """
        invocation_id = f"inv-{uuid.uuid4().hex[:12]}"
        config = function_config or {}

        # Validate API type
        if api_type not in self._handlers:
            return WasmExecutionResult(
                invocation_id=invocation_id,
                api_type=api_type,
                status="error",
                output={},
                execution_time_ms=0.0,
                memory_usage_bytes=0,
                error_message=f"Unsupported Shopify Function API target: '{api_type}'",
            )

        start_time = time.perf_counter()
        try:
            # Memory measurement emulation
            serialized_input = json.dumps(input_data)
            input_bytes = len(serialized_input.encode("utf-8"))
            if input_bytes > max_memory_bytes:
                return WasmExecutionResult(
                    invocation_id=invocation_id,
                    api_type=api_type,
                    status="memory_exceeded",
                    output={},
                    execution_time_ms=0.0,
                    memory_usage_bytes=input_bytes,
                    error_message=f"Input payload exceeds Wasm memory budget: {input_bytes} > {max_memory_bytes} bytes",
                )

            # Invoke sandbox handler
            handler = self._handlers[api_type]
            output_data = handler(input_data, config)

            # Measure execution duration
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            output_bytes = len(json.dumps(output_data).encode("utf-8"))
            total_memory_bytes = input_bytes + output_bytes

            status = "success"
            error_msg = None
            if duration_ms > timeout_ms:
                status = "timeout"
                error_msg = f"Execution exceeded maximum CPU budget of {timeout_ms}ms (took {duration_ms:.2f}ms)"

            return WasmExecutionResult(
                invocation_id=invocation_id,
                api_type=api_type,
                status=status,
                output=output_data,
                execution_time_ms=duration_ms,
                memory_usage_bytes=total_memory_bytes,
                error_message=error_msg,
            )

        except Exception as ex:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.exception("Shopify Function execution failed: %s", ex)
            return WasmExecutionResult(
                invocation_id=invocation_id,
                api_type=api_type,
                status="error",
                output={},
                execution_time_ms=duration_ms,
                memory_usage_bytes=0,
                error_message=str(ex),
            )

    # -------------------------------------------------------------------------
    # Default Sandbox Handlers conforming to Shopify Function API Schemas
    # -------------------------------------------------------------------------

    def _default_cart_transform_handler(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cart Transform API handler: evaluates bundle expand, merge, or price overrides.
        """
        operations: List[Dict[str, Any]] = []
        cart = input_data.get("cart", {})
        lines = cart.get("lines", [])
        rules = config.get("rules", [])

        for line in lines:
            line_id = line.get("id")
            merchandise = line.get("merchandise", {})
            variant_id = merchandise.get("id")
            quantity = line.get("quantity", 1)

            for rule in rules:
                if not rule.get("enabled", True):
                    continue
                trigger = rule.get("trigger_criteria", {})
                target_variant = trigger.get("parent_variant_id")
                min_qty = trigger.get("min_quantity", 1)

                if target_variant and target_variant == variant_id and quantity >= min_qty:
                    transform_type = rule.get("transform_type")
                    if transform_type == "bundle_expand":
                        expands = []
                        for op in rule.get("operations", []):
                            expands.append({
                                "merchandiseId": op.get("merchandise_id", variant_id),
                                "quantity": op.get("quantity", 1) * quantity,
                                "price": op.get("price_override"),
                            })
                        operations.append({
                            "expand": {
                                "cartLineId": line_id,
                                "expandedCartItems": expands,
                            }
                        })
                    elif transform_type == "price_override":
                        override_price = rule.get("operations", [{}])[0].get("price_override")
                        if override_price:
                            operations.append({
                                "update": {
                                    "cartLineId": line_id,
                                    "price": override_price,
                                }
                            })

        return {"operations": operations}

    def _default_discount_handler(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Product / Order Discounts API handler: evaluates tiered volume, B2B, and VIP rules.
        """
        discounts: List[Dict[str, Any]] = []
        cart = input_data.get("cart", {})
        lines = cart.get("lines", [])
        customer = input_data.get("customer", {})
        customer_tags = set(customer.get("tags", []))
        rules = config.get("rules", [])

        total_quantity = sum(line.get("quantity", 1) for line in lines)

        for rule in rules:
            if not rule.get("enabled", True):
                continue

            conditions = rule.get("conditions", {})
            min_qty = conditions.get("min_quantity", 0)
            required_tags = set(conditions.get("customer_tags", []))

            # Match conditions
            if required_tags and not (customer_tags & required_tags):
                continue
            if total_quantity < min_qty:
                continue

            # Calculate discount value
            val_type = rule.get("discount_value_type", "percentage")
            val = rule.get("discount_value", 0.0)

            discount_entry: Dict[str, Any] = {
                "message": rule.get("discount_title", "Custom Discount"),
                "targets": [{"cartLine": {"id": line.get("id")}} for line in lines],
            }
            if val_type == "percentage":
                discount_entry["value"] = {"percentage": {"value": str(val)}}
            else:
                discount_entry["value"] = {"fixedAmount": {"amount": str(val)}}

            discounts.append(discount_entry)

        return {"discounts": discounts, "discountApplicationStrategy": "FIRST"}

    def _default_delivery_customization_handler(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Delivery Customization API handler: hides, renames, or moves delivery options.
        """
        operations: List[Dict[str, Any]] = []
        rules = config.get("rules", [])

        # Normalize options from deliveryGroups, deliveryCustomization, or direct deliveryOptions
        delivery_options: List[Dict[str, Any]] = []
        if "deliveryGroups" in input_data:
            for group in input_data.get("deliveryGroups", []):
                delivery_options.extend(group.get("deliveryOptions", []))
        elif "deliveryCustomization" in input_data:
            delivery_options.extend(
                input_data.get("deliveryCustomization", {}).get("deliveryOptions", [])
            )
        elif "deliveryOptions" in input_data:
            delivery_options.extend(input_data.get("deliveryOptions", []))

        for option in delivery_options:
            option_handle = option.get("handle")
            option_title = option.get("title")

            for rule in rules:
                if not rule.get("enabled", True):
                    continue
                targets = rule.get("target_delivery_methods", [])
                if option_title in targets or option_handle in targets:
                    action = rule.get("action")
                    if action == "hide":
                        operations.append({
                            "hide": {
                                "deliveryOptionHandle": option_handle,
                            }
                        })
                    elif action == "rename":
                        new_name = rule.get("parameters", {}).get("rename_to", option_title)
                        operations.append({
                            "rename": {
                                "deliveryOptionHandle": option_handle,
                                "title": new_name,
                            }
                        })

        return {"operations": operations}

    def _default_payment_customization_handler(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Payment Customization API handler: hides or reorders payment gateways.
        """
        operations: List[Dict[str, Any]] = []
        rules = config.get("rules", [])

        # Normalize payment methods
        payment_methods: List[Dict[str, Any]] = []
        if "paymentMethods" in input_data:
            payment_methods.extend(input_data.get("paymentMethods", []))
        elif "paymentCustomization" in input_data:
            payment_methods.extend(
                input_data.get("paymentCustomization", {}).get("paymentMethods", [])
            )

        for method in payment_methods:
            method_name = method.get("name")
            method_id = method.get("id")

            for rule in rules:
                if not rule.get("enabled", True):
                    continue
                targets = rule.get("target_payment_methods", [])
                if method_name in targets or method_id in targets:
                    action = rule.get("action")
                    if action == "hide":
                        operations.append({
                            "hide": {
                                "paymentMethodId": method_id,
                            }
                        })

        return {"operations": operations}

    def _default_order_routing_handler(
        self, input_data: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Order Routing Location Rule API handler: ranks fulfillment locations.
        """
        locations = input_data.get("locations", [])
        ranks = []
        for idx, loc in enumerate(locations):
            ranks.append({
                "locationId": loc.get("id"),
                "rank": idx + 1,
            })
        return {"ranks": ranks}
