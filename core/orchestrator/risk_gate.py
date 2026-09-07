#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/risk_gate.py"
# purpose: "Safety Risk Gate & Destructive Operation Guard with snapshot rollback for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.6.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import datetime
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("dnk_risk_gate")


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


HIGH_RISK_COMMAND_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bdrop\s+database\b",
    r"\bdrop\s+table\b",
    r"\bdelete\s+from\b",
    r"\bdelete\b",
    r"\bremove\b",
    r"\btruncate\s+table\b",
    r"\bformat\b",
    r"\breset\s+--hard\b",
    r"\bclean\s+-fdx\b",
    r"\bpurge\b",
    r"\bdestroy\b",
    r"\bвидалити\b",
    r"\bзнищити\b",
    r"\bочистити\s+баз\w*\b",
]

MEDIUM_RISK_COMMAND_PATTERNS = [
    r"\bперепиши\b",
    r"\bпереписати\b",
    r"\brewrite\b",
    r"\brefactor\b",
    r"\bрефакторинг\b",
    r"\bmigrat\w*\b",
    r"\bміграц\w*\b",
    r"\bмодифікуй\b",
]

SENSITIVE_FILES_OR_PATTERNS = [
    r"\.env",
    r"vault",
    r"id_rsa",
    r"SOUL\.md",
    r"config/secrets",
    r"\.pem$",
    r"\.key$",
]


def assess_risk(user_query: str, target_files: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Evaluates operational risk of proposed actions and determines required safeguards.
    """
    target_files = target_files or []
    detected_patterns: List[str] = []
    detected_sensitive_files: List[str] = []
    risk_score = 0

    # 1. Scan query for destructive commands
    for pattern in HIGH_RISK_COMMAND_PATTERNS:
        if re.search(pattern, user_query, re.IGNORECASE):
            detected_patterns.append(pattern)
            risk_score += 45

    # 1.1 Scan query for medium risk operations (refactor/rewrite)
    for pattern in MEDIUM_RISK_COMMAND_PATTERNS:
        if re.search(pattern, user_query, re.IGNORECASE):
            detected_patterns.append(pattern)
            risk_score += 25

    # 2. Scan target files for sensitive assets
    for tf in target_files:
        for sens in SENSITIVE_FILES_OR_PATTERNS:
            if re.search(sens, tf, re.IGNORECASE):
                detected_sensitive_files.append(tf)
                risk_score += 40
                break

    # 3. File count impact
    if len(target_files) > 10:
        risk_score += 25
    elif len(target_files) > 3:
        risk_score += 15

    # Critical check: wipe command or ultra-high risk score
    is_critical_wipe = bool(re.search(r"rm\s+-rf\s+/", user_query, re.IGNORECASE))

    if is_critical_wipe or risk_score >= 180:
        risk_level = RiskLevel.CRITICAL
    elif risk_score >= 40:
        risk_level = RiskLevel.HIGH
    elif risk_score >= 20:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW

    requires_approval = risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    backup_required = risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.MEDIUM)
    rollback_required = risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    suggested_safeguards: List[str] = []
    if backup_required:
        suggested_safeguards.append("Create backup snapshot before execution (`create_backup_snapshot`)")
    if rollback_required:
        suggested_safeguards.append("Create git backup branch (`create_git_backup_branch`)")
    if requires_approval:
        suggested_safeguards.append("Require explicit human operator approval before proceeding")

    return {
        "risk_level": risk_level.value,
        "risk_score": risk_score,
        "requires_approval": requires_approval,
        "backup_required": backup_required,
        "rollback_required": rollback_required,
        "detected_high_risk_patterns": detected_patterns,
        "detected_sensitive_files": detected_sensitive_files,
        "suggested_safeguards": suggested_safeguards,
    }


def create_backup_snapshot(
    target_files: List[str],
    snapshot_dir: str = ".hermes/backups",
    root_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates an isolated file backup snapshot before destructive modifications.
    Protects against symlink attacks and path traversal vulnerabilities.
    Uses unique hashed filenames: {hash}_{original_name}.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = Path(snapshot_dir) / f"snap_{timestamp}"
    snapshot_path.mkdir(parents=True, exist_ok=True)

    cwd = Path(root_dir).resolve() if root_dir else Path.cwd().resolve()
    backed_up: List[str] = []
    skipped_files: List[str] = []
    manifest_entries: List[Dict[str, str]] = []

    for file_str in target_files:
        src = Path(file_str)
        if not src.is_absolute():
            src = cwd / file_str

        if not src.exists():
            continue

        # 1. Symlink Attack Protection
        if src.is_symlink():
            logger.warning("Skipping symlink file '%s' to avoid symlink exploit", file_str)
            skipped_files.append(file_str)
            continue

        resolved_src = src.resolve()

        # 2. Path Traversal Protection
        is_safe_traversal = False
        if root_dir:
            try:
                resolved_src.relative_to(cwd)
                is_safe_traversal = True
            except ValueError:
                pass
        else:
            # If root_dir not provided, reject relative traversal ('..')
            if ".." in Path(file_str).parts:
                is_safe_traversal = False
            else:
                is_safe_traversal = True

        if not is_safe_traversal:
            logger.warning("Skipping file '%s' outside root directory (path traversal)", file_str)
            skipped_files.append(file_str)
            continue

        # 3. Unique Hashed Backup Name to avoid collision: {sha256[:8]}_{filename}
        path_hash = hashlib.sha256(str(resolved_src).encode("utf-8")).hexdigest()[:8]
        backup_filename = f"{path_hash}_{src.name}"
        dest = snapshot_path / backup_filename

        try:
            shutil.copy2(resolved_src, dest)
            backed_up.append(str(dest))
            manifest_entries.append({
                "original_path": str(src),
                "resolved_path": str(resolved_src),
                "backup_path": str(dest),
                "sha256": path_hash,
                "backup_filename": backup_filename
            })
        except Exception as e:
            logger.error("Failed to backup file '%s': %s", file_str, e)
            skipped_files.append(file_str)

    manifest_file = snapshot_path / "manifest.json"
    manifest_data = {
        "snapshot_id": snapshot_path.name,
        "manifest_path": str(manifest_file),
        "timestamp": timestamp,
        "files_count": len(backed_up),
        "skipped_count": len(skipped_files),
        "backed_up_files": backed_up,
        "skipped_files": skipped_files,
        "manifest_entries": manifest_entries,
        "status": "SNAPSHOT_CREATED"
    }

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    return manifest_data


def restore_backup_snapshot(
    snapshot_manifest_or_dir: Union[str, Dict[str, Any], Path],
    root_dir: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Restores files from a backup snapshot to their original locations.
    Accepts path to manifest.json, directory, or parsed manifest dict.
    """
    snapshot_manifest = kwargs.get("snapshot_manifest", snapshot_manifest_or_dir)

    if isinstance(snapshot_manifest, (str, Path)):
        p = Path(snapshot_manifest)
        if p.is_dir():
            p = p / "manifest.json"
        if not p.exists():
            return {"restored": False, "files_restored": 0, "errors": [f"Manifest not found: {p}"]}
        with open(p, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    else:
        manifest_data = snapshot_manifest

    entries = manifest_data.get("manifest_entries", [])
    restored_count = 0
    errors: List[str] = []

    for item in entries:
        orig = Path(item["original_path"])
        if root_dir and not orig.is_absolute():
            orig = Path(root_dir) / orig

        bup = Path(item["backup_path"])

        if not bup.exists():
            errors.append(f"Backup file missing: {bup}")
            continue

        try:
            orig.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bup, orig)
            restored_count += 1
        except Exception as e:
            errors.append(f"Failed to restore {orig}: {e}")

    return {
        "restored": (restored_count > 0 and len(errors) == 0),
        "files_restored": restored_count,
        "total_files": len(entries),
        "errors": errors
    }


def cleanup_old_snapshots(snapshot_dir: str = ".hermes/backups", max_age_days: int = 7) -> Dict[str, Any]:
    """
    Removes backup snapshots older than max_age_days.
    """
    base_dir = Path(snapshot_dir)
    if not base_dir.exists():
        return {"deleted_snapshots": [], "retained_snapshots": [], "deleted_count": 0, "cleaned": 0}

    now = time.time()
    cutoff_sec = max_age_days * 86400
    deleted: List[str] = []
    retained: List[str] = []

    for entry in base_dir.iterdir():
        if entry.is_dir() and (entry.name.startswith("snap_") or entry.name.startswith("snapshot_")):
            mtime = entry.stat().st_mtime
            if (now - mtime) > cutoff_sec:
                try:
                    shutil.rmtree(entry)
                    deleted.append(entry.name)
                    logger.info("Deleted expired snapshot: %s", entry.name)
                except Exception as e:
                    logger.error("Failed to delete snapshot %s: %s", entry.name, e)
            else:
                retained.append(entry.name)

    return {
        "deleted_snapshots": deleted,
        "retained_snapshots": retained,
        "deleted_count": len(deleted),
        "cleaned": len(deleted)
    }


def create_git_backup_branch(branch_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates a dedicated git backup branch before risky operations.
    Executes safely with list arguments (shell=False).
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bname = branch_name or f"backup/auto-{timestamp}"

    try:
        res = subprocess.run(
            ["git", "branch", bname],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            shell=False
        )
        if res.returncode == 0:
            return {
                "success": True,
                "branch_name": bname,
                "action": "git branch created"
            }
        else:
            return {
                "success": False,
                "branch_name": bname,
                "error": res.stderr.strip()
            }
    except Exception as e:
        return {
            "success": False,
            "branch_name": bname,
            "error": str(e)
        }
