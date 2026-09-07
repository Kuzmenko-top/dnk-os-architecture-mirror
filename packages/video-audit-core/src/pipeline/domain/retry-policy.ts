/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/retry-policy.ts"
# purpose: "Deterministic Retry, Backoff Computation and Error Classification Engine."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditJob, JobError, JobErrorClassification } from './jobs/job.js';

const BACKOFF_SCHEDULE_MS: Record<number, number> = {
  1: 5_000,    // Attempt 1 -> 5 seconds
  2: 30_000,   // Attempt 2 -> 30 seconds
  3: 120_000,  // Attempt 3 -> 2 minutes
  4: 600_000   // Attempt 4 -> 10 minutes
};

export const MAX_RETRY_ATTEMPTS = 4;

export function calculateBackoffMs(attempt: number): number {
  if (attempt <= 0) return 0;
  if (attempt in BACKOFF_SCHEDULE_MS) {
    return BACKOFF_SCHEDULE_MS[attempt];
  }
  return BACKOFF_SCHEDULE_MS[MAX_RETRY_ATTEMPTS];
}

export function classifyError(error: unknown): {
  code: string;
  message: string;
  classification: JobErrorClassification;
  details?: Record<string, unknown>;
} {
  if (error && typeof error === 'object' && 'classification' in error) {
    const customErr = error as {
      code?: string;
      message?: string;
      classification: JobErrorClassification;
      details?: Record<string, unknown>;
    };
    return {
      code: customErr.code ?? 'UNKNOWN_ERROR',
      message: customErr.message ?? String(error),
      classification: customErr.classification,
      details: customErr.details
    };
  }

  const errMessage = error instanceof Error ? error.message : String(error);
  const lowerMsg = errMessage.toLowerCase();

  // Check permanent failure indicators
  if (
    lowerMsg.includes('invalid media') ||
    lowerMsg.includes('unsupported format') ||
    lowerMsg.includes('corrupt artifact') ||
    lowerMsg.includes('invalid contract') ||
    lowerMsg.includes('schema validation') ||
    lowerMsg.includes('zoderror')
  ) {
    return {
      code: 'PERMANENT_ERROR',
      message: errMessage,
      classification: 'permanent'
    };
  }

  // Check manual review indicators
  if (
    lowerMsg.includes('copyright') ||
    lowerMsg.includes('rights issue') ||
    lowerMsg.includes('low confidence') ||
    lowerMsg.includes('ambiguous source') ||
    lowerMsg.includes('manual_review')
  ) {
    return {
      code: 'MANUAL_REVIEW_REQUIRED',
      message: errMessage,
      classification: 'manual_review'
    };
  }

  // Otherwise default to retryable (transient network, timeout, rate limit, worker crash)
  return {
    code: 'TRANSIENT_FAILURE',
    message: errMessage,
    classification: 'retryable'
  };
}

export interface RetryEvaluation {
  shouldRetry: boolean;
  nextAttempt: number;
  availableAt?: string;
  nextAvailableAt?: string;
  terminalStatus?: 'permanent_error';
  reason: string;
}

export function evaluateRetry(
  job: VideoAuditJob,
  jobError: JobError,
  nowMs: number | Date = Date.now()
): RetryEvaluation {
  const currentTimestamp = nowMs instanceof Date ? nowMs.getTime() : nowMs;

  if (jobError.classification === 'permanent' || jobError.classification === 'manual_review') {
    return {
      shouldRetry: false,
      nextAttempt: job.attempt,
      terminalStatus: 'permanent_error',
      reason: `Non-retryable error classification: '${jobError.classification}' (${jobError.code}: ${jobError.message})`
    };
  }

  if (job.attempt >= job.maxAttempts) {
    return {
      shouldRetry: false,
      nextAttempt: job.attempt,
      terminalStatus: 'permanent_error',
      reason: `Max retry attempts reached (${job.attempt}/${job.maxAttempts})`
    };
  }

  const backoffMs = calculateBackoffMs(job.attempt);
  const nextAvailableIso = new Date(currentTimestamp + backoffMs).toISOString();

  return {
    shouldRetry: true,
    nextAttempt: job.attempt + 1,
    availableAt: nextAvailableIso,
    nextAvailableAt: nextAvailableIso,
    reason: `Retryable error scheduled with backoff ${backoffMs}ms for attempt ${job.attempt + 1}/${job.maxAttempts}`
  };
}

export const computeNextRetry = evaluateRetry;
