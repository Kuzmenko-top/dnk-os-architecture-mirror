#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/test_risk_gate.py"
# purpose: "Unit, security, and snapshot rollback tests for Risk Gate."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.1.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import time
import shutil
from pathlib import Path
import pytest
from core.orchestrator.risk_gate import (
    RiskLevel,
    assess_risk,
    create_backup_snapshot,
    restore_backup_snapshot,
    cleanup_old_snapshots,
    create_git_backup_branch,
)


def test_assess_risk_levels():
    critical = assess_risk("drop database production; rm -rf /")
    assert critical["risk_level"] == RiskLevel.CRITICAL.value
    assert critical["requires_approval"] is True
    assert critical["backup_required"] is True

    high = assess_risk("видалити старі файли з диску")
    assert high["risk_level"] == RiskLevel.HIGH.value
    assert high["requires_approval"] is True
    assert high["backup_required"] is True

    medium = assess_risk("перепиши архітектуру сервісу")
    assert medium["risk_level"] == RiskLevel.MEDIUM.value
    assert medium["backup_required"] is True

    low = assess_risk("перевір тести та прочитай документацію")
    assert low["risk_level"] == RiskLevel.LOW.value
    assert low["requires_approval"] is False


def test_backup_and_restore_cycle(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    file_a = root / "data.txt"
    file_a.write_text("INITIAL_CONTENT", encoding="utf-8")
    
    backup_dir = root / ".backups"
    
    # 1. Create snapshot
    snapshot_res = create_backup_snapshot(
        target_files=["data.txt"],
        snapshot_dir=str(backup_dir),
        root_dir=str(root)
    )
    assert snapshot_res["status"] == "SNAPSHOT_CREATED"
    assert snapshot_res["files_count"] == 1
    
    # Verify unique hash naming
    manifest_path = Path(snapshot_res["manifest_path"])
    assert manifest_path.is_file()
    
    # 2. Modify or delete original file
    file_a.write_text("CORRUPTED_CONTENT", encoding="utf-8")
    assert file_a.read_text(encoding="utf-8") == "CORRUPTED_CONTENT"
    
    # 3. Restore snapshot
    restore_res = restore_backup_snapshot(
        snapshot_manifest_or_dir=str(manifest_path),
        root_dir=str(root)
    )
    assert restore_res["restored"] is True
    assert restore_res["files_restored"] == 1
    assert file_a.read_text(encoding="utf-8") == "INITIAL_CONTENT"


def test_symlink_and_traversal_protection(tmp_path):
    root = tmp_path / "sandbox"
    root.mkdir()
    real_file = root / "real.txt"
    real_file.write_text("SAFE_TEXT")
    
    symlink_file = root / "link.txt"
    symlink_file.symlink_to(real_file)
    
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("OUTSIDE")
    
    backup_dir = root / ".backups"
    res = create_backup_snapshot(
        target_files=["real.txt", "link.txt", "../outside.txt"],
        snapshot_dir=str(backup_dir),
        root_dir=str(root)
    )
    assert res["files_count"] == 1  # only real.txt
    assert res["skipped_count"] == 2  # symlink and traversal skipped


def test_cleanup_old_snapshots(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    
    old_snap = backup_dir / "snapshot_1000"
    old_snap.mkdir()
    # Set mtime to 10 days ago
    past_time = time.time() - (10 * 86400)
    os.utime(old_snap, (past_time, past_time))
    
    new_snap = backup_dir / f"snapshot_{int(time.time())}"
    new_snap.mkdir()
    
    res = cleanup_old_snapshots(snapshot_dir=str(backup_dir), max_age_days=7)
    assert res["cleaned"] == 1
    assert not old_snap.exists()
    assert new_snap.exists()


def test_create_git_backup_branch():
    branch_name = f"backup/test-auto-{int(time.time())}"
    res = create_git_backup_branch(branch_name)
    assert isinstance(res, dict)
    assert "branch_name" in res
    assert res["branch_name"] == branch_name
    # Clean up test branch if created
    if res.get("created"):
        import subprocess
        subprocess.run(["git", "branch", "-D", branch_name], capture_output=True, text=True)
