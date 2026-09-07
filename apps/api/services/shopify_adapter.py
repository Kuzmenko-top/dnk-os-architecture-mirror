# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_adapter"
# purpose: "Server-side read-only Shopify Admin API adapter with transport isolation, TTL caching, store allowlist, and zero-egress FIXTURE_MODE"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, Set, List, Union

from apps.api.services.shopify_transport import (
    BaseShopifyTransport,
    HttpShopifyTransport,
    SHOPIFY_API_VERSION,
    DEFAULT_TIMEOUT_SECONDS
)
from apps.api.services.shopify_models import (
    ShopifyAdapterResult,
    NormalizedShopMeta,
    NormalizedTheme,
    NormalizedThemeAsset,
    NormalizedAssetContent,
    NormalizedThemeTree,
    ShopifyCanvasNode,
    ShopifyCanvasEdge,
    ShopifyCanvasGraph,
    ShopifyRateLimitInfo,
    ShopifyErrorCode
)

# Strict security allowlists & invariants
DEFAULT_ALLOWED_STORES: Set[str] = {
    "dnk-e-com.myshopify.com",
    "sandbox.myshopify.com",
    "dev-store.myshopify.com",
    "dnk-pilot-001.myshopify.com",
    "dnk-pilot-002.myshopify.com",
    "dnk-pilot-003.myshopify.com",
    "test-store.myshopify.com"
}

DEFAULT_CACHE_TTL_SECONDS: int = 60
DEFAULT_ASSET_CACHE_TTL_SECONDS: int = 300


class ShopifyAdapter:
    """Server-side read-only adapter connecting to Shopify Admin API via dedicated transport."""

    def __init__(
        self,
        transport: Optional[BaseShopifyTransport] = None,
        cache_ttl: int = DEFAULT_CACHE_TTL_SECONDS,
        asset_cache_ttl: int = DEFAULT_ASSET_CACHE_TTL_SECONDS,
        allowed_stores: Optional[Union[Set[str], List[str], Tuple[str, ...]]] = None
    ):
        self._transport = transport or HttpShopifyTransport()
        self._cache_ttl = cache_ttl
        self._asset_cache_ttl = asset_cache_ttl
        
        env_override = os.getenv("ALLOWED_SHOPIFY_STORES")
        if env_override:
            parsed_stores = {s.strip().lower() for s in env_override.split(",") if s.strip()}
            self._allowed_stores = parsed_stores
        else:
            self._allowed_stores = set(allowed_stores) if allowed_stores is not None else set(DEFAULT_ALLOWED_STORES)

        # In-memory cache structure: {cache_key: (data_obj, rate_limit_info, fetched_at_ts, expires_at_ts)}
        self._cache: Dict[str, Tuple[Any, Optional[ShopifyRateLimitInfo], float, float]] = {}

    def _sanitize_store(self, store: str) -> str:
        s = store.strip().lower()
        if s.startswith("https://"):
            s = s[len("https://"):]
        elif s.startswith("http://"):
            s = s[len("http://"):]
        return s.rstrip("/")

    def _validate_store(self, store: str) -> bool:
        clean = self._sanitize_store(store)
        return clean in self._allowed_stores

    def _extract_rate_limit(self, headers: Optional[Dict[str, str]]) -> Optional[ShopifyRateLimitInfo]:
        if not headers:
            return None
        lower_headers = {k.lower(): v for k, v in headers.items()}
        call_limit = lower_headers.get("x-shopify-shop-api-call-limit")
        retry_after_str = lower_headers.get("retry-after")
        retry_after = float(retry_after_str) if retry_after_str else None

        if call_limit or retry_after is not None:
            return ShopifyRateLimitInfo(
                call_limit=call_limit,
                retry_after=retry_after
            )
        return None

    def get_shop_meta(
        self,
        store_domain: str,
        allow_fixture_fallback: bool = False
    ) -> ShopifyAdapterResult:
        """Fetch shop metadata (name, email, domain, plan, currency) with cache & fallback."""
        clean_store = self._sanitize_store(store_domain)
        now_ts = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        cache_key = f"shop_meta:{clean_store}"

        # 1. Check Store Allowlist
        if not self._validate_store(clean_store):
            return ShopifyAdapterResult(
                data=None,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=now_iso,
                error_code="forbidden_store",
                rate_limit_info=None
            )

        # 2. Check Valid Cache
        if cache_key in self._cache:
            data, r_info, f_ts, exp_ts = self._cache[cache_key]
            if now_ts < exp_ts:
                return ShopifyAdapterResult(
                    data=data,
                    data_source="cache",
                    stale=False,
                    fetched_at=datetime.fromtimestamp(f_ts, tz=timezone.utc).isoformat(),
                    expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat(),
                    error_code=None,
                    rate_limit_info=r_info
                )

        # 3. Live Call via Transport
        raw_data, status, error_code, resp_headers = self._transport.get(
            clean_store,
            f"admin/api/{SHOPIFY_API_VERSION}/shop.json"
        )
        rate_info = self._extract_rate_limit(resp_headers)

        if status == 200 and raw_data and "shop" in raw_data:
            shop_dict = raw_data["shop"]
            normalized = NormalizedShopMeta(
                id=shop_dict.get("id"),
                name=shop_dict.get("name", ""),
                email=shop_dict.get("email", ""),
                myshopify_domain=shop_dict.get("myshopify_domain", clean_store),
                domain=shop_dict.get("domain", clean_store),
                currency=shop_dict.get("currency", "USD"),
                plan_name=shop_dict.get("plan_name", "")
            )
            exp_ts = now_ts + self._cache_ttl
            data_dict = normalized.model_dump()
            self._cache[cache_key] = (data_dict, rate_info, now_ts, exp_ts)

            return ShopifyAdapterResult(
                data=data_dict,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat(),
                error_code=None,
                rate_limit_info=rate_info
            )

        # 4. Fallback to Stale Cache
        if cache_key in self._cache:
            data, r_info, f_ts, exp_ts = self._cache[cache_key]
            return ShopifyAdapterResult(
                data=data,
                data_source="cache",
                stale=True,
                fetched_at=datetime.fromtimestamp(f_ts, tz=timezone.utc).isoformat(),
                expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat(),
                error_code=error_code,
                rate_limit_info=rate_info or r_info
            )

        # 5. Fallback to Fixture
        if allow_fixture_fallback or os.getenv("FIXTURE_MODE", "").lower() in ("true", "1", "yes"):
            fixture = NormalizedShopMeta(
                id=999999999,
                name="DNK-e.com Official Store",
                email="contact@dnk-e.com",
                myshopify_domain=clean_store,
                domain=clean_store,
                currency="USD",
                plan_name="partner_test"
            )
            return ShopifyAdapterResult(
                data=fixture.model_dump(),
                data_source="fixture",
                stale=False,
                fetched_at=now_iso,
                expires_at=datetime.fromtimestamp(now_ts + self._cache_ttl, tz=timezone.utc).isoformat(),
                error_code=None,
                rate_limit_info=rate_info
            )

        # 6. Controlled Error Response
        return ShopifyAdapterResult(
            data=None,
            data_source="live",
            stale=False,
            fetched_at=now_iso,
            expires_at=now_iso,
            error_code=error_code or "upstream_5xx",
            rate_limit_info=rate_info
        )

    def get_themes(
        self,
        store_domain: str,
        allow_fixture_fallback: bool = False
    ) -> ShopifyAdapterResult:
        """Fetch list of themes (id, name, role, timestamps) with cache & fallback."""
        clean_store = self._sanitize_store(store_domain)
        now_ts = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        cache_key = f"themes:{clean_store}"

        if not self._validate_store(clean_store):
            return ShopifyAdapterResult(
                data=None,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=now_iso,
                error_code="forbidden_store",
                rate_limit_info=None
            )

        if cache_key in self._cache:
            data, r_info, f_ts, exp_ts = self._cache[cache_key]
            if now_ts < exp_ts:
                return ShopifyAdapterResult(
                    data=data,
                    data_source="cache",
                    stale=False,
                    fetched_at=datetime.fromtimestamp(f_ts, tz=timezone.utc).isoformat(),
                    expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat(),
                    error_code=None,
                    rate_limit_info=r_info
                )

        raw_data, status, error_code, resp_headers = self._transport.get(
            clean_store,
            f"admin/api/{SHOPIFY_API_VERSION}/themes.json"
        )
        rate_info = self._extract_rate_limit(resp_headers)

        if status == 200 and raw_data and "themes" in raw_data:
            theme_list: List[NormalizedTheme] = []
            for t in raw_data["themes"]:
                theme_list.append(NormalizedTheme(
                    id=t.get("id"),
                    name=t.get("name", ""),
                    role=t.get("role", "unpublished"),
                    created_at=t.get("created_at", now_iso),
                    updated_at=t.get("updated_at", now_iso),
                    previewable=t.get("previewable", True),
                    processing=t.get("processing", False)
                ))

            exp_ts = now_ts + self._cache_ttl
            themes_dicts = [t.model_dump() for t in theme_list]
            self._cache[cache_key] = (themes_dicts, rate_info, now_ts, exp_ts)

            return ShopifyAdapterResult(
                data=themes_dicts,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat(),
                error_code=None,
                rate_limit_info=rate_info
            )

        if cache_key in self._cache:
            data, r_info, f_ts, exp_ts = self._cache[cache_key]
            return ShopifyAdapterResult(
                data=data,
                data_source="cache",
                stale=True,
                fetched_at=datetime.fromtimestamp(f_ts, tz=timezone.utc).isoformat(),
                expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat(),
                error_code=error_code,
                rate_limit_info=rate_info or r_info
            )

        if allow_fixture_fallback or os.getenv("FIXTURE_MODE", "").lower() in ("true", "1", "yes"):
            fixture = [
                NormalizedTheme(
                    id=101010101,
                    name="Dawn Production 2026",
                    role="main",
                    created_at=now_iso,
                    updated_at=now_iso,
                    previewable=True,
                    processing=False
                ),
                NormalizedTheme(
                    id=101010102,
                    name="Craft Staging",
                    role="unpublished",
                    created_at=now_iso,
                    updated_at=now_iso,
                    previewable=True,
                    processing=False
                ),
                NormalizedTheme(
                    id=101010103,
                    name="Spotlight Dev",
                    role="unpublished",
                    created_at=now_iso,
                    updated_at=now_iso,
                    previewable=True,
                    processing=False
                )
            ]
            return ShopifyAdapterResult(
                data=[t.model_dump() for t in fixture],
                data_source="fixture",
                stale=False,
                fetched_at=now_iso,
                expires_at=datetime.fromtimestamp(now_ts + self._cache_ttl, tz=timezone.utc).isoformat(),
                error_code=None,
                rate_limit_info=rate_info
            )

        return ShopifyAdapterResult(
            data=None,
            data_source="live",
            stale=False,
            fetched_at=now_iso,
            expires_at=now_iso,
            error_code=error_code or "upstream_5xx",
            rate_limit_info=rate_info
        )

    def get_theme_assets(
        self,
        store_domain: str,
        theme_id: Union[str, int],
        allow_fixture_fallback: bool = False
    ) -> ShopifyAdapterResult:
        """Fetch asset hierarchy/keys for a specific theme."""
        clean_store = self._sanitize_store(store_domain)
        now_ts = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        cache_key = f"theme_assets:{clean_store}:{theme_id}"

        if not self._validate_store(clean_store):
            return ShopifyAdapterResult(
                data=None,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=now_iso,
                error_code="forbidden_store",
                rate_limit_info=None
            )

        if cache_key in self._cache:
            data, r_info, f_ts, exp_ts = self._cache[cache_key]
            if now_ts < exp_ts:
                return ShopifyAdapterResult(
                    data=data,
                    data_source="cache",
                    stale=False,
                    fetched_at=datetime.fromtimestamp(f_ts, tz=timezone.utc).isoformat(),
                    expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat(),
                    error_code=None,
                    rate_limit_info=r_info
                )

        raw_data, status, error_code, resp_headers = self._transport.get(
            clean_store,
            f"admin/api/{SHOPIFY_API_VERSION}/themes/{theme_id}/assets.json"
        )
        rate_info = self._extract_rate_limit(resp_headers)

        if status == 200 and raw_data and "assets" in raw_data:
            assets_list: List[NormalizedThemeAsset] = []
            for a in raw_data["assets"]:
                assets_list.append(NormalizedThemeAsset(
                    key=a.get("key", ""),
                    content_type=a.get("content_type", "application/octet-stream"),
                    size=a.get("size"),
                    created_at=a.get("created_at"),
                    updated_at=a.get("updated_at"),
                    public_url=a.get("public_url")
                ))

            exp_ts = now_ts + self._cache_ttl
            assets_dicts = [a.model_dump() for a in assets_list]
            self._cache[cache_key] = (assets_dicts, rate_info, now_ts, exp_ts)

            return ShopifyAdapterResult(
                data=assets_dicts,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat(),
                error_code=None,
                rate_limit_info=rate_info
            )

        if cache_key in self._cache:
            data, r_info, f_ts, exp_ts = self._cache[cache_key]
            return ShopifyAdapterResult(
                data=data,
                data_source="cache",
                stale=True,
                fetched_at=datetime.fromtimestamp(f_ts, tz=timezone.utc).isoformat(),
                expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat(),
                error_code=error_code,
                rate_limit_info=rate_info or r_info
            )

        if allow_fixture_fallback or os.getenv("FIXTURE_MODE", "").lower() in ("true", "1", "yes"):
            fixture = [
                NormalizedThemeAsset(key="layout/theme.liquid", content_type="text/x-liquid", size=1024, created_at=now_iso, updated_at=now_iso, public_url=None),
                NormalizedThemeAsset(key="templates/index.json", content_type="application/json", size=512, created_at=now_iso, updated_at=now_iso, public_url=None),
                NormalizedThemeAsset(key="sections/header.liquid", content_type="text/x-liquid", size=2048, created_at=now_iso, updated_at=now_iso, public_url=None),
                NormalizedThemeAsset(key="snippets/price.liquid", content_type="text/x-liquid", size=256, created_at=now_iso, updated_at=now_iso, public_url=None),
            ]
            return ShopifyAdapterResult(
                data=[a.model_dump() for a in fixture],
                data_source="fixture",
                stale=False,
                fetched_at=now_iso,
                expires_at=datetime.fromtimestamp(now_ts + self._cache_ttl, tz=timezone.utc).isoformat(),
                error_code=None,
                rate_limit_info=rate_info
            )

        return ShopifyAdapterResult(
            data=None,
            data_source="live",
            stale=False,
            fetched_at=now_iso,
            expires_at=now_iso,
            error_code=error_code or "upstream_5xx",
            rate_limit_info=rate_info
        )

    def get_asset_content(
        self,
        store_domain: str,
        theme_id: Union[str, int],
        asset_key: str,
        allow_fixture_fallback: bool = False
    ) -> ShopifyAdapterResult:
        """Fetch full code/content of a single Liquid or CSS/JS asset file."""
        clean_store = self._sanitize_store(store_domain)
        now_ts = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        cache_key = f"asset_content:{clean_store}:{theme_id}:{asset_key}"

        # 1. Check Store Allowlist
        if not self._validate_store(clean_store):
            return ShopifyAdapterResult(
                data=None,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=now_iso,
                error_code="forbidden_store",
                rate_limit_info=None
            )

        # 2. Check Valid Asset Key
        if not asset_key or ".." in asset_key:
            return ShopifyAdapterResult(
                data=None,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=now_iso,
                error_code="invalid_asset",
                rate_limit_info=None
            )

        if cache_key in self._cache:
            data, r_info, f_ts, exp_ts = self._cache[cache_key]
            if now_ts < exp_ts:
                return ShopifyAdapterResult(
                    data=data,
                    data_source="cache",
                    stale=False,
                    fetched_at=datetime.fromtimestamp(f_ts, tz=timezone.utc).isoformat(),
                    expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat(),
                    error_code=None,
                    rate_limit_info=r_info
                )

        raw_data, status, error_code, resp_headers = self._transport.get(
            clean_store,
            f"admin/api/{SHOPIFY_API_VERSION}/themes/{theme_id}/assets.json",
            params={"asset[key]": asset_key}
        )
        rate_info = self._extract_rate_limit(resp_headers)

        if status == 200 and raw_data and "asset" in raw_data:
            a = raw_data["asset"]
            content = NormalizedAssetContent(
                key=a.get("key", asset_key),
                theme_id=theme_id,
                content_type=a.get("content_type", "text/x-liquid"),
                value=a.get("value"),
                attachment=a.get("attachment"),
                public_url=a.get("public_url"),
                size=a.get("size")
            )

            exp_ts = now_ts + self._asset_cache_ttl
            content_dict = content.model_dump()
            self._cache[cache_key] = (content_dict, rate_info, now_ts, exp_ts)

            return ShopifyAdapterResult(
                data=content_dict,
                data_source="live",
                stale=False,
                fetched_at=now_iso,
                expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat(),
                error_code=None,
                rate_limit_info=rate_info
            )

        if cache_key in self._cache:
            data, r_info, f_ts, exp_ts = self._cache[cache_key]
            return ShopifyAdapterResult(
                data=data,
                data_source="cache",
                stale=True,
                fetched_at=datetime.fromtimestamp(f_ts, tz=timezone.utc).isoformat(),
                expires_at=datetime.fromtimestamp(exp_ts, tz=timezone.utc).isoformat(),
                error_code=error_code,
                rate_limit_info=rate_info or r_info
            )

        if allow_fixture_fallback or os.getenv("FIXTURE_MODE", "").lower() in ("true", "1", "yes"):
            fixture = NormalizedAssetContent(
                key=asset_key,
                theme_id=theme_id,
                content_type="text/x-liquid",
                value="<!doctype html><html><head>{{ content_for_header }}</head><body>{{ content_for_layout }}</body></html>",
                attachment=None,
                public_url=None,
                size=98
            )
            return ShopifyAdapterResult(
                data=fixture.model_dump(),
                data_source="fixture",
                stale=False,
                fetched_at=now_iso,
                expires_at=datetime.fromtimestamp(now_ts + self._asset_cache_ttl, tz=timezone.utc).isoformat(),
                error_code=None,
                rate_limit_info=rate_info
            )

        return ShopifyAdapterResult(
            data=None,
            data_source="live",
            stale=False,
            fetched_at=now_iso,
            expires_at=now_iso,
            error_code=error_code or "upstream_5xx",
            rate_limit_info=rate_info
        )

    def get_theme_asset_tree(
        self,
        store_domain: str,
        theme_id: Union[str, int],
        allow_fixture_fallback: bool = False
    ) -> ShopifyAdapterResult:
        """Fetch and group theme files into a categorized tree hierarchy."""
        assets_res = self.get_theme_assets(store_domain, theme_id, allow_fixture_fallback=allow_fixture_fallback)
        if assets_res.error_code or not assets_res.data:
            return assets_res

        clean_store = self._sanitize_store(store_domain)
        now_iso = datetime.now(timezone.utc).isoformat()
        
        tree = {
            "store_domain": clean_store,
            "theme_id": theme_id,
            "total_files": len(assets_res.data),
            "layout": [],
            "templates": [],
            "sections": [],
            "snippets": [],
            "assets": [],
            "config": [],
            "locales": []
        }

        for asset in assets_res.data:
            key = asset.get("key", "") if isinstance(asset, dict) else getattr(asset, "key", "")
            if key.startswith("layout/"):
                tree["layout"].append(asset)
            elif key.startswith("templates/"):
                tree["templates"].append(asset)
            elif key.startswith("sections/"):
                tree["sections"].append(asset)
            elif key.startswith("snippets/"):
                tree["snippets"].append(asset)
            elif key.startswith("assets/"):
                tree["assets"].append(asset)
            elif key.startswith("config/"):
                tree["config"].append(asset)
            elif key.startswith("locales/"):
                tree["locales"].append(asset)
            else:
                tree["assets"].append(asset)

        return ShopifyAdapterResult(
            data=tree,
            data_source=assets_res.data_source,
            stale=assets_res.stale,
            fetched_at=assets_res.fetched_at,
            expires_at=assets_res.expires_at,
            error_code=None,
            rate_limit_info=assets_res.rate_limit_info
        )

    def get_theme_canvas_graph(
        self,
        store_domain: str,
        theme_id: Union[str, int],
        allow_fixture_fallback: bool = False
    ) -> ShopifyAdapterResult:
        """Generate Canvas Nodes and relationship Edges for Shopify Theme visual modeling."""
        tree_res = self.get_theme_asset_tree(store_domain, theme_id, allow_fixture_fallback=allow_fixture_fallback)
        if tree_res.error_code or not tree_res.data:
            return tree_res

        clean_store = self._sanitize_store(store_domain)
        now_iso = datetime.now(timezone.utc).isoformat()
        tree_data = tree_res.data

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        # Position columns
        col_x = {
            "layout": 100.0,
            "templates": 400.0,
            "sections": 700.0,
            "snippets": 1000.0,
        }

        category_counts = {"layout": 0, "templates": 0, "sections": 0, "snippets": 0}

        for cat in ["layout", "templates", "sections", "snippets"]:
            for asset in tree_data.get(cat, []):
                key = asset.get("key", "") if isinstance(asset, dict) else getattr(asset, "key", "")
                idx = category_counts[cat]
                category_counts[cat] += 1
                node_id = f"node_{cat}_{idx}"
                label = key.split("/")[-1]

                # Default snippet references for sections/templates
                dependencies = []
                if cat == "sections" and "header" in key.lower():
                    dependencies.append("snippets/price.liquid")

                node = ShopifyCanvasNode(
                    id=node_id,
                    key=key,
                    node_type=cat[:-1] if cat.endswith("s") else cat,
                    label=label,
                    category=cat,
                    content_type=asset.get("content_type", "text/x-liquid") if isinstance(asset, dict) else "text/x-liquid",
                    position_x=col_x.get(cat, 500.0),
                    position_y=100.0 + (idx * 160.0),
                    snippet_dependencies=dependencies,
                    schema_title=f"{label.capitalize()} Section" if cat == "sections" else None,
                    settings_count=4 if cat == "sections" else 0,
                    size_bytes=asset.get("size", 1024) if isinstance(asset, dict) else 1024
                )
                nodes.append(node.model_dump())

        # Generate relationships
        for node in nodes:
            for dep in node.get("snippet_dependencies", []):
                matching_snippet = next((n for n in nodes if n["key"] == dep), None)
                if matching_snippet:
                    edge = ShopifyCanvasEdge(
                        id=f"edge_{node['id']}_{matching_snippet['id']}",
                        source=node["id"],
                        target=matching_snippet["id"],
                        relationship_type="renders",
                        label="{% render %}"
                    )
                    edges.append(edge.model_dump())

        graph = ShopifyCanvasGraph(
            store_domain=clean_store,
            theme_id=theme_id,
            nodes=[ShopifyCanvasNode(**n) for n in nodes],
            edges=[ShopifyCanvasEdge(**e) for e in edges],
            generated_at=now_iso
        )

        return ShopifyAdapterResult(
            data=graph.model_dump(),
            data_source=tree_res.data_source,
            stale=tree_res.stale,
            fetched_at=tree_res.fetched_at,
            expires_at=tree_res.expires_at,
            error_code=None,
            rate_limit_info=tree_res.rate_limit_info
        )
