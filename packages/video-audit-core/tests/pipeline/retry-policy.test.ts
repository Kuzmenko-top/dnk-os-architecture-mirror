/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/retry-policy.test.ts"
# purpose: "Unit Tests for Backoff Schedule and Error Classification."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  calculateBackoffMs,
  classifyError,
  evaluateRetry
} from '../../src/pipeline/domain/retry-policy.js';
import { VideoAuditJob, JobError } from '../../src/pipeline/domain/jobs/job.js';

describe('Retry & Backoff Policy', () => {
  it('follows the deterministic backoff schedule', () => {
    expect(calculateBackoffMs(1)).toBe(5_000);   // Attempt 1 -> 5s
    expect(calculateBackoffMs(2)).toBe(30_000);  // Attempt 2 -> 30s
    expect(calculateBackoffMs(3)).toBe(120_000); // Attempt 3 -> 2m
    expect(calculateBackoffMs(4)).toBe(600_000); // Attempt 4 -> 10m
    expect(calculateBackoffMs(5)).toBe(600_000); // Fallback to max schedule
  });

  it('correctly classifies permanent, manual review, and retryable errors', () => {
    expect(classifyError(new Error('Invalid media stream format')).classification).toBe('permanent');
    expect(classifyError(new Error('Corrupt artifact payload')).classification).toBe('permanent');
    expect(classifyError(new Error('Schema validation failed')).classification).toBe('permanent');

    expect(classifyError(new Error('Possible copyright claim detected')).classification).toBe('manual_review');
    expect(classifyError(new Error('Low confidence OCR transcription')).classification).toBe('manual_review');

    expect(classifyError(new Error('Worker timeout after 30s')).classification).toBe('retryable');
    expect(classifyError(new Error('Rate limit exceeded (429)')).classification).toBe('retryable');
    expect(classifyError(new Error('ECONNRESET connection reset')).classification).toBe('retryable');
  });

  it('evaluates retryable error and returns nextAvailableAt', () => {
    const job: VideoAuditJob = {
      id: 'job-001',
      referenceAssetId: 'ref-001',
      type: 'transcription',
      status: 'running',
      attempt: 1,
      maxAttempts: 4,
      idempotencyKey: 'key-1',
      inputArtifactKeys: [],
      outputArtifactKeys: [],
      schemaVersion: 'audit-job.v1',
      createdAt: '2026-09-02T12:00:00.000Z',
      availableAt: '2026-09-02T12:00:00.000Z'
    };

    const err: JobError = {
      code: 'TIMEOUT',
      message: 'Worker timeout',
      classification: 'retryable',
      occurredAt: '2026-09-02T12:00:10.000Z'
    };

    const baseTimeMs = 1756814400000;
    const decision = evaluateRetry(job, err, baseTimeMs);

    expect(decision.shouldRetry).toBe(true);
    expect(decision.nextAttempt).toBe(2);
    expect(new Date(decision.availableAt!).getTime()).toBe(baseTimeMs + 5_000);
  });

  it('exhausts retries when attempt >= maxAttempts', () => {
    const job: VideoAuditJob = {
      id: 'job-001',
      referenceAssetId: 'ref-001',
      type: 'transcription',
      status: 'running',
      attempt: 4,
      maxAttempts: 4,
      idempotencyKey: 'key-1',
      inputArtifactKeys: [],
      outputArtifactKeys: [],
      schemaVersion: 'audit-job.v1',
      createdAt: '2026-09-02T12:00:00.000Z',
      availableAt: '2026-09-02T12:00:00.000Z'
    };

    const err: JobError = {
      code: 'TIMEOUT',
      message: 'Worker timeout',
      classification: 'retryable',
      occurredAt: '2026-09-02T12:00:10.000Z'
    };

    const decision = evaluateRetry(job, err);
    expect(decision.shouldRetry).toBe(false);
    expect(decision.terminalStatus).toBe('permanent_error');
  });

  it('immediately refuses retry on permanent errors', () => {
    const job: VideoAuditJob = {
      id: 'job-001',
      referenceAssetId: 'ref-001',
      type: 'transcription',
      status: 'running',
      attempt: 1,
      maxAttempts: 4,
      idempotencyKey: 'key-1',
      inputArtifactKeys: [],
      outputArtifactKeys: [],
      schemaVersion: 'audit-job.v1',
      createdAt: '2026-09-02T12:00:00.000Z',
      availableAt: '2026-09-02T12:00:00.000Z'
    };

    const err: JobError = {
      code: 'CORRUPT_MEDIA',
      message: 'Invalid media format',
      classification: 'permanent',
      occurredAt: '2026-09-02T12:00:10.000Z'
    };

    const decision = evaluateRetry(job, err);
    expect(decision.shouldRetry).toBe(false);
    expect(decision.terminalStatus).toBe('permanent_error');
  });
});
