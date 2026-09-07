#!/bin/bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/load_test/load_test.sh"
# purpose: "Load and stress testing orchestrator for DNK OS API, WebSocket, and Database."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

set -e

echo "🚀 DNK OS Load Testing"
echo "======================"

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
CONCURRENT_USERS="${CONCURRENT_USERS:-100}"
RAMP_UP="${RAMP_UP:-30}"
DURATION="${DURATION:-300}"

# Verify k6 presence or notify
if ! command -v k6 &> /dev/null; then
    echo "⚠️  k6 is not installed. To run k6 tests: brew install k6 or install k6 binary."
    echo "Running Python-based load validation..."
    python3 scripts/load_test/db_load_test.py
    exit 0
fi

# API Load Test
echo "Running API load test with k6..."
k6 run --vus "${CONCURRENT_USERS}" --duration "${DURATION}s" scripts/load_test/api_load_test.js

# WebSocket Load Test
if [ -f "scripts/load_test/ws_load_test.js" ]; then
    echo "Running WebSocket load test..."
    k6 run --vus 50 --duration 60s scripts/load_test/ws_load_test.js || echo "WebSocket test warning"
fi

# Database Load Test
echo "Running database load test..."
python3 scripts/load_test/db_load_test.py

echo ""
echo "🎉 Load Testing Complete!"
