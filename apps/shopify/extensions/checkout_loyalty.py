# --- DNK-MRH-HEADER ---
# mrh_id: "apps/shopify/extensions/checkout_loyalty.py"
# purpose: "Shopify Checkout UI Extension Python business logic engine for Loyalty Points"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class LoyaltyRedemptionResult(BaseModel):
    success: bool
    customer_id: str
    points_used: int
    remaining_points: int
    discount_amount: float
    currency: str = "USD"
    message: str


class CheckoutLoyaltyEngine:
    """
    Shopify Checkout Loyalty Points Engine for customer rewards redemption.
    """

    # In-memory customer balance store for simulation / integration
    _CUSTOMER_POINTS_DB: Dict[str, int] = {
        "customer-123": 250,
        "customer-vip": 1000,
        "customer-new": 50,
    }

    def __init__(
        self,
        customer_id: str,
        conversion_rate: float = 0.1,  # 10 points = $1.00 => $0.10 per point
        max_discount_percentage: float = 50.0,
    ):
        self.customer_id = customer_id
        self.conversion_rate = conversion_rate
        self.max_discount_percentage = max_discount_percentage

    def get_available_points(self) -> int:
        return self._CUSTOMER_POINTS_DB.get(self.customer_id, 100)

    def calculate_discount_value(self, points: int) -> float:
        return round(points * self.conversion_rate, 2)

    def apply_points(self, points_to_use: int, cart_total: Optional[float] = None) -> LoyaltyRedemptionResult:
        available = self.get_available_points()
        if points_to_use <= 0:
            return LoyaltyRedemptionResult(
                success=False,
                customer_id=self.customer_id,
                points_used=0,
                remaining_points=available,
                discount_amount=0.0,
                message="Points to use must be greater than zero.",
            )

        if points_to_use > available:
            return LoyaltyRedemptionResult(
                success=False,
                customer_id=self.customer_id,
                points_used=0,
                remaining_points=available,
                discount_amount=0.0,
                message=f"Insufficient points. Available: {available}, requested: {points_to_use}.",
            )

        discount_amount = self.calculate_discount_value(points_to_use)

        if cart_total is not None and cart_total > 0:
            max_allowed_discount = round(cart_total * (self.max_discount_percentage / 100.0), 2)
            if discount_amount > max_allowed_discount:
                discount_amount = max_allowed_discount
                # Recalculate points used
                points_to_use = int(discount_amount / self.conversion_rate)

        remaining = available - points_to_use
        self._CUSTOMER_POINTS_DB[self.customer_id] = remaining

        return LoyaltyRedemptionResult(
            success=True,
            customer_id=self.customer_id,
            points_used=points_to_use,
            remaining_points=remaining,
            discount_amount=discount_amount,
            message=f"Successfully applied {points_to_use} points for a ${discount_amount:.2f} discount.",
        )
