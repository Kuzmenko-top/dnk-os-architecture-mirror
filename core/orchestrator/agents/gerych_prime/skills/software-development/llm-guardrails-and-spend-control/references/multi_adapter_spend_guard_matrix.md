# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/llm-guardrails-and-spend-control/references/multi_adapter_spend_guard_matrix.md"
# purpose: "Gate 1 Multi-Adapter SpendGuard & Daily Budget Enforcement Specification"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym & Gerych"
# --- END DNK-MRH-HEADER ---

# Multi-Adapter SpendGuard Matrix & Daily Budget Enforcement

## 1. Budget Cap & Invariants
- **Daily Workspace Budget Cap:** `$10.00 USD / workspace / day`.
- **Threshold Tiers:**
  - `80% ($8.00)`: Warning Alert emitted to monitoring/telemetry/email.
  - `100% ($10.00)`: Hard Block (`SpendLimitExceededError` / HTTP 429 or 402 Fast Reject).
- **Correlation ID Tracking:** Every single adapter call must log cost, latency, status, and adapter name correlated with `correlation_id`.

## 2. Media & AI Adapter Pricing Matrix
| Adapter | Operation Type | Unit / Billing Basis | Default Cost (USD) | Pre-flight Guard Check |
| :--- | :--- | :--- | :--- | :--- |
| **BiRefNet** | Background Cutout / Matting | Per image | `$0.02` | Validate `remaining_budget >= 0.02` |
| **IC-Light** | Ambient Relighting & Harmonization | Per image | `$0.03` | Validate `remaining_budget >= 0.03` |
| **FLUX.1** | LayerDiffuse Image Gen | Per image | `$0.05` | Validate `remaining_budget >= 0.05` |
| **WhisperX** | Audio/Video Speech-to-Text (ASR) | Per minute (prorated) | `$0.01 / min` | Validate duration * rate |
| **Remotion** | 9:16 Video Composition & Render | Per render job | `$0.10` | Validate `remaining_budget >= 0.10` |
| **Shopify** | Asset / Media Upload Admin API | Per API call | `$0.00` (Free) | Rate-limit only |

## 3. Pre-Flight & Post-Flight Lifecycle
```python
# Pre-Flight Execution
spend_guard.validate_pre_request(
    workspace_id=workspace_id,
    adapter=adapter_name,
    estimated_cost=estimated_cost,
    correlation_id=correlation_id
)

# Remote API Call
result = await adapter.execute(*args, **kwargs)

# Post-Flight Accounting
spend_guard.record_usage(
    workspace_id=workspace_id,
    adapter=adapter_name,
    actual_cost=actual_cost,
    correlation_id=correlation_id,
    duration_ms=duration_ms
)
```

## 4. Telemetry Schema & Persistence
- Primary telemetry sink: `telemetry/accounting_log.json` (0600 file permissions, atomic file replacement).
- Aggregates surfaced via: `GET /api/v1/spend/metrics?workspace_id=...`.
- Real-time Redis/In-memory cache for fast zero-latency pre-flight budget checks.
