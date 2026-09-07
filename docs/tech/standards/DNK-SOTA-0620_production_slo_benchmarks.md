# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-SOTA-0620_production_slo_benchmarks.md"
# purpose: "Define production SLOs and execution classifications for DNK OS Live Gated Gateway."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

# 📊 DNK OS LLM GATEWAY PRODUCTION SLO & BENCHMARK STANDARD

This standard defines the Service Level Objectives (SLOs) and runtime classifications for live model gateway operations inside **DNK OS (Gate 5C-A Controlled Pilot)**.

## 🗂️ 1. Runtime Classifications

To ensure precision in measurement, all execution runs are divided into three distinct categories:

1. **Simulation (Local/Mock Mode)**:
   - *Description*: Uses local JSON fixtures or deterministic caches. Bypasses actual network requests. Used for functional test suites and CI.
   - *Target Latency*: `< 50 ms`
   - *Target Cost*: `$0.00`
   
2. **Real Provider Call (API Only)**:
   - *Description*: Performs active HTTPS requests to Vertex AI / Anthropic endpoints, bypassing database/persistence operations. Used to isolate provider performance.
   - *Target Latency*: `1.0s - 4.5s`
   
3. **Production-Like Run (PostgreSQL + Redis + Failover)**:
   - *Description*: Active network request with complete state storage in production PostgreSQL and real-time audit event logging to Redis. 
   - *Target Latency*: `2.0s - 7.0s` (due to database connection overhead and network hops)

---

## 📈 2. Service Level Objectives (SLOs)

These metrics must be strictly monitored during the **Gate 5C-A Controlled External Pilot**:

| SLO Metric | Target Threshold | Scope / Conditions | Emergency Action on Violation |
|---|---|---|---|
| **Success Rate** | `>= 99.5%` | Whitelisted Workspaces | Auto-switch to shadow mode / Alert triggered |
| **p95 Latency** | `< 4.5s` | Real Provider Calls (Claude/Gemini) | Fallback to faster routing tier / cache |
| **Provider Error Rate** | `< 5.0%` | Prior to fallback/retry orchestration | Alert triggered (Possible upstream API outage) |
| **Fallback Rate** | `< 2.0%` | Active failover count Gemini ➔ Claude | Alert triggered if fallback rate spikes |
| **Cost Per Execution** | `< $0.02` | Average per supervisor run | Budget cap block on workspace level |
| **Mutation Rejection** | `100.0%` | Cross-workspace or non-whitelisted | Strict Fail-Closed / Security alert |

---
**Approved by:** Maksym (Lead Developer / CTO)  
**Monitored by:** DNK OS Prometheus & Telemetry Stack  
