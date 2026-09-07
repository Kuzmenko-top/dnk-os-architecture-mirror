/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/shared/retry-policy.ts"
# purpose: "Idempotent Retry Policy & Execution Governor for LLM Providers."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { MultimodalAuditInput, MultimodalAuditContext } from '@dnk/video-audit-core';
import {
  RetryableProviderError,
  PermanentProviderError,
  SchemaViolationError,
} from './provider-errors.js';
import { ProviderAuditResult } from './provider-port.js';

export interface RetryOptions {
  maxAttempts: number;
  initialBackoffMs: number;
  maxBackoffMs: number;
  factor: number;
}

const DEFAULT_RETRY_OPTIONS: RetryOptions = {
  maxAttempts: 3,
  initialBackoffMs: 1000,
  maxBackoffMs: 10000,
  factor: 2,
};

/**
 * Computes a unique, deterministic idempotency key for an execution.
 */
export function generateIdempotencyKey(
  input: MultimodalAuditInput,
  context: MultimodalAuditContext,
  providerId: string,
  modelVersion: string,
  promptVersion: string
): string {
  const parts = [
    input.referenceAssetId,
    JSON.stringify(input.artifactRefs || {}),
    promptVersion,
    modelVersion,
    providerId,
    JSON.stringify(context.targetNiches || []),
  ];
  // Simple deterministic string representation of components
  return parts.join('::');
}

export class IdempotentRetryExecutor {
  // In-memory registry to track and deduplicate active running executions
  private static activeRuns = new Map<string, Promise<ProviderAuditResult>>();
  // Cache of completed executions (optional, can be backed by persistent storage)
  private static completedRuns = new Map<string, ProviderAuditResult>();

  constructor(private readonly options: Partial<RetryOptions> = {}) {}

  /**
   * Clears the static run registry (primarily for tests)
   */
  public static clearRegistry(): void {
    this.activeRuns.clear();
    this.completedRuns.clear();
  }

  /**
   * Executes a provider analyze action with idempotency and retry policy.
   */
  public async execute(
    input: MultimodalAuditInput,
    context: MultimodalAuditContext,
    providerId: string,
    modelVersion: string,
    promptVersion: string,
    analyzeFn: (feedback?: string[]) => Promise<ProviderAuditResult>,
    optionsOverride?: Partial<RetryOptions>
  ): Promise<ProviderAuditResult> {
    const opts = { ...DEFAULT_RETRY_OPTIONS, ...this.options, ...optionsOverride };
    const idempotencyKey = generateIdempotencyKey(
      input,
      context,
      providerId,
      modelVersion,
      promptVersion
    );

    // 1. Check if we already have a completed result for this exact execution
    const cached = IdempotentRetryExecutor.completedRuns.get(idempotencyKey);
    if (cached) {
      return cached;
    }

    // 2. Check if a concurrent run is already active for this exact execution
    const existingPromise = IdempotentRetryExecutor.activeRuns.get(idempotencyKey);
    if (existingPromise) {
      return existingPromise;
    }

    // 3. Initiate run with retry logic
    const runPromise = this.runWithRetry(analyzeFn, opts, providerId);

    IdempotentRetryExecutor.activeRuns.set(idempotencyKey, runPromise);

    try {
      const result = await runPromise;
      IdempotentRetryExecutor.completedRuns.set(idempotencyKey, result);
      return result;
    } finally {
      IdempotentRetryExecutor.activeRuns.delete(idempotencyKey);
    }
  }

  private async runWithRetry(
    analyzeFn: (feedback?: string[]) => Promise<ProviderAuditResult>,
    opts: RetryOptions,
    providerId: string
  ): Promise<ProviderAuditResult> {
    let attempt = 0;
    let delay = opts.initialBackoffMs;
    let feedback: string[] | undefined = undefined;

    while (attempt < opts.maxAttempts) {
      attempt++;
      try {
        return await analyzeFn(feedback);
      } catch (error: any) {
        if (error instanceof PermanentProviderError) {
          throw error;
        }

        // Handle retryable errors
        if (error instanceof RetryableProviderError) {
          if (attempt >= opts.maxAttempts) {
            throw error; // exhausted all attempts
          }

          // Specially handle SchemaViolationError - retry exactly once with feedback
          if (error instanceof SchemaViolationError) {
            if (feedback) {
              // If we already retried with feedback once, do not retry again (fails closed)
              throw error;
            }
            feedback = error.validationFeedback || [error.message];
            // Immediate retry for schema violation
            continue;
          }

          // General retryable backoff
          const waitMs = error.backoffSuggestMs !== undefined ? error.backoffSuggestMs : delay;
          await new Promise((resolve) => setTimeout(resolve, waitMs));

          // Calculate next backoff delay
          delay = Math.min(delay * opts.factor, opts.maxBackoffMs);
        } else {
          // Unclassified error - treat as permanent or map to retryable network error if it resembles fetch errors
          throw error;
        }
      }
    }

    throw new Error(`LLM provider execution exceeded max attempts (${opts.maxAttempts})`);
  }
}
