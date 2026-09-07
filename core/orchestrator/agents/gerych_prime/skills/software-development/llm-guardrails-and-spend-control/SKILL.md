---
name: llm-guardrails-and-spend-control
description: "Manage LLM guardrails, SpendGuard limits, and fallbacks with token-based pricing, telemetry, and secrets masking."
version: 0.3.0
author: "Maksym Kuzmenko (Maxim), Hermes Agent"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [llm, guardrails, spendguard, telemetry, fallbacks, compliance]
    related_skills: [dnk-swarm-orchestration, systematic-debugging]
---

# LLM Guardrails & Spend Control Skill

Guidelines for implementing robust LLM safety filters, brand compliance audits, budget protections (SpendGuard), dynamic telemetry, and deterministic fallbacks.

## When to Use
- Implementing or modifying LLM pipelines that require strict budgetary boundaries (SpendGuard).
- Designing brand compliance checkers, safety filters, or plagiarism/similarity guards.
- Writing deterministic templates to act as reliable fallback generators when LLM limits or budgets are exceeded.
- Setting up LLM telemetry, Langfuse export pipelines, and dashboard reporting.

## Prerequisites
- Active project virtual environment (`$VIRTUAL_ENV` = `.venv`).
- Familiarity with Zod / TypeScript schemas for structured LLM outputs and telemetry metrics.

## How to Run
- Run test suites for LLM pipelines using `terminal` with `pnpm test` or `pytest`.
- Audit budget tracking logs / test mocks for SpendGuard execution and metrics calculation.

## Quick Reference
- **Sentence-Level Splitting:** Avoid paragraph-level checks to prevent unverified claim overlap or false positives.
- **Stem/Prefix Matching:** Support Ukrainian/inflected languages by matching prefixes (first 5 characters for words > 5 letters).
- **Token-Based & Adapter-Based SpendGuard:** SpendGuard must compute high-precision costs using model-specific token pricing ($/1k tokens) or fixed adapter unit pricing (BiRefNet $0.02, IC-Light $0.03, FLUX.1 $0.05, WhisperX $0.01/min, Remotion $0.10) and perform pre-flight checks (`preFlightCheck`) *before* initiating network calls to fail closed.
- **Workspace Daily Budget Caps:** Support daily per-workspace budget limits ($10.00/workspace/day) with multi-tier alerts: 80% threshold warning and 100% hard block.
- **Correlation ID Tracking:** Every outbound AI request must be bound to a unique `correlation_id` across logging and telemetry.
- **Telemetry & Logs Sanitization:** Always sanitize secrets (Bearer tokens, passwords, hex keys >32 chars) in telemetry logs.
- **Resilient Exporter Fallback:** Telemetry should dispatch to remote collectors (Langfuse/OpenTelemetry) wrapped in a fallback decorator that diverts to a local JSON event log if remote delivery fails.
- **Zero-Click Cognitive Memory Hooks (SCONES Validation Middleware):** Intercept all memory storage writes (`add_memory`, `scones_add_memory`) at the engine level to validate schema, numerical ranges (`importance` in `[0.0, 1.0]`), and prevent path leaks (`no_hardcoded_user_paths`). In default mode, record violations in entry metadata (`_expectation_violations`) and warn; in strict mode or tool wrappers, surface structured validation errors (`validation_error`) allowing agent self-repair without crashing.
- **Online Welford & EMA Drift Baselines:** Maintain streaming statistics (entropy, length, TTR) with $O(1)$ memory using Welford's algorithm and Exponential Moving Average (EMA) rather than retaining full historical arrays in memory.
- **Zero-Cost Heuristic Local JSON Repair:** Prior to initiating expensive LLM retries or model switches, run an in-process heuristic repair pass (`repair_json_string`) to strip markdown fences, coerce Python booleans (`True`/`False`), prune trailing commas, and quote keys. If local parse succeeds, complete in $<1$ms without consuming additional tokens.
- **Defensive Telemetry Deserialization:** When consuming online baseline telemetry, guard against explicit `null` fields with null-coalescing expressions: `(data.get("welford_stats") or {}).get("entropy") or {}`.
- **Self-Healing Window Hygiene:** When retrying failed/unhealthy generations in closed-loop self-healers, always evict the rejected attempt from the monitor's rolling window (`current_window.pop()`) before retrying.
- **Dual Prometheus & Visual Shell Telemetry:** Export model drift and self-healing telemetry concurrently via standard Prometheus text exposition format (`# HELP`, `# TYPE`) joined into the central `MetricsRegistry.export_metrics()` and structured JSON (`/drift/telemetry`) for UI/Grafana visualization.
- **Vendor-Agnostic Self-Healing & Dynamic Fallback:** Real-time drift detection (Shannon entropy, TTR, Welford/EMA variance) and zero-cost heuristic repair operate on raw generation text independent of model provider (Claude, DeepSeek, Grok, LLaMA, Kimi). Fallback ladders must dynamically resolve against available workspace API keys rather than assuming a single static vendor.
- **Dashboard Metric Aggregates:** Compute p50/p95/p99 latencies using interpolation on sorted arrays, along with rolling hourly/daily/weekly spend.

## Procedure
1. **Sentence Isolation:** Split text using boundary punctuation regexes (e.g., `(?<=[.!?])\s+`) to inspect claims at the individual sentence level.
2. **Token-Based Cost Calculation:** Implement precise calculations for pricing models:
   $$\text{Total Cost} = \left(\frac{\text{Tokens In}}{1000} \times \text{Input Price Per 1k}\right) + \left(\frac{\text{Tokens Out}}{1000} \times \text{Output Price Per 1k}\right)$$
3. **Spend Verification:** Initialize SpendGuard with a strict limit. Verify cumulative expenses and block LLM invocations with a precise exception (e.g., `"Spend limit of $X.YYY exceeded!"`) if limits are breached.
4. **Telemetry Logging & Export:** Send metric records containing `requestId`, `modelId`, `latencyMs`, `tokensIn`, `tokensOut`, `spendTracked`, and `success` to a central orchestrator (such as Langfuse or a sanitized Local JSON file fallback).
5. **Secrets Masking:** Before writing error codes or log strings, replace hex keys (32+ chars), authorization headers, and credential query params with redacted placeholders.
6. **Dashboard Metric Aggregation:** Compile rolling window totals (last hour, day, week), average latencies, and percentiles (p50/p95/p99) to provide robust monitoring feeds.
7. **Deterministic Cascade:** Ensure that any LLM error, budget breach, or safety rejection cascades gracefully to a deterministic rule-based or template-based generator.
8. **Verification Gate:** Confirm the complete system passes standard typecheck, build, and test runners.

## Pitfalls
- **Paragraph-level matching:** Matching full paragraphs against facts yields oversized `unverifiedClaims` or incorrect exclusions. Always split to sentences.
- **Language inflection:** Direct string matching fails in inflected languages like Ukrainian. Use prefix stem matching for words longer than 5 letters.
- **Raw logs disclosure:** Never write raw prompts, responses, or API keys directly to public test logs or console output; redact or mock all sensitive elements.
- **Array interpolation sorting:** When computing p50/p95/p99 latencies, always sort the numeric array *before* calculating the index or interpolation weights.
- **Unvalidated Memory Ingestion:** Storing raw LLM memory episodes without schema and path hygiene checks risks poisoning cognitive recall with malformed keys or leaking local filesystem paths (`/Users/...`, `/home/...`). Always intercept writes with a zero-click expectation validator.
- **Window Poisoning in Self-Healing Loops:** In retry loops evaluating health or statistical drift against a rolling window, failing to pop rejected attempts from the monitor window causes the unaccepted generation to pollute subsequent window averages (e.g. dragging down entropy or inflating length z-scores), resulting in false-positive rejections of valid retries.
- **Burning LLM Tokens on Syntax Glitches:** Immediately retrying with the LLM API on malformed JSON outputs without attempting local regex-based heuristic repair (`repair_json_string`) introduces unnecessary round-trip latency (>1.5s) and token spend. Fast heuristic repair resolves markdown codeblock wrapping, trailing commas, and Python boolean literals in $<1$ms.
- **Chained Dict `.get()` on Nullable Telemetry Keys:** Using chained `.get("key", {})` on nested telemetry dictionaries where an intermediate key exists but has a `None` value (such as uninitialized online Welford statistics) crashes with an `AttributeError`. Always use null-coalescing patterns: `(data.get("welford_stats") or {}).get("entropy") or {}`.
- **Static Single-Vendor Fallback Ladder:** Hardcoding vendor-specific fallback models (e.g. falling back to Gemini when only Anthropic or DeepSeek API keys are provisioned) causes unhandled authentication crashes during model escalation. Ensure fallback ladders query available provider credentials dynamically.

## Verification
- Validate Zod/TS schema compatibility for guard compliance reports and telemetry records.
- Ensure test suites run with 100% green results: `pnpm test` / `pytest`.

## See Also
- [001E-PROD-PHASE-2 Spec Reference](references/001e_prod_phase_2_spec.md) — Detailed type definitions, pricing configurations, and secrets masking code patterns.
- [Multi-Adapter SpendGuard Matrix](references/multi_adapter_spend_guard_matrix.md) — Gate 1 adapter pricing matrix (BiRefNet, IC-Light, FLUX.1, WhisperX, Remotion, Shopify), daily workspace budget cap, and correlation tracking.
- [Zero-Click Memory Guardrails](references/zero_click_memory_guardrails.md) — SCONES Expectation Hook architecture, path sanitization, and structured validation recovery patterns.
- [Streaming Drift & Self-Healing Patterns](references/streaming_drift_and_self_heal_patterns.md) — Welford & EMA $O(1)$ streaming baseline calculations, entropy collapse detection, and retry window eviction hygiene.
