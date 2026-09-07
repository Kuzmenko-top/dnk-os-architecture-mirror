/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/application/spend-guard.ts"
# purpose: "SpendGuardEvaluator with token-based cost calculation, configurable model pricing, and pre-flight budget enforcement."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export interface ModelPricing {
  inputPricePer1k: number;
  outputPricePer1k: number;
}

export interface SpendGuardConfig {
  budgetLimit: number; // e.g. 5.00 ($5 USD)
  modelPricing: Record<string, ModelPricing>;
}

export const DEFAULT_MODEL_PRICING: Record<string, ModelPricing> = {
  'gemini-2.5-pro': {
    inputPricePer1k: 0.0025,
    outputPricePer1k: 0.0075,
  },
  'gemini-2.5-flash': {
    inputPricePer1k: 0.00075,
    outputPricePer1k: 0.003,
  },
  'gemini-1.5-pro': {
    inputPricePer1k: 0.00125,
    outputPricePer1k: 0.005,
  },
  'gemini-1.5-flash': {
    inputPricePer1k: 0.000075,
    outputPricePer1k: 0.0003,
  },
  'claude-3-5-sonnet-20241022': {
    inputPricePer1k: 0.003,
    outputPricePer1k: 0.015,
  },
  'default': {
    inputPricePer1k: 0.001,
    outputPricePer1k: 0.002,
  },
};

export const DEFAULT_SPENDGUARD_CONFIG: SpendGuardConfig = {
  budgetLimit: 5.00,
  modelPricing: DEFAULT_MODEL_PRICING,
};

export class SpendGuardEvaluator {
  private readonly config: SpendGuardConfig;
  private currentSpend: number = 0;

  constructor(config?: Partial<SpendGuardConfig>) {
    this.config = {
      budgetLimit: config?.budgetLimit ?? DEFAULT_SPENDGUARD_CONFIG.budgetLimit,
      modelPricing: {
        ...DEFAULT_MODEL_PRICING,
        ...(config?.modelPricing ?? {}),
      },
    };
  }

  public getPricing(modelId: string): ModelPricing {
    const pricing = this.config.modelPricing[modelId] ?? this.config.modelPricing['default'];
    if (!pricing) {
      throw new Error(`[SpendGuardEvaluator] Missing pricing configuration for model: "${modelId}"`);
    }
    return pricing;
  }

  public calculateCost(tokensIn: number, tokensOut: number, modelId: string): number {
    const pricing = this.getPricing(modelId);
    const inputCost = (tokensIn / 1000) * pricing.inputPricePer1k;
    const outputCost = (tokensOut / 1000) * pricing.outputPricePer1k;
    return Number((inputCost + outputCost).toFixed(8));
  }

  public preFlightCheck(
    tokensIn: number,
    tokensOut: number,
    modelId: string,
    currentSpend: number = this.currentSpend
  ): boolean {
    const estimatedCost = this.calculateCost(tokensIn, tokensOut, modelId);
    return (currentSpend + estimatedCost) <= this.config.budgetLimit;
  }

  public trackSpend(cost: number): void {
    if (this.currentSpend + cost > this.config.budgetLimit) {
      throw new Error(
        `[SpendGuardEvaluator] Spend limit of $${this.config.budgetLimit.toFixed(3)} exceeded! Current: $${this.currentSpend.toFixed(3)}, attempted: $${cost.toFixed(3)}`
      );
    }
    this.currentSpend = Number((this.currentSpend + cost).toFixed(8));
  }

  public recordTokenUsage(tokensIn: number, tokensOut: number, modelId: string): number {
    const cost = this.calculateCost(tokensIn, tokensOut, modelId);
    this.trackSpend(cost);
    return cost;
  }

  public getSpend(): number {
    return this.currentSpend;
  }

  public getBudgetLimit(): number {
    return this.config.budgetLimit;
  }

  public reset(): void {
    this.currentSpend = 0;
  }
}
