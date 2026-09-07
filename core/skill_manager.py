# --- DNK-MRH-HEADER ---
# mrh_id: "core/skill_manager.py"
# purpose: "SkillManager handles SKILL.md parsing, storage, and token-efficient trigger matching."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import os
import json
import re
from typing import Dict, List, Any, Optional

class SkillModel:
    def __init__(self, name: str, description: str, category: str, triggers: List[str], content: str = ""):
        self.name = name
        self.description = description
        self.category = category
        self.triggers = triggers
        self.content = content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "triggers": self.triggers,
            "content": self.content
        }

class SkillManager:
    """
    SkillManager handles local skill registration, validation of SKILL.md format,
    and Token-Efficient RAG trigger matching to prevent context bloat.
    """
    def __init__(self, skills_dir: Optional[str] = None):
        if skills_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.skills_dir = os.path.join(base_dir, "skills")
        else:
            self.skills_dir = skills_dir
            
        self.skills: Dict[str, SkillModel] = {}
        self.load_local_skills()

    def add_skill(self, name: str, description: str, category: str, triggers: List[str], content: str = "") -> SkillModel:
        """Registers a new skill in the manager."""
        skill = SkillModel(name, description, category, triggers, content)
        self.skills[name] = skill
        return skill

    def load_local_skills(self) -> None:
        """Pre-loads default MVP skills."""
        # Register a few default MVP skills
        self.add_skill(
            name="shopify-liquid-customizer",
            description="Compiles Liquid sections and PDP customizer blocks.",
            category="shopify",
            triggers=["liquid", "shopify", "bundle", "customizer"],
            content="Use Shopify CLI 3.0 to tinker Liquid sections."
        )
        self.add_skill(
            name="task-forest-sync",
            description="Synchronizes Markdown Task Forest with PostgreSQL.",
            category="core",
            triggers=["task-forest", "sync", "plant", "flower"],
            content="Scans docs/tasks/ directory and commits changes to DB."
        )

    def find_matching_skills(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Token-Efficient RAG: Scans the user prompt for matching trigger keywords,
        returning only the relevant skills to prevent context bloat.
        """
        matched = []
        prompt_lower = prompt.lower()
        for skill in self.skills.values():
            for trigger in skill.triggers:
                pattern = r"\b" + re.escape(trigger.lower()) + r"\b"
                if re.search(pattern, prompt_lower):
                    matched.append(skill.to_dict())
                    break  # Match found, skip other triggers for this skill
        return matched
