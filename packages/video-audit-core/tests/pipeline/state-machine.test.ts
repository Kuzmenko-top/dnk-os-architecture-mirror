/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/state-machine.test.ts"
# purpose: "Unit Tests for VideoAuditJob State Machine Transitions and Constraints."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  canTransition,
  validateTransition,
  applyJobTransition,
  InvalidJobTransitionError,
  ALLOWED_JOB_TRANSITIONS
} from '../../src/pipeline/domain/jobs/state-machine.js';
import { VideoAuditJob } from '../../src/pipeline/domain/jobs/job.js';

describe('VideoAuditJob State Machine', () => {
  const sampleJob: VideoAuditJob = {
    id: 'job-123',
    referenceAssetId: 'ref-456',
    type: 'transcription',
    status: 'queued',
    attempt: 1,
    maxAttempts: 5,
    idempotencyKey: 'ref-456:transcription:v1:whisperx-v1',
    inputArtifactKeys: [],
    outputArtifactKeys: [],
    schemaVersion: 'audit-job.v1',
    createdAt: '2026-09-02T12:00:00.000Z',
    availableAt: '2026-09-02T12:00:00.000Z'
  };

  it('allows all defined canonical transitions', () => {
    expect(canTransition('queued', 'leased')).toBe(true);
    expect(canTransition('leased', 'running')).toBe(true);
    expect(canTransition('leased', 'queued')).toBe(true); // lease expiry recovery
    expect(canTransition('running', 'succeeded')).toBe(true);
    expect(canTransition('running', 'retryable_error')).toBe(true);
    expect(canTransition('running', 'permanent_error')).toBe(true);
    expect(canTransition('running', 'cancelled')).toBe(true);
    expect(canTransition('retryable_error', 'queued')).toBe(true); // retry re-queue
    expect(canTransition('retryable_error', 'permanent_error')).toBe(true);
  });

  it('strictly prohibits invalid/terminal transitions', () => {
    expect(canTransition('succeeded', 'running')).toBe(false);
    expect(canTransition('succeeded', 'queued')).toBe(false);
    expect(canTransition('permanent_error', 'queued')).toBe(false);
    expect(canTransition('permanent_error', 'running')).toBe(false);
    expect(canTransition('cancelled', 'running')).toBe(false);
    expect(canTransition('queued', 'running')).toBe(false); // must be leased first
    expect(canTransition('queued', 'succeeded')).toBe(false);
  });

  it('throws InvalidJobTransitionError on invalid transition attempts', () => {
    expect(() => {
      validateTransition('job-123', 'succeeded', 'running', 'attempt to restart finished job');
    }).toThrow(InvalidJobTransitionError);

    try {
      validateTransition('job-999', 'permanent_error', 'queued');
    } catch (err: any) {
      expect(err).toBeInstanceOf(InvalidJobTransitionError);
      expect(err.jobId).toBe('job-999');
      expect(err.fromStatus).toBe('permanent_error');
      expect(err.toStatus).toBe('queued');
    }
  });

  it('applies transitions and records audit trail cleanly', () => {
    const timestamp = '2026-09-02T12:01:00.000Z';
    const { updatedJob, transitionRecord } = applyJobTransition(
      sampleJob,
      'leased',
      'worker-alpha',
      timestamp,
      'Lease acquired'
    );

    expect(updatedJob.status).toBe('leased');
    expect(updatedJob.leasedBy).toBe('worker-alpha');
    expect(transitionRecord.jobId).toBe('job-123');
    expect(transitionRecord.fromStatus).toBe('queued');
    expect(transitionRecord.toStatus).toBe('leased');
    expect(transitionRecord.actorId).toBe('worker-alpha');
    expect(transitionRecord.timestamp).toBe(timestamp);
    expect(transitionRecord.attempt).toBe(1);
  });
});
