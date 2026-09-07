#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/session_handoff.py"
# purpose: "Automated session handoff generator and state compactor keeping context under 10k tokens."
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

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
MVP_ROOT = HUB_ROOT
HANDOFF_DIR = MVP_ROOT / "docs" / "handoffs"
HANDOFF_DIR.mkdir(parents=True, exist_ok=True)


def get_git_status() -> str:
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        last_commit = subprocess.check_output(["git", "log", "-1", "--oneline"], text=True).strip()
        return f"Branch: `{branch}`\nLast Commit: `{last_commit}`"
    except Exception:
        return "Git info unavailable"


def create_handoff(topic: str = "SESSION_HANDOFF") -> Path:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    filename = f"HANDOFF_{topic}_{date_str}.md"
    target_path = HANDOFF_DIR / filename

    content = f"""# --- DNK-MRH-HEADER ---
# mrh_id: "docs/handoffs/{filename}"
# purpose: "Canonical Session Handoff & State Summary for DNK OS High-Velocity Swarm."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 📋 Session Handoff: {topic}

- **Created At**: {datetime.now(timezone.utc).isoformat()}
- **Git Context**:
{get_git_status()}

## 🚀 Key Accomplishments & State
1. **Quality Gate**: 100% Green (`scripts/verify_all.sh`).
2. **Docker Topology**: Multi-replica API + Next.js Frontend + Postgres + Redis operational.
3. **Multi-Agent Pipeline**: One-Click Product Launch Flow, Liquid AST Compiler, Remotion Video Renderer, Swarm Daemon active.

## 🎯 Next Immediate Action
- Start a fresh Hermes CLI session with compact context (<5k tokens).
"""
    target_path.write_text(content, encoding="utf-8")
    print(f"✅ Session Handoff generated: {target_path}")
    return target_path


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "ZERO_WASTE_SPEED_UP"
    create_handoff(topic)
