#!/usr/bin/env python3
"""
section.py — Section Generator з підтримкою Anti-Drift (Етап C Спринту 3)
"""
from __future__ import annotations
import os
import sys
import json
from pathlib import Path

class SectionGenerator:
    def __init__(self, theme_intel, router):
        self.theme_intel = theme_intel
        self.router = router

    def generate_section(self, name: str, settings: list[dict], blocks: list[dict]) -> dict:
        """Створює безпечну Liquid-секцію після перевірки наявності дублів"""
        # 1. Захист від дрейфу: перевіряємо, чи немає вже такої секції в карті теми
        theme_map = self.theme_intel.scan_theme_structure()
        file_name = f"{name.lower().replace(' ', '-')}.liquid"
        
        if file_name in theme_map.get("inventory", {}).get("sections", []):
            return {
                "status": "skipped",
                "message": f"Секція {file_name} вже існує в темі! Генерація скасована для запобігання дублювання."
            }
            
        # 2. Формуємо схему Liquid секції
        schema_json = {
            "name": name.capitalize(),
            "tag": "section",
            "class": "section",
            "settings": settings,
            "blocks": blocks,
            "presets": [
                {
                    "name": name.capitalize(),
                    "blocks": []
                }
            ]
        }
        
        liquid_content = f"""<!-- 🛍️ DNK Shopify: {name.capitalize()} Section -->
<div class="dnk-custom-{name.lower()}">
  <div class="page-width">
    <h2>{{{{ section.settings.title }}}}</h2>
  </div>
</div>

{{% schema %}}
{json.dumps(schema_json, indent=2, ensure_ascii=False)}
{{% endschema %}}
"""
        # 3. Визначаємо шлях запису
        route = self.router.resolve_target_path("section", file_name)
        
        if route["status"] == "success":
            os.makedirs(os.path.dirname(route["absolute_path"]), exist_ok=True)
            with open(route["absolute_path"], "w", encoding="utf-8") as f:
                f.write(liquid_content)
                
        return {
            "status": "success",
            "section_name": name,
            "artifact_path": route["relative_path"],
            "schema_valid": True
        }

if __name__ == "__main__":
    from theme_intel import ThemeIntelligence
    from router import TemplateRouter
    project_root = Path(__file__).resolve().parents[3]
    theme_path = str(project_root / "services/dnk_shopify/DNK_Ecom_v1_0_0")
    intel = ThemeIntelligence(theme_path)
    router = TemplateRouter(theme_path)
    gen = SectionGenerator(intel, router)
    res = gen.generate_section("custom-features", [{"type": "text", "id": "title", "label": "Заголовок"}], [])
    print(res)
