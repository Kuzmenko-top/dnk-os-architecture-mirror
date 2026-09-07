# --- DNK-MRH-HEADER ---
# mrh_id: "core/swarm_orchestrator.py"
# purpose: "Hybrid Swarm Orchestrator with YAML Manifests and <0.05s RAG skill injection backed by unified SwarmControlPlane."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import yaml
import time
from typing import Dict, List, Any, Tuple, Optional
from core.orchestrator.control_plane import SwarmControlPlane

class SwarmOrchestrator:
    """
    SwarmOrchestrator handles loading role manifests from YAML configs and
    high-velocity, low-latency (<0.05s) RAG skill injection from hub_memory.
    Backed by SwarmControlPlane as the unified state machine.
    """
    def __init__(self, control_plane: Optional[SwarmControlPlane] = None):
        self.control_plane = control_plane or SwarmControlPlane()
        self.roles: Dict[str, Dict[str, Any]] = self.control_plane.roles
        self.skills: Dict[str, Dict[str, Any]] = self.control_plane.skills

    def load_role_manifest(self, yaml_content: str) -> Dict[str, Any]:
        """Loads and registers an agent role manifest from a YAML string."""
        try:
            manifest = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML role manifest: {e}")

        if not isinstance(manifest, dict) or "name" not in manifest or "role" not in manifest:
            raise ValueError("Manifest must be a dict containing 'name' and 'role'")
            
        role_name = manifest["name"]
        self.roles[role_name] = manifest
        self.control_plane.register_role(role_name, manifest)
        return manifest

    def register_skill(self, name: str, description: str, content: str, tags: Optional[List[str]] = None) -> None:
        """Registers a procedural skill to the RAG memory store."""
        self.control_plane.register_skill(name, description, content, tags)

    def inject_skills_rag(self, agent_name: str, query: str, limit: int = 2) -> Tuple[List[Dict[str, Any]], float]:
        """
        Retrieves matching skills for the agent's task query under 0.05s.
        Uses a fast set-intersection token matching technique.
        Returns a tuple of (matched_skills_list, execution_duration_seconds).
        """
        return self.control_plane.inject_skills_rag(agent_name, query, limit=limit)

    def compile_agent_system_instructions(self, agent_name: str, task_query: str) -> str:
        """Injects matched skills dynamically into the agent's base system prompt."""
        agent = self.roles[agent_name]
        base_prompt = agent.get("system_instructions", "")
        
        matched_skills, duration = self.inject_skills_rag(agent_name, task_query)
        
        if matched_skills:
            injected_str = "\n\n=== INJECTED PROCEDURAL SKILLS (RAG) ==="
            for idx, skill in enumerate(matched_skills, 1):
                injected_str += f"\nSkill {idx}: {skill['name']}\nDescription: {skill['description']}\n{skill['content']}\n"
            injected_str += f"\n(Skill lookup completed in {duration:.6f}s, budget: 0.05s)"
            return base_prompt + injected_str
        return base_prompt
