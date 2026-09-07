#!/bin/bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/verify_all.sh"
# purpose: "Unified Fast Quality Gate verifying GCP token, clean paths, test suite, and MRH headers."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PY_BIN="$HUB_ROOT/.venv/bin/python3"

# Check for --affected / -a flag
AFFECTED_MODE=0
for arg in "$@"; do
  if [ "$arg" == "--affected" ] || [ "$arg" == "-a" ]; then
    AFFECTED_MODE=1
  fi
done

if [ "$AFFECTED_MODE" -eq 1 ]; then
  echo "⚡ [TARGETED MODE] --affected flag enabled: running focused tests based on blast radius."
fi


# Step 1: Preflight Sanitizer (GCP Token, SQLite DBs, Stray Dirs & Fast Syntax Check)
echo "🔍 [1/4] Running Preflight Sanitizer..."
"$PY_BIN" "$HUB_ROOT/scripts/system/preflight_sanitizer.py"
"$PY_BIN" "$HUB_ROOT/scripts/system/fast_compile_check.py"
echo "✅ [1/4] Preflight checks passed."

# Step 2: Relative Path & Path Hygiene Audit
echo "🔍 [2/4] Enforcing Relative Paths & SSOT Layout..."
(
  cd "$HUB_ROOT"
  "$HUB_ROOT/.venv/bin/python3" -c '
from core.playbooks.scripts.enforce_relative_paths import audit_relative_paths
violations = audit_relative_paths()
if violations > 0:
    print(f"❌ Found {violations} absolute path violations!")
    exit(1)
print("✅ Path hygiene verified: 0 absolute path violations.")
'
)
echo "✅ [2/4] Path hygiene verified."

# Step 2.1: Git Workspace Hygiene (No untracked tests or router files)
echo "🔍 [2.1/4] Enforcing Git Workspace Hygiene..."
"$PY_BIN" "$HUB_ROOT/scripts/system/git_hygiene_guard.py"
echo "✅ [2.1/4] Git hygiene verified."

# Step 2.5: Adversarial Review Gate & Probe Library (Auditor ⚔️ vs Builder 🛡️)
echo "🔍 [2.5/4] Running Adversarial Review Gate & Probe Library Evaluation..."
(
  cd "$HUB_ROOT"
  PYTHONPATH="$HUB_ROOT:$HUB_ROOT/services" \
    "$HUB_ROOT/.venv/bin/python3" \
    "$HUB_ROOT/scripts/system/adversarial_gate_runner.py"
)
echo "✅ [2.5/4] Adversarial Gate passed."

# Security Checks (gitleaks, pip-audit)
echo "🔒 [Security] Checking secrets with gitleaks..."
if command -v gitleaks &>/dev/null; then
  gitleaks protect --staged --redact 2>/dev/null || gitleaks detect --log-opts="-n 5" --redact
  echo "✅ [Security] gitleaks check passed."
else
  echo "⚠️ [Security] gitleaks not installed; skipping secret scan."
fi

echo "🔒 [Security] Checking dependencies with pip-audit..."
if [ -x "$HUB_ROOT/.venv/bin/pip-audit" ]; then
  "$HUB_ROOT/.venv/bin/pip-audit" --desc
  echo "✅ [Security] pip-audit dependency scan passed."
elif command -v pip-audit &>/dev/null; then
  pip-audit --desc
  echo "✅ [Security] pip-audit dependency scan passed."
else
  echo "⚠️ [Security] pip-audit not installed; skipping dependency scan."
fi

# Docker Configuration Validation
echo "🐳 [Docker] Validating Docker Compose configuration..."
if command -v docker &>/dev/null; then
  docker compose config -q
  echo "✅ [Docker] docker compose config is valid."
else
  echo "⚠️ [Docker] docker not available; skipping compose validation."
fi

# CI/CD Workflow Validation
echo "⚙️ [CI/CD] Validating GitHub Actions workflows..."
if command -v actionlint &>/dev/null; then
  actionlint .github/workflows/*.yml
  echo "✅ [CI/CD] actionlint static workflow validation passed."
elif command -v act &>/dev/null; then
  act -l -W .github/workflows > /dev/null
  echo "✅ [CI/CD] act workflow validation passed."
else
  echo "⚠️ [CI/CD] Neither actionlint nor act installed; skipping workflow validation."
fi

# Step 2.55: Grafana Dashboard Validation
echo "📊 [Grafana] Validating Grafana dashboards..."
"$PY_BIN" "$HUB_ROOT/scripts/system/validate_grafana_dashboards.py"
echo "✅ [Grafana] Grafana dashboards validated."

# Step 2.6: Architecture Layer Isolation & Import Cycles Guard
echo "🛡️ [2.6/4] Verifying Architecture Isolation & Import Cycles..."
"$HUB_ROOT/.venv/bin/python3" "$HUB_ROOT/scripts/system/architecture_and_cycle_guard.py"
echo "✅ [2.6/4] Architecture and import cycle invariants verified."

# Step 2.7: Deterministic Blast Radius Assessment
echo "🎯 [2.7/4] Calculating Blast Radius & Affected Surface..."
"$HUB_ROOT/.venv/bin/python3" "$HUB_ROOT/scripts/system/blast_radius_analyzer.py"

# Step 3: Fast Test Suite Verification — AUTO-DISCOVERY OR TARGETED
cd "$HUB_ROOT"
export SECURITY_RATE_LIMIT=100000
export PYTHONPATH="$HUB_ROOT:$HUB_ROOT/services"
export VERIFY_ALL=1

if [ "$AFFECTED_MODE" -eq 1 ]; then
  echo "🔍 [3/4] Running Targeted Affected Regression Tests (blast radius)..."
  TARGET_TESTS=$( "$HUB_ROOT/.venv/bin/python3" -c '
from scripts.system.blast_radius_analyzer import BlastRadiusAnalyzer
res = BlastRadiusAnalyzer().analyze()
tests = res.get("required_pytests", [])
print(" ".join(tests))
' )
  if [ -n "$TARGET_TESTS" ]; then
    echo "   🎯 Targeted pytest files: $TARGET_TESTS"
    "$HUB_ROOT/.venv/bin/python3" -m pytest \
      -c "$HUB_ROOT/pyproject.toml" \
      $TARGET_TESTS \
      --quiet \
      --tb=short
    echo "✅ [3/4] Targeted regression tests passed (100% Green)."
  else
    echo "✅ [3/4] No backend pytest tests affected by current changeset."
  fi

  TARGET_VITESTS=$( "$HUB_ROOT/.venv/bin/python3" -c '
from scripts.system.blast_radius_analyzer import BlastRadiusAnalyzer
res = BlastRadiusAnalyzer().analyze()
vitests = res.get("required_vitests", [])
print(" ".join(vitests))
' )
  if [ -n "$TARGET_VITESTS" ] && [ -d "$HUB_ROOT/visual_shell/open_design/apps/web" ]; then
    echo "   🎯 Targeted vitest files: $TARGET_VITESTS"
    (cd "$HUB_ROOT/visual_shell/open_design/apps/web" && npx vitest run $TARGET_VITESTS)
    echo "✅ [3.1/4] Targeted vitest tests passed (100% Green)."
  fi
else
  echo "🔍 [3/4] Running Regression Test Suites (auto-discovery)..."
  SKIP_DIRS="__pycache__|verification"

  TEST_DIR_ARGS=()
  while IFS= read -r d; do
    TEST_DIR_ARGS+=("$d")
  done < <(
    find "$HUB_ROOT/tests" -mindepth 1 -maxdepth 1 -type d \
      | grep -vE "/(${SKIP_DIRS})$" \
      | sort
  )

  TOP_LEVEL_TEST_ARGS=()
  while IFS= read -r f; do
    TOP_LEVEL_TEST_ARGS+=("$f")
  done < <(
    find "$HUB_ROOT/tests" -maxdepth 1 -name "test_*.py" | sort
  )

  EXTRA_VERIFICATION_ARGS=()
  while IFS= read -r f; do
    EXTRA_VERIFICATION_ARGS+=("$f")
  done < <(
    find "$HUB_ROOT/tests/verification" -name "*.py" -not -name "__init__.py" \
      2>/dev/null | sort
  )

  DIR_NAMES=$(printf '%s\n' "${TEST_DIR_ARGS[@]}" | xargs -I{} basename {} | tr '\n' ' ')
  TOP_COUNT=${#TOP_LEVEL_TEST_ARGS[@]}
  EXTRA_COUNT=${#EXTRA_VERIFICATION_ARGS[@]}
  echo "   📂 Test dirs    : ${DIR_NAMES}"
  echo "   📄 Top tests    : ${TOP_COUNT} test_*.py files"
  echo "   📄 Extra files  : ${EXTRA_COUNT} verification/*.py files"

  "$HUB_ROOT/.venv/bin/python3" -m pytest \
    -c "$HUB_ROOT/pyproject.toml" \
    "${TEST_DIR_ARGS[@]}" \
    "${TOP_LEVEL_TEST_ARGS[@]}" \
    "${EXTRA_VERIFICATION_ARGS[@]}" \
    --quiet \
    --tb=short

  echo "✅ [3/4] All regression test suites passed (100% Green)."
fi

# Step 3.5: Frontend TypeScript Integrity Check
echo "🔍 [3.5/4] Checking Frontend TypeScript Integrity..."
if [ -f "$HUB_ROOT/apps/web/package.json" ]; then
  npm --prefix "$HUB_ROOT/apps/web" run type-check
  echo "✅ [3.5/4] Frontend TypeScript integrity verified."
fi

# Step 4: Summary
echo "🔍 [4/4] Finalizing verification..."
echo "========================================================"
echo "🎉 ALL QUALITY CONTRACTS VERIFIED: SYSTEM IS READY FOR COMMIT"
echo "========================================================"
exit 0
