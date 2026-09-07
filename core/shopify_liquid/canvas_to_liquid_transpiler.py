# --- DNK-MRH-HEADER ---
# mrh_id: "core/shopify_liquid/canvas_to_liquid_transpiler.py"
# purpose: "Visual Canvas to Shopify OS 2.0 Liquid Section Transpiler with Remotion Video Bridge & Ledger Registration."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-CANVAS-TO-LIQUID-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime & Maksym Kuzmenko"
# --- END DNK-MRH-HEADER ---

import json
import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.orchestrator.swarm_ledger import SwarmLedger

logger = logging.getLogger("canvas_to_liquid_transpiler")


class CanvasNodeData(BaseModel):
    id: str
    type: str  # hero_banner, product_grid, feature_list, cta_banner, video_player
    title: Optional[str] = "Секція DNK"
    subtitle: Optional[str] = None
    price: Optional[str] = None
    cta_text: Optional[str] = "Купити зараз"
    cta_link: Optional[str] = "/collections/all"
    video_url: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    custom_props: Dict[str, Any] = Field(default_factory=dict)


class CanvasGraphPayload(BaseModel):
    screen_id: str
    section_name: str
    category: str = "DNK Studio Generated"
    nodes: List[CanvasNodeData] = Field(default_factory=list)
    task_id: Optional[str] = None


class TranspilationResult(BaseModel):
    section_name: str
    filename: str
    liquid_code: str
    schema_valid: bool
    nodes_count: int
    ledger_artifact_id: Optional[str] = None


class CanvasToLiquidTranspiler:
    """
    Transpiles arbitrary Visual Canvas graph nodes into a modular, production-ready
    Shopify OS 2.0 Liquid section with customizable blocks, native schemas, and Remotion video embeds.
    """

    def __init__(self, ledger: Optional[SwarmLedger] = None):
        self.ledger = ledger or SwarmLedger.get_instance()

    def transpile(self, payload: CanvasGraphPayload) -> TranspilationResult:
        html_parts: List[str] = []
        settings_defs: List[Dict[str, Any]] = [
            {
                "type": "text",
                "id": "section_heading",
                "label": "Головний заголовок",
                "default": payload.section_name.replace("_", " ").title(),
            },
            {
                "type": "checkbox",
                "id": "full_width",
                "label": "На всю ширину екрану",
                "default": False,
            },
        ]
        block_types: List[Dict[str, Any]] = []

        html_parts.append(f"<!-- 🛍️ DNK OS Canvas-Generated Section: {payload.section_name} -->")
        html_parts.append(
            '<section class="dnk-canvas-section py-12 px-4 {% if section.settings.full_width %}w-full{% else %}max-w-7xl mx-auto{% endif %}">'
        )
        html_parts.append("  <div class=\"container mx-auto\">")

        for idx, node in enumerate(payload.nodes):
            if node.type == "hero_banner":
                html_parts.append(self._render_hero_banner(node, idx))
                block_types.append(self._get_hero_block_schema())
            elif node.type == "video_player":
                html_parts.append(self._render_video_player(node, idx))
                block_types.append(self._get_video_block_schema())
            elif node.type == "product_grid":
                html_parts.append(self._render_product_grid(node, idx))
                block_types.append(self._get_product_grid_schema())
            elif node.type == "feature_list":
                html_parts.append(self._render_feature_list(node, idx))
                block_types.append(self._get_feature_list_schema())
            else:
                html_parts.append(self._render_generic_node(node, idx))

        html_parts.append("  </div>")
        html_parts.append("</section>")

        # Generate Shopify OS 2.0 Schema
        schema_dict = {
            "name": payload.section_name.replace("_", " ").title(),
            "tag": "section",
            "class": f"dnk-section-{payload.section_name}",
            "settings": settings_defs,
            "blocks": block_types,
            "presets": [
                {
                    "name": payload.section_name.replace("_", " ").title(),
                    "category": payload.category,
                }
            ],
        }

        schema_json = json.dumps(schema_dict, indent=2, ensure_ascii=False)
        liquid_code = "\n".join(html_parts) + f"\n\n{{% schema %}}\n{schema_json}\n{{% endschema %}}\n"

        # Validate Schema
        is_valid = self._validate_liquid_schema(liquid_code)

        # Register to Swarm Ledger for inter-agent communication
        artifact_id = None
        if self.ledger:
            artifact = self.ledger.register_artifact(
                key=f"liquid:section:{payload.section_name}",
                category="LIQUID_SECTION",
                producer_agent="dnk_shopify",
                content={
                    "section_name": payload.section_name,
                    "filename": f"sections/{payload.section_name}.liquid",
                    "liquid_code": liquid_code,
                    "nodes_count": len(payload.nodes),
                    "schema": schema_dict,
                },
                task_id=payload.task_id or f"task_transpile_{payload.screen_id}",
                metadata={"screen_id": payload.screen_id, "category": payload.category},
            )
            artifact_id = artifact.artifact_id

        return TranspilationResult(
            section_name=payload.section_name,
            filename=f"sections/{payload.section_name}.liquid",
            liquid_code=liquid_code,
            schema_valid=is_valid,
            nodes_count=len(payload.nodes),
            ledger_artifact_id=artifact_id,
        )

    def _render_hero_banner(self, node: CanvasNodeData, idx: int) -> str:
        return f"""    <!-- Node {node.id}: Hero Banner -->
    <div class="dnk-hero-banner relative rounded-2xl overflow-hidden bg-gradient-to-r from-slate-900 to-indigo-950 p-8 md:p-16 mb-8 text-white shadow-2xl border border-slate-800">
      <div class="max-w-2xl">
        <h1 class="text-3xl md:text-5xl font-extrabold tracking-tight mb-4">{node.title}</h1>
        {f'<p class="text-lg md:text-xl text-slate-300 mb-6">{node.subtitle}</p>' if node.subtitle else ''}
        {f'<div class="text-2xl font-bold text-emerald-400 mb-6">{node.price}</div>' if node.price else ''}
        <a href="{node.cta_link}" class="inline-flex items-center justify-center px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-white transition-all shadow-lg hover:shadow-indigo-500/25">
          {node.cta_text}
        </a>
      </div>
    </div>"""

    def _render_video_player(self, node: CanvasNodeData, idx: int) -> str:
        video_src = node.video_url or "{{ block.settings.video_url }}"
        return f"""    <!-- Node {node.id}: Remotion Video Player -->
    <div class="dnk-video-player rounded-2xl overflow-hidden bg-black p-4 mb-8 shadow-xl border border-slate-800">
      <h3 class="text-xl font-bold text-white mb-3">{node.title}</h3>
      <div class="relative aspect-video md:aspect-[9/16] max-w-sm mx-auto rounded-xl overflow-hidden bg-slate-950">
        <video src="{video_src}" controls autoplay loop muted playsinline class="w-full h-full object-cover">
          Ваш браузер не підтримує відтворення відео.
        </video>
      </div>
    </div>"""

    def _render_product_grid(self, node: CanvasNodeData, idx: int) -> str:
        return f"""    <!-- Node {node.id}: Product Grid -->
    <div class="dnk-product-grid mb-8">
      <h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-6">{node.title}</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white">
          <h4 class="font-bold text-lg mb-2">{node.title}</h4>
          <span class="text-emerald-400 font-bold">{node.price or 'Ціна за запитом'}</span>
        </div>
      </div>
    </div>"""

    def _render_feature_list(self, node: CanvasNodeData, idx: int) -> str:
        items = "\n".join([f'        <li class="flex items-center gap-2 text-slate-300">✓ {f}</li>' for f in node.features])
        return f"""    <!-- Node {node.id}: Feature List -->
    <div class="dnk-features-block p-6 bg-slate-900/60 rounded-xl border border-slate-800 mb-8">
      <h3 class="text-xl font-semibold text-white mb-4">{node.title}</h3>
      <ul class="space-y-2">
{items}
      </ul>
    </div>"""

    def _render_generic_node(self, node: CanvasNodeData, idx: int) -> str:
        return f"""    <!-- Node {node.id}: Generic Canvas Element ({node.type}) -->
    <div class="dnk-generic-node p-4 rounded-lg bg-slate-800/40 border border-slate-700/50 mb-4 text-white">
      <h4 class="font-semibold">{node.title}</h4>
    </div>"""

    def _get_hero_block_schema(self) -> Dict[str, Any]:
        return {
            "type": "hero_banner",
            "name": "Hero Showcase Banner",
            "settings": [
                {"type": "text", "id": "heading", "label": "Заголовок", "default": "Головний Банер"},
                {"type": "text", "id": "cta_text", "label": "Текст кнопки", "default": "Замовити"},
                {"type": "url", "id": "cta_link", "label": "Посилання кнопки"},
            ],
        }

    def _get_video_block_schema(self) -> Dict[str, Any]:
        return {
            "type": "video_player",
            "name": "Remotion 9:16 Video Player",
            "settings": [
                {"type": "text", "id": "video_url", "label": "Відео URL (Remotion Export)", "default": ""},
                {"type": "checkbox", "id": "autoplay", "label": "Автозапуск", "default": True},
            ],
        }

    def _get_product_grid_schema(self) -> Dict[str, Any]:
        return {
            "type": "product_grid",
            "name": "Product Grid",
            "settings": [
                {"type": "collection", "id": "collection", "label": "Колекція продуктів"},
                {"type": "range", "id": "products_to_show", "min": 2, "max": 12, "step": 2, "default": 4, "label": "Кількість"},
            ],
        }

    def _get_feature_list_schema(self) -> Dict[str, Any]:
        return {
            "type": "feature_list",
            "name": "Features List",
            "settings": [
                {"type": "text", "id": "features_title", "label": "Заголовок списку", "default": "Переваги"},
            ],
        }

    def _validate_liquid_schema(self, code: str) -> bool:
        match = re.search(r"\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}", code, re.DOTALL)
        if not match:
            return False
        try:
            parsed = json.loads(match.group(1).strip())
            return "name" in parsed and "settings" in parsed and "presets" in parsed
        except Exception:
            return False
