#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/gcp_token_daemon.py"
# purpose: "Autonomous Google Cloud OAuth2 token watchdog daemon ensuring 24/7 hot tokens for Vertex AI Gemini 3.x."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

TOKEN_DIR = Path.home() / ".hermes"
TOKEN_FILE = TOKEN_DIR / "vertex_token.txt"
PID_FILE = TOKEN_DIR / "token_daemon.pid"
LOG_FILE = TOKEN_DIR / "token_daemon.log"


class GCPTokenDaemon:
    """
    Autonomous Watchdog Daemon.
    Proactively checks and refreshes Google Cloud OAuth2 Access Tokens
    every 30-40 minutes so long-running sessions never hit 401 Unauthorized.
    """

    def __init__(self, refresh_interval_seconds: int = 2100):  # 35 minutes
        self.refresh_interval = refresh_interval_seconds
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)

    def log(self, message: str):
        timestamp = datetime.now(timezone.utc).isoformat()
        log_line = f"[{timestamp}] {message}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)

    def refresh_token(self) -> Optional[str]:
        """Fetch fresh token using gcloud CLI or Application Default Credentials."""
        try:
            account = os.environ.get("GCP_ACTIVE_ACCOUNT", "")
            if not account:
                res_acc = subprocess.run(["gcloud", "config", "get-value", "account"], capture_output=True, text=True, timeout=5)
                account = res_acc.stdout.strip()
            
            cmd = ["gcloud", "auth", "print-access-token"]
            if account:
                cmd.append(account)
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            token = res.stdout.strip()

            if not token or not token.startswith("ya29."):
                cmd_adc = ["gcloud", "auth", "application-default", "print-access-token"]
                res_adc = subprocess.run(cmd_adc, capture_output=True, text=True, timeout=10)
                token = res_adc.stdout.strip()

            if token and token.startswith("ya29."):
                TOKEN_FILE.write_text(token, encoding="utf-8")
                try:
                    repo_root = Path(__file__).resolve().parents[2]
                    (repo_root / ".vertex_token").write_text(token, encoding="utf-8")
                except Exception:
                    pass
                self.log(f"⚡ Successfully refreshed OAuth token for {account or 'ADC'} ({token[:10]}...{token[-5:]})")
                return token
            else:
                self.log(f"⚠️ Failed to obtain token: stdout={res.stdout}, stderr={res.stderr}")
                return None
        except Exception as exc:
            self.log(f"❌ Error refreshing token: {exc}")
            return None

    def get_token_status(self) -> Dict[str, Any]:
        if not TOKEN_FILE.exists():
            return {"active": False, "reason": "No token file found"}
        
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
        mod_time = TOKEN_FILE.stat().st_mtime
        age_seconds = round(time.time() - mod_time, 1)
        is_valid = (token.startswith("ya29.") and age_seconds < 3600)

        return {
            "active": is_valid,
            "token_prefix": f"{token[:10]}..." if token else "none",
            "age_seconds": age_seconds,
            "expires_in_seconds": max(0, 3600 - int(age_seconds)),
            "token_file": str(TOKEN_FILE),
        }

    def run_daemon_loop(self):
        """Continuous background watchdog loop."""
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
        self.log(f"🚀 GCP Token Watchdog Daemon started (PID: {os.getpid()})")

        try:
            while True:
                status = self.get_token_status()
                # If token is older than 30 minutes, refresh immediately
                if not status.get("active") or status.get("age_seconds", 0) > self.refresh_interval:
                    self.refresh_token()
                time.sleep(300)  # Check status every 5 minutes
        except KeyboardInterrupt:
            self.log("🛑 Watchdog daemon stopped by user.")
        finally:
            if PID_FILE.exists():
                PID_FILE.unlink(missing_ok=True)


gcp_token_daemon = GCPTokenDaemon()


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "refresh":
        tok = gcp_token_daemon.refresh_token()
        if tok:
            print(f"✅ Token refreshed: {tok[:10]}...{tok[-5:]}")
        else:
            print("❌ Failed to refresh token.")
    elif action == "status":
        stat = gcp_token_daemon.get_token_status()
        print(f"⚡ Token Status: {stat}")
    elif action == "daemon":
        gcp_token_daemon.run_daemon_loop()
    else:
        print("Usage: gcp_token_daemon.py [status|refresh|daemon]")
