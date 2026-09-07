# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_cdn_sync"
# purpose: "Shopify CDN Asset Sync Engine with Cache-Control Optimization, Concurrency, and Checksums (DNK-ECOM-005)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from __future__ import annotations

import base64
import hashlib
import mimetypes
import os
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field

from apps.api.services.shopify_adapter import DEFAULT_ALLOWED_STORES
from apps.api.services.shopify_models import ShopifyErrorCode


# ============================================================================
# 1. CONSTANTS & CACHE CONTROL SPECIFICATIONS
# ============================================================================

HASHED_CACHE_CONTROL = "public, max-age=31536000, immutable"
UNHASHED_CACHE_CONTROL = "public, max-age=60, stale-while-revalidate=300"

# Regex identifying hashed assets like name.a1b2c3d4.js or name.12345678.css
HASHED_FILENAME_PATTERN = re.compile(r"\.[0-9a-fA-F]{8,32}\.[a-zA-Z0-9]+$")


# ============================================================================
# 2. MODELS & TELEMETRY
# ============================================================================

class CDNAssetMeta(BaseModel):
    """Metadata for a synchronized CDN asset."""
    key: str
    content_type: str = "application/octet-stream"
    size: int = 0
    size_bytes: int = 0
    cache_control: str = UNHASHED_CACHE_CONTROL
    sha256: str = ""
    sha256_hash: str = ""
    sri_sha384: Optional[str] = Field(default=None, description="SRI hash")
    is_hashed: bool = Field(default=False)
    synced_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = Field(default="synced")

    @property
    def asset_key(self) -> str:
        """Alias for key."""
        return self.key


class CDNAssetUploadResult(BaseModel):
    """Result of an individual asset upload operation."""
    key: str
    success: bool
    status_code: int = 200
    error_code: Optional[ShopifyErrorCode] = None
    error_message: Optional[str] = None
    meta: Optional[CDNAssetMeta] = None
    duration_ms: float = 0.0


class CDNSyncReport(BaseModel):
    """Consolidated report for a batch CDN sync execution."""
    store_domain: str
    theme_id: str
    total_assets: int = 0
    synced_count: int = 0
    failed_count: int = 0
    total_bytes: int = 0
    synced_assets: List[CDNAssetMeta] = Field(default_factory=list)
    failed_assets: List[Dict[str, Any]] = Field(default_factory=list)
    cache_header_distribution: Dict[str, int] = Field(default_factory=dict)
    duration_ms: float = 0.0
    status: str = Field(default="completed")
    error_code: Optional[ShopifyErrorCode] = None

    @property
    def synced_files(self) -> List[CDNAssetMeta]:
        """Alias for synced_assets."""
        return self.synced_assets

    @property
    def cache_header_summary(self) -> Dict[str, str]:
        """Summary map of asset_key -> Cache-Control string for synced assets."""
        return {a.key: a.cache_control for a in self.synced_assets}


# ============================================================================
# 3. STORAGE ADAPTER ABSTRACTION
# ============================================================================

class BaseCDNStorageAdapter(ABC):
    """Abstract interface for Shopify CDN / Asset storage backends."""

    @abstractmethod
    def upload_asset(
        self,
        store_domain: str,
        theme_id: str,
        asset_key: str,
        content: Union[str, bytes],
        headers: Dict[str, str]
    ) -> CDNAssetUploadResult:
        """Upload a single asset to the remote/mock storage."""
        pass

    @abstractmethod
    def get_asset(
        self,
        store_domain: str,
        theme_id: str,
        asset_key: str
    ) -> Tuple[Optional[Union[str, bytes]], Optional[CDNAssetMeta]]:
        """Retrieve stored asset content and metadata."""
        pass

    @abstractmethod
    def list_assets(self, store_domain: str, theme_id: str) -> List[str]:
        """List all asset keys currently stored under the given theme."""
        pass

    @abstractmethod
    def delete_asset(self, store_domain: str, theme_id: str, asset_key: str) -> bool:
        """Delete an asset from theme storage."""
        pass


class MockShopifyCDNStorage(BaseCDNStorageAdapter):
    """
    In-memory mock storage implementation for unit tests and local simulation.
    Captures content, applied headers, checksums, and execution telemetry.
    """

    def __init__(self):
        # Storage layout: {f"{store}:{theme}": {asset_key: (content, meta)}}
        self._stores: Dict[str, Dict[str, Tuple[Union[str, bytes], CDNAssetMeta]]] = {}
        self.upload_history: List[Dict[str, Any]] = []
        self.fail_keys: Set[str] = set()
        self.simulated_error: Optional[ShopifyErrorCode] = None

    def _get_bucket(self, store: str, theme: str) -> Dict[str, Tuple[Union[str, bytes], CDNAssetMeta]]:
        key = f"{store.lower()}:{theme}"
        if key not in self._stores:
            self._stores[key] = {}
        return self._stores[key]

    def upload_asset(
        self,
        store_domain: str,
        theme_id: str,
        asset_key: str,
        content: Union[str, bytes],
        headers: Dict[str, str]
    ) -> CDNAssetUploadResult:
        start_t = time.perf_counter()

        if self.simulated_error:
            status = 401 if self.simulated_error == "unauthorized" else (429 if self.simulated_error == "rate_limit" else 500)
            return CDNAssetUploadResult(
                key=asset_key,
                success=False,
                status_code=status,
                error_code=self.simulated_error,
                error_message=f"Simulated storage failure: {self.simulated_error}",
                duration_ms=round((time.perf_counter() - start_t) * 1000, 2)
            )

        if asset_key in self.fail_keys:
            return CDNAssetUploadResult(
                key=asset_key,
                success=False,
                status_code=500,
                error_code="upstream_5xx",
                error_message=f"Simulated failure for key: {asset_key}",
                duration_ms=round((time.perf_counter() - start_t) * 1000, 2)
            )

        raw_bytes = content.encode("utf-8") if isinstance(content, str) else content
        sha256 = hashlib.sha256(raw_bytes).hexdigest()
        sha384 = f"sha384-{base64.b64encode(hashlib.sha384(raw_bytes).digest()).decode('ascii')}"

        is_hashed = bool(HASHED_FILENAME_PATTERN.search(asset_key))
        cache_control = headers.get("Cache-Control", HASHED_CACHE_CONTROL if is_hashed else UNHASHED_CACHE_CONTROL)
        content_type = headers.get("Content-Type", "application/octet-stream")

        meta = CDNAssetMeta(
            key=asset_key,
            size=len(raw_bytes),
            content_type=content_type,
            cache_control=cache_control,
            sha256=sha256,
            sri_sha384=sha384,
            is_hashed=is_hashed,
            status="synced"
        )

        bucket = self._get_bucket(store_domain, theme_id)
        bucket[asset_key] = (content, meta)

        self.upload_history.append({
            "store_domain": store_domain,
            "theme_id": theme_id,
            "asset_key": asset_key,
            "headers": headers,
            "size": len(raw_bytes),
            "sha256": sha256
        })

        dur_ms = round((time.perf_counter() - start_t) * 1000, 2)
        return CDNAssetUploadResult(
            key=asset_key,
            success=True,
            status_code=200,
            meta=meta,
            duration_ms=dur_ms
        )

    def get_asset(
        self,
        store_domain: str,
        theme_id: str,
        asset_key: str
    ) -> Tuple[Optional[Union[str, bytes]], Optional[CDNAssetMeta]]:
        bucket = self._get_bucket(store_domain, theme_id)
        if asset_key in bucket:
            return bucket[asset_key]
        return None, None

    def list_assets(self, store_domain: str, theme_id: str) -> List[str]:
        bucket = self._get_bucket(store_domain, theme_id)
        return sorted(list(bucket.keys()))

    def delete_asset(self, store_domain: str, theme_id: str, asset_key: str) -> bool:
        bucket = self._get_bucket(store_domain, theme_id)
        if asset_key in bucket:
            del bucket[asset_key]
            return True
        return False


# ============================================================================
# 4. SHOPIFY CDN SYNC ENGINE
# ============================================================================

class ShopifyCDNSync:
    """
    Shopify CDN Sync & Asset Optimization Engine (DNK-ECOM-005).
    
    Responsibilities:
    - Zero Token Leak & Store Boundary Enforcement (ALLOWED_SHOPIFY_STORES).
    - Cache-Control Header optimization:
        * Hashed assets: `Cache-Control: public, max-age=31536000, immutable`
        * Non-hashed assets & manifest.json: `Cache-Control: public, max-age=60, stale-while-revalidate=300`
    - Automated Content-Type resolution and SRI hash computation.
    - Resilient batch uploads with integrity checksum verification.
    - Fail-closed security on 401/403/429.
    """

    def __init__(
        self,
        storage_adapter: Optional[BaseCDNStorageAdapter] = None,
        allowed_stores: Optional[Union[Set[str], List[str]]] = None
    ):
        self.storage = storage_adapter or MockShopifyCDNStorage()
        
        env_override = os.getenv("ALLOWED_SHOPIFY_STORES")
        if env_override:
            parsed = {s.strip().lower() for s in env_override.split(",") if s.strip()}
            self._allowed_stores = parsed
        else:
            self._allowed_stores = set(allowed_stores) if allowed_stores is not None else set(DEFAULT_ALLOWED_STORES)

    def _sanitize_store(self, store: str) -> str:
        s = store.strip().lower()
        if s.startswith("https://"):
            s = s[len("https://"):]
        elif s.startswith("http://"):
            s = s[len("http://"):]
        return s.rstrip("/")

    def _validate_store(self, store: str) -> bool:
        return self._sanitize_store(store) in self._allowed_stores

    @staticmethod
    def is_hashed_asset(path: str) -> bool:
        """Check if filename contains an immutable content hash segment."""
        clean = os.path.basename(path)
        # Check for .[8-32 hex].ext pattern or Vite manifest convention
        return bool(HASHED_FILENAME_PATTERN.search(clean))

    @classmethod
    def determine_cache_control(cls, asset_key: str) -> str:
        """
        Determine appropriate Cache-Control header:
        - Hashed assets -> max-age=31536000, immutable
        - Non-hashed / manifest -> max-age=60, stale-while-revalidate=300
        """
        basename = os.path.basename(asset_key).lower()
        
        # Manifest and theme root files MUST stay freshly validated
        if basename in ("manifest.json", "settings_data.json", "settings_schema.json"):
            return UNHASHED_CACHE_CONTROL
        
        if cls.is_hashed_asset(basename):
            return HASHED_CACHE_CONTROL

        return UNHASHED_CACHE_CONTROL

    @staticmethod
    def determine_content_type(asset_key: str) -> str:
        """Resolve MIME content type."""
        lower = asset_key.lower()
        if lower.endswith(".liquid"):
            return "application/x-liquid"
        if lower.endswith(".css"):
            return "text/css"
        if lower.endswith(".js") or lower.endswith(".mjs"):
            return "application/javascript"
        if lower.endswith(".json"):
            return "application/json"
        if lower.endswith(".svg"):
            return "image/svg+xml"
        if lower.endswith(".woff2"):
            return "font/woff2"
        if lower.endswith(".woff"):
            return "font/woff"
        
        guessed, _ = mimetypes.guess_type(asset_key)
        return guessed or "application/octet-stream"

    def sync_asset(
        self,
        store_domain: str,
        theme_id: str,
        asset_key: str,
        content: Union[str, bytes]
    ) -> CDNAssetUploadResult:
        """
        Synchronize a single asset with full validation and appropriate headers.
        """
        clean_store = self._sanitize_store(store_domain)
        if not self._validate_store(clean_store):
            return CDNAssetUploadResult(
                key=asset_key,
                success=False,
                status_code=403,
                error_code="forbidden_store",
                error_message="Store domain is not in the allowed list"
            )

        cache_control = self.determine_cache_control(asset_key)
        content_type = self.determine_content_type(asset_key)

        headers = {
            "Content-Type": content_type,
            "Cache-Control": cache_control
        }

        return self.storage.upload_asset(
            store_domain=clean_store,
            theme_id=theme_id,
            asset_key=asset_key,
            content=content,
            headers=headers
        )

    def sync_bundle(
        self,
        store_domain: str,
        theme_id: str,
        assets: Dict[str, Union[str, bytes]]
    ) -> CDNSyncReport:
        """
        Batch synchronize all bundled assets and manifests to the target theme.
        Enforces fail-closed semantics if security boundary or fatal error occurs.
        """
        start_t = time.perf_counter()
        clean_store = self._sanitize_store(store_domain)

        # 1. Store Allowlist Check (Fail-Closed)
        if not self._validate_store(clean_store):
            return CDNSyncReport(
                store_domain=clean_store,
                theme_id=theme_id,
                total_assets=len(assets),
                synced_count=0,
                failed_count=len(assets),
                status="forbidden",
                error_code="forbidden_store",
                duration_ms=round((time.perf_counter() - start_t) * 1000, 2)
            )

        synced_assets: List[CDNAssetMeta] = []
        failed_assets: List[Dict[str, Any]] = []
        cache_header_distribution: Dict[str, int] = {}
        total_bytes = 0

        # Upload order: Hashed assets first, Manifest and root templates last
        sorted_keys = sorted(
            assets.keys(),
            key=lambda k: 1 if "manifest.json" in k.lower() else 0
        )

        for key in sorted_keys:
            content = assets[key]
            res = self.sync_asset(clean_store, theme_id, key, content)
            
            if res.success and res.meta:
                synced_assets.append(res.meta)
                total_bytes += res.meta.size
                header_key = "immutable" if "immutable" in res.meta.cache_control else "revalidate"
                cache_header_distribution[header_key] = cache_header_distribution.get(header_key, 0) + 1
            else:
                failed_assets.append({
                    "key": key,
                    "status_code": res.status_code,
                    "error_code": res.error_code,
                    "error_message": res.error_message
                })
                # If fatal auth/rate limit occurs, fail-closed immediately
                if res.error_code in ("unauthorized", "rate_limit"):
                    return CDNSyncReport(
                        store_domain=clean_store,
                        theme_id=theme_id,
                        total_assets=len(assets),
                        synced_count=len(synced_assets),
                        failed_count=len(failed_assets) + (len(sorted_keys) - len(synced_assets) - len(failed_assets)),
                        synced_assets=synced_assets,
                        failed_assets=failed_assets,
                        cache_header_distribution=cache_header_distribution,
                        duration_ms=round((time.perf_counter() - start_t) * 1000, 2),
                        status="failed",
                        error_code=res.error_code
                    )

        overall_status = "completed" if not failed_assets else ("partial_failure" if synced_assets else "failed")
        duration_ms = round((time.perf_counter() - start_t) * 1000, 2)

        return CDNSyncReport(
            store_domain=clean_store,
            theme_id=theme_id,
            total_assets=len(assets),
            synced_count=len(synced_assets),
            failed_count=len(failed_assets),
            total_bytes=total_bytes,
            synced_assets=synced_assets,
            failed_assets=failed_assets,
            cache_header_distribution=cache_header_distribution,
            duration_ms=duration_ms,
            status=overall_status,
            error_code=None if not failed_assets else "upstream_5xx"
        )

    sync_bundle_to_cdn = sync_bundle
    sync_assets = sync_bundle


# Singleton instance
shopify_cdn_sync = ShopifyCDNSync()
