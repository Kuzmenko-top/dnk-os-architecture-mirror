# --- DNK-MRH-HEADER ---
# mrh_id: "references_001e_prod_phase_2_spec"
# purpose: "Reference Specification and Code Examples for SpendGuard and Telemetry Core (001E-PROD-PHASE-2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-04"
# --- END DNK-MRH-HEADER ---

# SpendGuard & Telemetry Specification (001E-PROD-PHASE-2)

This reference file contains verified TypeScript interface definitions and configuration structures implemented in `packages/video-audit-core` and `services/dnk_video_ai_creator/infrastructure/llm`.

## 1. SpendGuard Config & Default Models

```typescript
export interface ModelPricing {
  inputPricePer1k: number;
  outputPricePer1k: number;
}

export interface SpendGuardConfig {
  budgetLimit: number;
  modelPricing: Record<string, ModelPricing>;
}

export const DEFAULT_MODEL_PRICING: Record<string, ModelPricing> = {
  'gemini-2.5-pro': { inputPricePer1k: 0.0025, outputPricePer1k: 0.0075 },
  'gemini-2.5-flash': { inputPricePer1k: 0.00075, outputPricePer1k: 0.003 },
  'gemini-1.5-pro': { inputPricePer1k: 0.00125, outputPricePer1k: 0.005 },
  'gemini-1.5-flash': { inputPricePer1k: 0.000075, outputPricePer1k: 0.0003 },
  'claude-3-5-sonnet-20241022': { inputPricePer1k: 0.003, outputPricePer1k: 0.015 },
  'default': { inputPricePer1k: 0.001, outputPricePer1k: 0.002 },
};
```

## 2. Pre-Flight Check Pattern

```typescript
export interface PreFlightCheckResult {
  allowed: boolean;
  estimatedCost: number;
  newTotalSpend: number;
  reason?: string;
}

public preFlightCheck(
  tokensIn: number,
  tokensOut: number,
  model: string,
  currentSpend?: number
): PreFlightCheckResult {
  const estimatedCost = this.estimateCost(tokensIn, tokensOut, model);
  const baseSpend = currentSpend !== undefined ? currentSpend : this.currentSpend;
  const newTotalSpend = Number((baseSpend + estimatedCost).toFixed(6));

  if (newTotalSpend > this.config.budgetLimit) {
    return {
      allowed: false,
      estimatedCost,
      newTotalSpend,
      reason: `Pre-flight spend limit exceeded: Estimated cost $${estimatedCost.toFixed(4)} would bring total spend to $${newTotalSpend.toFixed(4)}, exceeding budget of $${this.config.budgetLimit.toFixed(4)}`,
    };
  }

  return { allowed: true, estimatedCost, newTotalSpend };
}
```

## 3. Telemetry and Analytics Schema

```typescript
export interface LlmMetrics {
  requestId: string;
  modelId: string;
  latencyMs: number;
  tokensIn: number;
  tokensOut: number;
  spendTracked: number;
  circuitTripped?: boolean;
  success: boolean;
  errorCode?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface DashboardMetrics {
  spendPerHour: number;
  spendPerDay: number;
  spendPerWeek: number;
  totalSpend: number;
  avgLatencyMs: number;
  latencyP50: number;
  latencyP95: number;
  latencyP99: number;
  successRate: number;
  circuitBreakerTrips: number;
  topAdaptationRequestsByCost: Array<{
    requestId: string;
    modelId: string;
    spendTracked: number;
    timestamp: string;
  }>;
}
```

## 4. Percentile Calculation Invariant

```typescript
public calculatePercentile(values: number[], percentile: number): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const index = (percentile / 100) * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  const weight = index - lower;
  return Number((sorted[lower] * (1 - weight) + sorted[upper] * weight).toFixed(2));
}
```

## 5. Langfuse Adapter & Local JSON Fallback Pattern

```typescript
export interface TelemetryExporter {
  exportMetric(metric: LlmMetrics): Promise<void>;
  flush(): Promise<void>;
}

export class ResilientTelemetryExporter implements TelemetryExporter {
  constructor(
    private remoteExporter: TelemetryExporter,
    private localFallback: TelemetryExporter
  ) {}

  async exportMetric(metric: LlmMetrics): Promise<void> {
    try {
      await this.remoteExporter.exportMetric(metric);
    } catch (err) {
      // Gracefully fall back to local disk JSON buffer without dropping telemetry
      await this.localFallback.exportMetric(metric);
    }
  }

  async flush(): Promise<void> {
    try {
      await this.remoteExporter.flush();
    } catch {
      await this.localFallback.flush();
    }
  }
}
```

## 6. Masking and Sanitization Implementation Pattern

```typescript
private sanitizeString(text: string): string {
  let cleaned = text;
  cleaned = cleaned.replace(/\b[0-9a-fA-F]{32,}\b/g, '[REDACTED_HEX_KEY]');
  cleaned = cleaned.replace(/(bearer\s+)[a-zA-Z0-9_\-\.]+/gi, '$1[REDACTED_TOKEN]');
  cleaned = cleaned.replace(/(password|key|secret)=[^&\s]+/gi, '$1=[REDACTED]');
  return cleaned;
}
```
