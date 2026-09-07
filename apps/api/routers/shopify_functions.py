# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_shopify_functions"
# purpose: "FastAPI Router for Shopify Functions & Wasm Rule Management (DNK-ECOM-005 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from apps.api.services.shopify_functions_wasm_engine import ShopifyFunctionsWasmEngine
from apps.api.services.shopify_cart_transform_service import ShopifyCartTransformService
from apps.api.services.shopify_dynamic_discount_service import ShopifyDynamicDiscountService
from apps.api.services.shopify_checkout_customization_service import ShopifyCheckoutCustomizationService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/shopify/functions",
    tags=["Shopify Functions & Wasm"],
)

# Global engine and service singletons
_wasm_engine = ShopifyFunctionsWasmEngine()
_cart_transform_service = ShopifyCartTransformService(wasm_engine=_wasm_engine)
_discount_service = ShopifyDynamicDiscountService(wasm_engine=_wasm_engine)
_customization_service = ShopifyCheckoutCustomizationService(wasm_engine=_wasm_engine)


# -----------------------------------------------------------------------------
# Request & Response Models
# -----------------------------------------------------------------------------

class CartTransformRuleCreate(BaseModel):
    workspace_id: str = Field(default="ws-default")
    rule_name: str = Field(default="Bundle Starter Expansion")
    parent_variant_id: str = Field(default="gid://shopify/ProductVariant/bundle-1")
    components: List[Dict[str, Any]] = Field(default_factory=list)
    min_quantity: int = Field(default=1, ge=1)


class PriceOverrideRuleCreate(BaseModel):
    workspace_id: str = Field(default="ws-default")
    rule_name: str = Field(default="VIP Price Override")
    target_variant_id: str = Field(default="gid://shopify/ProductVariant/item-1")
    fixed_price: float = Field(default=0.0, ge=0.0)
    currency_code: str = Field(default="USD")


class DiscountRuleCreate(BaseModel):
    workspace_id: str = Field(default="ws-default")
    discount_title: str = Field(default="Volume Tier 10+")
    discount_type: str = Field(default="tiered_volume")
    min_quantity: int = Field(default=1)
    percentage_off: float = Field(default=0.0)
    customer_tags: Optional[List[str]] = None
    fixed_amount: Optional[float] = None


class DeliveryRuleCreate(BaseModel):
    workspace_id: str = Field(default="ws-default")
    rule_name: str = Field(default="Hide Air Freight")
    action: str = Field(default="hide")  # hide, rename
    target_delivery_methods: List[str] = Field(default_factory=list)
    rename_to: Optional[str] = None


class PaymentRuleCreate(BaseModel):
    workspace_id: str = Field(default="ws-default")
    rule_name: str = Field(default="Hide COD for High-Risk")
    target_payment_methods: List[str] = Field(default_factory=list)


class FunctionEvaluateRequest(BaseModel):
    workspace_id: str = Field(default="ws-default")
    api_type: str = Field(default="cart_transform")
    input_payload: Dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/health")
def get_functions_health():
    """Health check endpoint for Shopify Functions runtime."""
    return {
        "status": "healthy",
        "supported_targets": [
            "cart_transform",
            "product_discounts",
            "order_discounts",
            "delivery_customization",
            "payment_customization",
            "order_routing",
        ],
    }


# Cart Transform Endpoints
@router.post("/cart-transform/rules/bundle")
def create_bundle_expansion_rule(req: CartTransformRuleCreate):
    rule = _cart_transform_service.create_bundle_expansion_rule(
        workspace_id=req.workspace_id,
        rule_name=req.rule_name,
        parent_variant_id=req.parent_variant_id,
        components=req.components,
        min_quantity=req.min_quantity,
    )
    return {"status": "success", "rule": rule}


@router.post("/cart-transform/rules/price-override")
def create_price_override_rule(req: PriceOverrideRuleCreate):
    rule = _cart_transform_service.create_price_override_rule(
        workspace_id=req.workspace_id,
        rule_name=req.rule_name,
        target_variant_id=req.target_variant_id,
        fixed_price=req.fixed_price,
        currency_code=req.currency_code,
    )
    return {"status": "success", "rule": rule}


@router.get("/cart-transform/rules")
def list_cart_transform_rules(workspace_id: str = "ws-default"):
    rules = _cart_transform_service.list_rules(workspace_id)
    return {"workspace_id": workspace_id, "rules": rules}


@router.post("/cart-transform/evaluate")
def evaluate_cart_transform(workspace_id: str, payload: Dict[str, Any]):
    res = _cart_transform_service.evaluate_cart_transformation(workspace_id, payload)
    return res.to_dict()


@router.get("/cart-transform/manifest")
def get_cart_transform_manifest(workspace_id: str = "ws-default"):
    return _cart_transform_service.generate_function_manifest(workspace_id, "fn-cart-transform")


# Dynamic Discount Endpoints
@router.post("/discounts/rules")
def create_discount_rule(req: DiscountRuleCreate):
    if req.discount_type == "tiered_volume":
        rule = _discount_service.create_volume_tier_discount(
            workspace_id=req.workspace_id,
            discount_title=req.discount_title,
            min_quantity=req.min_quantity,
            percentage_off=req.percentage_off,
        )
    elif req.discount_type == "b2b_wholesale":
        rule = _discount_service.create_b2b_wholesale_discount(
            workspace_id=req.workspace_id,
            discount_title=req.discount_title,
            percentage_off=req.percentage_off,
            customer_tags=req.customer_tags,
        )
    elif req.discount_type == "vip_customer":
        rule = _discount_service.create_vip_fixed_discount(
            workspace_id=req.workspace_id,
            discount_title=req.discount_title,
            fixed_amount=req.fixed_amount or 0.0,
            customer_tags=req.customer_tags,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported discount type: {req.discount_type}")
    return {"status": "success", "rule": rule}


@router.get("/discounts/rules")
def list_discount_rules(workspace_id: str = "ws-default"):
    rules = _discount_service.list_rules(workspace_id)
    return {"workspace_id": workspace_id, "rules": rules}


@router.post("/discounts/evaluate")
def evaluate_discounts(workspace_id: str, payload: Dict[str, Any]):
    res = _discount_service.evaluate_discounts(workspace_id, payload)
    return res.to_dict()


@router.get("/discounts/manifest")
def get_discount_manifest(workspace_id: str = "ws-default"):
    return _discount_service.generate_function_manifest(workspace_id, "fn-discounts")


# Checkout Customization Endpoints
@router.post("/delivery/rules")
def create_delivery_rule(req: DeliveryRuleCreate):
    if req.action == "rename" and req.rename_to:
        rule = _customization_service.create_rename_delivery_option_rule(
            workspace_id=req.workspace_id,
            rule_name=req.rule_name,
            target_delivery_method=req.target_delivery_methods[0] if req.target_delivery_methods else "",
            rename_to=req.rename_to,
        )
    else:
        rule = _customization_service.create_hide_delivery_option_rule(
            workspace_id=req.workspace_id,
            rule_name=req.rule_name,
            target_delivery_methods=req.target_delivery_methods,
        )
    return {"status": "success", "rule": rule}


@router.get("/delivery/rules")
def list_delivery_rules(workspace_id: str = "ws-default"):
    rules = _customization_service.list_delivery_rules(workspace_id)
    return {"workspace_id": workspace_id, "rules": rules}


@router.post("/delivery/evaluate")
def evaluate_delivery_customization(workspace_id: str, payload: Dict[str, Any]):
    res = _customization_service.evaluate_delivery_customization(workspace_id, payload)
    return res.to_dict()


@router.post("/payment/rules")
def create_payment_rule(req: PaymentRuleCreate):
    rule = _customization_service.create_hide_payment_gateway_rule(
        workspace_id=req.workspace_id,
        rule_name=req.rule_name,
        target_payment_methods=req.target_payment_methods,
    )
    return {"status": "success", "rule": rule}


@router.get("/payment/rules")
def list_payment_rules(workspace_id: str = "ws-default"):
    rules = _customization_service.list_payment_rules(workspace_id)
    return {"workspace_id": workspace_id, "rules": rules}


@router.post("/payment/evaluate")
def evaluate_payment_customization(workspace_id: str, payload: Dict[str, Any]):
    res = _customization_service.evaluate_payment_customization(workspace_id, payload)
    return res.to_dict()


# Generic Function Evaluation
@router.post("/evaluate")
def evaluate_generic_function(req: FunctionEvaluateRequest):
    if req.api_type == "cart_transform":
        res = _cart_transform_service.evaluate_cart_transformation(req.workspace_id, req.input_payload)
    elif req.api_type in ("product_discounts", "order_discounts"):
        res = _discount_service.evaluate_discounts(req.workspace_id, req.input_payload)
    elif req.api_type == "delivery_customization":
        res = _customization_service.evaluate_delivery_customization(req.workspace_id, req.input_payload)
    elif req.api_type == "payment_customization":
        res = _customization_service.evaluate_payment_customization(req.workspace_id, req.input_payload)
    else:
        res = _wasm_engine.execute_function(req.api_type, req.input_payload)
    return res.to_dict()
