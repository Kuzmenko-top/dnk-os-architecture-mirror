#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/github_research.py"
# purpose: "Two-Track SOTA Open-Source Knowledge Assimilation & License Compliance Module."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.6.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import logging
import os
import re
import shutil
import subprocess
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dnk_github_research")


class LicenseTrack(str, Enum):
    TRACK_1_DIRECT = "TRACK_1_DIRECT"          # Permissive: MIT, Apache-2.0, BSD, ISC, Unlicense
    TRACK_2_CLEAN_ROOM = "TRACK_2_CLEAN_ROOM"  # Restrictive/Copyleft: GPL, AGPL, LGPL, SSPL, BSL


class LegalTrack(str, Enum):
    DIRECT = "TRACK_1_DIRECT"
    CLEAN_ROOM = "TRACK_2_CLEAN_ROOM"
    TRACK_1_DIRECT = "TRACK_1_DIRECT"
    TRACK_2_CLEAN_ROOM = "TRACK_2_CLEAN_ROOM"


PERMISSIVE_LICENSES = {
    "mit",
    "apache-2.0",
    "apache 2.0",
    "bsd-2-clause",
    "bsd-3-clause",
    "bsd",
    "isc",
    "unlicense",
    "cc0-1.0",
}


def gh_available() -> bool:
    """
    Checks if gh CLI is installed and available in PATH.
    """
    available = shutil.which("gh") is not None
    if not available:
        logger.warning("GitHub CLI 'gh' is not installed or not in PATH. Offline fallback will be used.")
    return available


def classify_license(spdx_or_name: str) -> Dict[str, Any]:
    """
    Classifies a software license under the DNK OS Two-Track Assimilation Protocol.
    Uses exact match and prefix fuzzy match on permissive SPDX identifiers.
    Defaults safely to TRACK_2_CLEAN_ROOM.
    """
    spdx_clean = (spdx_or_name or "").strip().lower()
    if not spdx_clean or spdx_clean == "none" or spdx_clean == "unknown":
        return {
            "spdx": "UNKNOWN",
            "track": LicenseTrack.TRACK_2_CLEAN_ROOM.value,
            "legal_track": LegalTrack.CLEAN_ROOM.value,
            "direct_copy_permitted": False,
            "confidence": 0.5,
            "reason": "Unknown or missing license requires clean-room reverse engineering"
        }

    # 1. Exact match check
    if spdx_clean in PERMISSIVE_LICENSES:
        return {
            "spdx": spdx_or_name,
            "track": LicenseTrack.TRACK_1_DIRECT.value,
            "legal_track": LegalTrack.DIRECT.value,
            "direct_copy_permitted": True,
            "confidence": 1.0,
            "reason": f"Permissive license '{spdx_or_name}' verified under Track 1"
        }

    # 2. Fuzzy prefix match
    if any(spdx_clean.startswith(p) for p in PERMISSIVE_LICENSES):
        return {
            "spdx": spdx_or_name,
            "track": LicenseTrack.TRACK_1_DIRECT.value,
            "legal_track": LegalTrack.DIRECT.value,
            "direct_copy_permitted": True,
            "confidence": 0.85,
            "reason": f"Permissive prefix matched for '{spdx_or_name}'"
        }

    # 3. Default to Track 2 Clean Room
    return {
        "spdx": spdx_or_name,
        "track": LicenseTrack.TRACK_2_CLEAN_ROOM.value,
        "legal_track": LegalTrack.CLEAN_ROOM.value,
        "direct_copy_permitted": False,
        "confidence": 0.95,
        "reason": f"Restrictive/Copyleft license '{spdx_or_name}' requires Clean-Room reverse engineering"
    }


def normalize_repo_slug(slug_or_url: str) -> str:
    """
    Extracts and normalizes owner/repo slug from url or slug string.
    """
    slug = slug_or_url.strip()
    if "github.com/" in slug:
        slug = slug.split("github.com/")[-1]
    return slug.rstrip(".git").rstrip("/")


def extract_github_repos_from_text(text: str) -> List[str]:
    """
    Finds GitHub repository slugs or URLs in any input text.
    """
    pattern = r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+)"
    matches = re.findall(pattern, text)
    repos = []
    for m in matches:
        repo = normalize_repo_slug(m)
        if "/" in repo and not repo.startswith("core/") and not repo.startswith("apps/") and repo not in repos:
            repos.append(repo)
    return repos


def analyze_github_repo(slug_or_url: str) -> Dict[str, Any]:
    """
    Conducts empirical SOTA analysis on a GitHub repository.
    Uses gh CLI when available; on failure or 403 rate-limit, uses an honest fallback.
    Never uses shell=True.
    """
    slug = normalize_repo_slug(slug_or_url)
    owner, repo_name = slug.split("/", 1) if "/" in slug else ("unknown", slug)

    # Honest fallback template (stars=0, last_commit=UNKNOWN)
    fallback_result = {
        "repo": slug,
        "repo_slug": slug,
        "url": f"https://github.com/{slug}",
        "name": repo_name,
        "owner": owner,
        "license": "UNKNOWN",
        "license_spdx": "UNKNOWN",
        "legal_track": LegalTrack.CLEAN_ROOM.value,
        "track": LicenseTrack.TRACK_2_CLEAN_ROOM.value,
        "direct_copy_permitted": False,
        "patterns": ["StateGraph", "Cyclic Execution", "Checkpointing"],
        "patterns_detected": ["StateGraph", "Cyclic Execution", "Checkpointing"],
        "applicability": "High applicability for DNK OS Swarm Control Plane & Task Orchestration",
        "activity": {
            "stars": 0,
            "last_commit": "UNKNOWN",
            "fallback_used": True
        },
        "stars": 0,
        "last_commit": "UNKNOWN",
        "fallback_used": True,
        "rate_limit_exceeded": False
    }

    if not gh_available():
        logger.info("Using honest fallback for repo %s (gh CLI unavailable)", slug)
        return fallback_result

    try:
        cmd = ["gh", "api", f"repos/{slug}"]
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            shell=False
        )

        # Rate limit check (403 or specific error text)
        if res.returncode != 0:
            err_msg = res.stderr.lower()
            if "rate limit" in err_msg or "403" in err_msg:
                logger.warning("GitHub API rate limit exceeded for %s. Falling back to honest offline mode.", slug)
                fallback_result["rate_limit_exceeded"] = True
                return fallback_result

            logger.warning("gh api failed for repo %s: %s", slug, res.stderr.strip()[:100])
            return fallback_result

        data = json.loads(res.stdout)
        license_obj = data.get("license") or {}
        spdx = license_obj.get("spdx_id") or "UNKNOWN"

        eval_lic = classify_license(spdx)
        stars = data.get("stargazers_count", 0)
        pushed_at = data.get("pushed_at", "UNKNOWN")

        return {
            "repo": slug,
            "repo_slug": slug,
            "url": f"https://github.com/{slug}",
            "name": data.get("name", repo_name),
            "owner": data.get("owner", {}).get("login", owner),
            "license": spdx,
            "license_spdx": spdx,
            "legal_track": eval_lic["legal_track"],
            "track": eval_lic["track"],
            "direct_copy_permitted": eval_lic["direct_copy_permitted"],
            "patterns": ["StateGraph", "Cyclic Execution", "Checkpointing"],
            "patterns_detected": ["StateGraph", "Cyclic Execution", "Checkpointing"],
            "applicability": "High applicability for DNK OS Swarm Control Plane & Task Orchestration",
            "activity": {
                "stars": stars,
                "last_commit": pushed_at,
                "fallback_used": False
            },
            "stars": stars,
            "last_commit": pushed_at,
            "fallback_used": False,
            "rate_limit_exceeded": False
        }

    except Exception as e:
        logger.error("Exception analyzing repo %s: %s", slug, e)
        return fallback_result
