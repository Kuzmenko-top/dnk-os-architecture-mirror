#!/usr/bin/env python3
"""
mudriy_craftiar_build.py — Скрипт автоматичної генерації контенту, сторінок та карток товарів для Мудрого Крафтяра
"""
from __future__ import annotations
import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "services/dnk_shopify"))

from src.router import TemplateRouter
from src.content import ContentEngine
from src.section import SectionGenerator
from src.theme_intel import ThemeIntelligence

def build_mudriy_craftiar():
    theme_dir = str(PROJECT_ROOT / "services/dnk_shopify/DNK_Ecom_v1_0_0")
    router = TemplateRouter(theme_dir)
    content_engine = ContentEngine(router)
    
    print("🚀 [Мудрий Крафтяр] Початок автоматичної генерації магазину...")
    
    # 1. Генерація Advertorial сторінки (огляд переваг коптилень)
    print("✍️ Генерація Advertorial сторінки...")
    advertorial_spec = content_engine.generate_page_spec(
        "advertorial", 
        "adv-chomu-koptylni", 
        ["hero-banner", "content-tabs", "product-compare-chart"]
    )
    
    # 2. Генерація Listicle сторінки (ТОП-5 причин купити димогенератор)
    print("✍️ Генерація Listicle сторінки...")
    listicle_spec = content_engine.generate_page_spec(
        "listicle", 
        "list-5-dymogenerator", 
        ["hero-banner", "promo-popup", "product-grid"]
    )
    
    # 3. Створення карток товарів (PDP) під коптильні та додаткове обладнання
    print("🛍️ Створення шаблону карток товарів (PDP)...")
    pdp_spec = content_engine.generate_page_spec(
        "pdp", 
        "pdp-koptylnya-pro", 
        ["main-product", "product-compare-chart", "facebook-reviews"]
    )
    
    pdp_accessories = content_engine.generate_page_spec(
        "pdp", 
        "pdp-dymogenerator-acc", 
        ["main-product", "promo-popup"]
    )
    
    # Зберігаємо логи запуску кейсу
    client_report = {
        "client_name": "Мудрий Крафтяр",
        "store": "m-craft-top",
        "generated_assets": {
            "advertorial": advertorial_spec["artifact_path"],
            "listicle": listicle_spec["artifact_path"],
            "pdp_main": pdp_spec["artifact_path"],
            "pdp_accessories": pdp_accessories["artifact_path"]
        },
        "status": "completed",
        "version_tag": "1.0.0-mudriy-craftiar.1"
    }
    
    report_path = str(PROJECT_ROOT / "services/dnk_shopify/docs/business/clients/mudriy_craftiar/generated_assets_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(client_report, f, indent=2, ensure_ascii=False)
        
    print(f"🎉 Магазин Мудрий Крафтяр успішно налаштований! Звіт збережено у: {report_path}")

if __name__ == "__main__":
    build_mudriy_craftiar()
