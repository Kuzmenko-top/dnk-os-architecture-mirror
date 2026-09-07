---
name: predictive-capacity-planning
description: "Use when forecasting capacity, load spikes, or autoscaling."
version: 1.1.0
author: Gerych Core + Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [capacity-planning, forecasting, holt-winters, autoscaling, anomaly-detection, queue-analytics, cost-optimization]
    category: devops
    requires_toolsets: [terminal]
---

# Predictive Capacity Planning, ML Forecasting & Auto-Scaling

Standard guide for architecting predictive telemetry forecasting, queue anomaly detection, and horizontal auto-scaling recommendations in distributed systems.

## When to Use

Use this skill when:
- Designing predictive capacity planning engines with time-series forecasting (CPU, RAM, GPU, IOPS, token throughput).
- Implementing Holt-Winters / Double Exponential Smoothing and Linear Trend Extrapolation with confidence quantiles ($p50, p90, p99$).
- Detecting queue anomalies (Z-score queue depth spikes, worker starvation/stall, dead-letter rates, $p95$ latency outliers).
- Building autonomous horizontal auto-scaling recommenders (proactive lookahead scaling, scale-in bounds, cost delta estimation).
- Optimizing infrastructure spend (Spot vs On-Demand node ratio analysis and idle resource reclamation).

---

## 1. Multi-Horizon Time-Series Forecasting Architecture

### 1.1 Mathematical Models
1. **Holt-Winters / Double Exponential Smoothing**:
   - Level update: $L_t = \alpha y_t + (1 - \alpha)(L_{t-1} + T_{t-1})$
   - Trend update: $T_t = \beta (L_t - L_{t-1}) + (1 - \beta) T_{t-1}$
   - Forecast: $\hat{y}_{t+h} = L_t + h \cdot T_t$
   - Residual variance update: $\sigma^2_t = \gamma (y_t - \hat{y}_t)^2 + (1 - \gamma) \sigma^2_{t-1}$
2. **Linear Trend Extrapolation**:
   - Slope $m = \frac{N \sum xy - \sum x \sum y}{N \sum x^2 - (\sum x)^2}$, Intercept $b = \frac{\sum y - m \sum x}{N}$
   - Goodness-of-fit $R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$

### 1.2 Quantile Estimation & Uncertainty Corridors
Quantile estimation uses normal distribution multipliers with monotonic expansion over forecast horizon $h$:
- $p50$: $\max(0.0, \hat{y}_{t+h})$ ($z_{50} = 0.0$)
- $p90$: $\max(p50, \hat{y}_{t+h} + 1.28155 \cdot \sigma_h)$ ($z_{90} \approx 1.282$)
- $p99$: $\max(p90, \hat{y}_{t+h} + 2.32635 \cdot \sigma_h)$ ($z_{99} \approx 2.326$)
- Time expansion factor: $\sigma_h = \sigma \cdot \sqrt{1 + 0.05 \cdot h}$

### 1.3 Standard Forecasting Horizons
- **15m**: 15 steps @ 1-min intervals (real-time reactive / short-term proactive spikes).
- **1h**: 12 steps @ 5-min intervals (task queue batch scheduling).
- **24h**: 24 steps @ 1-hour intervals (diurnal shift planning).
- **7d**: 14 steps @ 12-hour intervals (weekly budget & capacity reservations).

---

## 2. Queue Analytics & Anomaly Detection

### 2.1 Anomaly Classes & Detection Rules
1. **Queue Depth Spikes ($z$-score)**:
   - Compute rolling mean $\mu$ and standard deviation $\sigma$ over sliding window (e.g. 20 data points).
   - Flag spike when $z = \frac{x - \mu}{\sigma} \ge 3.0$ and depth $> 10$.
2. **Starvation / Worker Stall**:
   - Trigger when $\text{incoming\_rate} > 0.0$, $\text{processing\_rate} == 0.0$, and $\text{queue\_depth} > 10$.
3. **Dead-Letter Queue (DLQ) Outliers**:
   - Trigger critical alert immediately when $\text{dead\_letter\_count} > 0$ or dead-letter rate exceeds baseline.
4. **Latency Outliers**:
   - Flag when $p95 > \text{SLO threshold}$ or when $p95 > 2.5 \times \text{moving average}$.

---

## 3. Horizontal Auto-Scaling & Cost Optimization

### 3.1 Proactive Scaling Rule
```python
def compute_target_replicas(current_replicas: int, current_load: float, predicted_p90: float, target_load: float, min_rep: int = 1, max_rep: int = 100) -> int:
    effective_load = max(current_load, predicted_p90)
    if target_load <= 0:
        return current_replicas
    raw = math.ceil(current_replicas * (effective_load / target_load))
    return max(min_rep, min(max_rep, raw))
```

### 3.2 Spot vs On-Demand Strategy
- **Worker Pools**: Migrate up to 70-80% of stateless background worker capacity to Spot/Preemptible instances.
- **Core Orchestrators**: Keep critical consensus/orchestration services 100% On-Demand.
- **Cost Calculation**: $\Delta_{\text{savings}} = (C_{\text{on\_demand}} - C_{\text{spot}}) \times N_{\text{spot\_eligible}}$

---

## 4. Verification & Testing Standards

- Verify that $p50 \le p90 \le p99$ strictly holds across all future forecast steps.
- Ensure zero DivisionByZero errors on constant telemetry time series ($\sigma = 0$).
- Test starvation alerts by simulating stopped workers with non-zero incoming queue traffic.
- Validate cost delta calculations against on-demand and spot pricing matrices.

---

## 5. REST API & WebSocket Integration Patterns

1. **Ingestion Endpoints**: Return `201 Created` with the persisted record dictionary on telemetry/snapshot ingestion.
2. **Dual Telemetry Support**: Accept both DB-fetched telemetry history and client-provided `historical_values` array in forecast generation endpoints to support ad-hoc evaluation.
3. **Cost Schema Aliases**: Maintain both `potential_savings_usd` and `monthly_savings_usd` attributes in cost reports to support REST, CLI, and Web UI schema consumers seamlessly.
4. **Dual WebSocket Endpoint Mounting**: Register WebSocket routers at both `/capacity-analytics/ws` and `/api/v1/capacity-analytics/ws` to avoid gateway path rewriting issues.

---

## Pitfalls & Best Practices

1. **Monotonic Quantile Corridor**: When $\sigma$ is large, ensure $p50 \ge 0$, $p90 \ge p50$, and $p99 \ge p90$ by explicit bounding.
2. **Cold-Start Fallbacks**: If fewer than 5 historical data points exist, fall back to moving average or linear extrapolation rather than uncalibrated exponential smoothing.
3. **Flapping Prevention**: Enforce a cooldown window (e.g. 300s) on scale-in recommendations to prevent oscillatory thrashing.
4. **Router Path Alignment**: Double-check REST router status codes (`201` for ingestion, `200` for evaluations) and ensure WebSocket endpoints handle broadcast disconnections gracefully.

