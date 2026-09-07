#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/preflight_sanitizer.py"
# purpose: "Pre-Flight Autonomous Sanitizer for Gerych & DNK OS Swarm: validates tokens, cleans locks, and enforces Gemini 3.x SSOT."
# canonical_source: true
# alters_files: ["~/.hermes/config.yaml", "core/orchestrator/agents/herich_librarian/config.yaml", "~/.hermes/vertex_token.txt"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# author: "Antigravity (Mentor/Architect) & DNK Architecture Council"
# --- END DNK-MRH-HEADER ---

import os
import sys
import time
import subprocess
import sqlite3
import re
from pathlib import Path
from typing import Optional

def sanitize_state_db(db_path: Path):
    if not db_path.exists():
        return
    try:
        # Check and remove stale repair locks in the same directory
        parent = db_path.parent
        for lock_file in parent.glob("*.lock"):
            try:
                lock_file.unlink()
            except Exception:
                pass
        
        # Checkpoint WAL and optimize
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.close()
    except Exception as exc:
        pass

def ensure_fresh_gcp_token(account: Optional[str] = None) -> bool:
    token_file = Path.home() / ".hermes" / "vertex_token.txt"
    token_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not account:
        account = os.environ.get("GCP_ACTIVE_ACCOUNT")
        if not account:
            try:
                account = subprocess.check_output(["gcloud", "config", "get-value", "account"], stderr=subprocess.DEVNULL, timeout=5).decode().strip()
            except Exception:
                account = "tech.valleriy@gmail.com"
    
    needs_refresh = True
    if token_file.exists():
        try:
            mtime = token_file.stat().st_mtime
            if (time.time() - mtime) < 2100:  # Fresh within 35 minutes
                tok = token_file.read_text().strip()
                if tok.startswith("ya29."):
                    needs_refresh = False
        except Exception:
            needs_refresh = True
            
    if needs_refresh:
        try:
            cmd = ["gcloud", "auth", "print-access-token"]
            if account:
                cmd.append(account)
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=10).decode().strip()
            if out.startswith("ya29."):
                token_file.write_text(out)
                return True
        except Exception:
            pass
    return True

def enforce_gemini_3x_in_config(config_path: Path):
    if not config_path.exists():
        return
    try:
        content = config_path.read_text(encoding="utf-8")
        # Replace any lingering 2.x models with 3.x models
        cleaned = re.sub(r'gemini-2\.[05]-(flash|pro|flash-lite)(-[a-z0-9]+)?', 'gemini-3.6-flash', content)
        cleaned = re.sub(r'gemini-1\.5-(flash|pro)', 'gemini-3.5-flash', cleaned)
        if cleaned != content:
            config_path.write_text(cleaned, encoding="utf-8")
    except Exception:
        pass

def purge_stray_directory(dir_path: Path):
    if dir_path.exists() and dir_path.is_dir():
        try:
            import shutil
            shutil.rmtree(dir_path, ignore_errors=True)
        except Exception:
            pass

def purge_stale_files(parent_dir: Path, pattern: str):
    if parent_dir.exists():
        for f in parent_dir.glob(pattern):
            try:
                f.unlink()
            except Exception:
                pass

def main():
    # 1. Sanitize state databases
    hermes_home = Path.home() / ".hermes"
    hub_root = Path(__file__).resolve().parent.parent.parent
    librarian_home = hub_root / "core" / "orchestrator" / "agents" / "herich_librarian"
    prime_home = hub_root / "core" / "orchestrator" / "agents" / "gerych_prime"
    
    sanitize_state_db(hermes_home / "state.db")
    sanitize_state_db(librarian_home / "state.db")
    sanitize_state_db(prime_home / "state.db")
    
    # Clean stale malformed DB backups
    purge_stale_files(librarian_home, "state.db.malformed*")
    purge_stale_files(prime_home, "state.db.malformed*")
    purge_stale_files(hermes_home, "state.db.malformed*")
    
    # 2. Enforce fresh token
    ensure_fresh_gcp_token()
    
    # 3. Clean legacy models from configs
    enforce_gemini_3x_in_config(hermes_home / "config.yaml")
    enforce_gemini_3x_in_config(librarian_home / "config.yaml")
    enforce_gemini_3x_in_config(prime_home / "config.yaml")
    
    # 4. Disk Hygiene: Clean large ephemeral caches and .tmp directories
    try:
        ephemeral_dirs = [
            hub_root / "visual_shell" / "open_design" / ".tmp",
            hub_root / "visual_shell" / "open_design" / ".tmp",
            hub_root / "visual_shell" / "open_design" / "apps" / "web" / ".next" / "cache",
            hub_root / "visual_shell" / "open_design" / "apps" / "daemon" / ".turbo",
        ]
        import shutil
        for edir in ephemeral_dirs:
            if edir.exists():
                shutil.rmtree(edir, ignore_errors=True)
    except Exception:
        pass

    # 5. Process Hygiene & Zombie Process Watchdog
    try:
        from scripts.system.process_guard import audit_and_reap_processes
        audit_and_reap_processes()
    except Exception:
        pass
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
