#!/usr/bin/env bash
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/deploy.sh"
# purpose: "Production deployment automation script for DNK OS Multi-Agent Core"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

set -e

echo "🚀 Deploying DNK OS Multi-Agent Core..."

# Build Docker images
echo "📦 Building Docker images..."
docker-compose build

# Start services
echo "🏗️  Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking health..."
curl -f http://localhost:8000/health || exit 1

echo "✅ Deployment complete!"
echo "📊 API: http://localhost:8000"
echo "🎨 Frontend: http://localhost:3000"
