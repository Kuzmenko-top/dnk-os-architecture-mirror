# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_conftest"
# purpose: "Fixtures for Shopify product sync pilot tests (DNK-SHOPIFY-PILOT-001)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

import tempfile
import pytest
from cryptography.hazmat.primitives import serialization

from core.plugins.plugin_installer import PluginInstaller
from core.plugins.plugin_security_gate import (
    TrustKeyRegistry,
    generate_ed25519_keypair,
    sign_data_ed25519,
    calculate_package_hash,
)
from core.supervisor.shopify_sync_supervisor import ShopifySyncSupervisor


@pytest.fixture
def shopify_pilot_setup():
    temp_store = tempfile.mkdtemp(prefix="shopify_store_")
    registry = TrustKeyRegistry()
    priv_key, pub_key = generate_ed25519_keypair()

    pub_bytes = pub_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    key_id = "shopify_test_key_01"
    registry.register_key(key_id, pub_bytes, "DNK Test Publisher", "active")

    installer = PluginInstaller(base_store_dir=temp_store, key_registry=registry)
    supervisor = ShopifySyncSupervisor(installer=installer)

    return {
        "store_dir": temp_store,
        "registry": registry,
        "priv_key": priv_key,
        "pub_bytes": pub_bytes,
        "key_id": key_id,
        "installer": installer,
        "supervisor": supervisor,
    }


def create_shopify_plugin_package(priv_key, key_id, version="0.1.0", permissions=None, plugin_id="dnk-shopify-sync"):
    permissions = permissions or ["products.read"]
    code_bytes = (
        b"from plugins.dnk_shopify_sync.plugin import DNKShopifySyncPlugin\n"
        b"plugin = DNKShopifySyncPlugin()\n"
    )
    pkg_hash = calculate_package_hash(code_bytes)
    canonical_payload = f"{plugin_id}:{version}:{pkg_hash}".encode("utf-8")
    sig_b64 = sign_data_ed25519(canonical_payload, priv_key)

    raw_manifest = {
        "plugin_id": plugin_id,
        "name": "DNK Shopify Product Sync",
        "version": version,
        "publisher": "DNK Test Publisher",
        "entrypoint": "plugin.py",
        "runtime_compatibility": ">=0.1.0",
        "permissions": permissions,
        "dependencies": {"python": ">=3.12"},
        "content_hash": pkg_hash,
        "signature_metadata": {
            "key_id": key_id,
            "signature": sig_b64,
        }
    }
    return raw_manifest, code_bytes, pkg_hash


@pytest.fixture
def valid_shopify_product_payload():
    return {
        "id": "gid://shopify/Product/1001",
        "title": "ReBurn Sample Product",
        "handle": "reburn-sample-product",
        "status": "ACTIVE",
        "vendor": "DNK Test",
        "product_type": "hardware",
        "tags": ["reburn", "pilot"],
        "variants": [
            {
                "id": "gid://shopify/ProductVariant/2001",
                "sku": "RB-TEST-001",
                "price": "49.00",
                "inventory_quantity": 3
            }
        ]
    }
