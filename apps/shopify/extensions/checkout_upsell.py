# --- DNK-MRH-HEADER ---
# mrh_id: "apps/shopify/extensions/checkout_upsell.py"
# purpose: "Shopify Checkout UI Extension Python business logic engine for Dynamic Upsell"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CartLineItemCost(BaseModel):
    amount: float = Field(default=0.0)
    currency_code: str = Field(default="USD")


class CartLineItem(BaseModel):
    id: str
    merchandise_id: Optional[str] = None
    title: Optional[str] = None
    quantity: int = 1
    cost: Dict[str, Any] = Field(default_factory=dict)

    def get_amount(self) -> float:
        if not self.cost:
            return 0.0
        if "totalAmount" in self.cost:
            total = self.cost["totalAmount"]
            if isinstance(total, dict) and "amount" in total:
                try:
                    return float(total["amount"])
                except (ValueError, TypeError):
                    return 0.0
            if isinstance(total, (int, float, str)):
                try:
                    return float(total)
                except (ValueError, TypeError):
                    return 0.0
            return 0.0
        if "amount" in self.cost:
            amt = self.cost["amount"]
            if isinstance(amt, (int, float, str)):
                try:
                    return float(amt)
                except (ValueError, TypeError):
                    return 0.0
        return 0.0


class UpsellRecommendation(BaseModel):
    product_id: str
    title: str
    price: float
    currency: str = "USD"
    discount_percentage: float = 0.0


class CheckoutUpsellEngine:
    """
    Shopify Checkout Upsell Rule Engine for dynamic threshold promotions
    and contextual product recommendations.
    """

    def __init__(self, cart_lines: List[Dict[str, Any]], free_shipping_threshold: float = 100.0):
        self.raw_cart_lines = cart_lines
        self.free_shipping_threshold = free_shipping_threshold
        self.lines: List[CartLineItem] = [CartLineItem(**line) for line in cart_lines]

    def calculate_cart_total(self) -> float:
        return sum(line.get_amount() for line in self.lines)

    def should_show_upsell(self) -> bool:
        total = self.calculate_cart_total()
        return 0.0 < total < self.free_shipping_threshold

    def get_remaining_threshold(self) -> float:
        total = self.calculate_cart_total()
        return max(0.0, self.free_shipping_threshold - total)

    def get_recommended_upsell(self) -> Optional[UpsellRecommendation]:
        if not self.should_show_upsell():
            return None
        remaining = self.get_remaining_threshold()
        # Recommend matching accessory based on gap
        if remaining <= 25.0:
            return UpsellRecommendation(
                product_id="prod_express_warranty",
                title="DNK Extended Warranty & Fast Care",
                price=19.99,
                currency="USD",
                discount_percentage=15.0,
            )
        else:
            return UpsellRecommendation(
                product_id="prod_protective_armor_case",
                title="DNK Heavy-Duty Protective Sleeve",
                price=34.99,
                currency="USD",
                discount_percentage=20.0,
            )
