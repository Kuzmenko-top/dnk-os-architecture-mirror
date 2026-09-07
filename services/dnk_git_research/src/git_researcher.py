# --- DNK-MRH-HEADER ---
# mrh_id: "services_dnk_git_research_src_git_researcher"
# purpose: "GitHub Research & SOTA Assimilation Engine for finding, auditing, and extracting architectural patterns into DNK OS"
# author: "DNK-e.com Maksym"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-02"
# --- END DNK-MRH-HEADER ---

import os
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = HUB_ROOT / "docs" / "architecture" / "assimilation-registry.md"
PROVENANCE_PATH = HUB_ROOT / "docs" / "audit" / "oss-provenance-report.json"
SPECS_DIR = HUB_ROOT / "docs" / "tech" / "sota_assimilation"


class GitResearchEngine:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DNK-OS-GitResearcher/2.0"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search GitHub for repositories matching query."""
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.github.com/search/repositories?q={encoded_query}&sort={sort}&order={order}&per_page={limit}"
        
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("items", [])
                results = []
                for item in items:
                    results.append({
                        "full_name": item.get("full_name"),
                        "name": item.get("name"),
                        "owner": item.get("owner", {}).get("login"),
                        "description": item.get("description") or "",
                        "stars": item.get("stargazers_count", 0),
                        "forks": item.get("forks_count", 0),
                        "language": item.get("language") or "Unknown",
                        "license": item.get("license", {}).get("spdx_id") if item.get("license") else "None",
                        "url": item.get("html_url"),
                        "topics": item.get("topics", []),
                        "updated_at": item.get("updated_at")
                    })
                return results
        except Exception as e:
            # Fallback for offline or rate-limited environments
            return self._get_curated_fallback(query)

    def audit_and_classify(self, repo_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Classify repository by Assimilation Level (R1-R5) and assess compatibility."""
        license_type = repo_meta.get("license", "None")
        is_permissive = license_type in ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"]
        
        # Classification heuristics
        if not is_permissive and license_type != "None":
            level = "R1_research"
            reason = f"Copyleft or custom license ({license_type}) - Research and pattern inspection only."
        elif "framework" in repo_meta.get("topics", []) or "orchestrator" in repo_meta.get("description", "").lower():
            level = "R3_pattern_adaptation"
            reason = "Orchestration pattern - Adapt supervisor/worker state graphs into DNK TaskDNA."
        elif "ui" in repo_meta.get("topics", []) or "canvas" in repo_meta.get("topics", []):
            level = "R3_pattern_adaptation"
            reason = "Spatial UI / Canvas pattern - Integrate interaction rhythm and node visuals."
        else:
            level = "R3_pattern_adaptation"
            reason = "Core feature logic - Transpile into modular DNK service."

        return {
            "source_id": repo_meta.get("name", "unknown").lower().replace("-", "_"),
            "full_name": repo_meta.get("full_name"),
            "stars": repo_meta.get("stars", 0),
            "license": license_type,
            "assimilation_level": level,
            "classification_reason": reason,
            "license_approved": is_permissive,
            "url": repo_meta.get("url")
        }

    def assimilate_into_dnk(self, repo_meta: Dict[str, Any], target_context: str = "core/orchestrator") -> Path:
        """Generate Assimilation Spec and register repository into DNK OS Registry."""
        SPECS_DIR.mkdir(parents=True, exist_ok=True)
        repo_name = repo_meta.get("name", "repo").lower().replace("-", "_")
        spec_file = SPECS_DIR / f"{repo_name}.md"

        audit_res = self.audit_and_classify(repo_meta)

        content = f"""# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tech_sota_assimilation_{repo_name}"
# purpose: "SOTA Assimilation Spec for {repo_meta.get('full_name')} into DNK OS"
# author: "DNK Git Researcher"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Assimilation Spec: {repo_meta.get('full_name')}

- **Upstream URL**: [{repo_meta.get('full_name')}]({repo_meta.get('url')})
- **Stars**: {repo_meta.get('stars', 0)} ⭐
- **License**: `{repo_meta.get('license')}` (Approved: {audit_res['license_approved']})
- **Assimilation Mode**: `{audit_res['assimilation_level']}`
- **Target Bounded Context**: `{target_context}`

## 1. Description & Value Proposition
{repo_meta.get('description', 'No description provided.')}

## 2. Adopted Concepts (What we integrate)
- Architectural algorithms and data flow patterns.
- High-performance execution patterns adapted for Gerych Swarm.

## 3. Not Adopted (What we isolate)
- Upstream cloud lock-in and foreign persistence schemas.
- External unauthenticated write actions.

## 4. Integration Directives for Gerych Builder
- Transpile into clean modular Pydantic models & FastAPI endpoints.
- Ensure 100% test coverage under `tests/verification/`.
"""
        with open(spec_file, "w", encoding="utf-8") as f:
            f.write(content)

        return spec_file

    def _get_curated_fallback(self, query: str) -> List[Dict[str, Any]]:
        """Curated top agentic repositories fallback if GitHub API rate limits."""
        curated = [
            {
                "full_name": "langchain-ai/langgraph",
                "name": "langgraph",
                "owner": "langchain-ai",
                "description": "Build resilient language agents as graphs with human-in-the-loop approvals.",
                "stars": 11500,
                "forks": 1200,
                "language": "Python",
                "license": "MIT",
                "url": "https://github.com/langchain-ai/langgraph",
                "topics": ["agentic", "graph", "multi-agent", "supervisor"],
                "updated_at": "2026-08-30"
            },
            {
                "full_name": "xyflow/xyflow",
                "name": "xyflow",
                "owner": "xyflow",
                "description": "Powerful, highly customizable software for building node-based UIs and interactive workflow canvases.",
                "stars": 24000,
                "forks": 2100,
                "language": "TypeScript",
                "license": "MIT",
                "url": "https://github.com/xyflow/xyflow",
                "topics": ["canvas", "nodes", "flow", "react-flow"],
                "updated_at": "2026-08-31"
            },
            {
                "full_name": "remotion-dev/remotion",
                "name": "remotion",
                "owner": "remotion-dev",
                "description": "Make videos programmatically using React, WebGL, and modern animation primitives.",
                "stars": 21000,
                "forks": 1400,
                "language": "TypeScript",
                "license": "Custom/Permissive",
                "url": "https://github.com/remotion-dev/remotion",
                "topics": ["video", "motion", "rendering", "react"],
                "updated_at": "2026-08-30"
            }
        ]
        return [c for c in curated if any(w in (c["name"] + c["description"] + " ".join(c["topics"])).lower() for w in query.lower().split())] or curated
