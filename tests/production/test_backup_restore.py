# --- DNK-MRH-HEADER ---
# mrh_id: "tests/production/test_backup_restore.py"
# purpose: "Integration tests for automated database backup and restore scripts."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import subprocess


def test_backup_script():
    # Run backup script
    result = subprocess.run(
        ["bash", "scripts/backup/backup_database.sh"],
        capture_output=True,
        text=True,
        env={**os.environ, "DB_NAME": "test_db"},
    )

    assert result.returncode == 0
    assert "Backup completed" in result.stdout


def test_restore_from_backup():
    # Find latest backup
    backup_dir = os.environ.get("BACKUP_DIR", "/var/backups/dnk_os")
    if not os.path.exists(backup_dir) and os.path.exists("/tmp/backups/dnk_os"):
        backup_dir = "/tmp/backups/dnk_os"

    backups = [f for f in os.listdir(backup_dir) if f.endswith(".sql.gz")]
    assert len(backups) > 0
    latest_backup = max(backups)

    # Restore
    result = subprocess.run(
        ["gunzip", "-c", f"{backup_dir}/{latest_backup}"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "CREATE TABLE" in result.stdout or "-- PostgreSQL dump" in result.stdout
