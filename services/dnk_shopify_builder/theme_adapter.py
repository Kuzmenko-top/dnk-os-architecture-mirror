# --- DNK-MRH-HEADER ---
# mrh_id: "services_dnk_shopify_builder_theme_adapter"
# purpose: "Shopify Mega-Theme Adapter: unifies legacy theme assets (DNK_Ecom_v1) into Tinker modular block-first architecture, extracting AST schemas and building mega_component_registry.json"
# canonical_source: true
# alters_files: ["services/dnk_shopify/mega_component_registry.json"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import os
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.dnk_shopify_builder.liquid_compiler import liquid_compiler


class ThemeComponentCategory:
    HERO_AND_BANNERS = "hero_and_banners"
    PDP_CONVERSION = "pdp_conversion"
    SOCIAL_PROOF = "social_proof"
    CART_AND_CHECKOUT = "cart_and_checkout"
    DISCOVERY_AND_NAV = "discovery_and_nav"
    MARKETING_AND_PROMO = "marketing_and_promo"
    LAYOUT_AND_CHROME = "layout_and_chrome"
    GENERAL = "general"


class ThemeAdapter:
    """
    Adapts and indexes large Shopify theme libraries (Tinker + Legacy Ecom themes)
    into a unified AST component registry with categorization, schema validation,
    and Tinker block-first compatibility.
    """

    CATEGORY_KEYWORDS = {
        ThemeComponentCategory.HERO_AND_BANNERS: [
            "hero", "banner", "slideshow", "image-banner", "video-banner", "collage", "split-screen"
        ],
        ThemeComponentCategory.PDP_CONVERSION: [
            "bundle", "product", "price-compare", "true-to-size", "sizing", "delivery",
            "countdown", "sticky", "variant", "buy-button", "quantity", "inventory", "pdp"
        ],
        ThemeComponentCategory.SOCIAL_PROOF: [
            "review", "testimonial", "facebook", "tiktok", "rating", "star", "avatar",
            "trust", "guarantee", "badge", "compare-chart", "moneyback"
        ],
        ThemeComponentCategory.CART_AND_CHECKOUT: [
            "cart", "drawer", "shipping", "gift", "upsell", "cross-sell", "checkout", "progress"
        ],
        ThemeComponentCategory.DISCOVERY_AND_NAV: [
            "search", "menu", "nav", "collection", "filter", "tab", "accordion", "multirow", "grid"
        ],
        ThemeComponentCategory.MARKETING_AND_PROMO: [
            "popup", "promo", "announcement", "newsletter", "email", "discount", "coupon", "ticker"
        ],
        ThemeComponentCategory.LAYOUT_AND_CHROME: [
            "header", "footer", "divider", "scroll", "social", "logo", "icon"
        ]
    }

    def __init__(self, hub_root: Optional[str] = None):
        if hub_root:
            self.hub_root = Path(hub_root)
        else:
            self.hub_root = Path(__file__).resolve().parent.parent.parent
        self.tinker_dir = self.hub_root / "services" / "dnk_shopify" / "DNK-e.com"
        self.zip_path = self.hub_root / "services" / "dnk_shopify" / "DNK_Ecom_v1_0_0.zip"
        self.output_registry_path = self.hub_root / "services" / "dnk_shopify" / "mega_component_registry.json"

    def classify_component(self, name: str, content: str = "") -> str:
        """Determines conversion category based on filename and liquid content keywords."""
        name_lower = name.lower().replace("_", "-")
        content_lower = content.lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in name_lower or f"id: \"{kw}" in content_lower or f"class=\"{kw}" in content_lower:
                    return category

        return ThemeComponentCategory.GENERAL

    def scan_tinker_components(self) -> Dict[str, Any]:
        """Scans all blocks, sections, and snippets in the active Tinker theme directory."""
        registry = {
            "blocks": {},
            "sections": {},
            "snippets": {},
            "templates": {}
        }

        if not self.tinker_dir.exists():
            return registry

        # 1. Blocks
        blocks_dir = self.tinker_dir / "blocks"
        if blocks_dir.exists():
            for file_path in blocks_dir.glob("*.liquid"):
                name = file_path.stem
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                schema, schema_err = liquid_compiler.extract_schema(content)
                category = self.classify_component(name, content)

                registry["blocks"][name] = {
                    "id": name,
                    "type": "block",
                    "file_path": str(file_path.relative_to(self.hub_root)),
                    "category": category,
                    "has_schema": schema is not None,
                    "schema": schema or {},
                    "is_tinker_native": True,
                    "line_count": len(content.splitlines()),
                }

        # 2. Sections
        sections_dir = self.tinker_dir / "sections"
        if sections_dir.exists():
            for file_path in sections_dir.glob("*.liquid"):
                name = file_path.stem
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                schema, schema_err = liquid_compiler.extract_schema(content)
                category = self.classify_component(name, content)

                registry["sections"][name] = {
                    "id": name,
                    "type": "section",
                    "file_path": str(file_path.relative_to(self.hub_root)),
                    "category": category,
                    "has_schema": schema is not None,
                    "schema": schema or {},
                    "is_tinker_native": True,
                    "supports_content_for_blocks": "{% content_for 'blocks' %}" in content,
                    "line_count": len(content.splitlines()),
                }

        # 3. Snippets
        snippets_dir = self.tinker_dir / "snippets"
        if snippets_dir.exists():
            for file_path in snippets_dir.glob("*.liquid"):
                name = file_path.stem
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                category = self.classify_component(name, content)

                registry["snippets"][name] = {
                    "id": name,
                    "type": "snippet",
                    "file_path": str(file_path.relative_to(self.hub_root)),
                    "category": category,
                    "is_tinker_native": True,
                    "line_count": len(content.splitlines()),
                }

        return registry

    def scan_legacy_zip_components(self) -> Dict[str, Any]:
        """Scans the legacy DNK_Ecom_v1_0_0.zip archive for additional conversion sections and snippets."""
        registry = {
            "sections": {},
            "snippets": {},
            "templates": {}
        }

        if not self.zip_path.exists():
            return registry

        with zipfile.ZipFile(self.zip_path, 'r') as zf:
            for file_info in zf.infolist():
                filename = file_info.filename
                if filename.startswith("sections/") and filename.endswith(".liquid"):
                    name = Path(filename).stem
                    content = zf.read(filename).decode("utf-8", errors="ignore")
                    schema, schema_err = liquid_compiler.extract_schema(content)
                    category = self.classify_component(name, content)

                    registry["sections"][name] = {
                        "id": name,
                        "type": "section",
                        "source": "legacy_zip",
                        "zip_entry": filename,
                        "category": category,
                        "has_schema": schema is not None,
                        "schema": schema or {},
                        "line_count": len(content.splitlines()),
                    }

                elif filename.startswith("snippets/") and filename.endswith(".liquid"):
                    name = Path(filename).stem
                    content = zf.read(filename).decode("utf-8", errors="ignore")
                    category = self.classify_component(name, content)

                    registry["snippets"][name] = {
                        "id": name,
                        "type": "snippet",
                        "source": "legacy_zip",
                        "zip_entry": filename,
                        "category": category,
                        "line_count": len(content.splitlines()),
                    }

        return registry

    def build_mega_registry(self) -> Dict[str, Any]:
        """Merges Tinker native assets and Legacy Zip assets into a single unified catalog."""
        tinker_data = self.scan_tinker_components()
        legacy_data = self.scan_legacy_zip_components()

        # Merge blocks
        all_blocks = tinker_data.get("blocks", {})

        # Merge sections (Tinker native takes precedence if duplicate)
        all_sections = {}
        all_sections.update(legacy_data.get("sections", {}))
        all_sections.update(tinker_data.get("sections", {}))

        # Merge snippets
        all_snippets = {}
        all_snippets.update(legacy_data.get("snippets", {}))
        all_snippets.update(tinker_data.get("snippets", {}))

        # Category summary
        category_counts: Dict[str, int] = {}
        for item in list(all_blocks.values()) + list(all_sections.values()) + list(all_snippets.values()):
            cat = item.get("category", ThemeComponentCategory.GENERAL)
            category_counts[cat] = category_counts.get(cat, 0) + 1

        mega_registry = {
            "version": "2.0.0",
            "theme_base": "Tinker Theme (Shopify OS 2.0 Modular)",
            "updated_at": "2026-08-30",
            "stats": {
                "total_blocks": len(all_blocks),
                "total_sections": len(all_sections),
                "total_snippets": len(all_snippets),
                "total_components": len(all_blocks) + len(all_sections) + len(all_snippets),
                "categories": category_counts,
            },
            "blocks": all_blocks,
            "sections": all_sections,
            "snippets": all_snippets,
        }

        # Save to disk
        self.output_registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_registry_path, "w", encoding="utf-8") as f:
            json.dump(mega_registry, f, indent=2, ensure_ascii=False)

        return mega_registry

    def adapt_legacy_section_to_tinker_block(
        self,
        section_name: str,
        target_block_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Adapts a legacy monolithic section into a standalone Tinker block file.
        Extracts markup, wraps in a custom element if needed, and writes to blocks/.
        """
        target_name = target_block_name or f"converted-{section_name}"
        section_code = ""

        # Try to find in tinker sections first, then in zip
        section_file = self.tinker_dir / "sections" / f"{section_name}.liquid"
        if section_file.exists():
            section_code = section_file.read_text(encoding="utf-8", errors="ignore")
        elif self.zip_path.exists():
            with zipfile.ZipFile(self.zip_path, 'r') as zf:
                zip_entry = f"sections/{section_name}.liquid"
                if zip_entry in zf.namelist():
                    section_code = zf.read(zip_entry).decode("utf-8", errors="ignore")

        if not section_code:
            return {"success": False, "error": f"Section '{section_name}' not found."}

        schema, _ = liquid_compiler.extract_schema(section_code)
        category = self.classify_component(section_name, section_code)

        # Extract body (strip existing {% schema %} and {% style %} blocks)
        body = re.sub(r"\{%-?\s*schema\s*-?%\}.*?\{%-?\s*endschema\s*-?%\}", "", section_code, flags=re.DOTALL)
        body = re.sub(r"\{%-?\s*style\s*-?%\}.*?\{%-?\s*endstyle\s*-?%\}", "", body, flags=re.DOTALL).strip()

        # Build clean block schema
        block_schema = {
            "name": schema.get("name", target_name.replace("-", " ").title()) if schema else target_name,
            "tag": None,
            "settings": schema.get("settings", []) if schema else []
        }

        # Build Tinker block Liquid code
        block_liquid = [
            f"{{% comment %}}",
            f"  Tinker Block: {target_name}",
            f"  Adapted from Legacy Section: {section_name}",
            f"  Category: {category}",
            f"{{% endcomment %}}",
            "",
            body,
            "",
            "{% schema %}",
            json.dumps(block_schema, indent=2),
            "{% endschema %}"
        ]

        full_block_code = "\n".join(block_liquid) + "\n"

        # Write to blocks directory
        out_path = self.tinker_dir / "blocks" / f"{target_name}.liquid"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(full_block_code, encoding="utf-8")

        return {
            "success": True,
            "block_name": target_name,
            "category": category,
            "settings_count": len(block_schema["settings"]),
            "file_path": str(out_path.relative_to(self.hub_root)),
        }


theme_adapter = ThemeAdapter()
