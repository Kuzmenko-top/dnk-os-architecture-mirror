#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/deploy_production.sh"
# purpose: "Production Deployment, Container Lifecycle & Automated Smoke-Test Matrix for DNK OS v5.0.0"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$HUB_ROOT"

SMOKE_ONLY=0
if [[ "$1" == "--smoke-only" || "$1" == "--verify" ]]; then
    SMOKE_ONLY=1
fi

if [ "$SMOKE_ONLY" -eq 0 ]; then
    echo "========================================================"
    echo "🚀 Launching DNK OS v5.0.0 Production Deployment"
    echo "========================================================"

    # 1. Build Docker images
    echo "📦 Building Docker production images..."
    docker-compose -f docker-compose.prod.yml build

    # 2. Start all services
    echo "🏗️ Starting production containers (PostgreSQL, Redis, API, Web)..."
    docker-compose -f docker-compose.prod.yml up -d

    # 3. Wait for services
    echo "⏳ Waiting for health probes to stabilize (10s)..."
    sleep 10

    echo "📊 Container Status:"
    docker-compose -f docker-compose.prod.yml ps
    echo ""
fi

echo "========================================================"
echo "🧪 Running Automated Smoke-Test Matrix for 7 Core Modules"
echo "========================================================"

ROUTES=(
    "Backend Health Probe|http://localhost:8000/health"
    "Swagger API Docs|http://localhost:8000/docs"
    "Canvas API Default|http://localhost:8000/api/canvas/default-canvas-id"
    "Working Cabinet UI|http://localhost:3000/cabinet"
    "Visual Canvas UI|http://localhost:3000/canvas/default-canvas-id"
    "Whiteboard Engine|http://localhost:3000/whiteboard"
    "TaskDNA Dashboard|http://localhost:3000/taskdna"
    "SCONES L3 Memory|http://localhost:3000/memory-l3"
    "Patent Shield|http://localhost:3000/patent-shield"
    "Deep Analytics|http://localhost:3000/analytics"
)

ALL_PASSED=1

printf "%-26s | %-45s | %-10s\n" "Module / Endpoint" "Target URL" "Status"
printf "%-26s-+-%-45s-+-%-10s\n" "--------------------------" "---------------------------------------------" "----------"

for entry in "${ROUTES[@]}"; do
    IFS="|" read -r name url <<< "$entry"
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    if [[ "$status_code" =~ ^(200|307|308)$ ]]; then
        printf "%-26s | %-45s | \033[0;32m✅ %-6s\033[0m\n" "$name" "$url" "HTTP $status_code"
    else
        printf "%-26s | %-45s | \033[0;31m❌ %-6s\033[0m\n" "$name" "$url" "HTTP $status_code"
        ALL_PASSED=0
    fi
done

echo ""
if [ "$ALL_PASSED" -eq 1 ]; then
    echo "========================================================"
    echo "🎉 DNK OS v5.0.0 Production Stack is 100% HEALTHY & READY!"
    echo "🌐 Access Web UI: http://localhost:3000"
    echo "🔧 Access Backend: http://localhost:8000"
    echo "========================================================"
    exit 0
else
    echo "⚠️ Some endpoints did not return 200/307. Check container logs via: docker-compose -f docker-compose.prod.yml logs"
    exit 1
fi
