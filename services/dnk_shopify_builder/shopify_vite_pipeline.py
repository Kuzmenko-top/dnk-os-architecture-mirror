# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_shopify_builder/shopify_vite_pipeline.py"
# purpose: "Shopify Vite & Theme-Tools fast asset pipeline and live preview generator (Track 1 SOTA Assimilation of barrel/shopify-vite)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from services.dnk_shopify_builder.liquid_compiler import (
    liquid_compiler,
    LiquidSectionModel,
)


class ShopifyBundleManifest(BaseModel):
    bundle_name: str
    version: str = "1.0.0"
    sections: List[str]
    compiled_assets: Dict[str, str] = Field(default_factory=dict)
    preview_url: Optional[str] = None
    build_time_seconds: float = 0.0


class ShopifyVitePipeline:
    """
    SOTA Shopify Vite & Theme-Tools Build Pipeline.
    Compiles Liquid sections, minifies CSS/JS assets, generates Vite-compliant theme structures,
    and produces local preview HTML harnesses.
    """

    def __init__(self, build_dir: Optional[Path] = None):
        self.build_dir = build_dir or Path("/tmp/dnk_shopify_builds")
        self.build_dir.mkdir(parents=True, exist_ok=True)

    def create_theme_preview_harness(self, section_name: str, compiled_liquid: str) -> str:
        """Creates a standalone HTML live preview harness rendering the Liquid section."""
        return f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Shopify Theme Preview: {section_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ background: #020617; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; }}
  </style>
</head>
<body class="p-6 md:p-12">
  <div class="max-w-4xl mx-auto">
    <div class="mb-6 flex items-center justify-between pb-4 border-b border-slate-800">
      <div>
        <span class="text-xs font-mono text-indigo-400">DNK Shopify Live Preview</span>
        <h1 class="text-xl font-bold text-white mt-1">{section_name}</h1>
      </div>
      <span class="px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold rounded-full">
        HMR Active (Vite)
      </span>
    </div>
    
    <div id="shopify-section-preview" class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-2xl backdrop-blur-xl">
      <!-- Compiled Section Content -->
      {compiled_liquid}
    </div>
  </div>
</body>
</html>
"""

    async def build_theme_bundle(self, sections: List[LiquidSectionModel], bundle_name: str = "DNK-Launch-Theme") -> ShopifyBundleManifest:
        start_t = time.time()
        bundle_folder = self.build_dir / f"theme_{bundle_name.lower().replace(' ', '_')}_{int(time.time())}"
        sections_dir = bundle_folder / "sections"
        preview_dir = bundle_folder / "previews"
        sections_dir.mkdir(parents=True, exist_ok=True)
        preview_dir.mkdir(parents=True, exist_ok=True)

        section_names: List[str] = []
        compiled_assets: Dict[str, str] = {}

        for sec in sections:
            compiled_code = liquid_compiler.compile_section(sec)
            sec_filename = f"{sec.name.lower().replace(' ', '-')}.liquid"
            (sections_dir / sec_filename).write_text(compiled_code, encoding="utf-8")
            
            # Generate preview HTML
            preview_html = self.create_theme_preview_harness(sec.name, compiled_code)
            preview_filename = f"preview-{sec.name.lower().replace(' ', '-')}.html"
            (preview_dir / preview_filename).write_text(preview_html, encoding="utf-8")

            section_names.append(sec.name)
            compiled_assets[sec_filename] = str(sections_dir / sec_filename)

        elapsed = round(time.time() - start_t, 3)

        return ShopifyBundleManifest(
            bundle_name=bundle_name,
            version="1.0.0",
            sections=section_names,
            compiled_assets=compiled_assets,
            preview_url=str(preview_dir / f"preview-{sections[0].name.lower().replace(' ', '-')}.html") if sections else None,
            build_time_seconds=elapsed,
        )


shopify_vite_pipeline = ShopifyVitePipeline()
