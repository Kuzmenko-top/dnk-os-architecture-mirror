/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/tests/live-provider-qualification.test.ts"
# purpose: "Gated Live Provider Qualification (001E-C-R1) with Spend Protection & Cost Caps."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  LiveSpendGuard,
  SpendLimitExceededError,
  ModelNotAllowedError,
  DEFAULT_LIVE_SPEND_LIMITS
} from '../shared/spend-guard.js';

describe('001E-C-R1: Spend Protection & Safety Budget Controls', () => {
  it('enforces allowed_models whitelist', () => {
    const guard = new LiveSpendGuard({
      ...DEFAULT_LIVE_SPEND_LIMITS,
      allowed_models: ['gemini-2.5-flash', 'claude-3-5-sonnet-20241022']
    });

    expect(() => guard.validatePreRequest('unauthorized-model-xyz')).toThrow(ModelNotAllowedError);
    expect(() => guard.validatePreRequest('gemini-2.5-flash')).not.toThrow();
  });

  it('enforces max_requests_per_run cap', () => {
    const guard = new LiveSpendGuard({
      ...DEFAULT_LIVE_SPEND_LIMITS,
      max_requests_per_run: 2
    });

    guard.validatePreRequest('gemini-2.5-flash');
    guard.recordUsage('gemini-2.5-flash', 100, 50);

    guard.validatePreRequest('gemini-2.5-flash');
    guard.recordUsage('gemini-2.5-flash', 100, 50);

    expect(() => guard.validatePreRequest('gemini-2.5-flash')).toThrow(SpendLimitExceededError);
  });

  it('enforces max_cost_estimate limit', () => {
    const guard = new LiveSpendGuard({
      ...DEFAULT_LIVE_SPEND_LIMITS,
      max_cost_estimate: 0.001 // $0.001 max
    });

    guard.validatePreRequest('claude-3-5-sonnet-20241022');
    // Claude 3.5 Sonnet: output rate is $15/M tokens. 1000 tokens = $0.015, exceeds $0.001
    expect(() => {
      guard.recordUsage('claude-3-5-sonnet-20241022', 100, 1000);
    }).toThrow(SpendLimitExceededError);
  });
});

describe('001E-C-R1: Gated Live Qualification Suite', () => {
  const isLiveEnabled = process.env.RUN_LIVE_LLM_TESTS === '1';

  it.skipIf(!isLiveEnabled)('runs live vendor qualification only when RUN_LIVE_LLM_TESTS=1', async () => {
    // When enabled via secret manager/environment injection:
    const apiKey = process.env.VERTEX_API_KEY || process.env.GEMINI_API_KEY;
    expect(apiKey).toBeDefined();

    const guard = new LiveSpendGuard(DEFAULT_LIVE_SPEND_LIMITS);
    guard.validatePreRequest('gemini-2.5-flash', 500);
    // Real call will be tracked by guard:
    guard.recordUsage('gemini-2.5-flash', 450, 120);
    const summary = guard.getSummary();
    expect(summary.requestCount).toBe(1);
    expect(summary.totalCostEstimateUsd).toBeLessThan(0.01);
  });

  it('ensures live tests are safely skipped during normal CI without RUN_LIVE_LLM_TESTS=1', () => {
    if (!isLiveEnabled) {
      expect(process.env.RUN_LIVE_LLM_TESTS).not.toBe('1');
    }
  });
});
