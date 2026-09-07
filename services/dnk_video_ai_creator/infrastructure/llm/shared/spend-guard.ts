/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/shared/spend-guard.ts"
# purpose: "Spend Protection & Safety Budget Controls for Live Provider Qualification (001E-C-R1)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export interface LiveSpendConfig {
  max_requests_per_run: number;
  max_input_tokens: number;
  max_output_tokens: number;
  max_cost_estimate: number; // in USD
  allowed_models: string[];
}

export const DEFAULT_LIVE_SPEND_LIMITS: LiveSpendConfig = {
  max_requests_per_run: 5,
  max_input_tokens: 30000,
  max_output_tokens: 8000,
  max_cost_estimate: 0.15, // max $0.15 per qualification suite
  allowed_models: [
    'gemini-2.5-flash',
    'gemini-2.5-pro',
    'gemini-1.5-flash',
    'gemini-1.5-pro',
    'claude-3-5-sonnet-20241022',
    'claude-3-5-haiku-20241022'
  ]
};

export class SpendLimitExceededError extends Error {
  constructor(public readonly metric: string, public readonly current: number, public readonly limit: number) {
    super(`Spend limit exceeded for ${metric}: ${current} > ${limit}`);
    this.name = 'SpendLimitExceededError';
  }
}

export class ModelNotAllowedError extends Error {
  constructor(public readonly model: string, public readonly allowedModels: string[]) {
    super(`Model '${model}' is not in allowed models list: [${allowedModels.join(', ')}]`);
    this.name = 'ModelNotAllowedError';
  }
}

export class LiveSpendGuard {
  private requestCount = 0;
  private totalInputTokens = 0;
  private totalOutputTokens = 0;
  private totalCostEstimate = 0;

  // Approximate cost per million tokens (input / output)
  private readonly pricingPerMillion: Record<string, { input: number; output: number }> = {
    'gemini-2.5-flash': { input: 0.15, output: 0.60 },
    'gemini-2.5-pro': { input: 1.25, output: 5.00 },
    'gemini-1.5-flash': { input: 0.15, output: 0.60 },
    'gemini-1.5-pro': { input: 1.25, output: 5.00 },
    'claude-3-5-sonnet-20241022': { input: 3.00, output: 15.00 },
    'claude-3-5-haiku-20241022': { input: 1.00, output: 5.00 }
  };

  constructor(private readonly config: LiveSpendConfig = DEFAULT_LIVE_SPEND_LIMITS) {}

  public validatePreRequest(model: string, estimatedInputTokens: number = 0): void {
    if (!this.config.allowed_models.includes(model)) {
      throw new ModelNotAllowedError(model, this.config.allowed_models);
    }

    if (this.requestCount + 1 > this.config.max_requests_per_run) {
      throw new SpendLimitExceededError('max_requests_per_run', this.requestCount + 1, this.config.max_requests_per_run);
    }

    if (this.totalInputTokens + estimatedInputTokens > this.config.max_input_tokens) {
      throw new SpendLimitExceededError('max_input_tokens', this.totalInputTokens + estimatedInputTokens, this.config.max_input_tokens);
    }
  }

  public recordUsage(model: string, inputTokens: number, outputTokens: number): void {
    this.requestCount += 1;
    this.totalInputTokens += inputTokens;
    this.totalOutputTokens += outputTokens;

    const rates = this.pricingPerMillion[model] || { input: 1.00, output: 4.00 };
    const requestCost = (inputTokens / 1_000_000) * rates.input + (outputTokens / 1_000_000) * rates.output;
    this.totalCostEstimate += requestCost;

    if (this.totalOutputTokens > this.config.max_output_tokens) {
      throw new SpendLimitExceededError('max_output_tokens', this.totalOutputTokens, this.config.max_output_tokens);
    }

    if (this.totalCostEstimate > this.config.max_cost_estimate) {
      throw new SpendLimitExceededError('max_cost_estimate', this.totalCostEstimate, this.config.max_cost_estimate);
    }
  }

  public getSummary() {
    return {
      requestCount: this.requestCount,
      totalInputTokens: this.totalInputTokens,
      totalOutputTokens: this.totalOutputTokens,
      totalCostEstimateUsd: Number(this.totalCostEstimate.toFixed(5)),
      limits: this.config
    };
  }
}

export {
  SpendGuardEvaluator,
  SpendGuardConfig,
  ModelPricing,
  DEFAULT_MODEL_PRICING,
  DEFAULT_SPENDGUARD_CONFIG,
} from '@dnk/video-audit-core';
