/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/adaptation/spend-guard.test.ts"
# purpose: "Unit & Integration Tests for SpendGuardEvaluator, Token-based Pricing, Pre-flight Checks & Telemetry."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect, beforeEach } from 'vitest';
import {
  SpendGuardEvaluator,
  DEFAULT_MODEL_PRICING,
} from '../../src/pipeline/application/spend-guard.js';
import {
  LocalJsonTelemetry,
  MockLangfuseTelemetry,
  LlmMetrics,
} from '../../src/pipeline/application/telemetry.js';
import {
  LiveLlmScriptWriter,
  SpendGuard,
} from '../../src/adaptation/domain/script-writer/live-llm-script-writer.js';
import { REBURN_BRAND_PROFILE } from '../../src/adaptation/domain/brand/reburn-profile.js';
import { ExtractedMechanisms } from '../../src/adaptation/domain/mechanism-extractor.js';
import { AdaptationRequest } from '../../src/schemas/adaptation.js';

describe('SpendGuardEvaluator', () => {
  beforeEach(() => {
    SpendGuard.reset();
  });

  it('calculates cost correctly for Gemini 2.5 Pro', () => {
    const spendGuard = new SpendGuardEvaluator({
      budgetLimit: 5.0,
      modelPricing: {
        'gemini-2.5-pro': {
          inputPricePer1k: 0.0025,
          outputPricePer1k: 0.0075,
        },
      },
    });

    const cost = spendGuard.calculateCost(1000, 500, 'gemini-2.5-pro');
    expect(cost).toBeCloseTo(0.00625, 4); // (1 * 0.0025) + (0.5 * 0.0075)
  });

  it('calculates cost correctly for Gemini 2.5 Flash using default pricing', () => {
    const spendGuard = new SpendGuardEvaluator();
    // 2000 in, 1000 out -> (2 * 0.00075) + (1 * 0.003) = 0.0015 + 0.003 = 0.0045
    const cost = spendGuard.calculateCost(2000, 1000, 'gemini-2.5-flash');
    expect(cost).toBeCloseTo(0.0045, 4);
  });

  it('allows requests within budget in preFlightCheck', () => {
    const spendGuard = new SpendGuardEvaluator({
      budgetLimit: 5.0,
      modelPricing: DEFAULT_MODEL_PRICING,
    });

    const allowed = spendGuard.preFlightCheck(
      1000,
      500,
      'gemini-2.5-pro',
      1.0 // current_spend: 1.0 + 0.00625 = 1.00625 <= 5.0
    );

    expect(allowed).toBe(true);
  });

  it('blocks over-budget requests', () => {
    const spendGuard = new SpendGuardEvaluator({
      budgetLimit: 5.0,
      modelPricing: {
        'gemini-2.5-pro': {
          inputPricePer1k: 0.0025,
          outputPricePer1k: 0.0075,
        },
      },
    });

    // 100000 in (100 * 0.0025 = 0.25) + 50000 out (50 * 0.0075 = 0.375) = 0.625
    // current_spend 4.50 + 0.625 = 5.125 > 5.00
    const allowed = spendGuard.preFlightCheck(
      100000, // tokens_in
      50000, // tokens_out
      'gemini-2.5-pro',
      4.5 // current_spend
    );

    expect(allowed).toBe(false);
  });

  it('tracks spend and throws when limit is exceeded', () => {
    const spendGuard = new SpendGuardEvaluator({ budgetLimit: 0.01 });
    expect(spendGuard.getSpend()).toBe(0);

    spendGuard.trackSpend(0.005);
    expect(spendGuard.getSpend()).toBe(0.005);

    expect(() => {
      spendGuard.trackSpend(0.01);
    }).toThrow(/Spend limit of \$0.010 exceeded/);
  });

  it('records token usage and increments spend atomically', () => {
    const spendGuard = new SpendGuardEvaluator({ budgetLimit: 1.0 });
    const cost = spendGuard.recordTokenUsage(1000, 1000, 'gemini-2.5-flash');
    // 0.00075 + 0.003 = 0.00375
    expect(cost).toBeCloseTo(0.00375, 4);
    expect(spendGuard.getSpend()).toBeCloseTo(0.00375, 4);

    spendGuard.reset();
    expect(spendGuard.getSpend()).toBe(0);
  });
});

describe('Telemetry & Dashboard Metrics', () => {
  it('records metrics and calculates dashboard percentiles correctly', async () => {
    const telemetry = new LocalJsonTelemetry();
    const now = new Date();

    const sampleMetrics: LlmMetrics[] = [
      {
        requestId: 'req-1',
        modelId: 'gemini-2.5-flash',
        latencyMs: 120,
        tokensIn: 800,
        tokensOut: 200,
        spendTracked: 0.0012,
        success: true,
        timestamp: new Date(now.getTime() - 10 * 60 * 1000).toISOString(), // 10 min ago
      },
      {
        requestId: 'req-2',
        modelId: 'gemini-2.5-pro',
        latencyMs: 450,
        tokensIn: 2500,
        tokensOut: 800,
        spendTracked: 0.01225,
        success: true,
        timestamp: new Date(now.getTime() - 5 * 60 * 1000).toISOString(), // 5 min ago
      },
      {
        requestId: 'req-3',
        modelId: 'gemini-2.5-pro',
        latencyMs: 900,
        tokensIn: 0,
        tokensOut: 0,
        spendTracked: 0,
        circuitTripped: true,
        success: false,
        errorCode: 'BUDGET_LIMIT_EXCEEDED',
        timestamp: now.toISOString(),
      },
    ];

    for (const m of sampleMetrics) {
      await telemetry.recordMetrics(m);
    }

    const dashboard = telemetry.calculateDashboardMetrics(now);

    expect(dashboard.totalSpend).toBeCloseTo(0.01345, 5);
    expect(dashboard.spendPerHour).toBeCloseTo(0.01345, 5);
    expect(dashboard.spendPerDay).toBeCloseTo(0.01345, 5);
    expect(dashboard.successRate).toBeCloseTo(2 / 3, 2);
    expect(dashboard.circuitBreakerTrips).toBe(1);
    expect(dashboard.latencyP50).toBeGreaterThanOrEqual(120);
    expect(dashboard.latencyP95).toBeGreaterThanOrEqual(450);
    expect(dashboard.topAdaptationRequestsByCost[0].requestId).toBe('req-2');
  });

  it('MockLangfuseTelemetry records both local fallback and mock traces/generations', async () => {
    const mockLangfuse = new MockLangfuseTelemetry();

    const metric: LlmMetrics = {
      requestId: 'test-trace-001',
      modelId: 'gemini-2.5-pro',
      latencyMs: 320,
      tokensIn: 1000,
      tokensOut: 400,
      spendTracked: 0.0055,
      success: true,
      timestamp: new Date().toISOString(),
    };

    await mockLangfuse.recordMetrics(metric);

    expect(mockLangfuse.traces.length).toBe(1);
    expect(mockLangfuse.traces[0].id).toBe('test-trace-001');
    expect(mockLangfuse.generations.length).toBe(1);
    expect(mockLangfuse.generations[0].usage.total).toBe(1400);
    expect(mockLangfuse.getFallback().getRecords().length).toBe(1);
  });

  it('LiveLlmScriptWriter emits telemetry on execution and on fallback', async () => {
    const mockTelemetry = new MockLangfuseTelemetry();
    const evaluator = new SpendGuardEvaluator({ budgetLimit: 5.0 });
    const writer = new LiveLlmScriptWriter(
      undefined,
      evaluator,
      'gemini-2.5-flash',
      mockTelemetry
    );

    const mockRequest: AdaptationRequest = {
      schemaVersion: 'adaptation-request.v1',
      sourceAuditId: 'audit-tel-001',
      brandId: 'reburn-brand',
      niche: 'barbecue',
      audience: 'Підприємці',
      tone: 'Енергійний',
      desiredMechanisms: [],
      forbiddenElements: [],
      approvedFactIds: [],
      targetDurationMs: 30000,
      language: 'uk',
    };

    const mockMechanisms: ExtractedMechanisms = {
      hookMechanism: 'question_hook',
      narrativePattern: 'problem_solution',
      shotRhythm: 'steady_cadence',
      pausePattern: 'conversational_flow',
      ctaPattern: 'direct_commercial',
      keyInsights: ['insight 1'],
      recommendedPacingWpm: 130,
    };

    const script = await writer.generate(mockRequest, mockMechanisms, REBURN_BRAND_PROFILE);
    expect(script.id).toBeDefined();

    // Verify telemetry was recorded
    expect(mockTelemetry.traces.length).toBe(1);
    expect(mockTelemetry.traces[0].id).toBe('audit-tel-001');
    expect(mockTelemetry.traces[0].metadata.success).toBe(true);
    expect(mockTelemetry.generations[0].metadata.spendTracked).toBeGreaterThan(0);

    // Now exhaust budget so next attempt exceeds budget limit and triggers circuit breaker / fallback
    evaluator.trackSpend(evaluator.getBudgetLimit() - evaluator.getSpend());
    const fallbackScript = await writer.generate(mockRequest, mockMechanisms, REBURN_BRAND_PROFILE);
    expect(fallbackScript.id).toBeDefined();

    expect(mockTelemetry.traces.length).toBe(2);
    const failureTrace = mockTelemetry.traces[1];
    expect(failureTrace.metadata.success).toBe(false);
    expect(failureTrace.metadata.circuitTripped).toBe(true);
  });
});
