# --- DNK-MRH-HEADER ---
# mrh_id: "services_dnk_shopify_builder_theme_exporter"
# purpose: "Shopify Theme ZIP Exporter: packages synthesized OS 2.0 store templates, Tinker modular blocks, sections, snippets, assets, and config into a ready-to-deploy Shopify Theme ZIP archive."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import io
import json
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from services.dnk_shopify_builder.store_synthesizer import store_synthesizer


class ThemeExporter:
    """
    Exports synthesized Shopify OS 2.0 stores as valid, deployable Shopify theme ZIP archives.
    Combines Tinker's modular block-first foundation with synthesized JSON templates and
    custom Open Design color tokens.
    """

    def __init__(self, hub_root: Optional[str] = None):
        if hub_root:
            self.hub_root = Path(hub_root)
        else:
            self.hub_root = Path(__file__).resolve().parent.parent.parent
        self.tinker_dir = self.hub_root / "services" / "dnk_shopify" / "DNK-e.com"

    def export_store_zip(
        self,
        store_name: str,
        niche: str = "tech_apparel",
        theme_tokens: Optional[Dict[str, str]] = None,
        custom_templates: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Synthesizes the store (if templates not provided) and packages everything into an in-memory ZIP buffer.
        Returns: (zip_bytes, manifest_summary)
        """
        # 1. Synthesize templates if not supplied
        if not custom_templates:
            synthesized = store_synthesizer.synthesize_store(
                store_name=store_name,
                niche=niche,
                theme_tokens=theme_tokens or {},
            )
            templates = synthesized["templates"]
            niche_info = store_synthesizer.NICHE_PRESETS.get(niche, store_synthesizer.NICHE_PRESETS["general_ecom"])
        else:
            templates = custom_templates
            niche_info = store_synthesizer.NICHE_PRESETS.get(niche, store_synthesizer.NICHE_PRESETS["general_ecom"])

        tokens = theme_tokens or {}
        primary_color = tokens.get("accent", niche_info.get("primary_color", "#06b6d4"))
        bg_dark = tokens.get("bgDark", niche_info.get("bg_dark", "#030712"))

        zip_buffer = io.BytesIO()
        files_included = {
            "layout": 0,
            "templates": 0,
            "blocks": 0,
            "sections": 0,
            "snippets": 0,
            "assets": 0,
            "config": 0,
            "locales": 0,
            "total_files": 0,
        }

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # 2. Add base Tinker directories
            directories_to_copy = ["layout", "assets", "blocks", "sections", "snippets", "locales"]
            for dir_name in directories_to_copy:
                source_dir = self.tinker_dir / dir_name
                if source_dir.exists():
                    for file_path in source_dir.rglob("*"):
                        if file_path.is_file() and not file_path.name.startswith("."):
                            rel_path = file_path.relative_to(self.tinker_dir)
                            zf.write(file_path, arcname=str(rel_path))
                            files_included[dir_name] += 1
                            files_included["total_files"] += 1

            # 3. Add Synthesized Templates
            for tmpl_name, tmpl_data in templates.items():
                arc_name = f"templates/{tmpl_name}"
                tmpl_json_str = json.dumps(tmpl_data, indent=2, ensure_ascii=False)
                zf.writestr(arc_name, tmpl_json_str.encode("utf-8"))
                files_included["templates"] += 1
                files_included["total_files"] += 1

            # 4. Add or update config/settings_data.json
            config_dir = self.tinker_dir / "config"
            settings_data: Dict[str, Any] = {"current": {}, "presets": {}}
            if config_dir.exists() and (config_dir / "settings_data.json").exists():
                try:
                    with open(config_dir / "settings_data.json", "r", encoding="utf-8") as f:
                        settings_data = json.load(f)
                except Exception:
                    pass

            # Inject brand tokens into settings_data
            if "current" not in settings_data:
                settings_data["current"] = {}
            settings_data["current"]["store_name"] = store_name
            settings_data["current"]["colors_accent_1"] = primary_color
            settings_data["current"]["colors_background_1"] = bg_dark

            zf.writestr("config/settings_data.json", json.dumps(settings_data, indent=2).encode("utf-8"))
            files_included["config"] += 1
            files_included["total_files"] += 1

            # Copy settings_schema.json if exists
            if (config_dir / "settings_schema.json").exists():
                zf.write(config_dir / "settings_schema.json", arcname="config/settings_schema.json")
                files_included["config"] += 1
                files_included["total_files"] += 1

        zip_bytes = zip_buffer.getvalue()

        manifest = {
            "store_name": store_name,
            "niche": niche,
            "archive_name": f"{store_name.lower().replace(' ', '_')}_shopify_theme.zip",
            "size_bytes": len(zip_bytes),
            "size_kb": round(len(zip_bytes) / 1024, 2),
            "files_summary": files_included,
            "status": "ready_for_deploy",
        }

        return zip_bytes, manifest


theme_exporter = ThemeExporter()
