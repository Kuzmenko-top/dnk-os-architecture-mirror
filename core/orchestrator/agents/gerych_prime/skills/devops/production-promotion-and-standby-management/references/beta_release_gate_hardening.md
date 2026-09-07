# Beta Release Gate & Hardening Protocol

## Overview
When transitioning from local verification (E2E / synthetic tests) to a public or private Beta release candidate, an explicit **Feature Moratorium** is instituted. No new features may be added. All engineering velocity shifts to hardening across seven operational dimensions.

## The 7 Hardening Dimensions & Acceptance Criteria

### 1. Real Adapters (Priority 1)
- **Goal:** Replace synthetic mock/simulation adapters with real production providers under constrained quotas.
- **Scope:** Real GPU endpoints (BiRefNet, IC-Light, FLUX.1), ASR (WhisperX test clip), Remotion Lambda compilation (single 9:16 vertical render), and Shopify Admin API (`stagedUploadsCreate` + `fileCreate`).
- **Acceptance:**
  - Smoke tests execute against live endpoints with zero mock fallback.
  - Telemetry logs demonstrate authentic HTTP status codes, payload sizes, and transit latency.
  - Active SpendGuard budget caps enforce hard stop limits to eliminate runaway cloud costs.

### 2. Secrets Vault & Bundle Hygiene (Priority 1A)
- **Goal:** Zero leaked credentials, zero client-exposed secrets, fail-closed configuration.
- **Requirements:**
  - All secret keys retrieved strictly at runtime via `dnk_secrets_vault` or central Secret Manager.
  - Zero `process.env` secrets or `NEXT_PUBLIC_*` credential leaks in client bundles.
  - Non-destructive key rotation without requiring production redeploys.
  - **Fail-Closed Invariant:** Missing environment variables or vault keys must raise explicit HTTP 412/503 Precondition Failed / Service Unavailable errors. Silent fallback to mocks in release mode is strictly forbidden.
- **Acceptance:**
  - Static bundle audit verifies 0 API keys/tokens in `apps/web` or frontend static artifacts.
  - Launching without secrets yields an immediate clean failure response rather than mock data.

### 3. SSRF Filter & Ingestion Containment (Priority 1B)
- **Goal:** Protect URL ingestion endpoints (video, image downloads) against intranet access, loopback probing, and denial of service.
- **Requirements:**
  - Strict host allowlist for media ingestion (e.g. TikTok, Instagram, YouTube, Telegram, Shopify CDN).
  - Explicit blocklist for private, loopback, and link-local IP spaces: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`, IPv6 equivalents (`::1`, `fc00::/7`).
  - Strict limits: max payload size (e.g. 150MB), max duration, bounded connection timeout (e.g. 15s).
- **Acceptance:**
  - Requests targeting `http://127.0.0.1` or `http://192.168.x.x` are rejected before network socket dispatch.
  - Allowlisted domains stream through; non-allowlisted domains reject with clear structured error payloads.

### 4. Idempotency for External Sync (Priority 2)
- **Goal:** Prevent duplicate asset creation in remote CDNs or external services on network retry.
- **Requirements:**
  - Deterministic `X-Idempotency-Key` (e.g., `SHA256(asset_bytes + canvas_id + revision)`).
  - Key deduplication cache with TTL in Redis.
  - If a key has already completed processing, return the existing remote resource ID (e.g., Shopify `media.id`).
- **Acceptance:**
  - Retrying an identical sync operation does not spawn duplicate files in the CDN.
  - Logs register an explicit `idempotency hit`.

### 5. Observability & Spend Tracking (Priority 3)
- **Goal:** Comprehensive distributed tracing, latency profiling, and cost attribution.
- **Requirements:**
  - Client-originated `X-Correlation-ID` propagated through the entire stack (Gateway -> Backend -> Workers -> Storage).
  - Structured log schema: `correlation_id`, `agent`, `action`, `latency_ms`, `cost_usd`, `status`.
  - Metrics tracking: p95/p99 latency per agent, spend per workspace/tenant, failure rate.
- **Acceptance:**
  - Any given request can be traced end-to-end via a single correlation ID.
  - Dashboard surfaces real-time p95/p99 latency and per-workspace spend breakdown.

### 6. Operational Limits & Resilience (Priority 4)
- **Goal:** Protection against traffic surges, cascading failures, and hung worker processes.
- **Requirements:**
  - Redis-backed rate limiting per workspace / IP.
  - Hard timeouts on background tasks (e.g. 120s for video rendering/analysis).
  - Dead-Letter Queue (DLQ) for failed jobs with bounded exponential backoff retry policies.
- **Acceptance:**
  - Exceeding the rate limit returns HTTP 429 Too Many Requests with informative retry headers.
  - Timed-out jobs move cleanly to the DLQ and communicate failure status to the user.

### 7. Concurrency Stress & Collaborative Editing (Priority 5)
- **Goal:** Verify Optimistic Concurrency Control (OCC) and reconnection delta replay.
- **Scenario:**
  - Concurrent mutations on identical nodes from multiple sessions.
  - Temporary network disconnection during active canvas editing.
- **Acceptance:**
  - OCC versioning guarantees that only the valid sequential revision is committed; conflicting mutations raise conflict signals.
  - Upon reconnection, pending delta queues are flushed and synchronized to a consistent state.
