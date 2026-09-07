// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/lib/budgetGuard.ts"
// purpose: "Predictive Cost & Token Budget Guard for Swarm AI Co-Pilot Operations"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["TaskDNA-PHASE-3-BUDGET-GUARD"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-03"
// author: "DNK-e.com Maksym & Gerych"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

export interface CostEstimate {
  estimatedCost: number; // in USD
  estimatedTokens: number;
  riskLevel: 'low' | 'medium' | 'high';
  formattedCost: string;
}

export const AGENT_BASE_COSTS_PER_1K_TOKENS: Record<string, number> = {
  gerych_prime: 0.003,
  gerych_builder: 0.002,
  dnk_shopify: 0.003,
  dnk_video_ai_creator: 0.045,
  dnk_dev_fullstack: 0.004,
  gerych_researcher: 0.006,
  gerych_auditor: 0.008,
  dnk_security_guard: 0.002,
  dnk_scones_memory: 0.001,
  dnk_ui_builder: 0.0025,
};

export const ACTION_MULTIPLIERS: Record<string, number> = {
  generate: 1.0,
  expand: 1.5,
  reskin: 0.8,
  liquid: 1.3,
  storyboard: 2.2,
  audit: 1.1,
  translate: 0.9,
  decompose: 1.4,
};

export const budgetGuard = {
  /**
   * Estimate token count from input prompt and typical agent completion ratio
   */
  estimateTokens(prompt: string, action: string = 'generate'): number {
    const promptLen = prompt?.trim().length || 0;
    const inputTokens = Math.max(16, Math.ceil(promptLen / 3.6));
    const completionMultiplier = ACTION_MULTIPLIERS[action] || 1.0;
    const expectedOutputTokens = Math.round(inputTokens * 3.5 * completionMultiplier);
    return inputTokens + expectedOutputTokens;
  },

  /**
   * Estimate execution cost in USD
   */
  estimateCost(agent: string, action: string, prompt: string): number {
    const totalTokens = this.estimateTokens(prompt, action);
    const baseRatePer1k = AGENT_BASE_COSTS_PER_1K_TOKENS[agent] || 0.003;
    const actionMult = ACTION_MULTIPLIERS[action] || 1.0;

    const rawCost = (totalTokens / 1000) * baseRatePer1k * actionMult;
    // Bounded round to 5 decimal places
    return Math.round(rawCost * 100000) / 100000;
  },

  /**
   * Determine risk level threshold based on dollar threshold
   */
  getRiskLevel(cost: number): 'low' | 'medium' | 'high' {
    if (cost < 0.01) return 'low';
    if (cost < 0.05) return 'medium';
    return 'high';
  },

  /**
   * Formats cost nicely for UI badge
   */
  formatCost(cost: number): string {
    if (cost === 0) return '$0.000';
    if (cost < 0.001) return '<$0.001';
    return `$${cost.toFixed(3)}`;
  },

  /**
   * Full calculation summary for UI render
   */
  getEstimate(agent: string, action: string, prompt: string): CostEstimate {
    const tokens = this.estimateTokens(prompt, action);
    const cost = this.estimateCost(agent, action, prompt);
    const risk = this.getRiskLevel(cost);
    return {
      estimatedCost: cost,
      estimatedTokens: tokens,
      riskLevel: risk,
      formattedCost: this.formatCost(cost),
    };
  },
};
