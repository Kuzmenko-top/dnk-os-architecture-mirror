# --- DNK-MRH-HEADER ---
# mrh_id: "plugins_dnk_shopify_sync_plugin"
# purpose: "DNK Shopify Product Sync Test Plugin for Read-Only Dry-Run (DNK-SHOPIFY-PILOT-001)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "0.1.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

import re
from typing import Dict, Any, List
from core.plugins.plugin_base import Plugin

class DNKShopifySyncPlugin(Plugin):
    """
    Shopify Product Sync Plugin (Read-Only / Dry-Run).
    Allowed permissions: products.read
    Forbidden permissions: products.write, orders.read, orders.write, customers.read, credentials.read, network.egress
    """
    def __init__(self):
        self.initialized = False

    @property
    def name(self) -> str:
        return "dnk-shopify-sync"

    @property
    def version(self) -> str:
        return "0.1.0"

    def initialize(self) -> None:
        self.initialized = True

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "preview_product_sync",
                "description": "Normalizes Shopify product payload in read-only dry-run mode",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "payload": {"type": "object"}
                    },
                    "required": ["payload"]
                },
            }
        ]

    def get_event_handlers(self) -> Dict[str, callable]:
        return {
            "shopify_product_sync_dry_run": self.normalize_product_payload
        }

    def extract_external_id(self, raw_id: str) -> str:
        if not raw_id:
            return ""
        # Handle GID format like gid://shopify/Product/1001 or plain string "1001"
        match = re.search(r"(\d+)$", str(raw_id))
        if match:
            return match.group(1)
        return str(raw_id)

    def parse_price_minor(self, price_val: Any) -> int:
        try:
            val_float = float(price_val)
            return int(round(val_float * 100))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid price value: {price_val}")

    def normalize_product_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes raw Shopify product payload fixture and produces deterministic dry-run preview.
        """
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dictionary")

        source_product_id = payload.get("id")
        title = payload.get("title")
        handle = payload.get("handle")
        status = payload.get("status")
        variants = payload.get("variants")

        if not source_product_id or not title or not handle or not status or not isinstance(variants, list) or len(variants) == 0:
            raise ValueError("Missing required Shopify product fields")

        first_variant = variants[0]
        sku = first_variant.get("sku")
        price_raw = first_variant.get("price")
        inventory = first_variant.get("inventory_quantity")

        if sku is None or price_raw is None or inventory is None:
            raise ValueError("Missing required Shopify variant fields")

        external_id = self.extract_external_id(source_product_id)
        price_minor = self.parse_price_minor(price_raw)
        currency = payload.get("currency", "USD")

        # Tags: deduplicated and sorted
        raw_tags = payload.get("tags", [])
        if isinstance(raw_tags, str):
            raw_tags = [t.strip() for t in raw_tags.split(",")]
        normalized_tags = sorted(list(set(raw_tags)))

        normalized_data = {
            "external_id": external_id,
            "title": title,
            "handle": handle,
            "status": str(status).lower(),
            "sku": sku,
            "price_minor": price_minor,
            "currency": currency,
            "inventory_quantity": int(inventory),
            "tags": normalized_tags,
        }

        return {
            "plugin_id": self.name,
            "mode": "dry_run",
            "operation": "product_sync_preview",
            "source_product_id": source_product_id,
            "normalized": normalized_data,
            "mutations": [],
            "write_performed": False
        }
