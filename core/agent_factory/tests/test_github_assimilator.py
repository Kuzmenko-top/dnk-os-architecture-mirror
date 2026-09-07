# --- DNK-MRH-HEADER ---
# mrh_id: "core/agent_factory/tests/test_github_assimilator.py"
# purpose: "Unit tests for GitHubTechAssimilator creating native DNK OS Skills."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import tempfile
import pytest
from core.agent_factory.github_assimilator import GitHubTechAssimilator


def test_github_assimilator_creates_skill():
    with tempfile.TemporaryDirectory() as tmp_dir:
        assimilator = GitHubTechAssimilator(target_skills_dir=tmp_dir)
        res = assimilator.assimilate_repository(
            repo_url="https://github.com/AgentSwarms-fyi/agentswarms",
            repo_name="agentswarms",
            description="Agentic Swarm Patterns Repository"
        )

        assert res["status"] == "success"
        assert os.path.exists(res["skill_path"])

        skill_folder = os.path.dirname(res["skill_path"])
        assert os.path.exists(os.path.join(skill_folder, "scripts"))
        assert os.path.exists(os.path.join(skill_folder, "references"))
        assert os.path.exists(os.path.join(skill_folder, "examples"))

        with open(res["skill_path"], "r", encoding="utf-8") as f:
            text = f.read()

        assert "Agentic Swarm Patterns Repository" in text
        assert "agentswarms" in text
