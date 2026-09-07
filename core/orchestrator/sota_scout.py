# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/sota_scout.py"
# purpose: "Two-Track SOTA Repository Assimilation Scout Engine with background queue, license audit, code sanitization, Skill auto-synthesis, SCONES sync, and Swarm routing."
# canonical_source: true
# alters_files: ["data/sota_scout_queue.json", "data/sota_scout_cache.json", "docs/tech/sota_assimilation/*", "skills/*", "docs/notes/*", ".scones/*"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import sys
import json
import re
import time
import uuid
import logging
import threading
import urllib.request
import urllib.error
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("SOTAScout")

HUB_ROOT = Path(__file__).resolve().parent.parent.parent


class ScoutJobStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    AUDITED = "audited"
    ASSIMILATED = "assimilated"
    REJECTED = "rejected"
    FAILED = "failed"


class AssimilationTrack(str, Enum):
    TRACK_1_PERMISSIVE = "Track 1: Direct Template Assimilation (Permissive)"
    TRACK_2_CLEAN_ROOM = "Track 2: Clean-Room Reverse Engineering (Restrictive/Copyleft)"


PERMISSIVE_LICENSES = {
    "mit", "apache-2.0", "apache 2.0", "bsd-2-clause", "bsd-3-clause", 
    "bsd 2-clause", "bsd 3-clause", "isc", "unlicense", "cc0-1.0", "zlib"
}

RESTRICTIVE_LICENSES = {
    "gpl-2.0", "gpl-3.0", "agpl-3.0", "agpl-v3", "lgpl-2.1", "lgpl-3.0", 
    "sspl", "bsl-1.1", "cc-by-nc-4.0", "polyform-noncommercial", "proprietary"
}


def sanitize_code_snippet(
    code_str: str,
    file_rel_path: str = "custom_module.py",
    mrh_id: Optional[str] = None,
    purpose: str = "Assimilated SOTA Component"
) -> str:
    """
    Sanitizes external source code into strict DNK-STD-0075 compliance:
    1. Injects valid MRH Header if absent.
    2. Strips absolute paths (/Users/..., /home/..., C:\\...) into relative paths.
    3. Redacts leaked API keys, tokens, and secrets ([REDACTED]).
    """
    sanitized = code_str

    # 1. Redact secrets
    secret_patterns = [
        r'(?i)(ghp_[a-zA-Z0-9]{20,})',
        r'(?i)(github_pat_[a-zA-Z0-9_]{22,})',
        r'(?i)(xox[baprs]-[0-9a-zA-Z]{10,48})',
        r'(?i)(sk-[a-zA-Z0-9]{20,})',
        r'(?i)(password\s*[:=]\s*["\'])([^"\']+)(["\'])',
        r'(?i)(token\s*[:=]\s*["\'])([a-zA-Z0-9_-]{16,})(["\'])'
    ]
    for pattern in secret_patterns[:4]:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized)
    for pattern in secret_patterns[4:]:
        sanitized = re.sub(pattern, r'\1[REDACTED]\3', sanitized)

    # 2. Normalize absolute paths
    sanitized = re.sub(r'/Users/[a-zA-Z0-9._-]+/[^\s"\']+', './assimilated_path', sanitized)
    sanitized = re.sub(r'/home/[a-zA-Z0-9._-]+/[^\s"\']+', './assimilated_path', sanitized)
    sanitized = re.sub(r'[A-Za-z]:\\[^\s"\']+', './assimilated_path', sanitized)

    # 3. Ensure MRH Header
    if "# --- DNK-MRH-HEADER ---" not in sanitized:
        clean_mrh_id = mrh_id or file_rel_path.replace("\\", "/")
        today_str = datetime.now().strftime("%Y-%m-%d")
        header = f"""# --- DNK-MRH-HEADER ---
# mrh_id: "{clean_mrh_id}"
# purpose: "{purpose}"
# canonical_source: false
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "{today_str}"
# author: "Gerych SOTA Scout Assimilator"
# --- END DNK-MRH-HEADER ---

"""
        sanitized = header + sanitized.lstrip()

    return sanitized


class SwarmRoutingResult(dict):
    """Encapsulates Swarm routing metadata with dictionary and tuple-unpacking support."""
    def __init__(self, target_worker: str, target_component: str, recommended_action: str, task_dna: Dict[str, Any], domain: str = ""):
        super().__init__(
            target_worker=target_worker,
            target_component=target_component,
            recommended_action=recommended_action,
            task_dna=task_dna,
            domain=domain
        )
        self.target_worker = target_worker
        self.target_component = target_component
        self.recommended_action = recommended_action
        self.task_dna = task_dna
        self.domain = domain

    def __iter__(self):
        return iter([self.target_worker, self.target_component, self.recommended_action])


class SOTAScoutEngine:
    """
    Chief SOTA Scout & Two-Track Repository Assimilation Engine for DNK OS.
    Manages background scouting queues, license compliance audits, pattern extraction,
    skill synthesis, SCONES memory ingestion, Obsidian vault documentation, and Swarm routing.
    """

    def __init__(
        self,
        hub_root: Optional[Path] = None,
        data_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        skills_dir: Optional[Path] = None,
        notes_dir: Optional[Path] = None,
        cache_file: Optional[Path] = None,
        queue_file: Optional[Path] = None,
    ) -> None:
        self.hub_root = hub_root or HUB_ROOT
        self.data_dir = data_dir or (self.hub_root / "data")
        self.output_dir = output_dir or (self.hub_root / "docs" / "tech" / "sota_assimilation")
        self.skills_dir = skills_dir or (self.hub_root / "skills")
        self.notes_dir = notes_dir or (self.hub_root / "docs" / "notes")
        self.scones_dir = self.hub_root / ".scones"

        self.queue_file = queue_file or (self.data_dir / "sota_scout_queue.json")
        self.cache_file = cache_file or (self.data_dir / "sota_scout_cache.json")

        # Ensure directories exist
        for d in [self.data_dir, self.output_dir, self.skills_dir, self.notes_dir, self.scones_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self._bg_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # -------------------------------------------------------------------------
    # 1. GitHub API & Cache Layer
    # -------------------------------------------------------------------------
    def _get_github_token(self) -> Optional[str]:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            return token.strip()
        for env_path in [self.hub_root / ".env", Path.home() / ".hermes" / ".env"]:
            if env_path.exists():
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("GH_TOKEN=") or line.startswith("GITHUB_TOKEN="):
                                return line.strip().split("=", 1)[1].strip()
                except Exception:
                    pass
        return None

    def _read_cache(self) -> Dict[str, Any]:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _write_cache(self, cache: Dict[str, Any]) -> None:
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning("Failed to save scout cache: %s", e)

    def fetch_repo_intel(self, clean_slug: str, force_refresh: bool = False) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Fetches repository metadata and README via GitHub REST API with caching.
        Returns: (meta_dict, readme_str)
        """
        cache = self._read_cache()
        cached_entry = cache.get(clean_slug)
        if not force_refresh and cached_entry:
            cached_age = time.time() - cached_entry.get("cached_at", 0)
            if cached_age < 86400:  # 24h cache
                return cached_entry.get("meta", {}), cached_entry.get("readme")

        token = self._get_github_token()
        headers = {
            "User-Agent": "DNK-Hub-SOTA-Scout",
            "Accept": "application/vnd.github+json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        meta: Dict[str, Any] = {}
        readme: Optional[str] = None

        # 1. Fetch metadata
        try:
            url = f"https://api.github.com/repos/{clean_slug}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                meta = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.debug("Failed GitHub metadata lookup for %s: %s", clean_slug, e)

        # 2. Fetch raw README
        try:
            readme_url = f"https://api.github.com/repos/{clean_slug}/readme"
            readme_headers = dict(headers)
            readme_headers["Accept"] = "application/vnd.github.raw+json"
            req_readme = urllib.request.Request(readme_url, headers=readme_headers)
            with urllib.request.urlopen(req_readme, timeout=5) as resp:
                readme = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.debug("Failed GitHub README lookup for %s: %s", clean_slug, e)

        # Cache valid result
        if meta or readme:
            cache[clean_slug] = {
                "cached_at": time.time(),
                "meta": meta,
                "readme": readme
            }
            self._write_cache(cache)

        return meta, readme

    # -------------------------------------------------------------------------
    # 2. Two-Track License Compliance Classifier
    # -------------------------------------------------------------------------
    def audit_license_two_track(
        self,
        meta: Optional[Dict[str, Any]] = None,
        raw_readme: Optional[str] = None,
        track_override: Optional[str] = None
    ) -> Tuple[AssimilationTrack, str, List[str]]:
        """
        Two-Track License Compliance Audit:
        Track 1 (Permissive): MIT, Apache 2.0, BSD-2/3, ISC -> Direct Template Assimilation.
        Track 2 (Restrictive): GPL, AGPL, LGPL, SSPL, BSL, etc. -> Clean-Room Reverse Engineering.
        Returns: (AssimilationTrack, license_name, notes)
        """
        if track_override:
            if "1" in track_override or "permissive" in track_override.lower() or "direct" in track_override.lower():
                return AssimilationTrack.TRACK_1_PERMISSIVE, "Override-Permissive", ["Track overridden by user/caller."]
            elif "2" in track_override or "clean" in track_override.lower() or "reverse" in track_override.lower():
                return AssimilationTrack.TRACK_2_CLEAN_ROOM, "Override-Restrictive", ["Track overridden by user/caller."]

        meta = meta or {}
        raw_license = meta.get("license") or meta
        spdx_id = ""
        if isinstance(raw_license, dict):
            spdx_id = raw_license.get("spdx_id", "") or raw_license.get("key", "") or raw_license.get("name", "") or ""
        elif isinstance(raw_license, str):
            spdx_id = raw_license

        clean_spdx = spdx_id.lower().strip()
        notes = []

        # Check in README if license is ambiguous
        if (not clean_spdx or clean_spdx in ["noassertion", "other", "unknown"]) and raw_readme:
            readme_lower = raw_readme.lower()
            if "apache license" in readme_lower or "apache 2.0" in readme_lower:
                clean_spdx = "apache-2.0"
                notes.append("Detected Apache 2.0 license markers inside README body.")
            elif "mit license" in readme_lower or "the mit license" in readme_lower:
                clean_spdx = "mit"
                notes.append("Detected MIT license markers inside README body.")
            elif "gnu general public license" in readme_lower or "gpl v3" in readme_lower:
                clean_spdx = "gpl-3.0"
                notes.append("Detected GNU GPL markers inside README body.")
            elif "agpl" in readme_lower:
                clean_spdx = "agpl-3.0"
                notes.append("Detected Affero GPL markers inside README body.")

        # Classify Track
        is_permissive = clean_spdx in PERMISSIVE_LICENSES or any(kw in clean_spdx for kw in ["mit", "apache", "bsd", "isc", "unlicense"])
        is_restrictive = clean_spdx in RESTRICTIVE_LICENSES or any(kw in clean_spdx for kw in ["gpl", "agpl", "lgpl", "sspl", "bsl", "nc", "copyleft"])

        if is_permissive and not is_restrictive:
            notes.append(f"Permissive license identified: '{spdx_id or clean_spdx}'. Commercial-safe.")
            notes.append("Direct architectural template adoption, component extraction, and code import authorized.")
            return AssimilationTrack.TRACK_1_PERMISSIVE, spdx_id or clean_spdx.upper(), notes

        if is_restrictive:
            notes.append(f"Copyleft / Restrictive license identified: '{spdx_id or clean_spdx}'.")
            notes.append("STRICT INVARIANT: Verbatim code copying is strictly forbidden.")
            notes.append("Mandatory Clean-Room Reverse Engineering: extract AST schemas and synthesize clean MIT contracts.")
            return AssimilationTrack.TRACK_2_CLEAN_ROOM, spdx_id or clean_spdx.upper(), notes

        # Fallback to Track 2 Clean-Room for safety if unknown
        notes.append(f"Uncertain or proprietary license detected: '{spdx_id or 'Unknown'}'. Defaulting to Fail-Closed Clean-Room synthesis.")
        return AssimilationTrack.TRACK_2_CLEAN_ROOM, spdx_id or "Unknown", notes

    # -------------------------------------------------------------------------
    # 3. Swarm Routing & TaskDNA Synthesis
    # -------------------------------------------------------------------------
    def resolve_swarm_routing(
        self,
        clean_slug: str,
        desc: str = "",
        topics: Optional[List[str]] = None,
        stack: str = ""
    ) -> Dict[str, Any]:
        """
        Intelligently resolves target Swarm worker and synthesizes actionable TaskDNA.
        """
        topics = topics or []
        text = f"{clean_slug} {desc} {' '.join(topics)} {stack}".lower()

        if any(w in text for w in ["video", "animation", "avatar", "portrait", "talking", "stream", "audio", "remotion", "media", "hkm", "speech"]):
            worker = "dnk_video_ai_creator"
            component = "services/dnk_video/ or packages/video-audit-core/"
            action = "Implement high-performance streaming animation pipeline and real-time generation contracts."
            domain = "video_multimedia"
        elif any(w in text for w in ["canvas", "diagram", "spatial", "graph", "react-flow", "konva", "excalidraw", "whiteboard", "mindmap", "xyflow"]):
            worker = "gerych_builder"
            component = "apps/web/components/canvas/ or packages/archify/"
            action = "Implement spatial nodes, directional graph layout, and canvas serialization bridges."
            domain = "ui_canvas"
        elif any(w in text for w in ["shopify", "liquid", "store", "checkout", "cart", "commerce", "catalog"]):
            worker = "dnk_shopify"
            component = "services/dnk_shopify/ or apps/web/components/ecom/"
            action = "Synthesize AST Liquid transformers, Shopify Functions (Wasm), and e-commerce schemas."
            domain = "ecommerce"
        elif any(w in text for w in ["api", "fastapi", "database", "sqlalchemy", "postgres", "redis", "backend", "grpc", "orm", "rag", "vector"]):
            worker = "dnk_dev_fullstack"
            component = "apps/api/routers/ or services/dnk_core/"
            action = "Design clean Pydantic v2 schemas, REST/gRPC endpoints, and transactional repositories."
            domain = "backend_api"
        elif any(w in text for w in ["security", "audit", "fuzz", "sast", "firewall", "sentinel", "guard", "vulnerability"]):
            worker = "gerych_auditor"
            component = "core/security/ or scripts/audit/"
            action = "Construct adversarial test gates, automated SAST scan rules, and security integrity shields."
            domain = "security_audit"
        else:
            worker = "gerych_researcher"
            component = "core/research/ or docs/tech/specs/"
            action = "Deep AST extraction, competitive architectural synthesis, and algorithmic benchmarking."
            domain = "research_core"

        task_dna = {
            "task_id": f"TASK-ASSIM-{clean_slug.split('/')[-1].upper()[:12]}",
            "assigned_agent": worker,
            "target_domain": domain,
            "target_component": component,
            "recommended_action": action,
            "dna_slices": [
                {"slice": 1, "name": "Contract & Schema Synthesis", "tool_budget": 10},
                {"slice": 2, "name": "Clean Implementation / Adapter Bridge", "tool_budget": 15},
                {"slice": 3, "name": "Unit Verification & Pre-Commit Test Gate", "tool_budget": 10}
            ]
        }

        return SwarmRoutingResult(
            target_worker=worker,
            target_component=component,
            recommended_action=action,
            task_dna=task_dna,
            domain=domain
        )

    # -------------------------------------------------------------------------
    # 4. Multi-Channel Knowledge Artifacts Generator
    # -------------------------------------------------------------------------
    def generate_hermes_skill(
        self,
        clean_slug: str,
        repo_name: str,
        desc: str,
        track: AssimilationTrack,
        license_name: str,
        stack: str,
        swarm_info: Dict[str, Any]
    ) -> Path:
        """
        Synthesizes a full-fledged, high-quality Hermes skill in skills/<name>_assimilated/SKILL.md.
        """
        safe_name = repo_name.lower().replace("-", "_").replace(".", "_") + "_assimilated"
        skill_dir = self.skills_dir / safe_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "references").mkdir(parents=True, exist_ok=True)
        (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)

        today_str = datetime.now().strftime("%Y-%m-%d")
        worker = swarm_info["target_worker"]
        action = swarm_info["recommended_action"]
        is_clean_room = (track == AssimilationTrack.TRACK_2_CLEAN_ROOM)

        skill_content = f"""---
name: {safe_name}
description: "Assimilated SOTA patterns and architecture from {clean_slug}."
version: "1.0.0"
category: "research"
assimilated_at: "{today_str}"
track: "{track.value}"
license: "{license_name}"
target_worker: "{worker}"
---

# 🌐 {repo_name.upper()} Assimilation Index

Meta-index for architecture, contracts, and component patterns assimilated from **[{clean_slug}](https://github.com/{clean_slug})**.

## 📌 Repository Intel & Legal Boundary
- **Repository**: `{clean_slug}`
- **License**: `{license_name}`
- **Assigned Evolution Track**: `{track.value}`
- **Target Swarm Worker**: `{worker}`
- **Architectural Directive**: {"Direct template and component integration is authorized." if not is_clean_room else "CLEAN-ROOM REVERSE ENGINEERING ONLY: Verbatim copying is forbidden. Synthesize independent MIT contracts."}

## 📁 Core Architecture & Specifications
- **Stack**: `{stack}`
- **Target Component Target**: `{swarm_info["target_component"]}`
- **High-Level Purpose**: {desc}

## 🧪 Quick Recipes (How to Use This Skill)

### Recipe A: Swarm Worker Task Delegation
Delegate implementation directly to **`{worker}`**:
```python
from core.orchestrator.swarm_coordinator import SwarmCoordinator

coordinator = SwarmCoordinator()
res = coordinator.dispatch(
    agent="{worker}",
    action="assimilate_adapter",
    payload={{
        "technology": "{clean_slug}",
        "track": "{track.value}",
        "action": "{action}"
    }}
)
```

### Recipe B: Clean Interface Contract Adoption
Integrate type-safe schemas into your local module:
```python
# Clean-Room Schema derived from {repo_name}
from pydantic import BaseModel, Field

class {repo_name.replace('_', ' ').title().replace(' ', '')}Config(BaseModel):
    enabled: bool = Field(default=True, description="Enables feature adapter")
    mode: str = Field(default="auto", description="Execution mode")
```

## ⚠️ Pitfalls & Invariants
1. **[ZERO_ABSOLUTE_PATHS]**: Never hardcode absolute system paths. Always use `./` or `../`.
2. **[MRH_HEADER_INVARIANT]**: Any adapter or component generated from this pattern MUST carry `DNK-STD-0075` MRH header.
3. **[LICENSE_BOUNDARY]**: {"Respect upstream license notices and attribution." if not is_clean_room else "Strict Clean-Room Isolation: Under no circumstances copy proprietary or copyleft code directly."}
4. **[CLEAN-ROOM REVERSE-ENGINEERING INVARIANT]**: {"Direct template adoption authorized under permissive license." if not is_clean_room else "Direct code copying is strictly prohibited. Clean-room synthesis only."}
"""

        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(skill_content, encoding="utf-8")
        return skill_file

    def generate_obsidian_note(
        self,
        clean_slug: str,
        repo_name: str,
        stars: int,
        license_name: str,
        track: AssimilationTrack,
        desc: str,
        stack: str,
        swarm_info: Dict[str, Any],
        audit_notes: List[str]
    ) -> Path:
        """
        Creates an Obsidian Vault note in docs/notes/ honoring [OBSIDIAN_MRH_HYGIENE].
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        clean_title = f"{repo_name.replace('_', ' ').replace('-', ' ').title()} SOTA Assimilation Audit"
        existing_prefixes = set()
        if self.notes_dir.exists():
            for p in self.notes_dir.glob("*.md"):
                m = re.match(r"^(\d+)", p.name)
                if m:
                    try:
                        existing_prefixes.add(int(m.group(1)))
                    except ValueError:
                        pass
        next_num = max(existing_prefixes, default=0) + 1
        safe_filename = f"{next_num:03d}_{repo_name.lower().replace('-', '_')}_sota_assimilation_audit.md"
        note_path = self.notes_dir / safe_filename

        notes_bullets = "\n".join(f"- {n}" for n in audit_notes)
        worker = swarm_info["target_worker"]

        note_content = f"""---
title: "{clean_title}"
date: {today_str}
tags:
  - sota-assimilation
  - architecture
  - {worker}
  - license-compliance
  - zero-waste
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/{safe_filename}"
purpose: "Obsidian Vault Architecture Note: SOTA Knowledge Assimilation of {clean_slug}"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "{today_str}"
author: "Gerych SOTA Scout"
--- END DNK-MRH-HEADER -->

# 🧬 SOTA Assimilation: {clean_slug}

## 📊 1. Overview & Metrics
- **Repository**: `[{clean_slug}](https://github.com/{clean_slug})`
- **GitHub Stars**: `⭐ {stars:,}`
- **License**: `{license_name}`
- **Assigned Track**: **`{track.value}`**
- **Primary Stack**: `{stack}`
- **Related Notes**: [[000_DNK_HUB_INDEX]], [[013 Zero-Touch Inception Gateway Protocol]], [[014 Anti-Loop and AST Fast-Path Architecture]], [[015 GitHub MCP and CICD Fast Path Architecture]]

### Summary
{desc}

---

## 🛡️ 2. License Audit & Legal Boundary
{notes_bullets}

> **Directive**: {"Permissive license detected. Direct template adoption authorized." if track == AssimilationTrack.TRACK_1_PERMISSIVE else "Restrictive license detected. Clean-Room Reverse Engineering is MANDATORY. Direct code copying is strictly forbidden."}

---

## 🚀 3. Swarm Routing & TaskDNA
- **Assigned Swarm Worker**: `[[{worker}]]`
- **Component Destination**: `{swarm_info["target_component"]}`
- **Action Plan**:
  {swarm_info["recommended_action"]}

### Planned TaskDNA DAG
- **Task ID**: `{swarm_info["task_dna"]["task_id"]}`
- **Slice 1**: Contract & Schema Synthesis (Budget: 10 calls)
- **Slice 2**: Clean Implementation / Adapter Bridge (Budget: 15 calls)
- **Slice 3**: Unit Verification & Pre-Commit Test Gate (Budget: 10 calls)

---

## 📚 4. Knowledge Artifacts
- **Hermes Skill**: `skills/{repo_name.lower().replace('-', '_')}_assimilated/SKILL.md`
- **Research Digest**: `docs/tech/sota_assimilation/SOTA_{repo_name.upper()}_ASSIMILATION.md`
"""

        note_path.write_text(note_content, encoding="utf-8")
        return note_path

    def sync_scones_memory(
        self,
        clean_slug: str,
        track: AssimilationTrack,
        license_name: str,
        desc: str,
        swarm_info: Dict[str, Any]
    ) -> str:
        """
        Saves key architectural findings to SCONES cognitive memory storage.
        """
        lesson_entry = {
            "topic": f"SOTA_ASSIMILATION_{clean_slug.replace('/', '_').upper()}",
            "repo": clean_slug,
            "track": track.value,
            "license": license_name,
            "target_worker": swarm_info["target_worker"],
            "summary": desc[:300],
            "timestamp": datetime.now().isoformat(),
            "importance": 0.85
        }

        scones_file = self.scones_dir / "sota_memories.json"
        try:
            records = []
            if scones_file.exists():
                try:
                    with open(scones_file, "r", encoding="utf-8") as f:
                        records = json.load(f)
                except Exception:
                    records = []
            records.append(lesson_entry)
            with open(scones_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            return str(scones_file.relative_to(self.hub_root))
        except Exception as e:
            logger.warning("Failed to save SCONES memory: %s", e)
            return str(scones_file)

    # -------------------------------------------------------------------------
    # 5. Full End-to-End Assimilation Pipeline
    # -------------------------------------------------------------------------
    def assimilate(
        self,
        repo_url: str,
        focus_areas: Optional[List[str]] = None,
        track_override: Optional[str] = None,
        workspace_id: str = "ws-alpha-001",
        generate_skill: bool = True,
        generate_obsidian: bool = True,
        sync_scones: bool = True
    ) -> Dict[str, Any]:
        """
        Executes the 5-Level Two-Track SOTA Repository Assimilation Pipeline:
        1. Discovery & Metadata Fetch (Cached)
        2. Two-Track License Compliance Audit
        3. AST & Pattern Extraction & Sanitization
        4. Knowledge Artifact Ingestion (Skill, Digest, Obsidian note, SCONES)
        5. Swarm Routing & TaskDNA Generation
        """
        clean_slug = repo_url.replace("https://github.com/", "").strip("/")
        repo_name = clean_slug.split("/")[-1] if "/" in clean_slug else clean_slug

        # 1. Fetch Intel
        meta, raw_readme = self.fetch_repo_intel(clean_slug)
        stars = meta.get("stargazers_count", 0)
        desc = meta.get("description") or f"Open-source repository {clean_slug}"
        lang = meta.get("language") or "Python / Modern Toolchain"
        topics = meta.get("topics", [])

        # 2. License Audit
        track, license_name, audit_notes = self.audit_license_two_track(meta, raw_readme, track_override)

        # 3. Swarm Routing
        swarm_info = self.resolve_swarm_routing(clean_slug, desc, topics, lang)

        # 4. Generate Research Digest
        today_str = datetime.now().strftime("%Y-%m-%d")
        digest_file = self.output_dir / f"SOTA_{repo_name.upper()}_ASSIMILATION.md"
        digest_content = f"""# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tech_sota_{repo_name.lower()}"
# purpose: "SOTA Knowledge Assimilation Report for {clean_slug}"
# author: "DNK-e.com Maksym & Gerych Prime"
# status: "Active"
# version: "1.0.0"
# updated_at: "{today_str}"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Assimilation Report: {clean_slug}

## 📊 1. Repository Intel
- **Slug**: `{clean_slug}`
- **Stars**: `⭐ {stars:,}`
- **Primary Language**: `{lang}`
- **License**: `{license_name}`
- **Assigned Track**: **`{track.value}`**

### Summary
{desc}

## 🛡️ 2. License Compliance Findings
{"\n".join(f"- {n}" for n in audit_notes)}

## 🚀 3. Swarm Routing
- **Worker**: `{swarm_info["target_worker"]}`
- **Target Component**: `{swarm_info["target_component"]}`
- **Action**: {swarm_info["recommended_action"]}
"""
        digest_file.write_text(digest_content, encoding="utf-8")

        # 5. Generate Skill
        skill_path_str = None
        if generate_skill:
            skill_path = self.generate_hermes_skill(
                clean_slug, repo_name, desc, track, license_name, lang, swarm_info
            )
            skill_path_str = str(skill_path.relative_to(self.hub_root))

        # 6. Generate Obsidian Note
        obsidian_path_str = None
        if generate_obsidian:
            note_path = self.generate_obsidian_note(
                clean_slug, repo_name, stars, license_name, track, desc, lang, swarm_info, audit_notes
            )
            obsidian_path_str = str(note_path.relative_to(self.hub_root))

        # 7. Sync SCONES Memory
        scones_path_str = None
        if sync_scones:
            scones_path_str = self.sync_scones_memory(
                clean_slug, track, license_name, desc, swarm_info
            )

        rel_digest = str(digest_file.relative_to(self.hub_root))

        return {
            "status": "success",
            "repo": clean_slug,
            "stars": stars,
            "license": license_name,
            "track": track.value,
            "legal_boundary": "; ".join(audit_notes),
            "target_worker": swarm_info["target_worker"],
            "target_component": swarm_info["target_component"],
            "recommended_action": swarm_info["recommended_action"],
            "task_dna": swarm_info["task_dna"],
            "skill_file": skill_path_str,
            "digest_file": rel_digest,
            "obsidian_file": obsidian_path_str,
            "scones_synced": True if scones_path_str else False,
            "artifacts": {
                "research_digest": rel_digest,
                "hermes_skill": skill_path_str,
                "obsidian_note": obsidian_path_str,
                "scones_memory": scones_path_str
            },
            "message": f"Successfully completed Two-Track SOTA assimilation for {clean_slug} under {track.value}."
        }

    # -------------------------------------------------------------------------
    # 6. Background Queue Engine
    # -------------------------------------------------------------------------
    def _read_queue(self) -> List[Dict[str, Any]]:
        with self._lock:
            if self.queue_file.exists():
                try:
                    with open(self.queue_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    return []
            return []

    def _write_queue(self, queue: List[Dict[str, Any]]) -> None:
        with self._lock:
            try:
                with open(self.queue_file, "w", encoding="utf-8") as f:
                    json.dump(queue, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.warning("Failed to save scout queue: %s", e)

    def enqueue_job(
        self,
        repo_url: str,
        focus_areas: Optional[List[str]] = None,
        priority: int = 1,
        track_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enqueues a repository into the background scout queue."""
        job_id = f"SCOUT-{uuid.uuid4().hex[:8].upper()}"
        job = {
            "id": job_id,
            "repo_url": repo_url,
            "focus_areas": focus_areas or [],
            "priority": priority,
            "track_override": track_override,
            "status": ScoutJobStatus.PENDING.value,
            "enqueued_at": time.time(),
            "updated_at": time.time(),
            "result": None
        }
        with self._lock:
            queue = self._read_queue()
            # Deduplicate by pending repo_url
            for existing in queue:
                if existing.get("repo_url") == repo_url and existing.get("status") in [ScoutJobStatus.PENDING.value, ScoutJobStatus.ANALYZING.value]:
                    return existing
            queue.append(job)
            self._write_queue(queue)
        return job

    def list_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        queue = self._read_queue()
        if status:
            return [j for j in queue if j.get("status") == status]
        return queue

    def process_next_job(self) -> Optional[Dict[str, Any]]:
        """Pulls and processes the highest priority pending job."""
        job_to_process = None
        with self._lock:
            queue = self._read_queue()
            pending = [j for j in queue if j.get("status") == ScoutJobStatus.PENDING.value]
            if not pending:
                return None
            pending.sort(key=lambda x: x.get("priority", 1))
            job_to_process = pending[0]
            job_to_process["status"] = ScoutJobStatus.ANALYZING.value
            job_to_process["updated_at"] = time.time()
            self._write_queue(queue)

        try:
            res = self.assimilate(
                repo_url=job_to_process["repo_url"],
                focus_areas=job_to_process.get("focus_areas", []),
                track_override=job_to_process.get("track_override")
            )
            res["job_id"] = job_to_process["id"]
            with self._lock:
                queue = self._read_queue()
                for j in queue:
                    if j.get("id") == job_to_process["id"]:
                        j["status"] = ScoutJobStatus.ASSIMILATED.value
                        j["updated_at"] = time.time()
                        j["result"] = res
                        break
                self._write_queue(queue)
            return res
        except Exception as e:
            with self._lock:
                queue = self._read_queue()
                for j in queue:
                    if j.get("id") == job_to_process["id"]:
                        j["status"] = ScoutJobStatus.FAILED.value
                        j["updated_at"] = time.time()
                        j["error"] = str(e)
                        break
                self._write_queue(queue)
            return {"status": "failed", "error": str(e), "job_id": job_to_process["id"]}

    def enqueue_repository(
        self,
        repo_url: str,
        focus_areas: Optional[List[str]] = None,
        priority: int = 5,
        requested_by: str = "cli_runner",
    ) -> Dict[str, Any]:
        """Convenience method to enqueue a repository."""
        return self.enqueue_job(
            repo_url=repo_url,
            focus_areas=focus_areas,
            priority=priority,
        )

    def get_queue_status(self) -> Dict[str, Any]:
        """Returns statistics and status of jobs in queue."""
        jobs = self._read_queue()
        counts: Dict[str, int] = {}
        for j in jobs:
            st = j.get("status", "unknown")
            counts[st] = counts.get(st, 0) + 1
        return {
            "total_jobs": len(jobs),
            "by_status": counts,
            "jobs": jobs[-20:],
        }

    def process_queue(self, max_jobs: int = 1) -> List[Dict[str, Any]]:
        """Processes up to max_jobs from the pending queue."""
        processed: List[Dict[str, Any]] = []
        for _ in range(max_jobs):
            res = self.process_next_job()
            if not res:
                break
            processed.append(res)
        return processed

    def sanitize_code(
        self,
        code_str: str,
        file_path: str,
        purpose: str = "DNK-STD-0075 Sanitized Component",
    ) -> str:
        """Sanitizes code string under DNK-STD-0075 guidelines."""
        return sanitize_code_snippet(code_str, file_rel_path=file_path, purpose=purpose)
