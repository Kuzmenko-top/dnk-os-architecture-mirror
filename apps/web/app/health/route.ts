// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_app_health_route_ts"
// purpose: "Health check endpoint for DNK OS Web UI"
// author: "DNK-e.com Maksym"
// license: "MIT"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// --- END DNK-MRH-HEADER ---

import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'canvas-web'
  });
}
