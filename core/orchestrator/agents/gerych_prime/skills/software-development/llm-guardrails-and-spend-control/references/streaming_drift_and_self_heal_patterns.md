# Streaming Statistical Drift & Self-Healing Window Hygiene

This reference documents the architecture and mathematical invariants for real-time drift detection and closed-loop self-healing in LLM production runtimes.

## 1. Welford's Algorithm for $O(1)$ Memory Baselines

Storing generation history in memory creates unbounded memory leaks in continuous agent servers. Welford's algorithm computes running mean and sample variance in a single pass with numerical stability.

### Mathematical Invariants
Given incoming sample $x_n$ at count $n$:

$$\delta = x_n - \mu_{n-1}$$
$$\mu_n = \mu_{n-1} + \frac{\delta}{n}$$
$$\delta_2 = x_n - \mu_n$$
$$M_{2,n} = M_{2,n-1} + \delta \cdot \delta_2$$
$$s_n^2 = \frac{M_{2,n}}{n - 1} \quad (\text{for } n > 1)$$

### Exponential Moving Average (EMA) for Concept Drift
To make the baseline sensitive to recent distribution shifts while dampening transient spikes:

$$\mu_{\text{ema}} \leftarrow (1 - \alpha) \cdot \mu_{\text{ema}} + \alpha \cdot x_n$$
$$\sigma^2_{\text{ema}} \leftarrow (1 - \alpha) \cdot \left(\sigma^2_{\text{ema}} + \alpha \cdot (x_n - \mu_{\text{ema}})^2\right)$$

Recommended $\alpha \in [0.05, 0.2]$ (e.g., $\alpha = 0.1$).

## 2. Metrics Tracked in Online Baselines
- **Shannon Entropy**: Measures token diversity; sharp drops indicate repetition loops or mode collapse.
- **Type-Token Ratio (TTR)**: Vocabulary richness ($V / N$).
- **Character / Token Length**: Detected via standard score ($Z$-score) against baseline standard deviation:
  $$Z = \frac{|L_{\text{current}} - \mu_L|}{\max(\sigma_L, \text{floor})}$$
- **JSON Structural Validity Rate**: Ratio of valid JSON parses over total samples.

## 3. Window Poisoning in Auto-Healing Loops (Crucial Pitfall)

In multi-attempt self-healing loops (`GeminiSelfHealer`):
```python
for attempt in range(1, max_retries + 2):
    raw_output = invoke_model(current_params)
    monitor.record_response(raw_output)
    report = monitor.evaluate_drift(...)
    
    if is_healthy(report, raw_output):
        return raw_output
        
    # CRITICAL: Before retrying, remove the unhealthy attempt from current_window!
    if monitor.current_window:
        monitor.current_window.pop()
        
    current_params = adapt_params(report)
```

**Why this is mandatory:**
If attempt 1 produces a collapsed repetition loop (e.g. 500 characters of `"stuck stuck..."`), its presence in `monitor.current_window` artificially shifts the window's mean length and drops its entropy. Even if attempt 2 generates a perfect response, the window still averages attempts 1 and 2 together, failing health checks again and exhausting retry budgets.

## 4. Dual Prometheus & Visual Shell Telemetry Architecture

To achieve zero-overhead observability in production without running separate scraper daemons:

### Prometheus Text Exposition Integration
Domain exporters (`GeminiTelemetryExporter`) should format metrics adhering strictly to Prometheus line protocol:
- Standard headers: `# HELP <metric> <doc>` and `# TYPE <metric> <type>` (gauge, counter).
- Deterministic label formatting: `{label="val",...}`.
- Single scrape endpoint: Instead of spinning up a standalone HTTP port, register domain exporters into the centralized `MetricsRegistry` (`register_drift_exporter(exporter)`). The main `/metrics` endpoint executes `metrics_registry.export_metrics()`, seamlessly concatenating core Prometheus client metrics with domain exporter blocks.

### Visual Shell JSON Telemetry
Provide an ergonomic JSON endpoint (`/api/v1/analytics/drift/telemetry`) consumed by UI dashboards (DNK Visual Shell or Grafana JSON Data Source) reporting:
- `health_status`: Categorical enum (`HEALTHY`, `WARNING`, `CRITICAL`).
- `welford_stats` / `welford_online`: Summary of running mean, stdev, sample count.
- `ema_stats`: Instantaneous exponential moving average.
- `self_healing`: Aggregated counts of auto-recoveries, fallback switches, and retries.
- `active_alarms`: Live list of triggered drift alarms.

## 5. Zero-Cost Local Heuristic JSON Repair Protocol

Before escalating to expensive LLM retries or fallback models on JSON syntax corruptions, always execute an in-process heuristic repair step (`repair_json_string`):

1. **Direct Parse Probe**: Test raw input with standard `json.loads`.
2. **Markdown Codeblock Stripping**: Match ````(?:json)?\s*([\s\S]*?)\s*```` and extract the innermost payload.
3. **Outermost Bracket Bounding**: Locate first `{` or `[` and match with last `}` or `]` to slice away external chatter or preambles.
4. **Python Literal Normalization**: Replace `True` -> `true`, `False` -> `false`, `None` -> `null`.
5. **Trailing Comma Pruning**: Strip trailing commas preceding closing braces or brackets (`,\s*([}\]])` -> `\1`).
6. **Unquoted Key Quoting**: Quote bare alphanumeric keys (`([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:` -> `\1"\2":`).

If repair succeeds, return `LOCAL_JSON_HEAL` immediately ($< 1$ms execution, zero token spend). Only if local heuristics fail to parse should the healer trigger prompt modification with temperature dampening or escalate to `FALLBACK_MODEL`.

## 6. Defensive Telemetry Deserialization Invariant

Telemetry payloads generated from streaming or online accumulators can produce `null` fields prior to sample ingestion (e.g. `{"welford_stats": {"entropy": null}}`).
Consumers MUST NOT use direct chained `.get()` calls like `data.get("welford_stats", {}).get("entropy", {}).get("mean")`, because `.get("entropy", {})` returns `None` (not `{}`) when the key is explicitly mapped to `None`.

**Mandatory Safe Pattern**:
```python
welford_stats = data.get("welford_stats") or {}
entropy_stats = welford_stats.get("entropy") or {}
entropy_mean = entropy_stats.get("mean", 0.0)
```

## 7. Multi-Provider & Vendor-Agnostic Portability

The core mathematical and heuristic algorithms are completely vendor-agnostic and operate over arbitrary LLM output strings (Anthropic Claude, DeepSeek, Grok, Meta LLaMA, Moonshot/Kimi):
1. **Universal Text Analytics**: Shannon entropy, Type-Token Ratio, character counts, and Welford/EMA variance computations are tokenizer-independent string operations.
2. **Universal JSON Repair**: Syntax glitches (markdown blocks, Python booleans, trailing commas) occur across all transformer models; local repair resolves them identically regardless of model origin.
3. **Dynamic Fallback Ladder Resolution**:
   - Rather than hardcoding vendor-specific models (e.g. `gemini-1.5-flash`), query the runtime credential store/vault (`ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, `XAI_API_KEY`, `OPENAI_API_KEY`).
   - Construct an active fallback ladder matching available provider tokens, avoiding hard crashes due to missing keys for a static fallback.

## 8. End-to-End Live Verification Pattern

To verify online baseline convergence, zero-cost JSON repair, and telemetry export without mock server overhead or test server hangs:
1. **Simulate Online Baseline Convergence**: Feed 5-10 nominal healthy samples through `record_response` to seed Welford mean and variance.
2. **Exercise Heuristic Repair**: Pass malformed JSON (wrapped in markdown fences with Python booleans and trailing commas) to `execute_with_healing` with `expect_json=True`. Assert status `LOCAL_JSON_HEAL` and latency $< 2$ms.
3. **Simulate Mode Collapse & Recovery**: Inject a collapsed repetition loop (e.g. `"stuck stuck stuck..."`), assert entropy drop, and verify prompt modification adjustment.
4. **Scrape Telemetry Endpoints**: Verify that both Prometheus text output contains valid exposition lines (`# HELP`, `# TYPE`, metric values) and JSON telemetry returns HTTP 200 with non-null `welford_online` and `health_status`.
