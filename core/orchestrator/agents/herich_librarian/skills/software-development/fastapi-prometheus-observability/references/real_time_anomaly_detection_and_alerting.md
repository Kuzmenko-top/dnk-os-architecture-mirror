# Real-Time Anomaly Detection & Advanced Alerting Engine Architecture

Guide for implementing streaming anomaly detection algorithms, dynamic threshold auto-tuning, composite alerting rules, and multi-channel alert dispatchers in production FastAPI applications.

## 1. Streaming Anomaly Detection Algorithms

### Statistical & Forecasting Detectors

1. **Z-Score Detector**:
   - Computes standard score: $z = \frac{x - \mu}{\sigma}$.
   - Anomaly flag triggered when $|z| > \text{threshold}$ (typically 3.0 or calibrated by sensitivity).
   - Anomaly score calculated as $\min(1.0, \frac{|z|}{\text{threshold} \times 1.5})$.

2. **IQR (Interquartile Range) Outlier Detector**:
   - Calculates $Q1$ (25th percentile), $Q3$ (75th percentile), and $IQR = Q3 - Q1$.
   - Bounds: $\text{Lower} = Q1 - k \times IQR$, $\text{Upper} = Q3 + k \times IQR$.
   - Suitable for non-normal or skewed metric distributions (e.g. latency percentiles, queue depth).

3. **Holt-Winters Forecasting Detector**:
   - Triple exponential smoothing capturing level $\alpha$, trend $\beta$, and seasonality $\gamma$.
   - Compares actual metric value $y_t$ against forecasted $\hat{y}_t$.
   - Anomaly score proportional to relative residual error $\frac{|y_t - \hat{y}_t|}{\sigma_{\text{residual}}}$.

4. **Lightweight Isolation Forest**:
   - Tree-based isolation partitioning data points across metric feature spaces.
   - Points isolated at shallower tree depths are assigned higher anomaly scores.

5. **Ensemble Anomaly Detector**:
   - Combines normalized scores from multiple algorithms using weighted averaging or max-voting.
   - Reduces false positives by requiring consensus across statistical and forecasting detectors.

---

## 2. Dynamic Threshold Auto-Tuning Engine

- Calculates rolling statistics over sliding time windows (e.g., rolling 24h / 7d).
- Evaluates percentiles ($p_{10}, p_{50}, p_{90}$), mean, and standard deviation.
- Dynamically adjusts bounds based on noise level:
  $$\text{Sensitivity} = \text{clamp}(0.95 - 0.5 \times \frac{\sigma}{\mu}, 0.50, 0.95)$$
- Prevents false-positive alert fatigue during high-volatility operational periods.

---

## 3. Composite Alerting & Deduplication

### Composite Alert Rules
Evaluates boolean expressions combining multiple metric thresholds with `AND` / `OR` logical operators:
```json
{
  "and": [
    {"metric": "error_rate", "operator": "gt", "value": 0.05},
    {"metric": "latency_p95", "operator": "gt", "value": 500.0}
  ]
}
```

### Cooldown & Deduplication
- Tracks recent alert timestamps per workspace/rule combination.
- Suppresses duplicate alert triggers occurring within the configured cooldown period (e.g., 300 seconds).

---

## 4. Multi-Channel Alert Dispatcher

Dispatches triggered alerts concurrently across configured endpoints:
- **Telegram**: Webhook request to Telegram Bot API `sendMessage`.
- **Slack**: Incoming Webhook payload formatted with markdown blocks and color-coded severity.
- **PagerDuty**: Events v2 API payload for critical incidents.
- **Email**: SMTP / SendGrid delivery with alert summary and context metadata.

Skipped or disabled channels return explicit status markers (`skipped_disabled`, `failed`, `sent`).

---

## 5. Flap Detection, Auto-Healing Playbooks & Safety Circuit Breakers

### Flap Prevention
- Tracks metric breach history within evaluation sliding windows.
- If status alternates rapidly between normal and breached within the window (exceeding `max_flaps_per_window`), the incident transitions to `FLAPPING` state rather than toggling state endlessly.
- Suppresses redundant alert storms while flapping is active.

### Automated Remediation Playbooks
- Executes automated corrective playbooks when incidents enter critical or high severity:
  - `restart_service`: Bounded container/process restart.
  - `drain_traffic` / `reroute`: Adjust routing weight in mesh router or load balancer.
  - `purge_cache`: Evict expired/heavy keyspaces.
  - `scale_replicas`: Incremental horizontal scaling (+1 replica up to max cap).
  - `trip_circuit_breaker`: Isolate failing mesh node or upstream adapter.

### Remediation Guardrails & Circuit Breakers
- **Cooldown Window**: Requires minimum duration (e.g., 300s) between successive executions for the same service and action.
- **Max Retries & Exponential Backoff**: Limits retries (e.g., max 3) with backoff multiplier before marking remediation `FAILED_MAX_RETRIES`.
- **Flap Lock Suppression**: Blocks automated execution if the underlying incident is flagged as `FLAPPING`.

---

## 6. Implementation & Model Mapping Pitfalls

1. **ORM Models Used Outside DB Session**: When ORM models (`HealthMetricRule`, `SystemIncident`, `RemediationAction`) are instantiated in memory or unit tests without an active SQLAlchemy session flush, implement explicit `__init__(self, **kwargs)` with default ID generation (`inc_<uuid>` or `act_<uuid>`) to prevent `AttributeError` on detached access.
2. **Threshold Field Compatibility**: When mapping incoming API payloads (e.g., `threshold`) to split ORM fields (`warning_threshold`, `critical_threshold`), compute defaults (`critical_threshold = threshold`, `warning_threshold = threshold * 0.8`) to ensure backwards compatibility with single-threshold clients.
3. **Incident Type & Severity Matching Hierarchy**: In auto-healing playbooks and remediation executors, policies may be registered with specific severities (`HIGH`, `CRITICAL`), wildcard `ANY` (`*`, `ALL`), or metric names. Ensure policy matchers implement severity tier matching (e.g., policies configured for `HIGH` match both `HIGH` and `CRITICAL` incidents), normalize case sensitivity (`pt.upper()`), and support case-insensitive playbook handler lookups (e.g., `RESTART_SERVICE` vs `restart_service`) to prevent unintended `SKIPPED` status.

