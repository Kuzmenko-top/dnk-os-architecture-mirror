# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tech_specs_dnk_impl_008_analytics_dashboard"
# purpose: "Technical specification and architecture documentation for the Advanced Analytics Dashboard"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# --- END DNK-MRH-HEADER ---

# DNK-IMPL-008: Advanced Analytics Dashboard

This document details the implementation of the **Advanced Analytics Dashboard** in the DNK OS Visual Shell MVP application.

## 1. Analytics API (Backend)

The backend implementation resides in `apps/api/routers/analytics.py` and provides high-performance data aggregations over the **Timeline DB** (`timeline` schema) with clean fallback and caching capabilities.

### Endpoints:
- `GET /api/analytics/overview?period_days={days}` — Returns total runs, success rate, average duration, total error count, and top error list.
- `GET /api/analytics/agents/{agent_id}/performance?period_days={days}` — Evaluates concrete agent total runs, success rates, speed metrics, and specific task failures.
- `GET /api/analytics/bottlenecks?period_days={days}` — Groups tasks to list averages and highlight which phases (research, write, validate) have higher latency or error spikes.
- `GET /api/analytics/timeline?period_days={days}` — Daily time-series run/success/error statistics for lines and area visualization.
- `GET /api/analytics/recommendations` — Returns recommendations and optimization actions pulled from the Knowledge Base or generated dynamically.

---

## 2. Frontend (Dashboard UI)

The frontend is implemented under the Next.js 14 App Router and utilizes Tailwind CSS v4 for a premium dark layout.

### Components:
- `apps/web/app/analytics/page.tsx` — Main dashboard page displaying overview cards, charts grid, agent table, and advice panel.
- `apps/web/components/analytics/OverviewCard.tsx` — Key stat cards (Total Runs, Success Rate, Speed, Errors) with beautiful glassmorphism.
- `apps/web/components/analytics/AgentPerformanceTable.tsx` — Grid list displaying individual agent run and success counts.
- `apps/web/components/analytics/BottlenecksChart.tsx` — Premium custom horizontal SVG bars indicating average times and failures.
- `apps/web/components/analytics/TimelineChart.tsx` — High-fidelity SVG polyline line chart rendering multi-colored metrics trends with gradients.

---

## 3. Integration with Knowledge Base

The `/api/analytics/recommendations` endpoint queries the pgvector `timeline.knowledge_documents` table for timeline-sourced insights. If none are found, it triggers a dynamic optimization rule logic that automatically inspects bottlenecks (e.g. high research failure rates) and produces action plans such as retry timeouts or RAG parameter tuning.

---

## 4. Configuration

The configuration parameters are set in `core/config/analytics_config.py`:
- `ANALYTICS_CACHE_TTL` (default = 300s) — Cache duration for analytics queries.
- `ANALYTICS_DEFAULT_PERIOD_DAYS` (default = 7 days) — Initial view interval.
- `ANALYTICS_MAX_PERIOD_DAYS` (default = 90 days) — Cap for requested duration.

---

## 5. Verification Tests

Verified by automated test suite in `tests/verification/test_analytics_dashboard.py`:
1. `test_overview_endpoint` — Asserts overview shape.
2. `test_agent_performance_endpoint` — Asserts agent performance.
3. `test_bottlenecks_endpoint` — Checks grouped task metrics.
4. `test_timeline_endpoint` — Verifies time-series trends.
5. `test_recommendations_endpoint` — Confirms optimization proposals.
6. `test_frontend_overview` — Static checks for overview cards.
7. `test_frontend_charts` — Static verification of charts rendering.
