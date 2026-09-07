# --- DNK-MRH-HEADER ---
# mrh_id: "skills/registry.py"
# purpose: "Manage registering, discovering, and validating design skills."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, Optional
from .models import BaseSkill
from .dnk_ui_generate_workspace import DNKUiGenerateWorkspaceSkill

class SkillRegistry:
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        # Register default skills
        self.register(DNKUiGenerateWorkspaceSkill())

    def register(self, skill: BaseSkill):
        self._skills[skill.contract.id] = skill

    def get_skill(self, skill_id: str) -> Optional[BaseSkill]:
        return self._skills.get(skill_id)

    def list_skills(self) -> Dict[str, Any]:
        return {skill_id: skill.contract.dict() for skill_id, skill in self._skills.items()}

# Global registry instance
registry = SkillRegistry()
