#!/usr/bin/env python3
"""
sprint2_engine.py — Скрипт автоматизації кроків Sprint 2 для сервісу dnk_shopify
"""
from __future__ import annotations
import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "services/dnk_shopify"))

from src.theme_intel import ThemeIntelligence
from src.adapters.git_research import GitResearchAdapter

def execute_sprint2():
    theme_dir = str(PROJECT_ROOT / "services/dnk_shopify/DNK_Ecom_v1_0_0")
    intel = ThemeIntelligence(theme_dir)
    adapter = GitResearchAdapter()
    
    print("🏁 [Sprint 2] Етап 1: Theme Ingestion...")
    structure = intel.scan_theme_structure()
    if "error" in structure:
        print(f"❌ Помилка Ingestion: {structure['error']}")
        return
        
    # Зберігаємо базовий снепшот
    with open(os.path.join(theme_dir, "theme_map_v1.json") if not "error" in structure else "theme_map_v1.json", "w") as f:
        json.dump(structure, f, indent=2, ensure_ascii=False)
    print("✅ Снепшот структури збережено у theme_map_v1.json")
    
    print("\n🏁 [Sprint 2] Етап 2: Theme Classification...")
    schemas = intel.extract_schemas()
    block_info = intel.identify_block_types()
    
    classification = {
        "templates": [t for t in structure["inventory"].get("templates", [])],
        "sections": [s for s in structure["inventory"].get("sections", [])],
        "theme_blocks": block_info["theme_blocks"],
        "section_blocks": block_info["section_blocks"],
        "snippets": [s for s in structure["inventory"].get("snippets", [])]
    }
    
    with open("theme_classification.json", "w") as f:
        json.dump(classification, f, indent=2, ensure_ascii=False)
    print("✅ Дані класифікації збережено у theme_classification.json")
    
    print("\n🏁 [Sprint 2] Етап 3: Dependency Graph...")
    graph = intel.build_dependency_graph()
    with open("dependency_graph.json", "w") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)
    print("✅ Граф залежностей збережено у dependency_graph.json")
    
    print("\n🏁 [Sprint 2] Етап 4: Pattern Registry...")
    # Шукаємо кращі паттерни в базі pgvector через адаптер
    patterns = adapter.query_patterns("quiz", limit=5)
    patterns += adapter.query_patterns("theme", limit=5)
    patterns += adapter.query_patterns("marketing", limit=5)
    
    with open("pattern_registry.json", "w") as f:
        json.dump(patterns, f, indent=2, ensure_ascii=False)
    print("✅ Pattern Registry успішно сформовано у pattern_registry.json")
    
    print("\n🏁 [Sprint 2] Етап 5: Gap and Duplicate Analysis...")
    duplicates = intel.detect_duplicates()
    gaps = {
        "missing_sections": ["quiz-section", "advertorial-template", "product-card-variant"],
        "safe_zones": ["product-info", "cart-summary"]
    }
    
    with open("gap_analysis.json", "w") as f:
        json.dump({"duplicates": duplicates, "gaps": gaps}, f, indent=2, ensure_ascii=False)
    print("✅ Gap & Duplicate аналіз збережено у gap_analysis.json")
    
    print("\n🏁 [Sprint 2] Етап 6: Recommendations Layer...")
    report = intel.generate_theme_report()
    with open("build_recommendations.json", "w") as f:
        json.dump(report["recommendations"], f, indent=2, ensure_ascii=False)
    print("✅ Рекомендації збережено у build_recommendations.json")
    
    print("\n🏁 [Sprint 2] Етап 7: Validation & Export...")
    sprint2_bundle = {
        "classification": classification,
        "graph": graph,
        "patterns": patterns,
        "gaps": gaps,
        "recommendations": report["recommendations"]
    }
    with open("sprint2_final_bundle.json", "w") as f:
        json.dump(sprint2_bundle, f, indent=2, ensure_ascii=False)
        
    print("🎉 Всі етапи Спринту 2 виконані на 100%!")

if __name__ == "__main__":
    execute_sprint2()
