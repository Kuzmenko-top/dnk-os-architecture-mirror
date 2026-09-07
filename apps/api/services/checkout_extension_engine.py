# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_checkout_extension_engine"
# purpose: "Shopify Checkout UI Extension Evaluation & Widget Content Generation Engine (DNK-ECOM-006 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


class CheckoutExtensionEngine:
    """
    Engine for evaluating conditional rules and generating dynamic widget
    content for Shopify Checkout UI Extensions.
    """

    SUPPORTED_EXTENSION_POINTS = [
        "purchase.checkout.block.render",
        "purchase.checkout.cart-line-item.render-after",
        "purchase.checkout.shipping-option-list.render-after",
        "purchase.checkout.actions.render-before",
        "purchase.thank-you.block.render",
    ]

    SUPPORTED_TYPES = ["cross_sell", "banner", "custom_field", "trust_badge"]

    @classmethod
    def evaluate_rule(cls, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Evaluate if a checkout extension rule matches the given checkout context.
        Context can contain:
          - cart_total: float
          - line_items: list of dicts with product_id, variant_id, price, quantity
          - customer_tags: list of str
          - shipping_country: str (ISO 2-letter)
          - currency: str
        """
        if not rule:
            return True

        cart_total = float(context.get("cart_total", 0.0))
        min_total = rule.get("min_cart_total")
        if min_total is not None and cart_total < float(min_total):
            return False

        max_total = rule.get("max_cart_total")
        if max_total is not None and cart_total > float(max_total):
            return False

        currency = context.get("currency")
        allowed_currencies = rule.get("allowed_currencies")
        if allowed_currencies and currency and currency not in allowed_currencies:
            return False

        shipping_country = context.get("shipping_country")
        allowed_countries = rule.get("allowed_countries")
        if allowed_countries and shipping_country and shipping_country not in allowed_countries:
            return False

        customer_tags = set(context.get("customer_tags", []))
        required_tags = rule.get("required_customer_tags")
        if required_tags:
            if not any(tag in customer_tags for tag in required_tags):
                return False

        cart_product_ids = {
            str(item.get("product_id"))
            for item in context.get("line_items", [])
            if item.get("product_id")
        }

        matching_product_ids = rule.get("matching_product_ids")
        if matching_product_ids:
            if not any(str(pid) in cart_product_ids for pid in matching_product_ids):
                return False

        excluded_product_ids = rule.get("excluded_product_ids")
        if excluded_product_ids:
            if any(str(pid) in cart_product_ids for pid in excluded_product_ids):
                return False

        return True

    @classmethod
    def filter_and_rank_extensions(
        cls,
        extensions: List[Dict[str, Any]],
        extension_point: str,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Filter extensions matching the extension point and context rules, sorted by priority (descending).
        """
        eligible = []
        for ext in extensions:
            if ext.get("status") != "active":
                continue
            if ext.get("extension_point") != extension_point:
                continue

            rules = ext.get("rules_payload", {})
            if cls.evaluate_rule(rules, context):
                eligible.append(ext)

        # Sort by priority descending (higher number = higher priority)
        eligible.sort(key=lambda x: int(x.get("priority", 10)), reverse=True)
        return eligible

    @classmethod
    def generate_widget_payload(
        cls,
        extension: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate structured widget payload ready for client-side rendering in Checkout UI extension.
        """
        ext_type = extension.get("extension_type", "cross_sell")
        config = extension.get("config_schema", {})
        title = extension.get("title", "Special Offer")

        widget = {
            "extension_id": extension.get("id"),
            "extension_point": extension.get("extension_point"),
            "extension_type": ext_type,
            "title": title,
            "rendered_at": datetime.now(timezone.utc).isoformat(),
        }

        if ext_type == "cross_sell":
            products = config.get("products", [])
            discount_pct = float(config.get("discount_percentage", 10.0))
            rendered_products = []
            for prod in products:
                orig_price = float(prod.get("price", 0.0))
                disc_price = round(orig_price * (1.0 - (discount_pct / 100.0)), 2)
                rendered_products.append({
                    "product_id": prod.get("product_id"),
                    "title": prod.get("title", "Recommended Add-on"),
                    "original_price": orig_price,
                    "discounted_price": disc_price,
                    "currency": context.get("currency", "USD"),
                    "image_url": prod.get("image_url"),
                })
            widget["content"] = {
                "headline": config.get("headline", "Frequently Bought Together"),
                "discount_percentage": discount_pct,
                "items": rendered_products,
                "cta_text": config.get("cta_text", "Add to Order"),
            }

        elif ext_type == "banner":
            widget["content"] = {
                "banner_type": config.get("banner_type", "info"),  # info, warning, success
                "message": config.get("message", "Free worldwide shipping on orders over $100!"),
                "icon": config.get("icon", "truck"),
                "dismissible": config.get("dismissible", False),
            }

        elif ext_type == "custom_field":
            widget["content"] = {
                "field_type": config.get("field_type", "text"),  # text, textarea, select, checkbox
                "field_key": config.get("field_key", "order_note"),
                "label": config.get("label", "Special Delivery Instructions"),
                "placeholder": config.get("placeholder", "E.g. Leave package by the side door"),
                "required": config.get("required", False),
                "options": config.get("options", []),
            }

        elif ext_type == "trust_badge":
            widget["content"] = {
                "badges": config.get("badges", [
                    {"type": "money_back", "title": "30-Day Money Back Guarantee", "icon": "shield-check"},
                    {"type": "secure_checkout", "title": "256-Bit SSL Encryption", "icon": "lock"},
                    {"type": "fast_dispatch", "title": "Dispatched within 24 Hours", "icon": "bolt"},
                ]),
                "layout": config.get("layout", "horizontal"),
            }

        else:
            widget["content"] = config

        return widget
