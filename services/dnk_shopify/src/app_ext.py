#!/usr/bin/env python3
"""
app_ext.py — Шар ізольованої підготовки додатків та розширень (Етап D Спринту 3)
"""
from __future__ import annotations
import os
import sys
import json
from pathlib import Path

class AppExtensionScaffold:
    def __init__(self, base_dir: str):
        self.extensions_dir = os.path.join(base_dir, "extensions")

    def create_app_block(self, extension_name: str, block_name: str) -> dict:
        """Створює структуру та конфігурацію розширення теми без змішування з темою"""
        ext_path = os.path.join(self.extensions_dir, extension_name)
        blocks_path = os.path.join(ext_path, "blocks")
        
        os.makedirs(blocks_path, exist_ok=True)
        
        # Створюємо shopify.extension.toml
        toml_content = f"""# 🔌 Shopify Extension Configuration
type = "theme_app_extension"
name = "{extension_name}"
"""
        with open(os.path.join(ext_path, "shopify.extension.toml"), "w", encoding="utf-8") as f:
            f.write(toml_content)
            
        # Створюємо сам блок розширення
        block_schema = {
            "name": block_name.capitalize(),
            "target": "section",
            "templates": ["product", "index"],
            "settings": []
        }
        
        block_content = f"""<!-- Theme App Extension Block: {block_name} -->
<div class="dnk-app-{block_name}">
  <span>App Embed: {block_name.capitalize()}</span>
</div>

{{% schema %}}
{json.dumps(block_schema, indent=2, ensure_ascii=False)}
{{% endschema %}}
"""
        with open(os.path.join(blocks_path, f"{block_name}.liquid"), "w", encoding="utf-8") as f:
            f.write(block_content)
            
        return {
            "status": "success",
            "extension_name": extension_name,
            "scaffold_path": os.path.relpath(ext_path, start=os.path.dirname(self.extensions_dir))
        }

if __name__ == "__main__":
    base_dir = str(Path(__file__).resolve().parent.parent)
    scaffold = AppExtensionScaffold(base_dir)
    print(scaffold.create_app_block("reburn-conversion-booster", "countdown-timer"))
