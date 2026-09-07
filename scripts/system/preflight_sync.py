#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/preflight_sync.py"
# purpose: "Pre-Flight Briefing & Invariant Synchronizer for Gerych Swarm Sessions."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.1"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import subprocess
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent


def run_cmd(cmd: list) -> str:
    try:
        return subprocess.check_output(cmd, cwd=HUB_ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return ""


def sync_monorepo():
    """Verify monorepo directory health in the unified workspace."""
    required_dirs = [
        "services",
        "apps/api",
        "apps/web",
        "tests",
        "scripts/system",
        "core",
    ]
    for rel in required_dirs:
        d = HUB_ROOT / rel
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)


def main():
    sync_monorepo()

    if not (os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")):
        env_file = HUB_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("GH_TOKEN=") or line.startswith("GITHUB_TOKEN="):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        os.environ[parts[0].strip()] = parts[1].strip()
        if not os.getenv("GH_TOKEN") and os.getenv("GITHUB_TOKEN"):
            os.environ["GH_TOKEN"] = os.environ["GITHUB_TOKEN"]

    branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "main"
    sha = run_cmd(["git", "rev-parse", "HEAD"])[:10] or "unknown"
    has_token = bool(os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN"))
    venv_path = HUB_ROOT / ".venv"
    venv_ok = venv_path.exists()
    branch_status = (
        "⚠️  ON 'main' BRANCH — To enable 1-Click Auto-PR creation on GitHub, switch to a feature branch:\n"
        "   git checkout -b feature/<task_id>-<slug>"
        if branch == "main"
        else f"✅ Feature branch active: {branch} (Auto-PR delivery ready)"
    )

    lessons_section = ""
    lessons_file = HUB_ROOT / ".scones" / "session_lessons.json"
    if lessons_file.exists():
        try:
            import json
            lessons_data = json.loads(lessons_file.read_text(encoding="utf-8"))
            if lessons_data:
                lessons_lines = []
                for item in lessons_data[-4:]:
                    cat = item.get("category", "GENERAL")
                    rule = item.get("rule", "")
                    lessons_lines.append(f"  • [{cat}] {rule}")
                lessons_section = "\n💡 SELF-IMPROVED LESSONS (Distilled from past sessions — NEVER repeat errors!):\n" + "\n".join(lessons_lines) + "\n"
        except Exception:
            pass

    milestones_section = ""
    catalog_file = HUB_ROOT / ".scones" / "task_evolution_catalog.json"
    if catalog_file.exists():
        try:
            import json
            catalog_data = json.loads(catalog_file.read_text(encoding="utf-8"))
            if catalog_data:
                m_lines = []
                for m in catalog_data[-3:]:
                    title = m.get("title") or (m.get("user_prompt") or "")[:40]
                    aff_count = len(m.get("affected_files", []))
                    eff = m.get("efficiency_pct", 100)
                    m_lines.append(f"  • [{m.get('session_id', '')[:15]}] {title} ({aff_count} files, {eff}% efficiency)")
                milestones_section = "\n🏛️  RECENT TASK MILESTONES (Continuous Evolution & Zero Forgetting):\n" + "\n".join(m_lines) + "\n"
        except Exception:
            pass

    briefing = f"""
================================================================================
🛡️  DNK OS GERYCH PRE-FLIGHT BRIEFING & ZERO-WASTE CAPABILITY CARD
================================================================================
📍 Branch: {branch} (Commit: {sha})
🌿 Branch Status: {branch_status}
🐍 SSOT Virtualenv: {venv_path} {'[ACTIVE ✅]' if venv_ok else '[MISSING ❌]'}
🐙 GitHub CLI: {'[AUTHENTICATED ✅]' if has_token else '[UNAUTHENTICATED ⚠️]'}
🏛️ Architecture: [UNIFIED MONOREPO SSOT ✅]

🗺️  ARCHITECTURE FAST-INDEX (Never guess or run 15 ls commands!):
  • Web App:          apps/web/ (Next.js 14 Web Command Center)
  • Visual Shell:     visual_shell/open_design/apps/web/ & /daemon/
  • API Backend:      apps/api/ (FastAPI dynamic router gateway)
  • Microservices:    services/ (dnk_shopify_builder, dnk_video_ai_creator, etc.)
  • Core Engines:     core/ (orchestrator, security, scones_memory, task_engine)
  • Full Architecture Map: python3 scripts/system/repo_map.py

⚡ PRE-APPROVED CANONICAL WORKFLOW UTILITIES:
  1. In-Memory API Verifier:  ./.venv/bin/python3 scripts/system/verify_fast_endpoints.py (0 restarts)
  2. Process Guard:           ./.venv/bin/python3 scripts/system/process_guard.py
  3. Adversarial Review Gate: ./.venv/bin/python3 scripts/system/adversarial_gate_runner.py
  4. Swarm Parallel Dispatch: bash scripts/system/gerych_swarm.sh --parallel
  5. Pre-Commit Quality Gate: bash scripts/verify_all.sh
  6. GitHub Fast-Path:        gh pr create / gh api (Pre-authenticated via $GH_TOKEN, NO manual credentials!)
  7. Fast Symbol Resolver:     ./.venv/bin/python3 scripts/system/repo_map.py --symbol <name>
  8. Level-of-Detail Skills:   skill_view(name, section="<section_title>")
{milestones_section}{lessons_section}
🚨 MANDATORY FIRST-STEP INVARIANTS:
  • RELATIVE PATHS ONLY: Always use relative paths (./scripts/..., ./apps/..., ./core/...). Never construct /Users/... absolute paths!
  • ZERO-WASTE FAST VERIFICATION: Use in-memory endpoint verification instead of killing/restarting uvicorn.
  • TASK-DNA FIRST: Run dnk_decompose_task_dna(goal) before editing multiple files.
  • SCONES MEMORY FIRST: Query scones_get_memories(topic) before writing new boilerplate.
  • MANDATORY ATOMIC SLICE (MASE): 1 Session = 1 Atomic Slice (≤ 25 tool calls). NEVER pass multi-slice monoliths!
  • CONTEXT DIET: Read targeted slices (view_file(StartLine, EndLine) <= 100 lines).
  • ADVERSARIAL GATE: Pass adversarial review before opening PRs.
================================================================================
"""
    print(briefing)


if __name__ == "__main__":
    main()