/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/shared/token-budget.ts"
# purpose: "Context & Token Budget Governor for Multimodal Audits."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { ContextOverflowError } from './provider-errors.js';

export interface ModelBudgetLimit {
  maxContextTokens: number;
  maxOutputTokens: number;
}

export const PROVIDER_MODEL_BUDGETS: Record<string, Record<string, ModelBudgetLimit>> = {
  gemini: {
    'gemini-1.5-pro': { maxContextTokens: 2000000, maxOutputTokens: 8192 },
    'gemini-1.5-flash': { maxContextTokens: 1000000, maxOutputTokens: 8192 },
  },
  claude: {
    'claude-3-opus-20240229': { maxContextTokens: 200000, maxOutputTokens: 4096 },
    'claude-3-5-sonnet-20240620': { maxContextTokens: 200000, maxOutputTokens: 8192 },
    'claude-3-5-sonnet-20241022': { maxContextTokens: 200000, maxOutputTokens: 8192 },
  },
};

export class TokenBudgetManager {
  private static cumulativeInputTokens = 0;
  private static cumulativeOutputTokens = 0;

  /**
   * Resets global tracking metrics.
   */
  public static resetMetrics(): void {
    this.cumulativeInputTokens = 0;
    this.cumulativeOutputTokens = 0;
  }

  /**
   * Returns accumulated metrics.
   */
  public static getCumulativeMetrics() {
    return {
      inputTokens: this.cumulativeInputTokens,
      outputTokens: this.cumulativeOutputTokens,
    };
  }

  /**
   * Records completed token usage.
   */
  public static recordUsage(inputTokens: number, outputTokens: number): void {
    this.cumulativeInputTokens += inputTokens;
    this.cumulativeOutputTokens += outputTokens;
  }

  /**
   * Gets the budget for a specific provider and model.
   */
  public static getBudget(providerId: string, modelName: string): ModelBudgetLimit {
    const providerModels = PROVIDER_MODEL_BUDGETS[providerId];
    if (!providerModels) {
      // Default conservative budget
      return { maxContextTokens: 200000, maxOutputTokens: 4096 };
    }
    const budget = providerModels[modelName];
    if (!budget) {
      // Default for unknown model of known provider
      return providerId === 'gemini'
        ? { maxContextTokens: 1000000, maxOutputTokens: 8192 }
        : { maxContextTokens: 200000, maxOutputTokens: 8192 };
    }
    return budget;
  }

  /**
   * Roughly estimates token count for a text string (4 chars ≈ 1 token rule of thumb).
   */
  public static estimateTokens(text: string): number {
    return Math.ceil(text.length / 4);
  }

  /**
   * Enforces that the estimated prompt context does not overflow the model context budget.
   */
  public static enforceBudget(
    providerId: string,
    modelName: string,
    renderedPromptText: string,
    outputTokensLimit?: number
  ): void {
    const budget = this.getBudget(providerId, modelName);
    const estimatedInputTokens = this.estimateTokens(renderedPromptText);
    const requestedOutputLimit = outputTokensLimit || budget.maxOutputTokens;

    const totalEstimated = estimatedInputTokens + requestedOutputLimit;

    if (totalEstimated > budget.maxContextTokens) {
      throw new ContextOverflowError(
        `Token budget validation failed for ${providerId}/${modelName}. Estimated input tokens (${estimatedInputTokens}) + output limit (${requestedOutputLimit}) exceeds model context limit (${budget.maxContextTokens}).`,
        providerId
      );
    }
  }
}
