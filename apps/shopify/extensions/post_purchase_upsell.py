# --- DNK-MRH-HEADER ---
# mrh_id: "apps/shopify/extensions/post_purchase_upsell.py"
# purpose: "Shopify Post-Purchase UI Extension Python business logic engine for 1-click upsells"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class PostPurchaseOfferSpec(BaseModel):
    offer_id: str
    variant_id: str
    title: str
    description: str
    original_price: float
    discounted_price: float
    currency: str = "USD"
    timer_seconds: int = 180


class PostPurchaseExecutionResult(BaseModel):
    success: bool
    order_id: str
    variant_id: str
    added_amount: float
    currency: str
    new_order_total: float
    message: str


class PostPurchaseUpsellEngine:
    """
    Shopify Post-Purchase Upsell Engine for seamless 1-click order mutations.
    """

    CATALOG_OFFERS: Dict[str, PostPurchaseOfferSpec] = {
        "var_cyber_armor_001": PostPurchaseOfferSpec(
            offer_id="offer_audio_case",
            variant_id="var_cyber_armor_001",
            title="DNK Cyber Armor Magnetic Storage Case",
            description="Exclusive 1-click addition to your completed order. No extra shipping fees!",
            original_price=39.99,
            discounted_price=19.99,
            currency="USD",
            timer_seconds=180,
        ),
        "var_fast_charger_65w": PostPurchaseOfferSpec(
            offer_id="offer_charger",
            variant_id="var_fast_charger_65w",
            title="DNK GaN 65W Fast Charge Adapter",
            description="Ultra-compact multi-port power adapter.",
            original_price=49.99,
            discounted_price=24.99,
            currency="USD",
            timer_seconds=120,
        ),
    }

    def __init__(self, order_id: str, base_order_total: float = 120.0, currency: str = "USD"):
        self.order_id = order_id
        self.base_order_total = base_order_total
        self.currency = currency
        self.accepted_offers: List[PostPurchaseOfferSpec] = []

    def get_eligible_offer(self, variant_id: Optional[str] = None) -> Optional[PostPurchaseOfferSpec]:
        if variant_id is not None:
            return self.CATALOG_OFFERS.get(variant_id)
        return self.CATALOG_OFFERS.get("var_cyber_armor_001")

    def execute_upsell(self, variant_id: str) -> PostPurchaseExecutionResult:
        offer = self.get_eligible_offer(variant_id)
        if not offer:
            return PostPurchaseExecutionResult(
                success=False,
                order_id=self.order_id,
                variant_id=variant_id,
                added_amount=0.0,
                currency=self.currency,
                new_order_total=self.base_order_total,
                message=f"Offer not found for variant {variant_id}.",
            )

        self.accepted_offers.append(offer)
        new_total = round(self.base_order_total + offer.discounted_price, 2)

        return PostPurchaseExecutionResult(
            success=True,
            order_id=self.order_id,
            variant_id=offer.variant_id,
            added_amount=offer.discounted_price,
            currency=offer.currency,
            new_order_total=new_total,
            message=f"Added {offer.title} to order #{self.order_id} via 1-click upsell.",
        )
