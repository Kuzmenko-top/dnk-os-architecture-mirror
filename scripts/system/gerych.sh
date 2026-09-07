#!/bin/bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/gerych.sh"
# purpose: "Canonical launcher for Gerych Hermes Agent runtime with Process Lock, Proactive Auth, and Path Hygiene."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.1.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Silence macOS libmalloc debug warnings on child process fork/exec
unset MallocStackLogging MallocStackLoggingNoCompact MALLOC_STACK_LOGGING 2>/dev/null || true
export -n MallocStackLogging MallocStackLoggingNoCompact MALLOC_STACK_LOGGING 2>/dev/null || true

# Get the root directory of DNK_HUB
REAL_SCRIPT="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$( cd "$( dirname "$REAL_SCRIPT" )" && pwd )"
if [ -f "$SCRIPT_DIR/../AGENTS.md" ]; then
    HUB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
elif [ -f "$SCRIPT_DIR/../../AGENTS.md" ]; then
    HUB_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
else
    HUB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
cd "$HUB_ROOT"
export PATH="$HUB_ROOT/.venv/bin:$PATH"
export PYTHONPATH="$HUB_ROOT:$HUB_ROOT/services"

# Ensure DNK OS TUI Integrity on startup
python3 "${HUB_ROOT}/scripts/system/ensure_dnk_tui_integrity.py" >/dev/null 2>&1 || true

# Parse --agent <name> and --force if passed
TARGET_AGENT="${HERMES_AGENT_NAME:-gerych_prime}"
FORCE_FLAG=""
HERMES_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --agent)
            TARGET_AGENT="$2"
            shift 2
            ;;
        --force)
            FORCE_FLAG="--force"
            shift
            ;;
        *)
            if [ -d "$HUB_ROOT/core/orchestrator/agents/$1" ]; then
                TARGET_AGENT="$1"
                shift
            else
                HERMES_ARGS+=("$1")
                shift
            fi
            ;;
    esac
done

set -- "${HERMES_ARGS[@]}"

# Fast-path for version and verify commands
if [ "$1" = "--version" ] || [ "$1" = "-v" ] || [ "$1" = "version" ]; then
    echo "DNK OS Hermes v2.1.0"
    exit 0
fi

if [ "$1" = "--verify" ] || [ "$1" = "verify" ]; then
    python3 "$HUB_ROOT/scripts/system/auto_precommit_guard.py"
    exit $?
fi

# Fast-path for Zero-Waste Runner DAG status, step, and auto execution
if [ "$1" = "--status" ] || [ "$1" = "--plan" ]; then
    python3 "$HUB_ROOT/scripts/system/zero_waste_runner.py" --status
    exit $?
fi

if [ "$1" = "--step" ]; then
    python3 "$HUB_ROOT/scripts/system/zero_waste_runner.py" --step
    exit $?
fi

if [ "$1" = "--auto" ]; then
    python3 "$HUB_ROOT/scripts/system/zero_waste_runner.py" --auto
    exit $?
fi

if [ "$1" = "--reset" ]; then
    python3 "$HUB_ROOT/scripts/system/zero_waste_runner.py" --reset
    exit $?
fi


# 1. Process Hygiene Audit & Stale Process Reaping
python3 "$HUB_ROOT/scripts/system/process_guard.py" --audit >/dev/null 2>&1 || true

# 2. Single-Instance / Process Lock Acquisition
if ! python3 "$HUB_ROOT/scripts/system/process_guard.py" --check-lock "$TARGET_AGENT" $FORCE_FLAG; then
    exit 1
fi

SENTINEL_PID=""

function cleanup_on_exit() {
    # Prevent duplicate execution
    if [ "${_CLEANUP_CALLED:-0}" -eq 1 ]; then
        return 0
    fi
    _CLEANUP_CALLED=1

    # 1. Release single-instance process lock
    python3 "$HUB_ROOT/scripts/system/process_guard.py" --release-lock "$TARGET_AGENT" >/dev/null 2>&1 || true

    # 2. Autonomous Post-Session Audit & Distillation (Continuous Self-Improvement)
    python3 "$HUB_ROOT/scripts/system/auto_session_auditor.py" --latest --agent "$TARGET_AGENT" >/dev/null 2>&1 || true

    # 3. Session Sentinel: Self-Healing Task Synthesis & Canvas Enqueueing
    python3 "$HUB_ROOT/scripts/system/session_sentinel.py" --audit-latest --agent "$TARGET_AGENT" >/dev/null 2>&1 || true

    # 4. Cleanup background sentinel if still running
    if [ -n "$SENTINEL_PID" ] && kill -0 "$SENTINEL_PID" 2>/dev/null; then
        kill -TERM "$SENTINEL_PID" 2>/dev/null || true
    fi
}
on_session_exit() {
    cleanup_on_exit
}
trap cleanup_on_exit EXIT INT TERM

# Launch parallel Shadow Observer / Sentinel in background
python3 "$HUB_ROOT/scripts/system/session_sentinel.py" --watch --agent "$TARGET_AGENT" --pid $$ >/dev/null 2>&1 &
SENTINEL_PID=$!



# Set Agent Home to target agent profile if exists
if [ -d "$HUB_ROOT/core/orchestrator/agents/$TARGET_AGENT" ]; then
    export HERMES_HOME="$HUB_ROOT/core/orchestrator/agents/$TARGET_AGENT"
elif [ -z "$HERMES_HOME" ]; then
    export HERMES_HOME="$HUB_ROOT/core/orchestrator/agents/herich_librarian"
fi

# Ensure runtime caches (lsp, checkpoints, cache, logs) are isolated to ~/.hermes/runtime
RUNTIME_AGENT_DIR="$HOME/.hermes/runtime/$TARGET_AGENT"
mkdir -p "$RUNTIME_AGENT_DIR/lsp" "$RUNTIME_AGENT_DIR/checkpoints" "$RUNTIME_AGENT_DIR/cache" "$RUNTIME_AGENT_DIR/logs"
for rdir in lsp checkpoints cache logs; do
    if [ ! -e "$HERMES_HOME/$rdir" ]; then
        ln -s "$RUNTIME_AGENT_DIR/$rdir" "$HERMES_HOME/$rdir" 2>/dev/null || true
    fi
done

# Load environment variables from project .env
if [ -f "$HUB_ROOT/.env" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        if [[ ! "$line" =~ ^# ]] && [[ -n "$line" ]]; then
            clean_line=$(echo "$line" | tr -d '\r')
            export "$clean_line"
        fi
    done < "$HUB_ROOT/.env"
fi

# Ensure GitHub Token is inherited from environment or fetched via gh auth token
if [ -z "$GH_TOKEN" ] && [ -z "$GITHUB_TOKEN" ]; then
    DETECTED_GH_TOKEN="$(gh auth token 2>/dev/null || true)"
    if [ -n "$DETECTED_GH_TOKEN" ]; then
        export GH_TOKEN="$DETECTED_GH_TOKEN"
        export GITHUB_TOKEN="$DETECTED_GH_TOKEN"
    fi
else
    export GH_TOKEN="${GH_TOKEN:-$GITHUB_TOKEN}"
    export GITHUB_TOKEN="${GITHUB_TOKEN:-$GH_TOKEN}"
fi
export PYTHONPATH="$HUB_ROOT:$HUB_ROOT/services"

# === Ensure Active Google Cloud Project & Account from SSOT ===
if [ -f "$HUB_ROOT/.dnk_active_project.env" ]; then
    # shellcheck source=/dev/null
    source "$HUB_ROOT/.dnk_active_project.env"
elif [ -f "$HOME/.hermes/.env" ]; then
    # shellcheck source=/dev/null
    source "$HOME/.hermes/.env"
fi

export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null || echo "project-930a8ed3-3e40-4f43-9d4")}"
ACTIVE_ACCOUNT="${GCP_ACTIVE_ACCOUNT:-$(gcloud config get-value account 2>/dev/null || echo "tech.valleriy@gmail.com")}"

# === Inject fresh gcloud token for Vertex AI / Agent Platform API ===
ADC_TOKEN=""
VERTEX_TOKEN_FILE="$HOME/.hermes/vertex_token.txt"
TOKEN_MAX_AGE_SEC=2400  # 40 minutes proactive threshold

# Fast path: check cached token age
if [ -f "$VERTEX_TOKEN_FILE" ]; then
    FILE_MOD_TIME=$(stat -f "%m" "$VERTEX_TOKEN_FILE" 2>/dev/null || stat -c "%Y" "$VERTEX_TOKEN_FILE" 2>/dev/null || echo 0)
    CURRENT_TIME=$(date +%s)
    AGE=$((CURRENT_TIME - FILE_MOD_TIME))
    if [ "$AGE" -lt "$TOKEN_MAX_AGE_SEC" ]; then
        CACHED=$(tr -d '[:space:]' < "$VERTEX_TOKEN_FILE")
        if [[ "$CACHED" == ya29.* ]]; then
            ADC_TOKEN="$CACHED"
        fi
    fi
fi

# Refresh token if not cached or expired
if [ -z "$ADC_TOKEN" ] && command -v gcloud &> /dev/null; then
    ADC_TOKEN=$(gcloud auth print-access-token "$ACTIVE_ACCOUNT" 2>/dev/null || true)
    if [ -z "$ADC_TOKEN" ] || [[ "$ADC_TOKEN" != ya29.* ]]; then
        ADC_TOKEN=$(gcloud auth application-default print-access-token 2>/dev/null || true)
        ACTIVE_ACCOUNT="${ACTIVE_ACCOUNT} (ADC)"
    fi
    if [ -n "$ADC_TOKEN" ] && [[ "$ADC_TOKEN" == ya29.* ]]; then
        mkdir -p "$HOME/.hermes"
        echo "$ADC_TOKEN" > "$VERTEX_TOKEN_FILE"
        echo "[GCP] ⚡ Refreshed OAuth token for $ACTIVE_ACCOUNT"
    fi
fi

if [ -n "$ADC_TOKEN" ]; then
    export VERTEX_API_KEY="$ADC_TOKEN"
    export VERTEX_TOKEN="$ADC_TOKEN"
    export VERTEX_REGION="${VERTEX_REGION:-global}"
    export VERTEX_PROJECT_ID="$GOOGLE_CLOUD_PROJECT"
    export VERTEX_BASE_URL="https://aiplatform.googleapis.com/v1/projects/${GOOGLE_CLOUD_PROJECT}/locations/${VERTEX_REGION:-global}/publishers/google"
    unset GEMINI_API_KEY
    unset GOOGLE_API_KEY
    echo "[GCP] OAuth2 token active (account: $ACTIVE_ACCOUNT, project: $GOOGLE_CLOUD_PROJECT, region: ${VERTEX_REGION:-global} - Gemini 3.x)"
else
    echo "[GCP] ⚠️  No token found. Run in terminal: gcloud auth application-default login"
fi

cd "$HUB_ROOT"
export PATH="$HUB_ROOT/.venv/bin:$PATH"
export PYTHONPATH="$HUB_ROOT:$HUB_ROOT/services"
export HERMES_MAX_TOKENS=65535
export HERMES_MAX_ITERATIONS="${HERMES_MAX_ITERATIONS:-150}"
export TERMINAL_CWD="$HUB_ROOT"
export HERMES_CWD="$HUB_ROOT"
export HERMES_ACCEPT_HOOKS=1
export HERMES_HOOKS_AUTO_ACCEPT=1

# === Autonomous Step 0 Triage & Smart Router ===
if [ "$#" -gt 0 ] && [[ "$1" != -* ]]; then
    KNOWN_COMMANDS="chat model moa fallback worktree secrets egress migrate gateway proxy lsp setup whatsapp whatsapp-cloud slack send login logout auth status pause resume cron sync webhook peer portal kanban project hooks doctor verify security approvals dump debug backup checkpoints import import-agent config skin console pairing skills bundles plugins curator pets journey learning memory-graph memory tools computer-use mcp sessions insights monitoring claw update uninstall acp profile completion dashboard serve desktop gui logs prompt-size version"
    FIRST_WORD="$1"
    IS_KNOWN=0
    for cmd in $KNOWN_COMMANDS; do
        if [ "$FIRST_WORD" = "$cmd" ]; then
            IS_KNOWN=1
            break
        fi
    done

    if [ $IS_KNOWN -eq 0 ]; then
        # Check if first argument is a file path
        if [ -f "$1" ]; then
            PROMPT_CONTENT="$(cat "$1")"
            echo "📄 [Gerych Launcher] Loaded task specification from: $1"
        else
            PROMPT_CONTENT="$*"
        fi

        # Step 0 Autonomous Triage
        TRIAGE_DATA=$(python3 -c "
import sys, json
from core.orchestrator.task_triage import dnk_triage_task
res = dnk_triage_task(sys.argv[1])
print(json.dumps({'mode': res.mode, 'score': res.complexity_score, 'rationale': res.rationale}))
" "$PROMPT_CONTENT" 2>/dev/null || echo '{"mode": "SOLO", "score": 0, "rationale": "Direct execution"}')

        TRIAGE_MODE=$(echo "$TRIAGE_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin).get('mode', 'SOLO'))" 2>/dev/null || echo "SOLO")
        TRIAGE_SCORE=$(echo "$TRIAGE_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin).get('score', 0))" 2>/dev/null || echo "0")
        TRIAGE_RATIONALE=$(echo "$TRIAGE_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin).get('rationale', ''))" 2>/dev/null || echo "")

        if [ "$TRIAGE_MODE" = "SWARM_PARALLEL" ] || [ "$TRIAGE_MODE" = "SWARM_SEQUENTIAL" ]; then
            echo ""
            echo "========================================================"
            echo "🐝 [DNK OS Step 0 Triage] High-Complexity Task Detected"
            echo "📊 Mode: $TRIAGE_MODE | Complexity Score: C = $TRIAGE_SCORE (> 3)"
            echo "💡 $TRIAGE_RATIONALE"
            echo "⚡ Auto-engaging Zero-Waste Swarm Coordinator..."
            echo "========================================================"
            python3 "$HUB_ROOT/scripts/system/zero_waste_runner.py" --goal "$PROMPT_CONTENT" --auto
            EXIT_CODE=$?
            exit $EXIT_CODE
        else
            echo "🎯 [DNK OS Step 0 Triage] Lightweight Task (Mode: SOLO, C=$TRIAGE_SCORE <= 3)"
            echo "⚡ Executing directly via Gerych Prime (bounded: <= 35 iterations, <= 25 tools)..."
            export DNK_ATOMIC_SLICE=1
            export HERMES_MAX_ITERATIONS=35
            python3 "$HUB_ROOT/scripts/system/preflight_sync.py"
            uv run --project "$HUB_ROOT/core/hermes_agent" python3 "$HUB_ROOT/core/hermes_agent/hermes" -z "$PROMPT_CONTENT"
            EXIT_CODE=$?
            exit $EXIT_CODE
        fi
    fi
fi

# === Pre-Flight Capabilities & Invariants Briefing ===
python3 "$HUB_ROOT/scripts/system/preflight_sync.py"

uv run --project "$HUB_ROOT/core/hermes_agent" python3 "$HUB_ROOT/core/hermes_agent/hermes" "$@"
EXIT_CODE=$?
exit $EXIT_CODE



