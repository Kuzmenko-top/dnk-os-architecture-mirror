# --- DNK-MRH-HEADER ---
# mrh_id: "core/bricks/registry.py"
# purpose: "Core Brick Registry & Dynamic Dependency Resolution Engine for DNK OS AI Product Foundry."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Antigravity Orchestrator"
# --- END DNK-MRH-HEADER ---

import os
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml
from pydantic import BaseModel, Field


class BrickContracts(BaseModel):
    python_schema: Optional[str] = None
    typescript_types: Optional[str] = None


class BrickDependencies(BaseModel):
    internal: List[str] = Field(default_factory=list)
    external_python: List[str] = Field(default_factory=list)
    external_npm: List[str] = Field(default_factory=list)


class BrickQualityGate(BaseModel):
    test_suite: str
    min_coverage: int = 80


class BrickManifest(BaseModel):
    id: str
    name: str
    version: str = "1.0.0"
    mrh_id: str
    category: str
    description: str
    paths: List[str] = Field(default_factory=list)
    dependencies: BrickDependencies = Field(default_factory=BrickDependencies)
    contracts: BrickContracts = Field(default_factory=BrickContracts)
    entrypoints: Dict[str, str] = Field(default_factory=dict)
    quality_gate: Optional[BrickQualityGate] = None


class DNKBrickRegistry:
    """
    Universal Registry for Composable DNK OS Bricks.
    Handles discovery, validation, DAG dependency resolution, and packaging.
    """

    def __init__(self, registry_dir: Optional[Path] = None):
        if registry_dir is None:
            self.registry_dir = Path(__file__).resolve().parent
        else:
            self.registry_dir = Path(registry_dir).resolve()
        self._bricks: Dict[str, BrickManifest] = {}
        self.load_bricks()

    def load_bricks(self) -> Dict[str, BrickManifest]:
        self._bricks.clear()
        if not self.registry_dir.exists():
            return self._bricks

        for manifest_path in self.registry_dir.glob("*/brick.manifest.yaml"):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    raw_data = yaml.safe_load(f)
                if not raw_data:
                    continue

                # Normalize dependencies format if needed
                deps = raw_data.get("dependencies", {})
                if isinstance(deps, dict):
                    ext = deps.get("external", {})
                    ext_py = ext.get("python", []) if isinstance(ext, dict) else deps.get("external_python", [])
                    ext_npm = ext.get("npm", []) if isinstance(ext, dict) else deps.get("external_npm", [])
                    raw_deps = BrickDependencies(
                        internal=deps.get("internal", []),
                        external_python=ext_py,
                        external_npm=ext_npm,
                    )
                    raw_data["dependencies"] = raw_deps

                manifest = BrickManifest(**raw_data)
                self._bricks[manifest.id] = manifest
            except Exception as e:
                print(f"⚠️ Error loading brick manifest at {manifest_path}: {e}")

        return self._bricks

    def get_brick(self, brick_id: str) -> Optional[BrickManifest]:
        return self._bricks.get(brick_id)

    def list_bricks(self) -> List[BrickManifest]:
        return list(self._bricks.values())

    def resolve_dependencies(self, requested_brick_ids: List[str]) -> List[str]:
        """
        Resolves the topological dependency DAG for a set of requested bricks.
        Returns an ordered list of brick IDs (dependencies first).
        """
        resolved: List[str] = []
        visited: Set[str] = set()
        visiting: Set[str] = set()

        def dfs(b_id: str):
            if b_id in visiting:
                raise ValueError(f"Cyclic dependency detected involving brick '{b_id}'")
            if b_id in visited:
                return

            visiting.add(b_id)
            brick = self._bricks.get(b_id)
            if not brick:
                raise KeyError(f"Requested brick '{b_id}' is not registered in DNKBrickRegistry")

            for dep in brick.dependencies.internal:
                dfs(dep)

            visiting.remove(b_id)
            visited.add(b_id)
            resolved.append(b_id)

        for b_id in requested_brick_ids:
            if b_id not in visited:
                dfs(b_id)

        return resolved

    def collect_export_paths(self, brick_ids: List[str]) -> List[str]:
        """
        Resolves the transitive brick list and gathers all source file paths to export.
        """
        resolved_ids = self.resolve_dependencies(brick_ids)
        paths: Set[str] = set()
        for b_id in resolved_ids:
            brick = self._bricks[b_id]
            for p in brick.paths:
                paths.add(p)
        return sorted(list(paths))

    def get_lean_python_dependencies(self, brick_ids: List[str]) -> List[str]:
        """
        Collects deduplicated external Python packages required for the resolved bricks.
        """
        resolved_ids = self.resolve_dependencies(brick_ids)
        base_deps = [
            "fastapi>=0.110.0",
            "uvicorn>=0.28.0",
            "pydantic>=2.7.0",
            "pyyaml>=6.0",
            "pytest>=8.0.0",
        ]
        deps_set = set(base_deps)
        for b_id in resolved_ids:
            brick = self._bricks[b_id]
            for d in brick.dependencies.external_python:
                if d and d != "sqlite3":
                    deps_set.add(d)
        return sorted(list(deps_set))

    def generate_lean_requirements_txt(self, brick_ids: List[str]) -> str:
        deps = self.get_lean_python_dependencies(brick_ids)
        return "# Auto-generated Lean Requirements for DNK Modular App\n" + "\n".join(deps) + "\n"

    def generate_lean_pyproject_toml(self, app_id: str, brick_ids: List[str]) -> str:
        deps = self.get_lean_python_dependencies(brick_ids)
        formatted_deps = ",\n    ".join(f'"{d}"' for d in deps)
        return f"""# Auto-generated Lean pyproject.toml for DNK Modular App: {app_id}
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{app_id}"
version = "1.0.0"
description = "Autonomous Standalone Application generated by DNK OS AI Product Foundry"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    {formatted_deps}
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
"""

    def get_active_entrypoints(self, brick_ids: List[str]) -> Dict[str, Dict[str, str]]:
        resolved_ids = self.resolve_dependencies(brick_ids)
        return {b_id: self._bricks[b_id].entrypoints for b_id in resolved_ids}

