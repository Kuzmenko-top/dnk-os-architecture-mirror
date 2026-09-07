# --- DNK-MRH-HEADER ---
# mrh_id: "apps/shopify/extensions/__init__.py"
# purpose: "Shopify App Bridge 2.0 Checkout UI Extensions module export manifest"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

from .checkout_upsell import (
    CheckoutUpsellEngine,
    CheckoutUpsellEngine as CheckoutUpsell,
    CartLineItem,
    UpsellRecommendation,
)
from .checkout_loyalty import (
    CheckoutLoyaltyEngine,
    CheckoutLoyaltyEngine as CheckoutLoyalty,
    LoyaltyRedemptionResult,
)
from .post_purchase_upsell import (
    PostPurchaseUpsellEngine,
    PostPurchaseUpsellEngine as PostPurchaseUpsell,
    PostPurchaseOfferSpec,
    PostPurchaseExecutionResult,
)

__all__ = [
    "CheckoutUpsellEngine",
    "CheckoutUpsell",
    "CartLineItem",
    "UpsellRecommendation",
    "CheckoutLoyaltyEngine",
    "CheckoutLoyalty",
    "LoyaltyRedemptionResult",
    "PostPurchaseUpsellEngine",
    "PostPurchaseUpsell",
    "PostPurchaseOfferSpec",
    "PostPurchaseExecutionResult",
]
