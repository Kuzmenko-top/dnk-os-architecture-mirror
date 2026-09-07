#!/bin/bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/worktree_spawn.sh"
# purpose: "Ephemeral Git Worktree Manager for Isolated Multi-Agent Swarm Execution in DNK OS."
# canonical_source: true
# alters_files: [".worktrees/"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Antigravity & Gerych"
# --- END DNK-MRH-HEADER ---

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKTREES_DIR="$HUB_ROOT/.worktrees"

function show_help {
    echo "========================================================"
    echo "🌳 DNK OS Ephemeral Git Worktree Manager"
    echo "========================================================"
    echo "Usage: $0 [COMMAND] [ARGS...]"
    echo ""
    echo "Commands:"
    echo "  create <task_id> [base_branch]  Create isolated worktree at .worktrees/<task_id>"
    echo "  remove <task_id>                Remove worktree and clean up references"
    echo "  list                            List all active swarm worktrees"
    echo "  merge <task_id> [target_branch] Run verification and merge into target branch"
    echo "  help                            Show this help message"
    echo "========================================================"
}

if [ $# -lt 1 ]; then
    show_help
    exit 1
fi

COMMAND="$1"
shift

cd "$HUB_ROOT"
mkdir -p "$WORKTREES_DIR"

case "$COMMAND" in
    create)
        TASK_ID="$1"
        BASE_BRANCH="${2:-main}"
        if [ -z "$TASK_ID" ]; then
            echo "❌ Error: task_id is required."
            exit 1
        fi
        WORKTREE_PATH="$WORKTREES_DIR/$TASK_ID"
        BRANCH_NAME="feat/$TASK_ID"

        if [ -d "$WORKTREE_PATH" ]; then
            echo "⚠️  Worktree already exists at $WORKTREE_PATH"
            exit 0
        fi

        echo "🚀 Spawning isolated worktree for [$TASK_ID] on branch [$BRANCH_NAME]..."
        # Create branch if doesn't exist, otherwise checkout
        if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
            git worktree add "$WORKTREE_PATH" "$BRANCH_NAME"
        else
            git worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH" "$BASE_BRANCH"
        fi

        echo "✅ Worktree ready: $WORKTREE_PATH"
        ;;

    remove)
        TASK_ID="$1"
        if [ -z "$TASK_ID" ]; then
            echo "❌ Error: task_id is required."
            exit 1
        fi
        WORKTREE_PATH="$WORKTREES_DIR/$TASK_ID"

        echo "🧹 Removing worktree [$TASK_ID]..."
        if [ -d "$WORKTREE_PATH" ]; then
            git worktree remove "$WORKTREE_PATH" --force || rm -rf "$WORKTREE_PATH"
        fi
        git worktree prune
        echo "✅ Worktree [$TASK_ID] removed and pruned."
        ;;

    list)
        echo "🌳 Active Git Worktrees:"
        git worktree list
        ;;

    merge)
        TASK_ID="$1"
        TARGET_BRANCH="${2:-main}"
        if [ -z "$TASK_ID" ]; then
            echo "❌ Error: task_id is required."
            exit 1
        fi
        WORKTREE_PATH="$WORKTREES_DIR/$TASK_ID"
        BRANCH_NAME="feat/$TASK_ID"

        if [ ! -d "$WORKTREE_PATH" ]; then
            echo "❌ Error: Worktree not found at $WORKTREE_PATH"
            exit 1
        fi

        echo "🧪 Running pre-merge verification in worktree [$TASK_ID]..."
        cd "$WORKTREE_PATH"
        if [ -f "scripts/verify_all.sh" ]; then
            bash scripts/verify_all.sh || {
                echo "❌ Merge aborted: verification failed in $WORKTREE_PATH"
                exit 1
            }
        fi

        cd "$HUB_ROOT"
        echo "🔀 Merging branch [$BRANCH_NAME] into [$TARGET_BRANCH]..."
        git checkout "$TARGET_BRANCH"
        git merge "$BRANCH_NAME" --no-edit

        echo "🧹 Auto-cleaning worktree after successful merge..."
        git worktree remove "$WORKTREE_PATH" --force || rm -rf "$WORKTREE_PATH"
        git branch -d "$BRANCH_NAME" || true
        git worktree prune
        echo "✅ Successfully merged and cleaned up task [$TASK_ID]."
        ;;

    help|-h|--help)
        show_help
        ;;

    *)
        echo "❌ Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
