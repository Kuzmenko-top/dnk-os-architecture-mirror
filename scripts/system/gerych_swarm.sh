#!/bin/bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/gerych_swarm.sh"
# purpose: "Unified Swarm Launcher for Gerych Prime, Builder, Researcher, Stitch Engine & Auditor."
# author: "DNK-e.com Maksym"
# canonical_source: true
# status: "Active"
# version: "2.2.0"
# updated_at: "2026-09-02"
# --- END DNK-MRH-HEADER ---

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AGENTS_DIR="$HUB_ROOT/core/orchestrator/agents"
export GH_TOKEN="${GH_TOKEN:-}"
export GITHUB_TOKEN="${GITHUB_TOKEN:-$GH_TOKEN}"

# Show Help
function show_help {
    echo "========================================================"
    echo "🐝 Gerych Multi-Agent Swarm Launcher (DNK OS)"
    echo "========================================================"
    echo "Usage: $0 [OPTIONS] [TASK...]"
    echo ""
    echo "Options:"
    echo "  -p, --prime            Launch Gerych Prime (Chief Orchestrator, Gemini 3.7)"
    echo "  -b, --builder          Launch Gerych Builder (Fullstack & Systems, Gemini 3.7)"
    echo "  -r, --researcher       Launch Gerych Researcher (SOTA Knowledge & AST, Gemini 3.6)"
    echo "  -a, --auditor          Launch Gerych Auditor (QA & Security Gate, Gemini 3.5 Lite)"
    echo "  --agent <name>         Launch specific agent by name"
    echo "  --list                 List all available swarm agents & capabilities"
    echo "  --pipeline <goal>      Run full 4-stage autonomous pipeline (Prime->Research->Build->Audit)"
    echo "  --parallel             Run parallel subagents batch execution (Builder, Auditor, Shopify, Fullstack)"
    echo "  --adversarial-review   Run 2-agent adversarial review debate (Auditor attacks ⚔️ Builder defends)"
    echo "  --repo-map [query]     Generate zero-token AST code skeleton map"
    echo "  --visual-synth         Synthesize code from sample/given Canvas visual scene"
    echo "  --stitch-gen <prompt>  Console AI Stitch screen generation & auto-export to Shopify Liquid"
    echo "  --stitch-audit <path>  Parse DESIGN.md & audit contrast against WCAG 2.1 AA"
    echo "  -w, --worktree <id>    Run agent inside ephemeral isolated git worktree (.worktrees/<id>)"
    echo "  -h, --help             Show this help message"
    echo "========================================================"
}

TARGET_AGENT="gerych_prime"
RUN_PIPELINE=0
PIPELINE_GOAL=""
RUN_PARALLEL=0
RUN_ADVERSARIAL=0
RUN_REPO_MAP=0
REPO_QUERY=""
RUN_VISUAL_SYNTH=0
RUN_STITCH_GEN=0
STITCH_PROMPT=""
RUN_STITCH_AUDIT=0
STITCH_AUDIT_PATH=""
RUN_WORKTREE=0
WORKTREE_ID=""

PASSTHROUGH_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--prime)
            TARGET_AGENT="gerych_prime"
            shift
            ;;
        -b|--builder)
            TARGET_AGENT="gerych_builder"
            shift
            ;;
        -r|--researcher)
            TARGET_AGENT="gerych_researcher"
            shift
            ;;
        -a|--auditor)
            TARGET_AGENT="gerych_auditor"
            shift
            ;;
        --agent)
            TARGET_AGENT="$2"
            shift 2
            ;;
        --list)
            cd "$HUB_ROOT"
            ./.venv/bin/python3 -c '
from core.orchestrator.swarm_coordinator import swarm_coordinator
agents = swarm_coordinator.list_agents()
print("\n🐝 Registered Gerych Swarm Agents:")
for a in agents:
    aid = a.get("agent_id", "unknown")
    name = a.get("name", aid)
    desc = a.get("description", "")
    caps = ", ".join(a.get("capabilities", []))
    print(f"  • {aid} ({name})\n    Description: {desc}\n    Capabilities: {caps}\n")
'
            exit 0
            ;;
        --pipeline)
            RUN_PIPELINE=1
            PIPELINE_GOAL="$2"
            shift 2
            ;;
        --parallel)
            RUN_PARALLEL=1
            shift
            ;;
        --adversarial-review)
            RUN_ADVERSARIAL=1
            shift
            ;;
        --repo-map)
            RUN_REPO_MAP=1
            shift
            if [[ $# -gt 0 ]] && [[ ! "$1" =~ ^- ]]; then
                REPO_QUERY="$1"
                shift
            fi
            ;;
        --visual-synth)
            RUN_VISUAL_SYNTH=1
            shift
            ;;
        --stitch-gen)
            RUN_STITCH_GEN=1
            STITCH_PROMPT="$2"
            shift 2
            ;;
        --stitch-audit)
            RUN_STITCH_AUDIT=1
            STITCH_AUDIT_PATH="$2"
            shift 2
            ;;
        -w|--worktree)
            RUN_WORKTREE=1
            WORKTREE_ID="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            if [ -d "$AGENTS_DIR/$1" ]; then
                TARGET_AGENT="$1"
                shift
            else
                PASSTHROUGH_ARGS+=("$1")
                shift
            fi
            ;;
    esac
done

cd "$HUB_ROOT"

# Stitch Screen Generation Mode
if [ "$RUN_STITCH_GEN" -eq 1 ]; then
    echo "⚡ Launching Google Stitch Screen Generation for Prompt: '$STITCH_PROMPT'..."
    ./.venv/bin/python3 -c "
from core.adapters.dnk_stitch_adapter import dnk_stitch_adapter

res = dnk_stitch_adapter.generate_screen_sync(prompt='$STITCH_PROMPT', device_type='mobile')
screen_id = res.id
liquid_code = dnk_stitch_adapter.transpile_screen_to_shopify_liquid(screen_id)

print(f'✅ Screen Generated: {res.title} (ID: {screen_id})')
print(f'   • Device: {res.device_type}')
print(f'   • Shopify Liquid Transpiled Size: {len(liquid_code)} bytes')
print('\n--- Generated Shopify Liquid Snippet ---')
print(liquid_code[:400] + ('...' if len(liquid_code) > 400 else ''))
"
    exit 0
fi

# Stitch DESIGN.md Audit Mode
if [ "$RUN_STITCH_AUDIT" -eq 1 ]; then
    echo "🔍 Launching Stitch DESIGN.md Contrast Audit for: '$STITCH_AUDIT_PATH'..."
    ./.venv/bin/python3 -c "
import os
from core.adapters.dnk_stitch_adapter import parse_design_md, validate_wcag_contrast, export_to_tailwind_v4

path = '$STITCH_AUDIT_PATH'
content = ''
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
else:
    content = '''---
name: Cyberpunk Theme
version: 1.0.0
colors:
  primary: '#06B6D4'
  background: '#090D16'
  surface: '#111827'
  text_primary: '#F8FAFC'
  text_muted: '#64748B'
components:
  card-dark:
    backgroundColor: '#090D16'
    textColor: '#111827'
---
# Cyberpunk Token Specs
'''

parsed = parse_design_md(content)
fm = parsed['frontmatter']
violations = validate_wcag_contrast(fm)
tailwind_theme = export_to_tailwind_v4(fm)

print(f'✅ DESIGN.md Parsed: {fm.get(\"name\", \"Theme\")}')
print(f'   • Colors Defined: {len(fm.get(\"colors\", {}))}')
print(f'   • WCAG 2.1 AA Violations Found: {len(violations)}')
for v in violations:
    print(f'     ⚠️  [{v.get(\"component\", \"token\")}] Issue: {v.get(\"issue\")} (Ratio: {v.get(\"ratio\", 0):.2f})')
print('\n--- Exported Tailwind v4 @theme ---')
print(tailwind_theme)
"
    exit 0
fi

# AST Repo Map Mode
if [ "$RUN_REPO_MAP" -eq 1 ]; then
    echo "🗺️  Generating Codebase AST Repo-Map..."
    ./.venv/bin/python3 -c "
from core.orchestrator.swarm_coordinator import swarm_coordinator
print(swarm_coordinator.get_codebase_repo_map(query='$REPO_QUERY'))
"
    exit 0
fi

# Visual-to-Code Synthesizer Mode
if [ "$RUN_VISUAL_SYNTH" -eq 1 ]; then
    echo "🎨 Synthesizing Code from Canvas Scene..."
    ./.venv/bin/python3 -c "
from core.orchestrator.swarm_coordinator import swarm_coordinator
dummy_scene = {'elements': [{'id': 'n1', 'label': 'Hero Conversion Section', 'width': 300}, {'id': 'n2', 'label': 'Analytics Graph', 'width': 250}]}
code = swarm_coordinator.synthesize_code_from_canvas(dummy_scene, target_framework='react')
print(code)
"
    exit 0
fi

# Adversarial Review Debate Mode
if [ "$RUN_ADVERSARIAL" -eq 1 ]; then
    echo "⚔️  Launching Adversarial AI Review Debate (Auditor ⚔️  Builder)..."
    ./.venv/bin/python3 -c "
import sys
from core.orchestrator.swarm_coordinator import swarm_coordinator
res = swarm_coordinator.run_adversarial_review()
print(f'✅ Adversarial Review Verdict: {res[\"status\"].upper()} (Duration: {res[\"duration_ms\"]}ms)')
print(f'   • Candidates Surfaced: {res[\"total_candidates_detected\"]}')
print(f'   • False Positives Refuted by Builder: {res[\"false_positives_refuted\"]} ({res[\"false_positive_rate_pct\"]}%)')
print(f'   • Confirmed Issues to Heal: {res[\"confirmed_issues_count\"]}')
"
    exit 0
fi

# Parallel Subagents Execution Mode
if [ "$RUN_PARALLEL" -eq 1 ]; then
    echo "⚡ Launching Autonomous Parallel Subagents Batch Execution..."
    ./.venv/bin/python3 -c "
import sys
from core.orchestrator.swarm_coordinator import swarm_coordinator
tasks = [
    {'agent': 'gerych_builder', 'action': 'synthesize_components', 'payload': {'domain': 'ecom'}},
    {'agent': 'dnk_dev_fullstack', 'action': 'generate_fastapi_routers', 'payload': {'domain': 'core'}},
    {'agent': 'dnk_shopify', 'action': 'compile_liquid_functions', 'payload': {'domain': 'checkout'}},
    {'agent': 'gerych_auditor', 'action': 'adversarial_review', 'payload': {}}
]
res = swarm_coordinator.dispatch_parallel(tasks)
print(f'✅ Swarm Parallel Batch: {res[\"status\"].upper()} (Tasks: {res[\"task_count\"]}, Duration: {res[\"total_duration_seconds\"]}s)')
for t in res['completed_tasks']:
    print(f'   • [{t[\"agent\"]}] {t[\"action\"]} -> {t[\"status\"].upper()} ({t[\"duration_seconds\"]}s)')
"
    exit 0
fi

# Pipeline Execution Mode
if [ "$RUN_PIPELINE" -eq 1 ]; then
    echo "🚀 Launching Autonomous Gerych Swarm Pipeline for Goal: '$PIPELINE_GOAL'..."
    ./.venv/bin/python3 -c "
import sys
from core.orchestrator.swarm_coordinator import swarm_coordinator
res = swarm_coordinator.run_pipeline('$PIPELINE_GOAL')
print(f'✅ Swarm Pipeline Status: {res[\"status\"]} (Duration: {res[\"duration_seconds\"]}s)')
for s in res['pipeline_stages']:
    print(f'   [Stage {s[\"stage\"]}] {s[\"agent\"]}: {s[\"action\"]} -> {s[\"status\"].upper()}')
"
    exit 0
fi

# Single Agent Interactive / Command Launch Mode
AGENT_PATH="$AGENTS_DIR/$TARGET_AGENT"
if [ ! -d "$AGENT_PATH" ]; then
    echo "❌ Error: Agent directory '$AGENT_PATH' does not exist."
    exit 1
fi

echo "========================================================"
echo "🐝 Launching Agent Profile: [$TARGET_AGENT]"
echo "📁 Path: $AGENT_PATH"
if [ "$RUN_WORKTREE" -eq 1 ] && [ -n "$WORKTREE_ID" ]; then
    "$HUB_ROOT/scripts/system/worktree_spawn.sh" create "$WORKTREE_ID"
    WORKTREE_PATH="$HUB_ROOT/.worktrees/$WORKTREE_ID"
    echo "🌳 Isolated Worktree Active: $WORKTREE_PATH"
    cd "$WORKTREE_PATH"
fi
echo "========================================================"

export HERMES_HOME="$AGENT_PATH"
export HERMES_AGENT_NAME="$TARGET_AGENT"
exec "$HUB_ROOT/scripts/system/gerych.sh" --agent "$TARGET_AGENT" "${PASSTHROUGH_ARGS[@]}"
