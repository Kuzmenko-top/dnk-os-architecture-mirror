#!/usr/bin/env python3
"""
content.py — Content Generation Engine (Етап B Спринту 3)
"""
from __future__ import annotations
import os
import sys
import json
from pathlib import Path

class ContentEngine:
    def __init__(self, router):
        self.router = router

    def generate_page_spec(self, page_type: str, title: str, sections_list: list[str]) -> dict:
        """Генерує Shopify-ready JSON template структуру для сторінок"""
        # Створюємо базову валідну схему JSON-шаблону сторінки Shopify
        template_json = {
            "wrapper": "div",
            "sections": {},
            "order": []
        }
        
        for idx, sec in enumerate(sections_list):
            sec_id = f"custom_{sec}_{idx}"
            template_json["sections"][sec_id] = {
                "type": sec,
                "settings": {
                    "title": f"{title} - {sec.capitalize()}",
                    "heading_size": "h2"
                }
            }
            template_json["order"].append(sec_id)
            
        # Роутимо запит
        route = self.router.resolve_target_path(page_type, f"page.{page_type}-{title.lower().replace(' ', '-')}")
        
        if route["status"] == "success":
            # Записуємо специфікацію
            os.makedirs(os.path.dirname(route["absolute_path"]), exist_ok=True)
            with open(route["absolute_path"], "w", encoding="utf-8") as f:
                json.dump(template_json, f, indent=2, ensure_ascii=False)
                
        return {
            "status": "success",
            "page_type": page_type,
            "title": title,
            "artifact_path": route["relative_path"],
            "structure": template_json
        }

if __name__ == "__main__":
    from router import TemplateRouter
    base_theme = Path(__file__).resolve().parent.parent / "DNK_Ecom_v1_0_0"
    router = TemplateRouter(str(base_theme))
    engine = ContentEngine(router)
    spec = engine.generate_page_spec("landing", "ReBurn Summer Promo", ["hero-banner", "product-grid"])
    print(json.dumps(spec, indent=2, ensure_ascii=False))
