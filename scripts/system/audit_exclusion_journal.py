#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/audit_exclusion_journal.py"
# purpose: "Audit Exclusion Journal & SSOT Manifest Engine for runtime environments, secret stores, and assimilated projects."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-01"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import argparse
import fnmatch
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None


def _parse_yaml_fallback(text: str) -> Dict[str, Any]:
    """Lightweight fallback parser for YAML when pyyaml is not in global env."""
    data: Dict[str, Any] = {
        "environments_and_build": {"patterns": []},
        "secrets_and_credentials": {"patterns": []},
        "assimilated_projects": []
    }
    
    current_section = None
    current_proj: Dict[str, Any] = {}
    
    for line in text.splitlines():
        line_strip = line.strip()
        if not line_strip or line_strip.startswith("#"):
            continue
            
        if line_strip.startswith("environments_and_build:"):
            current_section = "environments_and_build"
            continue
        elif line_strip.startswith("secrets_and_credentials:"):
            current_section = "secrets_and_credentials"
            continue
        elif line_strip.startswith("assimilated_projects:"):
            current_section = "assimilated_projects"
            continue
        elif line_strip.startswith("patterns:"):
            continue

        if current_section == "environments_and_build" and line_strip.startswith("- "):
            val = line_strip[2:].strip().strip('"\'')
            data["environments_and_build"]["patterns"].append(val)
        elif current_section == "secrets_and_credentials" and line_strip.startswith("- "):
            val = line_strip[2:].strip().strip('"\'')
            data["secrets_and_credentials"]["patterns"].append(val)
        elif current_section == "assimilated_projects":
            if line_strip.startswith("- id:"):
                if current_proj:
                    data["assimilated_projects"].append(current_proj)
                current_proj = {"id": line_strip[5:].strip().strip('"\'')}
            elif ":" in line_strip and current_proj:
                k, v = line_strip.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"\'')
                if v.lower() == "true":
                    v = True
                elif v.lower() == "false":
                    v = False
                current_proj[k] = v
                
    if current_proj:
        data["assimilated_projects"].append(current_proj)
        
    return data


DEFAULT_MANIFEST_PATH = "config/audit_exclusions.yaml"


class AuditExclusionJournal:
    def __init__(self, hub_root: Optional[Path] = None, manifest_path: Optional[Path] = None):
        if hub_root is None:
            # Resolve from script location
            self.hub_root = Path(__file__).resolve().parents[2]
        else:
            self.hub_root = Path(hub_root).resolve()

        if manifest_path is None:
            self.manifest_path = self.hub_root / DEFAULT_MANIFEST_PATH
        else:
            self.manifest_path = Path(manifest_path).resolve()

        self.manifest_data = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        if not self.manifest_path.exists():
            return {
                "version": "1.0.0",
                "environments_and_build": {"patterns": [".venv", "node_modules", ".next", "dist", "build", "__pycache__", ".git"]},
                "secrets_and_credentials": {"patterns": [".env", "*.pem", "*.key", "*.token", "*.db"]},
                "assimilated_projects": [],
            }

        text = self.manifest_path.read_text(encoding="utf-8")
        if yaml:
            return yaml.safe_load(text) or {}
        else:
            return _parse_yaml_fallback(text)

    @property
    def env_patterns(self) -> List[str]:
        return self.manifest_data.get("environments_and_build", {}).get("patterns", [])

    @property
    def secret_patterns(self) -> List[str]:
        return self.manifest_data.get("secrets_and_credentials", {}).get("patterns", [])

    @property
    def assimilated_projects(self) -> List[Dict[str, Any]]:
        return self.manifest_data.get("assimilated_projects", [])

    def is_environment_or_build(self, rel_path: str) -> bool:
        normalized = rel_path.strip("/").replace("\\", "/")
        parts = normalized.split("/")
        for part in parts:
            for pat in self.env_patterns:
                if fnmatch.fnmatch(part, pat) or part == pat:
                    return True
        return False

    def is_secret_or_credential(self, rel_path: str) -> bool:
        normalized = rel_path.strip("/").replace("\\", "/")
        filename = normalized.split("/")[-1]
        for pat in self.secret_patterns:
            if fnmatch.fnmatch(filename, pat) or fnmatch.fnmatch(normalized, pat):
                return True
        return False

    def get_assimilated_project(self, rel_path: str) -> Optional[Dict[str, Any]]:
        normalized = rel_path.strip("/").replace("\\", "/")
        for proj in self.assimilated_projects:
            proj_path = proj.get("path", "").strip("/").replace("\\", "/")
            if normalized == proj_path or normalized.startswith(proj_path + "/"):
                return proj
        return None

    def should_skip_deep_scan(self, rel_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Determines whether recursive scanning inside this path should be skipped.
        Returns: (should_skip, reason, metadata)
        """
        normalized = rel_path.strip("/").replace("\\", "/")
        
        # Check environment/build
        if self.is_environment_or_build(normalized):
            return True, "ENVIRONMENT_OR_BUILD_ARTIFACT", None

        # Check secret
        if self.is_secret_or_credential(normalized):
            return True, "SECRET_OR_CREDENTIAL_DATA", None

        # Check assimilated project
        proj = self.get_assimilated_project(normalized)
        if proj:
            proj_path = proj.get("path", "").strip("/").replace("\\", "/")
            # If we are directly at the root of the project, or deeper inside it
            if proj.get("skip_deep_scan", False):
                if normalized == proj_path:
                    return True, f"ASSIMILATED_PROJECT_CERTIFIED:{proj.get('id')}", proj
                elif normalized.startswith(proj_path + "/"):
                    return True, f"INSIDE_ASSIMILATED_PROJECT:{proj.get('id')}", proj

        return False, "SCAN_REQUIRED", None

    def compute_project_fingerprint(self, rel_path: str) -> str:
        """Compute SHA-256 fingerprint of the top-level manifest/structure."""
        target_dir = self.hub_root / rel_path
        if not target_dir.exists():
            return "NOT_FOUND"

        hasher = hashlib.sha256()
        # Hash names and sizes of top-level items
        try:
            for item in sorted(target_dir.iterdir(), key=lambda p: p.name):
                hasher.update(item.name.encode("utf-8"))
                if item.is_file():
                    hasher.update(str(item.stat().st_size).encode("utf-8"))
            return hasher.hexdigest()[:16]
        except Exception:
            return "ERROR_COMPUTING_HASH"


def main():
    parser = argparse.ArgumentParser(description="DNK OS Audit Exclusion Journal SSOT Engine")
    parser.add_argument("--check", help="Check if a path is excluded and why")
    parser.add_argument("--list-assimilated", action="store_true", help="List all certified assimilated projects")
    parser.add_argument("--list-patterns", action="store_true", help="List all exclusion patterns")
    args = parser.parse_args()

    journal = AuditExclusionJournal()

    if args.list_patterns:
        print("🛡️ [DNK OS Audit Exclusion Patterns]")
        print("📁 Environments & Build:")
        for p in journal.env_patterns:
            print(f"   • {p}")
        print("🔒 Secrets & Credentials:")
        for p in journal.secret_patterns:
            print(f"   • {p}")
        sys.exit(0)

    if args.list_assimilated:
        print("🧬 [DNK OS Certified Assimilated Projects Registry]")
        for proj in journal.assimilated_projects:
            print(f"   • ID: {proj.get('id')} | Path: {proj.get('path')}")
            print(f"     Name: {proj.get('name')}")
            print(f"     License: {proj.get('license')} ({proj.get('track')})")
            print(f"     Status: {proj.get('audit_status')} (Certified by {proj.get('certified_by')})")
            print(f"     Skip Deep Scan: {proj.get('skip_deep_scan')}")
        sys.exit(0)

    if args.check:
        skip, reason, meta = journal.should_skip_deep_scan(args.check)
        print(f"Path: {args.check}")
        print(f"Skip Deep Scan: {skip}")
        print(f"Reason: {reason}")
        if meta:
            print(f"Project Metadata: {meta}")
        sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
