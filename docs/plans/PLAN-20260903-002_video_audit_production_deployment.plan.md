# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plans/PLAN-20260903-002_video_audit_production_deployment.plan.md"
# purpose: "Production Deployment Blueprint & Live LLM SpendGuard Integration for Video Audit Pipeline (001E-PROD)."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["VIDEO-AUDIT-PROD-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Production Deployment Blueprint: Video Intelligence & Niche Adaptation Engine (001E-PROD)

## 1. Executive Summary
Following the complete certification and 100% test pass of **VIDEO-AUDIT-PIPELINE-001E-F-LIVE** (138 core tests, 17 live/adaptation tests), the system moves into **Option A: Production Deployment**.

This plan outlines the activation of live multimodal LLM adapters (Gemini / Claude / DNK Model Proxy), integration with **SpendGuard**, latency/cost observability, and fail-safe fallback guarantees.

---

## 2. Core Architecture & Invariants

```text
       [ Adaptation Request ]
                 │
                 ▼
     ┌───────────────────────┐
     │  SpendGuard Evaluator │ ◄── [ Pre-Flight Budget Check (< $5.00) ]
     └───────────┬───────────┘
                 │
        ┌────────┴────────┐
   [Within Cap]       [Cap Exceeded / Network Error]
        │                         │
        ▼                         ▼
┌───────────────────┐    ┌───────────────────────────┐
│ Live LLM Writer   │    │ DeterministicScriptWriter │
│ (Gemini / Claude) │    │ (Zero-Cost Fail-Safe)     │
└─────────┬─────────┘    └─────────────┬─────────────┘
          │                            │
          └──────────────┬─────────────┘
                         ▼
             [ Similarity Guard 🛡️ ]
                         ▼
         [ Brand Alignment Validator 🔍 ]
                         ▼
             [ Approved Script v1 ]
```

### Key Invariants:
1. **SpendGuard Hard Cap**: Strict budget limiter ($5.00 default cap, configurable per tenant/workspace). Any attempt to exceed the cap instantly triggers a graceful fallback to deterministic writing with zero disruption to end users.
2. **Fail-Closed Brand Safety**: Live outputs pass through identical similarity gates, unverified claims filters, and prosody tokenizers before human or teleprompter consumption.
3. **Zero Secrets in Code**: API keys (`VERTEX_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) sourced exclusively from environment variables or Vault.

---

## 3. Implementation Phases

### Phase 1: Live LLM Connector & Adapter Protocol
- Enhance `LiveLlmScriptWriter` in `packages/video-audit-core` to accept a live provider interface (`LLMProviderClient`).
- Support provider backends:
  - **Vertex Gemini** (`gemini-2.5-pro`, `gemini-2.5-flash`)
  - **Universal Model Proxy** (`core/model_proxy/universal_model_proxy.py`)
- Implement structured prompt injection preserving extracted mechanisms, brand voice constraints, and teleprompter prosody rules.

### Phase 2: SpendGuard Observability & Metrics
- Add per-call token usage calculation alongside flat estimates.
- Emit structured metric events (`adaptation.spend_tracked`, `adaptation.circuit_tripped`, `adaptation.latency_ms`).
- Provide telemetry export for DNK OS Admin Dashboard.

### Phase 3: Resilience & Canary Verification
- Automated timeout handling (default: 8000ms max per live request).
- Retry policy with exponential backoff for transient 429 / 503 errors.
- Vitest live test suite (`pnpm test:live`) integration testing real model responses when live keys are present.

---

## 4. Acceptance Criteria
- [ ] Live LLM writer produces valid `ScriptDocument` compliant with `script.v1` schema.
- [ ] SpendGuard hard stops calls exceeding cumulative budget limit.
- [ ] Network failures automatically degrade to deterministic writer without throwing unhandled exceptions.
- [ ] 100% green test suite maintained across all 32 test files.
