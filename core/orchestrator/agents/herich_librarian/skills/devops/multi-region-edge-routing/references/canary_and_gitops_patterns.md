# --- DNK-MRH-HEADER ---
# mrh_id: "references_canary_and_gitops_patterns"
# purpose: "Reference patterns for ArgoCD Rollouts, Flux CD, Statistical Canary Analysis & Automated Rollback"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

# Progressive Canary & GitOps Orchestration Patterns

## 1. ArgoCD Rollout CRD (`argoproj.io/v1alpha1`)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: dnk-api-rollout
  namespace: production
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: dnk-api-green
      stableService: dnk-api-blue
      trafficRouting:
        nginx:
          stableIngress: dnk-api-ingress
          additionalIngressAnnotations:
            canary-by-header: X-Canary
      steps:
      - setWeight: 1
      - pause: {duration: 2m}
      - setWeight: 5
      - pause: {duration: 5m}
      - setWeight: 25
      - pause: {duration: 10m}
      - setWeight: 50
      - pause: {duration: 15m}
      - setWeight: 100
      analysis:
        templates:
        - templateName: latency-and-error-rate-check
        args:
        - name: service-name
          value: dnk-api-green
```

## 2. Flux CD Kustomization

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: dnk-api-gitops
  namespace: flux-system
spec:
  interval: 1m
  path: ./k8s/production
  prune: true
  sourceRef:
    kind: GitRepository
    name: dnk-core-repo
```

## 3. Statistical Analysis Decision Matrix

| Metric / Test | Condition | Action |
|---|---|---|
| **Mann-Whitney U** | $p < 0.05 \land \Delta_{\text{latency}} > 10\%$ | `rollback` (Statistically significant latency degradation) |
| **Welch's T-Test** | $p < 0.05 \land \Delta_{\text{latency}} > 10\%$ | `rollback` (Parametric distribution degradation) |
| **Error Rate Delta** | $\text{Err}_{\text{candidate}} - \text{Err}_{\text{baseline}} > 0.5\%$ | `rollback` (Excessive failure spike) |
| **Sample Size** | $N < 10$ samples per distribution | `wait` (Insufficient statistical power) |
| **Consecutive Probes** | Failure streak $\ge 3$ consecutive checks | `rollback` (Automated Liveness/Readiness failure) |
| **All Green** | $p \ge 0.05 \land \Delta_{\text{latency}} \le 10\% \land \Delta_{\text{err}} \le 0.5\%$ | `promote` (Candidate verified healthy) |
