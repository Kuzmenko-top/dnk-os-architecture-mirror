#!/usr/bin/env python3
"""
router.py — Template Routing Layer (Етап A Спринту 3)
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

class TemplateRouter:
    def __init__(self, theme_dir: str):
        self.theme_dir = theme_dir

    def resolve_target_path(self, task_type: str, file_name: str) -> dict:
        """Визначає точний Shopify-native шлях для нового артефакту"""
        # Створюємо мапу роутингу
        routing_map = {
            "pdp": "templates",
            "landing": "templates",
            "advertorial": "templates",
            "listicle": "templates",
            "section": "sections",
            "theme_block": "blocks",
            "app_extension": "extensions"
        }
        
        folder = routing_map.get(task_type)
        if not folder:
            return {"status": "error", "message": f"Невідомий тип завдання: {task_type}"}
            
        # Формуємо розширення за замовчуванням
        if task_type in ["pdp", "landing", "advertorial", "listicle"] and not file_name.endswith(".json"):
            file_name = f"{file_name}.json"
        elif task_type in ["section", "theme_block"] and not file_name.endswith(".liquid"):
            file_name = f"{file_name}.liquid"
            
        # Якщо це розширення — ізолюємо в окрему папку extensions/
        if folder == "extensions":
            target_dir = os.path.join(os.path.dirname(self.theme_dir), "extensions")
        else:
            target_dir = os.path.join(self.theme_dir, folder)
            
        absolute_path = os.path.join(target_dir, file_name)
        relative_path = os.path.relpath(absolute_path, start=os.path.dirname(self.theme_dir))
        
        return {
            "status": "success",
            "folder": folder,
            "file_name": file_name,
            "absolute_path": absolute_path,
            "relative_path": relative_path
        }

if __name__ == "__main__":
    base_theme = str(Path(__file__).resolve().parent.parent / "DNK_Ecom_v1_0_0")
    router = TemplateRouter(base_theme)
    print(router.resolve_target_path("landing", "summer-sale"))
    print(router.resolve_target_path("section", "promo-banner"))
