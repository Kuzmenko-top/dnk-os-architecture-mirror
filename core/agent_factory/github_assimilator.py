# --- DNK-MRH-HEADER ---
# mrh_id: "core/agent_factory/github_assimilator.py"
# purpose: "GitHub Tech Assimilator parsing GitHub repository URLs and auto-synthesizing DNK OS Skills and Swarm Agent capabilities."
# canonical_source: true
# alters_files: ["skills/*", "core/agent_factory/agents/*"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import re
from typing import Dict, Any, Optional


class GitHubTechAssimilator:
    """
    Assimilates GitHub technology repositories into native DNK OS Skills and Agents.
    """
    def __init__(self, target_skills_dir: str = "skills") -> None:
        self.target_skills_dir = target_skills_dir
        os.makedirs(self.target_skills_dir, exist_ok=True)

    def assimilate_repository(self, repo_url: str, repo_name: str, description: str) -> Dict[str, Any]:
        """
        Creates a native DNK OS skill structure for the assimilated GitHub repository.
        """
        safe_name = repo_name.lower().replace(" ", "-").replace("/", "-")
        skill_dir = os.path.join(self.target_skills_dir, safe_name)
        os.makedirs(os.path.join(skill_dir, "scripts"), exist_ok=True)
        os.makedirs(os.path.join(skill_dir, "references"), exist_ok=True)
        os.makedirs(os.path.join(skill_dir, "examples"), exist_ok=True)

        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        content = f"""---
name: "{safe_name}"
description: "Асимільована навичка з GitHub ({repo_url}): {description}"
repo_url: "{repo_url}"
assimilated_at: "2026-08-07"
---

# 🌐 Навичка: {repo_name} (Assimilated from GitHub)

Цю навичку автоматично синтезовано з репозиторію **[{repo_name}]({repo_url})**.

## 📌 Опис Технології
{description}

## 🛠️ Використання У Свармі Герича
Герич та субагенти використовують цю навичку для впровадження паттернів з {repo_name}.
"""

        with open(skill_md_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "status": "success",
            "skill_name": safe_name,
            "skill_path": skill_md_path,
            "repo_url": repo_url
        }
