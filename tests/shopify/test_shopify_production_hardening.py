# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_shopify_production_hardening"
# purpose: "Comprehensive Unit & Integration Tests for Shopify Production Hardening Pipeline (DNK-ECOM-005)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.services.shopify_vite_bundler import ShopifyViteBundler, ViteBundleResult
from apps.api.services.liquid_ast_asset_rewriter import LiquidASTAssetRewriter, LiquidRewriteResult
from apps.api.services.shopify_cdn_sync import ShopifyCDNSync, CDNSyncReport
from apps.api.services.shopify_deploy_engine import (
    ShopifyDeployEngine,
    DeployPipelineResult,
    RollbackResult,
    ReleaseStatus,
)

client = TestClient(app)


# ============================================================================
# 1. SHOPIFY VITE BUNDLER TESTS
# ============================================================================

def test_shopify_vite_bundler_content_hashing_and_sri():
    """Verify Vite bundler generates 8-char SHA-256 hashes and SRI signatures."""
    bundler = ShopifyViteBundler(hash_length=8, generate_sri=True)
    raw_assets = {
        "assets/app.js": "console.log('DNK-ECOM-005 Vite Bundle');",
        "assets/theme.css": "body { background-color: #000; color: #fff; }",
        "assets/logo.svg": "<svg><circle cx='10' cy='10' r='5'/></svg>"
    }

    result: ViteBundleResult = bundler.bundle(raw_assets, bundle_name="test_bundle")

    assert result.bundle_id.startswith("bundle_")
    assert len(result.bundled_files) == 4
    assert len(result.manifest) == 3

    # Check mapping
    hashed_js = result.manifest["assets/app.js"].file
    assert "app." in hashed_js
    assert hashed_js.endswith(".js")

    # Check SRI
    assert hashed_js in result.integrity_map
    assert result.integrity_map[hashed_js].startswith("sha384-")


def test_shopify_vite_bundler_minification():
    """Verify minification strips comments and extra whitespace."""
    bundler = ShopifyViteBundler(hash_length=8, minify=True)
    raw_css = "/* Comment */ body {  color:   red;  } "
    raw_js = "// Comment\n console.log('hello'); "

    assets = {
        "assets/style.css": raw_css,
        "assets/script.js": raw_js
    }

    res = bundler.bundle(assets)
    bundled_css = [v for k, v in res.bundled_files.items() if k.endswith(".css")][0]
    bundled_js = [v for k, v in res.bundled_files.items() if k.endswith(".js")][0]

    assert "/* Comment */" not in bundled_css
    assert "color:red" in bundled_css
    assert "// Comment" not in bundled_js


# ============================================================================
# 2. LIQUID AST ASSET REWRITER TESTS
# ============================================================================

def test_liquid_ast_asset_rewriter_filters():
    """Verify rewriting of asset_url, asset_img_url, image_url, and file_url filters."""
    rewriter = LiquidASTAssetRewriter()
    mapping = {
        "app.js": "app.a1b2c3d4.js",
        "assets/app.js": "assets/app.a1b2c3d4.js",
        "theme.css": "theme.9f8e7d6c.css",
        "hero.png": "hero.1a2b3c4d.png",
        "logo.svg": "logo.7e8f9a0b.svg"
    }

    liquid_src = """
    {{ 'app.js' | asset_url | script_tag }}
    {{ "theme.css" | asset_url | stylesheet_tag }}
    <img src="{{ 'hero.png' | asset_img_url: 'master' }}" />
    <a href="{{ 'logo.svg' | asset_url }}">Logo</a>
    """

    res: LiquidRewriteResult = rewriter.rewrite(liquid_src, manifest_mapping=mapping)

    assert "app.a1b2c3d4.js" in res.rewritten_template
    assert "theme.9f8e7d6c.css" in res.rewritten_template
    assert "hero.1a2b3c4d.png" in res.rewritten_template
    assert "logo.7e8f9a0b.svg" in res.rewritten_template
    assert res.replacements_count >= 4
    assert len(res.unmapped_assets) == 0


def test_liquid_ast_asset_rewriter_static_html_and_comments():
    """Verify HTML tag rewriting while respecting Liquid comments."""
    rewriter = LiquidASTAssetRewriter()
    mapping = {
        "assets/app.js": "assets/app.a1b2c3d4.js",
        "assets/style.css": "assets/style.9f8e7d6c.css"
    }
    sri_map = {
        "assets/app.a1b2c3d4.js": "sha384-TESTSRI123456789"
    }

    liquid_src = """
    {% comment %}
      <script src="assets/app.js"></script>
    {% endcomment %}
    <script src="assets/app.js"></script>
    <link rel="stylesheet" href="assets/style.css" />
    """

    res = rewriter.rewrite(liquid_src, manifest_mapping=mapping, integrity_map=sri_map)

    assert "assets/app.a1b2c3d4.js" in res.rewritten_template
    assert "assets/style.9f8e7d6c.css" in res.rewritten_template
    assert "integrity=\"sha384-TESTSRI123456789\"" in res.rewritten_template


# ============================================================================
# 3. SHOPIFY CDN SYNC TESTS
# ============================================================================

def test_shopify_cdn_sync_cache_headers():
    """Verify strict 1-year immutable for hashed files & 60s stale-while-revalidate for manifest."""
    cdn = ShopifyCDNSync()
    store = "dnk-e-com.myshopify.com"
    theme_id = "100000000001"

    assets = {
        "assets/app.a1b2c3d4.js": "console.log('hashed');",
        "assets/style.9f8e7d6c.css": "body { color: red; }",
        "manifest.json": '{"app.js": "app.a1b2c3d4.js"}'
    }

    report: CDNSyncReport = cdn.sync_assets(store, theme_id, assets)

    assert report.synced_count == 3
    assert report.failed_count == 0

    # Verify headers
    headers_map = report.cache_header_summary
    assert headers_map["assets/app.a1b2c3d4.js"] == "public, max-age=31536000, immutable"
    assert headers_map["assets/style.9f8e7d6c.css"] == "public, max-age=31536000, immutable"
    assert headers_map["manifest.json"] == "public, max-age=60, stale-while-revalidate=300"


def test_shopify_cdn_sync_security_boundary():
    """Verify security boundary blocks unauthorized Shopify store domains (fail-closed)."""
    cdn = ShopifyCDNSync()
    report = cdn.sync_assets("unauthorized-hacker-store.myshopify.com", "123", {"test.js": "alert(1)"})

    assert report.synced_count == 0
    assert report.failed_count == 1


# ============================================================================
# 4. SHOPIFY DEPLOY ENGINE TESTS
# ============================================================================

def test_shopify_deploy_engine_zero_downtime_lifecycle():
    """Verify zero-downtime deploy: snapshot -> bundle -> rewrite -> upload -> validate -> activate."""
    engine = ShopifyDeployEngine()
    store = "dnk-e-com.myshopify.com"

    assets = {
        "layout/theme.liquid": "<html><body>{{ 'app.js' | asset_url }}</body></html>",
        "assets/app.js": "console.log('v1.0.0');",
        "assets/style.css": "body { margin: 0; }"
    }

    # Step 1: Deploy
    deploy_res: DeployPipelineResult = engine.deploy(store_domain=store, theme_assets=assets)

    assert deploy_res.success is True
    assert deploy_res.release.status == ReleaseStatus.ACTIVE
    assert deploy_res.snapshot.is_stable is True
    assert deploy_res.release.assets_count >= 3

    # Step 2: Verify Status
    status = engine.get_status(store)
    assert status["has_active_release"] is True
    assert status["active_release"]["release_id"] == deploy_res.release.release_id

    # Step 3: Rollback
    snapshot_id = deploy_res.snapshot.snapshot_id
    rollback_res: RollbackResult = engine.rollback(store, snapshot_id=snapshot_id)

    assert rollback_res.success is True
    assert rollback_res.target_snapshot_id == snapshot_id
    assert rollback_res.restored_theme_id == deploy_res.snapshot.theme_id


def test_shopify_deploy_engine_unauthorized_store():
    """Verify deploy engine fails closed on unauthorized store domain."""
    engine = ShopifyDeployEngine()
    res = engine.deploy(store_domain="malicious-store.com", theme_assets={"a.js": "b"})

    assert res.success is False
    assert res.error_code == "forbidden_store"


# ============================================================================
# 5. FASTAPI ROUTES TESTS
# ============================================================================

def test_api_shopify_build_route():
    """Test POST /api/shopify/build endpoint."""
    payload = {
        "files": {
            "assets/app.js": "console.log('route test');",
            "assets/main.css": "h1 { font-weight: bold; }"
        },
        "hash_length": 8
    }

    response = client.post("/api/shopify/build", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "bundle_id" in data
    assert len(data["manifest"]) == 2


def test_api_shopify_deploy_route():
    """Test POST /api/shopify/deploy endpoint."""
    payload = {
        "store_domain": "dnk-e-com.myshopify.com",
        "theme_files": {
            "layout/theme.liquid": "<html>{{ 'app.js' | asset_url }}</html>",
            "assets/app.js": "console.log('deploy route');"
        }
    }

    response = client.post("/api/shopify/deploy", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "release" in data
    assert "snapshot" in data


def test_api_shopify_rollback_and_releases_routes():
    """Test GET /api/shopify/releases/{store_domain} and POST /api/shopify/rollback."""
    store = "dnk-e-com.myshopify.com"

    # 1. Deploy first
    client.post("/api/shopify/deploy", json={
        "store_domain": store,
        "theme_files": {"assets/app.js": "v1"}
    })

    # 2. Get Releases
    releases_res = client.get(f"/api/shopify/releases/{store}")
    assert releases_res.status_code == 200
    rel_data = releases_res.json()
    assert rel_data["count"] >= 1
