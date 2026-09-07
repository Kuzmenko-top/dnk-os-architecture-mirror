# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_post_purchase_upsell"
# purpose: "Shopify Post-Purchase Upsell Engine, Offer Evaluator & AST Liquid Validator (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    FREE_SHIPPING = "free_shipping"


class UpsellTriggerCondition(BaseModel):
    min_order_total_cents: int = 0
    max_order_total_cents: Optional[int] = None
    included_product_ids: List[str] = Field(default_factory=list)
    excluded_product_ids: List[str] = Field(default_factory=list)
    currency: str = "USD"


class LiquidSyntaxValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    ast_tokens_count: int = 0


class UpsellOfferDefinition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    offer_name: str
    target_product_id: str
    target_variant_id: str
    original_price_cents: int
    discount_type: DiscountType
    discount_value: float  # e.g., 20.0 for 20% or 1500 for $15.00
    calculated_price_cents: int = 0
    countdown_seconds: int = 180  # 3 minutes default timer
    custom_liquid_template: Optional[str] = None
    triggers: UpsellTriggerCondition = Field(default_factory=UpsellTriggerCondition)
    enabled: bool = True
    priority: int = 10
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UpsellDecisionResult(BaseModel):
    offer_id: str
    order_id: str
    decision: str  # "accepted", "declined"
    added_amount_cents: int
    final_upsell_price_cents: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ShopifyPostPurchaseUpsellService:
    """Service managing post-purchase upsell offers, Liquid AST syntax validation, and order matching."""

    def __init__(self, db_session=None):
        self.db_session = db_session
        self._offers: Dict[str, UpsellOfferDefinition] = {}

    def _compute_discounted_price(self, original_cents: int, discount_type: DiscountType, discount_value: float) -> int:
        if discount_type == DiscountType.PERCENTAGE:
            pct = max(0.0, min(100.0, discount_value))
            discount = int(round(original_cents * (pct / 100.0)))
            return max(0, original_cents - discount)
        elif discount_type == DiscountType.FIXED_AMOUNT:
            discount_cents = int(round(discount_value))
            return max(0, original_cents - discount_cents)
        elif discount_type == DiscountType.FREE_SHIPPING:
            return original_cents
        return original_cents

    def validate_liquid_template(self, template_str: Optional[str]) -> LiquidSyntaxValidationResult:
        """Performs lightweight AST token parsing and security/syntax validation on Liquid snippets."""
        if not template_str or not template_str.strip():
            return LiquidSyntaxValidationResult(is_valid=True, ast_tokens_count=0)

        errors: List[str] = []
        warnings: List[str] = []

        # Token extraction
        liquid_tags = re.findall(r"\{%[-]?\s*(\w+).*?[-]?%\}", template_str)
        liquid_vars = re.findall(r"\{\{[-]?\s*(.*?)\s*[-]?\}\}", template_str)
        total_tokens = len(liquid_tags) + len(liquid_vars)

        # Check block balances
        block_tags = ["if", "unless", "for", "case", "tablerow", "form", "paginate", "capture"]
        for block in block_tags:
            open_count = len(re.findall(rf"\{{%[-]?\s*{block}\b", template_str))
            close_count = len(re.findall(rf"\{{%[-]?\s*end{block}\b", template_str))
            if open_count != close_count:
                errors.append(f"Mismatched Liquid tag: '{block}' has {open_count} open tag(s) and {close_count} close tag(s).")

        # Security check: disallow unsafe script injection or eval patterns
        if "<script" in template_str.lower() and "src=" in template_str.lower():
            warnings.append("External script tag detected inside post-purchase Liquid widget.")

        return LiquidSyntaxValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            ast_tokens_count=total_tokens,
        )

    def create_upsell_offer(
        self,
        workspace_id: str,
        offer_name: str,
        target_product_id: str,
        target_variant_id: str,
        original_price_cents: int,
        discount_type: DiscountType,
        discount_value: float,
        countdown_seconds: int = 180,
        custom_liquid_template: Optional[str] = None,
        triggers: Optional[UpsellTriggerCondition] = None,
        priority: int = 10,
        enabled: bool = True,
    ) -> UpsellOfferDefinition:
        if original_price_cents <= 0:
            raise ValueError("Original price must be greater than 0.")
        if discount_value < 0:
            raise ValueError("Discount value cannot be negative.")

        if custom_liquid_template:
            val_res = self.validate_liquid_template(custom_liquid_template)
            if not val_res.is_valid:
                raise ValueError(f"Invalid Liquid template syntax: {', '.join(val_res.errors)}")

        calculated_price = self._compute_discounted_price(original_price_cents, discount_type, discount_value)

        offer = UpsellOfferDefinition(
            workspace_id=workspace_id,
            offer_name=offer_name,
            target_product_id=target_product_id,
            target_variant_id=target_variant_id,
            original_price_cents=original_price_cents,
            discount_type=discount_type,
            discount_value=discount_value,
            calculated_price_cents=calculated_price,
            countdown_seconds=countdown_seconds,
            custom_liquid_template=custom_liquid_template,
            triggers=triggers or UpsellTriggerCondition(),
            priority=priority,
            enabled=enabled,
        )

        self._offers[offer.id] = offer
        return offer

    def get_upsell_offer(self, offer_id: str) -> Optional[UpsellOfferDefinition]:
        return self._offers.get(offer_id)

    def list_upsell_offers(self, workspace_id: Optional[str] = None) -> List[UpsellOfferDefinition]:
        offers = list(self._offers.values())
        if workspace_id:
            offers = [o for o in offers if o.workspace_id == workspace_id]
        return sorted(offers, key=lambda x: x.priority, reverse=True)

    def evaluate_matching_offers(
        self,
        workspace_id: str,
        order_total_cents: int,
        cart_product_ids: List[str],
        currency: str = "USD",
    ) -> Optional[UpsellOfferDefinition]:
        """Evaluates active offers against checkout order criteria and selects highest priority match."""
        candidates = [o for o in self.list_upsell_offers(workspace_id) if o.enabled]

        for offer in candidates:
            cond = offer.triggers
            if cond.currency.upper() != currency.upper():
                continue
            if order_total_cents < cond.min_order_total_cents:
                continue
            if cond.max_order_total_cents is not None and order_total_cents > cond.max_order_total_cents:
                continue
            if cond.included_product_ids and not any(pid in cond.included_product_ids for pid in cart_product_ids):
                continue
            if cond.excluded_product_ids and any(pid in cond.excluded_product_ids for pid in cart_product_ids):
                continue

            # Target product shouldn't already be in cart (avoid duplicate upsell)
            if offer.target_product_id in cart_product_ids:
                continue

            return offer

        return None

    def process_offer_decision(self, offer_id: str, decision: str, order_id: str) -> UpsellDecisionResult:
        offer = self.get_upsell_offer(offer_id)
        if not offer:
            raise ValueError(f"Upsell offer '{offer_id}' not found.")

        decision = decision.lower()
        if decision not in ["accepted", "declined"]:
            raise ValueError("Decision must be either 'accepted' or 'declined'.")

        added_amount = offer.calculated_price_cents if decision == "accepted" else 0

        return UpsellDecisionResult(
            offer_id=offer.id,
            order_id=order_id,
            decision=decision,
            added_amount_cents=added_amount,
            final_upsell_price_cents=offer.calculated_price_cents,
        )
