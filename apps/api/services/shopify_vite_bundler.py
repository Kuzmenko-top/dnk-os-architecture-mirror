# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_vite_bundler"
# purpose: "Shopify Vite Production Bundler & Asset Manifest Engine with Content Hashing and SRI Integrity (DNK-ECOM-005)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field


# ============================================================================
# 1. MODELS & DATA STRUCTURES
# ============================================================================

class ViteManifestEntry(BaseModel):
    """Vite-compliant manifest entry for an asset."""
    file: str = Field(..., description="Hashed relative file path in theme assets/ directory")
    src: Optional[str] = Field(default=None, description="Original source path or entry name")
    isEntry: Optional[bool] = Field(default=None, description="Whether this asset is a primary entry point")
    css: Optional[List[str]] = Field(default=None, description="Associated CSS chunks for this JS entry")
    assets: Optional[List[str]] = Field(default=None, description="Imported static assets (images, fonts, etc.)")
    integrity: Optional[str] = Field(default=None, description="Subresource Integrity (SRI) sha384 hash")
    hash: str = Field(..., description="Short content hash (8-12 hex chars)")
    size: int = Field(default=0, description="Asset size in bytes")
    content_type: str = Field(default="application/octet-stream", description="MIME content type")


class BundleStats(BaseModel):
    """Aggregated build statistics for the Vite bundle."""
    total_files: int = 0
    total_raw_bytes: int = 0
    total_bundled_bytes: int = 0
    compression_ratio: float = 1.0
    hash_length: int = 8
    build_time_ms: float = 0.0


class ViteBundleResult(BaseModel):
    """Complete bundle result returned by ShopifyViteBundler."""
    bundle_id: str
    manifest: Dict[str, ViteManifestEntry] = Field(default_factory=dict)
    manifest_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Lookup mapping: original asset key/path -> hashed asset key/path"
    )
    integrity_map: Dict[str, str] = Field(
        default_factory=dict,
        description="Lookup mapping: hashed asset key -> SRI sha384 hash"
    )
    bundled_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of output relative paths -> text/base64 bundled content"
    )
    entry_points: List[str] = Field(default_factory=list)
    stats: BundleStats = Field(default_factory=BundleStats)

    @property
    def asset_mapping(self) -> Dict[str, str]:
        """Alias for manifest_mapping."""
        return self.manifest_mapping


class BundlerConfig(BaseModel):
    """Configuration options for the Vite bundler engine."""
    hash_length: int = Field(default=8, ge=8, le=32, description="Length of content hash slice")
    minify: bool = Field(default=True, description="Enable whitespace and comment stripping")
    generate_sri: bool = Field(default=True, description="Generate SRI sha384 integrity hashes")
    assets_dir_prefix: str = Field(default="assets/", description="Target assets directory prefix")
    entry_patterns: List[str] = Field(
        default_factory=lambda: ["app.js", "theme.css", "main.js", "application.js", "application.css"],
        description="Asset filenames treated as root entry points"
    )


# ============================================================================
# 2. CORE VITE BUNDLER IMPLEMENTATION
# ============================================================================

class ShopifyViteBundler:
    """
    Shopify Vite Production Bundler & Asset Manifest Engine (DNK-ECOM-005).
    
    Responsibilities:
    - Content-addressable hashing (SHA-256 sliced to 8-12 hex characters: `[name].[hash].[ext]`).
    - Subresource Integrity (SRI sha384) generation for secure asset loading.
    - Standard Vite `manifest.json` generation matching Shopify Theme Vite conventions.
    - Deterministic minification and asset mapping dictionary construction.
    """

    def __init__(
        self,
        config: Optional[BundlerConfig] = None,
        hash_length: Optional[int] = None,
        minify: Optional[bool] = None,
        generate_sri: Optional[bool] = None
    ):
        if config:
            self.config = config
        else:
            kwargs = {}
            if hash_length is not None:
                kwargs["hash_length"] = hash_length
            if minify is not None:
                kwargs["minify"] = minify
            if generate_sri is not None:
                kwargs["generate_sri"] = generate_sri
            self.config = BundlerConfig(**kwargs)

    @staticmethod
    def compute_content_hash(content: Union[str, bytes], length: int = 8) -> str:
        """Compute SHA-256 hash slice of asset content."""
        raw_bytes = content.encode("utf-8") if isinstance(content, str) else content
        full_hash = hashlib.sha256(raw_bytes).hexdigest()
        return full_hash[:length]

    @staticmethod
    def compute_sri_hash(content: Union[str, bytes]) -> str:
        """Compute Subresource Integrity (SRI) sha384 base64 string."""
        raw_bytes = content.encode("utf-8") if isinstance(content, str) else content
        sha384_digest = hashlib.sha384(raw_bytes).digest()
        b64 = base64.b64encode(sha384_digest).decode("ascii")
        return f"sha384-{b64}"

    @staticmethod
    def detect_content_type(filename: str) -> str:
        """Determine MIME type by file extension with Liquid / CSS / JS fallbacks."""
        lower = filename.lower()
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
        
        guessed, _ = mimetypes.guess_type(filename)
        return guessed or "application/octet-stream"

    def _format_hashed_filename(self, path: str, content_hash: str) -> str:
        """
        Format filename to [name].[hash].[ext].
        Handles path prefixes (e.g. 'assets/app.js' -> 'assets/app.a1b2c3d4.js').
        """
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)

        if "." in basename:
            parts = basename.rsplit(".", 1)
            name_part, ext_part = parts[0], parts[1]
            # If already hashed with same length hex pattern, avoid double hashing
            hex_pattern = rf"\.[0-9a-fA-F]{{{len(content_hash)}}}$"
            name_cleaned = re.sub(hex_pattern, "", name_part)
            hashed_basename = f"{name_cleaned}.{content_hash}.{ext_part}"
        else:
            hashed_basename = f"{basename}.{content_hash}"

        if dirname:
            return f"{dirname}/{hashed_basename}"
        return hashed_basename

    def minify_content(self, filename: str, content: str) -> str:
        """Minify JS/CSS/JSON content while preserving syntax and liquid delimiters."""
        if not self.config.minify or not isinstance(content, str):
            return content

        lower = filename.lower()
        
        # 1. JSON Minification
        if lower.endswith(".json"):
            try:
                parsed = json.loads(content)
                return json.dumps(parsed, separators=(",", ":"))
            except Exception:
                return content

        # 2. CSS Minification (strip comments and excess whitespace, preserve liquid tags)
        if lower.endswith(".css"):
            # Strip CSS comments /* ... */
            no_comments = re.sub(r"/\*[\s\S]*?\*/", "", content)
            # Normalize whitespace around selectors and braces
            no_excess_space = re.sub(r"\s+", " ", no_comments)
            no_excess_space = re.sub(r"\s*([{}:;,])\s*", r"\1", no_excess_space)
            return no_excess_space.strip()

        # 3. JS Minification (safe single-line & multi-line comment stripping without breaking URLs)
        if lower.endswith(".js") or lower.endswith(".mjs"):
            # Remove multi-line comments /* ... */
            no_block_comments = re.sub(r"/\*[\s\S]*?\*/", "", content)
            # Remove single-line comments not part of URL protocol (http://)
            lines = []
            for line in no_block_comments.splitlines():
                stripped = line.strip()
                if stripped.startswith("//"):
                    continue
                # If there's an inline // comment, clean if not http:// or https://
                if "//" in stripped and "://" not in stripped:
                    parts = stripped.split("//", 1)
                    lines.append(parts[0].strip())
                else:
                    lines.append(stripped)
            return "\n".join([l for l in lines if l])

        return content

    def bundle(
        self,
        assets: Dict[str, Union[str, bytes]],
        bundle_name: str = "dnk_theme",
        custom_entries: Optional[List[str]] = None
    ) -> ViteBundleResult:
        """
        Execute bundling, content hashing, manifest generation, and SRI computation.

        Args:
            assets: Map of input asset relative paths -> content (e.g. {"src/app.js": "...", "src/theme.css": "..."})
            bundle_name: Logical bundle identifier
            custom_entries: Explicit list of entry asset filenames

        Returns:
            ViteBundleResult containing manifest.json, mappings, integrity map, and bundled files.
        """
        start_time = time.perf_counter()
        timestamp_id = int(time.time())
        bundle_id = f"bundle_{bundle_name}_{timestamp_id}"

        manifest_entries: Dict[str, ViteManifestEntry] = {}
        manifest_mapping: Dict[str, str] = {}
        integrity_map: Dict[str, str] = {}
        bundled_files: Dict[str, str] = {}
        entry_points: List[str] = []

        total_raw_bytes = 0
        total_bundled_bytes = 0

        # Determine entry set
        target_entries = set(custom_entries or self.config.entry_patterns)

        # 1. First pass: Process and bundle individual assets
        processed_css_files: List[str] = []

        for original_path, raw_content in assets.items():
            raw_str = raw_content if isinstance(raw_content, str) else raw_content.decode("utf-8", errors="ignore")
            raw_len = len(raw_content.encode("utf-8") if isinstance(raw_content, str) else raw_content)
            total_raw_bytes += raw_len

            # Minification step
            bundled_content = self.minify_content(original_path, raw_str)
            bundled_bytes = bundled_content.encode("utf-8")
            bundled_len = len(bundled_bytes)
            total_bundled_bytes += bundled_len

            # Content Hashing
            content_hash = self.compute_content_hash(bundled_bytes, length=self.config.hash_length)
            
            # Form target hashed path inside assets/
            basename = os.path.basename(original_path)
            target_asset_path = self._format_hashed_filename(f"assets/{basename}", content_hash)
            
            # SRI Integrity
            sri_integrity = self.compute_sri_hash(bundled_bytes) if self.config.generate_sri else None
            content_type = self.detect_content_type(basename)

            is_entry = basename in target_entries or original_path in target_entries
            if is_entry:
                entry_points.append(original_path)

            if basename.endswith(".css"):
                processed_css_files.append(target_asset_path)

            # Record in manifest
            entry_model = ViteManifestEntry(
                file=target_asset_path,
                src=original_path,
                isEntry=is_entry if is_entry else None,
                integrity=sri_integrity,
                hash=content_hash,
                size=bundled_len,
                content_type=content_type
            )
            manifest_entries[original_path] = entry_model

            # Mappings for convenient lookup
            # Map full original path
            manifest_mapping[original_path] = target_asset_path
            # Map bare filename (e.g. 'app.js' -> 'assets/app.a1b2c3d4.js' or 'app.a1b2c3d4.js')
            manifest_mapping[basename] = os.path.basename(target_asset_path)
            manifest_mapping[f"assets/{basename}"] = target_asset_path

            if sri_integrity:
                integrity_map[target_asset_path] = sri_integrity
                integrity_map[os.path.basename(target_asset_path)] = sri_integrity

            bundled_files[target_asset_path] = bundled_content

        # 2. Second pass: Link CSS chunks to JS entry points
        for orig_path, entry in manifest_entries.items():
            if entry.isEntry and (orig_path.endswith(".js") or orig_path.endswith(".ts")):
                if processed_css_files:
                    entry.css = processed_css_files

        # 3. Generate manifest.json file
        manifest_json_dict = {
            k: v.model_dump(exclude_none=True) for k, v in manifest_entries.items()
        }
        manifest_json_str = json.dumps(manifest_json_dict, indent=2)
        bundled_files["assets/manifest.json"] = manifest_json_str
        manifest_mapping["manifest.json"] = "assets/manifest.json"
        manifest_mapping["assets/manifest.json"] = "assets/manifest.json"

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        compression_ratio = round(total_bundled_bytes / max(total_raw_bytes, 1), 4)

        stats = BundleStats(
            total_files=len(manifest_entries),
            total_raw_bytes=total_raw_bytes,
            total_bundled_bytes=total_bundled_bytes,
            compression_ratio=compression_ratio,
            hash_length=self.config.hash_length,
            build_time_ms=elapsed_ms
        )

        return ViteBundleResult(
            bundle_id=bundle_id,
            manifest=manifest_entries,
            manifest_mapping=manifest_mapping,
            integrity_map=integrity_map,
            bundled_files=bundled_files,
            entry_points=entry_points,
            stats=stats
        )


# Singleton instance with default configuration
shopify_vite_bundler = ShopifyViteBundler()
