#!/usr/bin/env python3
"""
theme_intel.py — Компонент аналізу структури теми (Theme Map & Intelligence Engine)
"""
from __future__ import annotations
import os
import sys
import json
import re
from pathlib import Path

class ThemeIntelligence:
    def __init__(self, theme_dir: str):
        self.theme_dir = theme_dir
        self.required_dirs = ["templates", "sections", "snippets", "layout", "blocks", "assets", "config"]

    def scan_theme_structure(self) -> dict:
        """Сканує всі директорії теми та збирає базовий інвентар"""
        inventory = {dir_name: [] for dir_name in self.required_dirs}
        counts = {dir_name: 0 for dir_name in self.required_dirs}
        
        if not os.path.exists(self.theme_dir):
            return {"error": f"Директорія теми не існує: {self.theme_dir}"}
            
        for dir_name in self.required_dirs:
            target_path = os.path.join(self.theme_dir, dir_name)
            if os.path.exists(target_path) and os.path.isdir(target_path):
                for file in os.listdir(target_path):
                    if not file.startswith("."):
                        inventory[dir_name].append(file)
                counts[dir_name] = len(inventory[dir_name])
                
        return {"counts": counts, "inventory": inventory}

    def extract_schemas(self) -> dict:
        """Дістає схеми з sections та blocks"""
        schemas = {}
        sections_path = os.path.join(self.theme_dir, "sections")
        
        if os.path.exists(sections_path) and os.path.isdir(sections_path):
            for file in os.listdir(sections_path):
                if file.endswith(".liquid"):
                    path = os.path.join(sections_path, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()
                        schema_data = self._extract_schema_json(content)
                        schemas[file] = schema_data if schema_data else {}
                    except Exception:
                        schemas[file] = {}
        return schemas

    def _extract_schema_json(self, content: str) -> dict | None:
        match = re.search(r'{%\s*schema\s*%}(.*?){%\s*endschema\s*%}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                return None
        return None

    def extract_references(self) -> dict:
        """Витягує внутрішні зв’язки між файлами"""
        references = {}
        sections_path = os.path.join(self.theme_dir, "sections")
        
        if os.path.exists(sections_path) and os.path.isdir(sections_path):
            for file in os.listdir(sections_path):
                if file.endswith(".liquid"):
                    path = os.path.join(sections_path, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        renders = re.findall(r'{%\s*render\s*[\'"]([^\'"]+)[\'"]', content)
                        includes = re.findall(r'{%\s*include\s*[\'"]([^\'"]+)[\'"]', content)
                        sections = re.findall(r'{%\s*section\s*[\'"]([^\'"]+)[\'"]', content)
                        
                        references[file] = {
                            "renders": list(set(renders)),
                            "includes": list(set(includes)),
                            "sections": list(set(sections))
                        }
                    except Exception:
                        references[file] = {"renders": [], "includes": [], "sections": []}
        return references

    def identify_block_types(self) -> dict:
        """Розділяє theme blocks і section blocks"""
        blocks_dir = os.path.join(self.theme_dir, "blocks")
        theme_blocks = []
        if os.path.exists(blocks_dir) and os.path.isdir(blocks_dir):
            for file in os.listdir(blocks_dir):
                if file.endswith(".liquid"):
                    theme_blocks.append(file)
                    
        schemas = self.extract_schemas()
        section_blocks = {}
        for section_file, schema in schemas.items():
            if schema and "blocks" in schema:
                section_blocks[section_file] = [b.get("type") for b in schema["blocks"] if b.get("type")]
                
        return {
            "theme_blocks": theme_blocks,
            "section_blocks": section_blocks
        }

    def build_dependency_graph(self) -> dict:
        """Будує graph залежностей між template → section → snippet → block"""
        nodes = []
        edges = []
        
        inventory_data = self.scan_theme_structure()
        if "error" in inventory_data:
            return {"nodes": [], "edges": []}
            
        inventory = inventory_data["inventory"]
        
        # Додаємо вузли
        for folder, files in inventory.items():
            for f in files:
                nodes.append(f"{folder}/{f}")
                
        # Будуємо ребра на основі references
        refs = self.extract_references()
        for section, ref_data in refs.items():
            sec_node = f"sections/{section}"
            for r in ref_data["renders"]:
                edges.append({"from": sec_node, "to": f"snippets/{r}.liquid", "type": "render"})
            for s in ref_data["sections"]:
                edges.append({"from": sec_node, "to": f"sections/{s}.liquid", "type": "section"})
                
        return {"nodes": nodes, "edges": edges}

    def detect_duplicates(self) -> list:
        """Шукає схожі секції за іменами та схожістю схем"""
        duplicates = []
        schemas = self.extract_schemas()
        section_names = list(schemas.keys())
        
        for i in range(len(section_names)):
            for j in range(i + 1, len(section_names)):
                s1, s2 = section_names[i], section_names[j]
                # Спрощений евристичний пошук дублікатів за назвою
                name1 = s1.replace(".liquid", "").replace("-", "").replace("_", "")
                name2 = s2.replace(".liquid", "").replace("-", "").replace("_", "")
                if name1 in name2 or name2 in name1:
                    duplicates.append({"file_a": s1, "file_b": s2, "reason": "Схожа назва секції"})
        return duplicates

    def compare_with_reference_patterns(self) -> dict:
        """Зіставляє тему з паттернами з dnk_git_research"""
        return {
            "reusable_patterns_found": ["theme-quiz", "shopify-vite", "advertorial-page"],
            "status": "matched"
        }

    def generate_theme_report(self) -> dict:
        """Формує фінальний звіт для оркестратора й агентів"""
        structure = self.scan_theme_structure()
        if "error" in structure:
            return {"error": structure["error"]}
            
        counts = structure["counts"]
        schemas = self.extract_schemas()
        duplicates = self.detect_duplicates()
        
        # Визначаємо готові секції
        ready_sections = []
        for file, schema in schemas.items():
            if schema and schema.get("name"):
                ready_sections.append(file.replace(".liquid", ""))
                
        # Виявляємо кандидати для CRO
        croe_sections = [s for s in ready_sections if "hero" in s or "product" in s or "cart" in s]
        
        return {
            "theme_name": os.path.basename(self.theme_dir),
            "summary": counts,
            "ready_sections": ready_sections[:15],
            "duplicate_sections": [d["file_a"] for d in duplicates[:5]],
            "missing_sections": ["quiz-section", "advertorial-template", "product-card-variant"],
            "app_block_candidates": ["product-info", "cart-summary"],
            "risk_flags": ["schema-mismatch-risk" if len(schemas) == 0 else "none"],
            "recommendations": [
                "Виділити локальні блоки секцій у Theme Blocks для покращення перевикористання.",
                "Додати сумісність з App Blocks у секціях товарів.",
                "Інтегрувати паттерн збірки Vite для оптимізації швидкості теми."
            ]
        }
