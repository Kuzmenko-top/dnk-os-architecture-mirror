/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/tests/provider-adapters.test.ts"
# purpose: "Comprehensive Unit & Integration Test Suite for Provider Adapters."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { GeminiAdapter } from '../gemini/adapter.js';
import { ClaudeAdapter } from '../claude/adapter.js';
import { IdempotentRetryExecutor, generateIdempotencyKey } from '../shared/retry-policy.js';
import { TokenBudgetManager } from '../shared/token-budget.js';
import { LLMTelemetryManager } from '../shared/telemetry.js';
import { RateLimitError, InvalidCredentialsError } from '../shared/provider-errors.js';
import { MultimodalAuditInput, MultimodalAuditContext } from '@dnk/video-audit-core';

// Standard structured test input and context matching the model definition
const mockInput: MultimodalAuditInput = {
  referenceAssetId: 'asset_123',
  metadata: {
    durationMs: 10000,
    width: 1920,
    height: 1080,
    hasAudio: true,
    hasVideo: true,
  },
  artifactRefs: {
    transcript: {
      key: 'tx_ref',
      sha256: 'a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j01234',
      schemaVersion: 'transcript.v1',
    },
    scenes: {
      key: 'sc_ref',
      sha256: 'b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a01234',
      schemaVersion: 'scenes.v1',
    },
  },
  evidence: {
    schemaVersion: 'multimodal-evidence.v1',
    referenceAssetId: 'asset_123',
    generatedAt: new Date().toISOString(),
    aggregateStatus: 'completed',
    temporalCorrelations: [],
  },
  transcript: {
    schemaVersion: 'transcript.v1',
    id: 'tx_123',
    referenceAssetId: 'asset_123',
    language: 'en',
    provider: 'whisper',
    modelVersion: 'v3',
    segments: [
      { id: 'seg_01', ordinal: 1, startMs: 0, endMs: 5000, text: 'Hello', words: [], confidence: 0.95 },
    ],
    durationMs: 10000,
    confidence: 0.95,
    status: 'completed',
    warnings: [],
  },
  scenes: {
    schemaVersion: 'scenes.v1',
    referenceAssetId: 'asset_123',
    extractor: { provider: 'ffmpeg', version: '1.0.0', method: 'scndetect' },
    scenes: [
      { id: 'scene_01', ordinal: 1, startMs: 0, endMs: 10000, durationMs: 10000, boundaryConfidence: 0.99, shotType: 'wide' },
    ],
    durationMs: 10000,
    warnings: [],
  },
};

const mockContext: MultimodalAuditContext = {
  correlationId: 'asset_123',
  targetNiches: ['educational_short'],
};

// Valid audit JSON output sample expected from providers
const validAuditResponseContent = JSON.stringify({
  schemaVersion: 'multimodal-audit.v1',
  referenceAssetId: 'asset_123',
  status: 'accepted',
  metadata: {
    provider: 'gemini',
    model: 'gemini-1.5-flash',
    modelSetVersion: 'gemini-1.5-flash',
    promptTemplateVersion: '1.0.0',
    inputArtifactHashes: {
      transcript: 'a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j01234',
      scenes: 'b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a01234',
    },
    outputSchemaVersion: 'multimodal-audit.v1',
    processingDurationMs: 250,
  },
  claims: [
    {
      claimId: 'claim_01',
      classification: 'observed',
      confidence: 1.0,
      description: 'First introduction screen',
      evidenceRefs: [{ type: 'scene', id: 'scene_01' }],
    },
  ],
  adaptationRecommendations: [],
  warnings: [],
});

describe('VIDEO-AUDIT-PIPELINE-001E-C Provider Adapters', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    TokenBudgetManager.resetMetrics();
  });

  describe('Gemini Adapter Tests', () => {
    it('successfully processes prompt context and maps valid Gemini response', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        status: 200,
        headers: new Headers(),
        json: async () => ({
          candidates: [
            {
              content: {
                parts: [{ text: validAuditResponseContent }],
              },
              finishReason: 'STOP',
            },
          ],
          usageMetadata: {
            promptTokenCount: 1500,
            candidatesTokenCount: 450,
          },
        }),
      });

      const adapter = new GeminiAdapter('gemini-1.5-flash', {
        apiKey: 'test-api-key',
        fetchFn: mockFetch,
      });

      const result = await adapter.analyze(mockInput, mockContext);

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(result.providerId).toBe('gemini');
      expect(result.modelVersion).toBe('gemini-1.5-flash');
      expect(result.usage?.inputTokens).toBe(1500);
      expect(result.usage?.outputTokens).toBe(450);
      expect(JSON.parse(result.rawOutput as string).status).toBe('accepted');
    });

    it('correctly maps 429 rate limit to RateLimitError', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        status: 429,
        headers: new Headers(),
        json: async () => ({
          error: {
            code: 429,
            message: 'Resource has been exhausted',
            status: 'RESOURCE_EXHAUSTED',
          },
        }),
      });

      const adapter = new GeminiAdapter('gemini-1.5-flash', {
        apiKey: 'test-api-key',
        fetchFn: mockFetch,
      });

      await expect(adapter.analyze(mockInput, mockContext)).rejects.toThrow(RateLimitError);
    });
  });

  describe('Claude Adapter Tests', () => {
    it('successfully processes prompt context and maps valid Claude response', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        status: 200,
        headers: new Headers(),
        json: async () => ({
          id: 'msg_012345',
          content: [{ type: 'text', text: validAuditResponseContent }],
          usage: {
            input_tokens: 1600,
            output_tokens: 500,
          },
        }),
      });

      const adapter = new ClaudeAdapter('claude-3-5-sonnet-20241022', {
        apiKey: 'test-api-key',
        fetchFn: mockFetch,
      });

      const result = await adapter.analyze(mockInput, mockContext);

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(result.providerId).toBe('claude');
      expect(result.modelVersion).toBe('claude-3-5-sonnet-20241022');
      expect(result.usage?.inputTokens).toBe(1600);
      expect(result.usage?.outputTokens).toBe(500);
    });

    it('correctly maps authentication failure to InvalidCredentialsError', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        status: 401,
        headers: new Headers(),
        json: async () => ({
          error: {
            type: 'authentication_error',
            message: 'Invalid API Key',
          },
        }),
      });

      const adapter = new ClaudeAdapter('claude-3-5-sonnet-20241022', {
        apiKey: 'test-api-key',
        fetchFn: mockFetch,
      });

      await expect(adapter.analyze(mockInput, mockContext)).rejects.toThrow(InvalidCredentialsError);
    });
  });

  describe('Token Budget Manager', () => {
    it('throws ContextOverflowError when prompt size exceeds maximum capacity', () => {
       const longPrompt = 'a'.repeat(1000 * 1000 * 5); // Est. ~1.25M tokens (limit for Claude is 200k)
       expect(() => {
         TokenBudgetManager.enforceBudget('claude', 'claude-3-5-sonnet-20241022', longPrompt, 4096);
       }).toThrow();
    });

    it('successfully records and retrieves token usage telemetry', () => {
      TokenBudgetManager.recordUsage(500, 200);
      const metrics = TokenBudgetManager.getCumulativeMetrics();
      expect(metrics.inputTokens).toBe(500);
      expect(metrics.outputTokens).toBe(200);
    });
  });

  describe('Idempotency & Retry Execution Policy', () => {
    const input: MultimodalAuditInput = {
      referenceAssetId: 'asset_123',
      artifactRefs: {
        transcript: {
          schemaVersion: '1.0.0',
          key: 'ref_1',
          sha256: 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
        },
      },
      evidence: {} as any,
      metadata: {} as any,
    };
    const context: MultimodalAuditContext = {
      targetNiches: ['educational_short'],
    };

    beforeEach(() => {
      IdempotentRetryExecutor.clearRegistry();
    });

    it('correctly generates deterministic idempotency key', () => {
      const key1 = generateIdempotencyKey(input, context, 'gemini', 'gemini-1.5-flash', '1.0.0');
      const key2 = generateIdempotencyKey(input, context, 'gemini', 'gemini-1.5-flash', '1.0.0');
      expect(key1).toBe(key2);
    });

    it('retries on retryable errors and succeeds when backend recovers', async () => {
      let attempts = 0;
      const fn = vi.fn().mockImplementation(async () => {
        attempts++;
        if (attempts < 2) {
          throw new RateLimitError('Rate limit exceeded', 'gemini');
        }
        return {
          rawOutput: { success: true },
          providerId: 'gemini',
          modelVersion: 'gemini-1.5-flash',
          promptVersion: '1.0.0',
          inputArtifactHashes: {},
        };
      });

      const executor = new IdempotentRetryExecutor({
        maxAttempts: 3,
        initialBackoffMs: 1, // Minimize delay for fast testing
        factor: 1,
      });

      const result = await executor.execute(input, context, 'gemini', 'gemini-1.5-flash', '1.0.0', fn);

      expect(attempts).toBe(2);
      expect(result.rawOutput).toEqual({ success: true });
    });

    it('prevents overlapping duplicate parallel requests for the same idempotency key', async () => {
      const fn = vi.fn().mockImplementation(() => new Promise((resolve) => setTimeout(() => resolve({
        rawOutput: { success: true },
        providerId: 'gemini',
        modelVersion: 'gemini-1.5-flash',
        promptVersion: '1.0.0',
        inputArtifactHashes: {},
      }), 50)));
      
      const executor = new IdempotentRetryExecutor();

      // Launch in parallel
      const p1 = executor.execute(input, context, 'gemini', 'gemini-1.5-flash', '1.0.0', fn);
      const p2 = executor.execute(input, context, 'gemini', 'gemini-1.5-flash', '1.0.0', fn);

      // In real world, p2 will resolve to the same promise (coalescing) rather than throwing!
      // This is a beautiful coalescing lock feature. Let's assert both return the exact same object reference!
      const [res1, res2] = await Promise.all([p1, p2]);
      expect(res1).toBe(res2);
      expect(fn).toHaveBeenCalledTimes(1); // Only called once!
    });
  });
});
