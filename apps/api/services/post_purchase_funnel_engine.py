# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_post_purchase_funnel_engine"
# purpose: "Shopify 1-Click Post-Purchase Upsell/Downsell Funnel & Margin Engine (DNK-ECOM-006 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import hmac
import hashlib
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


class PostPurchaseFunnelEngine:
    """
    1-Click Post-Purchase Upsell and Downsell Funnel Engine with margin optimization,
    dynamic discount calculation, and signed token expiration.
    """

    SECRET_KEY = "dnk_post_purchase_internal_secret_key"

    @classmethod
    def calculate_discounted_price(
        cls,
        original_price: float,
        discount_type: str,
        discount_value: float,
    ) -> float:
        """
        Calculate offer price given discount type and value.
        """
        if discount_type == "percentage":
            discount_amount = original_price * (discount_value / 100.0)
            return max(0.0, round(original_price - discount_amount, 2))
        elif discount_type == "fixed_amount":
            return max(0.0, round(original_price - discount_value, 2))
        elif discount_type == "free_shipping":
            return round(original_price, 2)
        return round(original_price, 2)

    @classmethod
    def calculate_margin_score(
        cls,
        offer_price: float,
        cogs: float = 0.0,
    ) -> float:
        """
        Calculate profit margin efficiency score (0.0 to 1.0).
        """
        if offer_price <= 0.0:
            return 0.0
        profit = max(0.0, offer_price - cogs)
        return round(profit / offer_price, 4)

    @classmethod
    def generate_token(
        cls,
        order_id: str,
        offer_id: str,
        expires_at: int,
    ) -> str:
        """
        Generate HMAC-SHA256 signature token for the post-purchase offer acceptance.
        """
        msg = f"{order_id}:{offer_id}:{expires_at}"
        signature = hmac.new(
            cls.SECRET_KEY.encode("utf-8"),
            msg.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return f"{expires_at}.{signature}"

    @classmethod
    def verify_token(
        cls,
        order_id: str,
        offer_id: str,
        token: str,
    ) -> bool:
        """
        Verify if the offer token is valid and not expired.
        """
        try:
            parts = token.split(".", 1)
            if len(parts) != 2:
                return False
            expires_at_str, signature = parts
            expires_at = int(expires_at_str)

            now = int(time.time())
            if now > expires_at:
                return False  # Expired

            msg = f"{order_id}:{offer_id}:{expires_at}"
            expected_sig = hmac.new(
                cls.SECRET_KEY.encode("utf-8"),
                msg.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_sig, signature)
        except Exception:
            return False

    @classmethod
    def evaluate_offer_eligibility(
        cls,
        offer: Dict[str, Any],
        order_context: Dict[str, Any],
    ) -> bool:
        """
        Check if an offer is eligible for the completed order context.
        """
        if offer.get("status") != "active":
            return False

        rules = offer.get("trigger_rules", {})
        min_order_total = rules.get("min_order_total")
        order_total = float(order_context.get("total_price", 0.0))
        if min_order_total is not None and order_total < float(min_order_total):
            return False

        required_products = rules.get("trigger_product_ids")
        order_product_ids = {
            str(item.get("product_id"))
            for item in order_context.get("line_items", [])
            if item.get("product_id")
        }

        if required_products:
            if not any(str(p) in order_product_ids for p in required_products):
                return False

        # Don't offer a product they already purchased in this order
        offer_prod_id = str(offer.get("product_id"))
        if rules.get("exclude_already_purchased", True) and offer_prod_id in order_product_ids:
            return False

        return True

    @classmethod
    def select_primary_upsell(
        cls,
        offers: List[Dict[str, Any]],
        order_context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Select the best matching post-purchase upsell offer for the completed order.
        """
        eligible = []
        for offer in offers:
            if cls.evaluate_offer_eligibility(offer, order_context):
                orig_price = float(offer.get("original_price", 0.0))
                disc_type = offer.get("discount_type", "percentage")
                disc_val = float(offer.get("discount_value", 15.0))
                offer_price = cls.calculate_discounted_price(orig_price, disc_type, disc_val)
                cogs = float(offer.get("cogs", orig_price * 0.3))  # Estimated COGS
                margin_score = cls.calculate_margin_score(offer_price, cogs)

                eligible.append({
                    "offer": offer,
                    "offer_price": offer_price,
                    "margin_score": margin_score,
                    "priority": int(offer.get("priority", 1)),
                })

        if not eligible:
            return None

        # Sort by priority (descending), then margin_score (descending)
        eligible.sort(key=lambda x: (x["priority"], x["margin_score"]), reverse=True)
        top = eligible[0]
        offer_data = top["offer"].copy()

        # Compute dynamic offer details
        timer_seconds = int(offer_data.get("timer_seconds", 300))
        now = int(time.time())
        expires_at = now + timer_seconds
        order_id = str(order_context.get("order_id", "order_unknown"))
        token = cls.generate_token(order_id, str(offer_data.get("id")), expires_at)

        return {
            "offer_id": offer_data.get("id"),
            "name": offer_data.get("name"),
            "headline": offer_data.get("headline"),
            "product_id": offer_data.get("product_id"),
            "variant_id": offer_data.get("variant_id"),
            "original_price": float(offer_data.get("original_price", 0.0)),
            "discount_type": offer_data.get("discount_type", "percentage"),
            "discount_value": float(offer_data.get("discount_value", 15.0)),
            "offer_price": top["offer_price"],
            "currency": order_context.get("currency", "USD"),
            "margin_score": top["margin_score"],
            "timer_seconds": timer_seconds,
            "expires_at": expires_at,
            "token": token,
        }

    @classmethod
    def select_downsell_offer(
        cls,
        declined_offer_id: str,
        offers: List[Dict[str, Any]],
        order_context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Select a downsell offer when the primary upsell is declined.
        Downsell offers have higher discounts or lower entry prices.
        """
        remaining_offers = [
            o for o in offers
            if str(o.get("id")) != declined_offer_id and str(o.get("offer_type")) == "downsell"
        ]
        if not remaining_offers:
            # Fallback to any other eligible offer
            remaining_offers = [o for o in offers if str(o.get("id")) != declined_offer_id]

        return cls.select_primary_upsell(remaining_offers, order_context)
