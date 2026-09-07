#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/test_fast.sh"
# purpose: "L1/L2 High-Velocity Target Test Runner for Instant Developer and Agent Feedback (<2s)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$HUB_ROOT/.venv/bin/activate" ]; then
    source "$HUB_ROOT/.venv/bin/activate"
fi

export PYTHONPATH="$HUB_ROOT:$HUB_ROOT/services:${PYTHONPATH:-}"
export SECURITY_RATE_LIMIT=100000

if [ $# -gt 0 ]; then
    echo "⚡ [L1 Fast Runner] Running targeted tests: $@"
    exec pytest "$@" --tb=short -q
fi

# If no args provided, detect changed files or run core unit tests
echo "⚡ [L2 Pre-Commit Fast Runner] Auto-detecting modified test targets..."

CHANGED_TESTS=$(git status --porcelain 2>/dev/null | grep -E '\.py$' | awk '{print $2}' | grep '^tests/' || true)

if [ -n "$CHANGED_TESTS" ]; then
    echo "🔍 Found modified tests:"
    echo "$CHANGED_TESTS"
    exec pytest $CHANGED_TESTS --tb=short -q
else
    echo "🚀 Running Fast Core Suites (Shopify, Canvas, Verification)..."
    exec pytest tests/shopify/ tests/canvas/ tests/verification/ \
        -k "not test_timeline and not test_security_gate and not test_knowledge_base_rag and not test_improvement_loop and not test_multi_agent_collaboration" \
        --tb=short -q
fi
