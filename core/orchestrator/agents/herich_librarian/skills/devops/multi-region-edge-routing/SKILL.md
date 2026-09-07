---
name: multi-region-edge-routing
description: Architect multi-region cloud deployment, GSLB, edge rules & canary splitting.
version: "1.1.0"
author: "DNK-e.com Maksym"
license: "MIT"
metadata:
  hermes:
    tags: ["multi-region", "gslb", "edge-routing", "canary-deployment", "blue-green", "istio", "nginx-ingress"]
    related_skills: ["fastapi-prometheus-observability", "workspace-realtime-collaboration"]
---

# Multi-Region Deployment, Edge Routing & Global Load Balancing (GSLB)

This skill provides architecture patterns, health-scoring algorithms, edge worker generators, database replication monitoring strategies, and zero-downtime blue/green & progressive canary traffic splitting.

## When to Use

- Designing high-availability active-passive or active-active multi-region cloud topologies (AWS, GCP, Azure).
- Implementing DNS-based Global Server Load Balancing (GSLB) with automated failover.
- Deploying Edge Routing rules and generating CDN edge scripts (Cloudflare Workers, CloudFront Functions, GCP Cloud CDN).
- Tracking cross-region database logical replication lag and cache sync health.
- Implementing zero-downtime Blue/Green deployments and progressive Canary traffic shifting (1% -> 5% -> 25% -> 50% -> 100%) with Nginx Ingress or Istio Service Mesh.

## 📚 Reference Documentation

- Detailed worker scripts & SQL replication queries: `references/routing_and_replication.md`
- GitOps manifests (ArgoCD Rollout, Flux CD) & Statistical Canary decision matrix: `references/canary_and_gitops_patterns.md`

## 📐 Architecture Overview

```
[ Client Request ]
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ GLOBAL LOAD BALANCER (GSLB)                             │
│ (Route53 / Cloud DNS / Cloudflare DNS)                  │
└──────────────────────────┬──────────────────────────────┘
                           │ Health-Scored Routing
                           ▼
┌─────────────────────────────────────────────────────────┐
│ EDGE ROUTING LAYER                                      │
│ (Cloudflare Workers / CloudFront / GCP Cloud CDN)       │
└──────────────┬──────────────────────────┬───────────────┘
               │                          │
               ▼                          ▼
    ┌────────────────────┐     ┌────────────────────┐
    │  REGION A (Primary)│     │ REGION B (Failover)│
    │  (e.g., us-east-1) │     │ (e.g., eu-west-1)  │
    └──────────┬─────────┘     └──────────┬─────────┘
               │                          │
               └──── Cross-Region DB ─────┘
                    Logical Replication
```

---

## ⚡ 1. Region Management & Health Scoring

Maintain real-time health scores ($S \in [0, 100]$) per region based on synthetic liveness checks, latency, and error rates:

$$\text{HealthScore} = \max\left(0, 100 - (\text{Latency}_{p95\_ms} \times 0.1) - (\text{ErrorRate}_{\%} \times 5)\right)$$

### Region States:
- **`active`**: Health score $> 70$. Handles primary traffic.
- **`degraded`**: Health score between $30$ and $70$. Traffic throttled or routed to fallback.
- **`offline` / `maintenance`**: Health score $< 30$ or explicitly marked. Zero traffic routed.

---

## 🌐 2. Global Server Load Balancer (GSLB) Routing Strategies

1. **Latency-Based Routing**: Route client to the region with lowest RTT (Round Trip Time).
2. **Geolocation Routing**: Match client continent/country code directly to nearest regional cluster.
3. **Weighted Round-Robin**: Distribute traffic proportionally according to assigned regional weight vectors ($w_i$).
4. **Failover Priority**: Primary region serves 100% traffic; secondary region activated automatically when primary health score drops below threshold (e.g., $< 40$).

---

## 🔀 3. Edge Routing & Multi-Cloud Script Generation

Propagate edge match rules (e.g., path patterns, geo-headers, tenant IDs) to CDN edge workers.

### Cloudflare Worker Pattern (TypeScript / JS):
```javascript
export default {
  async fetch(request, env, ctx) {
    const country = request.headers.get("cf-ipcountry") || "US";
    const url = new URL(request.url);

    // Geo-routing match rule
    if (country === "EU" || country === "GB") {
      url.hostname = "eu-west-1.api.dnk-os.com";
      return fetch(url.toString(), request);
    }

    url.hostname = "us-east-1.api.dnk-os.com";
    return fetch(url.toString(), request);
  }
};
```

---

## 🔄 4. Cross-Region Data Replication Monitoring

Track logical replication lag for PostgreSQL Read Replicas and Redis Cross-Region Sync:

- **Thresholds**:
  - `healthy`: Lag $\le 5.0$ seconds.
  - `lagging`: $5.0\text{s} < \text{Lag} \le 30.0\text{s}$.
  - `broken`: Lag $> 30.0$ seconds or connection stream terminated.
- **GSLB Circuit Breaker**: Disallow failover promotion to a secondary region if its replication lag exceeds maximum allowed threshold (preventing dirty reads/data loss).

---

## 🚦 5. Zero-Downtime Blue/Green & Progressive Canary Traffic Splitting

Orchestrate smooth transitions between production environments (`blue` and `green`) using weighted canary splits:

### Progressive Canary Steps & Statistical Watchdog:
- Sequence: `1% -> 5% -> 25% -> 50% -> 100%`.
- Between each step, evaluate health probes (Liveness, Readiness, Startup) and custom SLO metrics (p95/p99 latency, error rate, saturation).
- **Statistical Canary Analysis**:
  - Compare baseline (Blue) and candidate (Green) latency samples via **Mann-Whitney U rank-sum test** or **Welch's T-test** ($p < 0.05$).
  - Calculate error rate delta $\Delta_{\text{err}} = \text{Err}_{\text{green}} - \text{Err}_{\text{blue}}$ and latency degradation % $\Delta_{\text{lat}} = \frac{p95_{\text{green}} - p95_{\text{blue}}}{p95_{\text{blue}}} \times 100$.
  - Recommendations: `promote`, `rollback` (if $\Delta_{\text{err}} > 0.5\%$ or $p < 0.05 \land \Delta_{\text{lat}} > 10\%$), `wait` (insufficient sample size), or `hold`.
- **Auto-Rollback Engine**: Instantly revert traffic to 100% active baseline if error rate exceeds threshold, consecutive probe failures exceed streak threshold, or statistical analysis triggers `rollback`.

### Ingress & Service Mesh Manifest Patterns:
1. **Nginx Ingress Canary**:
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: dnk-service-canary
     annotations:
       nginx.ingress.kubernetes.io/canary: "true"
       nginx.ingress.kubernetes.io/canary-weight: "25"
       nginx.ingress.kubernetes.io/canary-by-header: "X-Canary"
   ```
2. **Istio VirtualService Weighted Routing**:
   ```yaml
   apiVersion: networking.istio.io/v1alpha3
   kind: VirtualService
   metadata:
     name: dnk-service-vs
   spec:
     hosts: ["api.dnk-e.com"]
     http:
     - route:
       - destination:
           host: dnk-service-blue
         weight: 75
       - destination:
           host: dnk-service-green
         weight: 25
   ```

---

## ⚠️ Pitfalls & Implementation Notes

- **Split-Brain Prevention**: Always enforce single-leader write policies for database master nodes unless using conflict-free multi-master engines (e.g. Spanner / CockroachDB).
- **DNS TTL Propagation**: Keep GSLB DNS record TTL low ($10\text{s} - 30\text{s}$) to ensure rapid failover execution across global ISPs.
- **Edge Cache Invalidation**: When updating edge routing rules, emit purge cache requests to prevent stale edge routing logic.
- **Sticky Canary Sessions**: Always hash client identifier (e.g. user_id or IP) to maintain consistent candidate/baseline routing across subsequent requests during a progressive rollout.
