# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_liquid_ast_asset_rewriter"
# purpose: "Liquid AST & Template Asset URL Rewriter with Manifest Mapping and SRI Injection (DNK-ECOM-005)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field


# ============================================================================
# 1. MODELS & REWRITE REPORTING
# ============================================================================

class LiquidRewriteResult(BaseModel):
    """Result of rewriting asset references in a single Liquid template."""
    source_template: str
    rewritten_template: str
    replacements_count: int = 0
    rewritten_mappings: Dict[str, str] = Field(
        default_factory=dict,
        description="Original asset string -> Hashed asset string replacements performed"
    )
    unmapped_assets: List[str] = Field(
        default_factory=list,
        description="Asset references found in template with no match in manifest"
    )
    warnings: List[str] = Field(default_factory=list)


class BatchRewriteResult(BaseModel):
    """Aggregated report for batch rewriting theme templates."""
    results: Dict[str, LiquidRewriteResult] = Field(default_factory=dict)
    total_templates: int = 0
    total_replacements: int = 0
    all_unmapped_assets: List[str] = Field(default_factory=list)
    has_errors: bool = False


class RewriterOptions(BaseModel):
    """Configurable options for the Liquid AST asset rewriter."""
    strict_manifest: bool = Field(
        default=False,
        description="If True, missing manifest keys cause errors; if False, retain original asset name with warning"
    )
    rewrite_static_html_tags: bool = Field(
        default=True,
        description="Rewrite static <script>, <link>, and <img> asset URLs alongside Liquid filters"
    )
    rewrite_css_urls: bool = Field(
        default=True,
        description="Rewrite url('...') expressions in inline styles or style tags"
    )
    inject_sri_attributes: bool = Field(
        default=False,
        description="Inject integrity attributes on static script/link tags when SRI hash is available"
    )


# ============================================================================
# 2. LIQUID ASSET REWRITER ENGINE
# ============================================================================

class LiquidASTAssetRewriter:
    """
    Shopify Liquid AST Asset URL Rewriter (DNK-ECOM-005).
    
    Transforms unhashed asset references in Liquid templates to their content-hashed equivalents
    using a Vite `manifest.json` or asset mapping dictionary.
    
    Supported Liquid Filters:
      - `asset_url`
      - `asset_img_url`
      - `image_url`
      - `file_url`
      - `file_img_url`
    
    Supported Static HTML / CSS Tags:
      - `<script src="...">`
      - `<link href="...">`
      - `<img src="...">`
      - `url('...')`
    """

    # Liquid filters targeting Shopify assets/ directory
    ASSET_FILTERS = {"asset_url", "asset_img_url", "image_url", "file_url", "file_img_url"}

    # Regex patterns for matching Liquid variables with asset filters
    # Matches: {{ 'app.js' | asset_url }} or {{- "styles.css" | asset_url | stylesheet_tag -}}
    LIQUID_VAR_ASSET_PATTERN = re.compile(
        r"(\{\{\s*[-]?\s*)(['\"])([^'\"]+)\2(\s*\|\s*(?:asset_url|asset_img_url|image_url|file_url|file_img_url)\b[\s\S]*?[-]?\s*\}\})"
    )

    # Protected raw/comment blocks that should not be touched
    PROTECTED_BLOCKS_PATTERN = re.compile(
        r"(\{%\s*[-]?\s*(?:comment|raw)\s*[-]?\s*%\})[\s\S]*?(\{%\s*[-]?\s*(?:endcomment|endraw)\s*[-]?\s*%\})"
    )

    # Static HTML attributes regex (e.g. href="assets/theme.css" or src="assets/app.js")
    HTML_SRC_HREF_PATTERN = re.compile(
        r"""\b(src|href)=(['"])(assets/[^'"]+?|\/?assets\/[^'"]+?)\2""",
        re.IGNORECASE
    )

    # CSS url() pattern
    CSS_URL_PATTERN = re.compile(
        r"""\burl\(\s*(['"]?)(assets\/[^'"\)]+?|\/?assets\/[^'"\)]+?)\1\s*\)""",
        re.IGNORECASE
    )

    def __init__(self, options: Optional[RewriterOptions] = None):
        self.options = options or RewriterOptions()

    def _resolve_hashed_name(
        self,
        original_ref: str,
        manifest_mapping: Dict[str, str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Resolve an original asset reference against the manifest mapping.
        
        Returns:
            Tuple of (hashed_name, matched_key) or (None, None) if not found.
        """
        clean_ref = original_ref.strip().lstrip("/")
        basename = os.path.basename(clean_ref)

        # 1. Direct match on clean ref (e.g. "assets/app.js" or "app.js")
        if clean_ref in manifest_mapping:
            return manifest_mapping[clean_ref], clean_ref

        # 2. Match on basename (e.g. "app.js")
        if basename in manifest_mapping:
            return manifest_mapping[basename], basename

        # 3. Match on prefixed "assets/" path
        prefixed = f"assets/{basename}"
        if prefixed in manifest_mapping:
            return manifest_mapping[prefixed], prefixed

        # 4. Try matching against src entry paths (e.g. "src/app.js")
        for k, v in manifest_mapping.items():
            if os.path.basename(k) == basename:
                return v, k

        return None, None

    def rewrite(
        self,
        template_source: str,
        manifest_mapping: Dict[str, str],
        integrity_map: Optional[Dict[str, str]] = None
    ) -> LiquidRewriteResult:
        """
        Rewrite asset references inside a Liquid template string.

        Args:
            template_source: Liquid code string.
            manifest_mapping: Mapping dict (original filename -> hashed filename).
            integrity_map: Optional map (hashed filename -> SRI hash).

        Returns:
            LiquidRewriteResult with rewritten source and telemetry.
        """
        if not template_source or not manifest_mapping:
            return LiquidRewriteResult(
                source_template=template_source,
                rewritten_template=template_source,
                replacements_count=0
            )

        rewritten_mappings: Dict[str, str] = {}
        unmapped_assets: List[str] = []
        warnings: List[str] = []
        replacements_count = 0

        # Protect {% comment %} and {% raw %} blocks by masking them temporarily
        protected_segments: List[str] = []

        def mask_protected(match: re.Match) -> str:
            idx = len(protected_segments)
            protected_segments.append(match.group(0))
            return f"__DNK_PROTECTED_BLOCK_{idx}__"

        masked_source = self.PROTECTED_BLOCKS_PATTERN.sub(mask_protected, template_source)

        # 1. Rewrite Liquid variables with asset filters: {{ 'app.js' | asset_url }}
        def replace_liquid_var(match: re.Match) -> str:
            nonlocal replacements_count
            prefix = match.group(1)       # e.g. {{
            quote = match.group(2)        # ' or "
            asset_ref = match.group(3)    # e.g. app.js or assets/app.js
            suffix = match.group(4)       # e.g. | asset_url }}

            hashed_path, matched_key = self._resolve_hashed_name(asset_ref, manifest_mapping)

            if hashed_path:
                # If asset_ref was just 'app.js', use the basename of hashed_path
                # Shopify's asset_url filter expects basename: 'app.a1b2c3d4.js'
                if "/" not in asset_ref or not asset_ref.startswith("assets/"):
                    new_ref = os.path.basename(hashed_path)
                else:
                    new_ref = hashed_path

                rewritten_mappings[asset_ref] = new_ref
                replacements_count += 1
                return f"{prefix}{quote}{new_ref}{quote}{suffix}"
            else:
                if asset_ref not in unmapped_assets and not asset_ref.startswith(("http://", "https://", "//")):
                    unmapped_assets.append(asset_ref)
                    msg = f"Asset reference '{asset_ref}' not found in manifest mapping"
                    warnings.append(msg)
                    if self.options.strict_manifest:
                        raise ValueError(msg)
                return match.group(0)

        rewritten_source = self.LIQUID_VAR_ASSET_PATTERN.sub(replace_liquid_var, masked_source)

        # 2. Rewrite static HTML tags (e.g. <script src="assets/app.js">)
        if self.options.rewrite_static_html_tags:
            def replace_html_tag(match: re.Match) -> str:
                nonlocal replacements_count
                attr_name = match.group(1)
                quote = match.group(2)
                raw_path = match.group(3)

                hashed_path, _ = self._resolve_hashed_name(raw_path, manifest_mapping)
                if hashed_path:
                    # Maintain prefix format
                    if raw_path.startswith("/"):
                        final_path = f"/{hashed_path.lstrip('/')}"
                    else:
                        final_path = hashed_path

                    rewritten_mappings[raw_path] = final_path
                    replacements_count += 1

                    sri_attr = ""
                    if (self.options.inject_sri_attributes or integrity_map) and integrity_map:
                        sri_val = integrity_map.get(hashed_path) or integrity_map.get(os.path.basename(hashed_path))
                        if sri_val:
                            sri_attr = f' integrity="{sri_val}"'

                    return f'{attr_name}={quote}{final_path}{quote}{sri_attr}'
                return match.group(0)

            rewritten_source = self.HTML_SRC_HREF_PATTERN.sub(replace_html_tag, rewritten_source)

        # 3. Rewrite CSS url('assets/...')
        if self.options.rewrite_css_urls:
            def replace_css_url(match: re.Match) -> str:
                nonlocal replacements_count
                quote = match.group(1) or ""
                raw_path = match.group(2)

                hashed_path, _ = self._resolve_hashed_name(raw_path, manifest_mapping)
                if hashed_path:
                    rewritten_mappings[raw_path] = hashed_path
                    replacements_count += 1
                    return f"url({quote}{hashed_path}{quote})"
                return match.group(0)

            rewritten_source = self.CSS_URL_PATTERN.sub(replace_css_url, rewritten_source)

        # Restore protected blocks
        for idx, block in enumerate(protected_segments):
            rewritten_source = rewritten_source.replace(f"__DNK_PROTECTED_BLOCK_{idx}__", block)

        return LiquidRewriteResult(
            source_template=template_source,
            rewritten_template=rewritten_source,
            replacements_count=replacements_count,
            rewritten_mappings=rewritten_mappings,
            unmapped_assets=unmapped_assets,
            warnings=warnings
        )

    def rewrite_template(
        self,
        template_source_or_path: str,
        template_source: Optional[str] = None,
        manifest_mapping: Optional[Dict[str, str]] = None,
        integrity_map: Optional[Dict[str, str]] = None
    ) -> LiquidRewriteResult:
        """
        Convenience method to rewrite a template.
        Supports both (path, source, manifest_mapping, integrity_map) and (source, manifest_mapping, integrity_map).
        """
        if template_source is not None and isinstance(template_source, str) and manifest_mapping is not None:
            # Called as rewrite_template(path, source, manifest_mapping, integrity_map)
            return self.rewrite(template_source, manifest_mapping, integrity_map)
        elif isinstance(template_source, dict):
            # Called as rewrite_template(source, manifest_mapping, integrity_map)
            return self.rewrite(template_source_or_path, template_source, manifest_mapping) # template_source is manifest_mapping here
        else:
            return self.rewrite(template_source_or_path, manifest_mapping or {}, integrity_map)

    def rewrite_theme_files(
        self,
        theme_files: Dict[str, str],
        manifest_mapping: Dict[str, str],
        integrity_map: Optional[Dict[str, str]] = None
    ) -> BatchRewriteResult:
        """
        Batch rewrite an entire dictionary of theme files (layouts, templates, sections, snippets).

        Args:
            theme_files: Map of file path -> string content.
            manifest_mapping: Original -> Hashed asset path mapping.
            integrity_map: Optional SRI integrity mapping.

        Returns:
            BatchRewriteResult with per-file rewrite results and overall status.
        """
        results: Dict[str, LiquidRewriteResult] = {}
        total_replacements = 0
        all_unmapped: Set[str] = set()
        has_errors = False

        for filepath, content in theme_files.items():
            # Only process Liquid or CSS files that may reference assets
            lower_path = filepath.lower()
            if lower_path.endswith((".liquid", ".css", ".html", ".svg")):
                try:
                    res = self.rewrite(content, manifest_mapping, integrity_map)
                    results[filepath] = res
                    total_replacements += res.replacements_count
                    all_unmapped.update(res.unmapped_assets)
                except Exception as e:
                    has_errors = True
                    results[filepath] = LiquidRewriteResult(
                        source_template=content,
                        rewritten_template=content,
                        warnings=[f"Failed to rewrite {filepath}: {str(e)}"]
                    )
            else:
                # Retain unedited non-template file
                results[filepath] = LiquidRewriteResult(
                    source_template=content,
                    rewritten_template=content,
                    replacements_count=0
                )

        return BatchRewriteResult(
            results=results,
            total_templates=len(theme_files),
            total_replacements=total_replacements,
            all_unmapped_assets=sorted(list(all_unmapped)),
            has_errors=has_errors
        )


# Singleton instance with default options
liquid_ast_asset_rewriter = LiquidASTAssetRewriter()
