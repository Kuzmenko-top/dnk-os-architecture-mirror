/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/orchestration-integration.test.ts"
# purpose: "Integration Tests for Video Audit Pipeline Orchestrator, Fake Workers, Retries, and Recovery."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect, beforeEach } from 'vitest';
import { VideoAuditOrchestrator } from '../../src/pipeline/application/orchestrator.js';
import { InMemoryJobRepository } from '../../src/pipeline/infrastructure/in-memory/in-memory-job-repository.js';
import { InMemoryArtifactStore } from '../../src/pipeline/infrastructure/in-memory/in-memory-artifact-store.js';
import { InMemoryEventBus } from '../../src/pipeline/infrastructure/in-memory/in-memory-event-bus.js';
import { DeterministicFakeWorker } from '../../src/pipeline/infrastructure/fake-worker/deterministic-fake-worker.js';
import { FixedClock } from '../../src/pipeline/infrastructure/system/system-clock.js';
import { DeterministicIdGenerator } from '../../src/pipeline/infrastructure/system/uuid-id-generator.js';
import { AuditEvent } from '../../src/pipeline/domain/events/events.js';
import { toDomainJob, toDomainArtifactManifest } from '../../src/pipeline/dto/mappers.js';
import { SchemaVersionMismatchError } from '../../src/validation/errors.js';

describe('Video Audit Orchestrator Integration Suite', () => {
  let repository: InMemoryJobRepository;
  let artifactStore: InMemoryArtifactStore;
  let eventBus: InMemoryEventBus;
  let clock: FixedClock;
  let idGenerator: DeterministicIdGenerator;
  let orchestrator: VideoAuditOrchestrator;
  let fakeWorker: DeterministicFakeWorker;
  let recordedEvents: AuditEvent[];

  beforeEach(async () => {
    repository = new InMemoryJobRepository();
    artifactStore = new InMemoryArtifactStore();
    eventBus = new InMemoryEventBus();
    clock = new FixedClock('2026-09-02T12:00:00.000Z');
    idGenerator = new DeterministicIdGenerator();
    orchestrator = new VideoAuditOrchestrator({
      jobRepository: repository,
      artifactStore,
      eventBus,
      clock,
      idGenerator
    });
    fakeWorker = new DeterministicFakeWorker('worker-alpha', artifactStore);
    recordedEvents = [];

    await eventBus.subscribe('*', async (event) => {
      recordedEvents.push(event);
    });
  });

  it('executes full canonical flow: submit -> lease -> run -> success', async () => {
    const { job, isNew } = await orchestrator.submitJob({
      referenceAssetId: 'ref_001',
      type: 'transcription',
      inputVersion: 'v1',
      processorVersion: 'whisperx-v1'
    });

    expect(isNew).toBe(true);
    expect(job.status).toBe('queued');
    expect(job.attempt).toBe(1);

    // Verify AuditJobCreated event
    expect(recordedEvents.some((e) => e.type === 'AuditJobCreated.v1')).toBe(true);

    // Worker polls and processes next job
    const result = await orchestrator.pollAndExecuteNext('worker-alpha', async (j, store) => {
      return fakeWorker.processJob(j);
    });

    expect(result).not.toBeNull();
    expect(result?.job.status).toBe('succeeded');
    expect(result?.job.finishedAt).toBeDefined();
    expect(result?.job.outputArtifactKeys.length).toBeGreaterThan(0);

    // Verify artifact stored in artifact store
    const outputKey = result!.job.outputArtifactKeys[0];
    const artifactExists = await artifactStore.exists(outputKey);
    expect(artifactExists).toBe(true);

    // Verify transition events
    const eventTypes = recordedEvents.map((e) => e.type);
    expect(eventTypes).toContain('AuditJobCreated.v1');
    expect(eventTypes).toContain('AuditJobLeased.v1');
    expect(eventTypes).toContain('AuditJobRunning.v1');
    expect(eventTypes).toContain('AuditJobSucceeded.v1');
  });

  it('guarantees idempotency on duplicate job submission', async () => {
    const submitInput = {
      referenceAssetId: 'ref_001',
      type: 'transcription' as const,
      inputVersion: 'v1',
      processorVersion: 'whisperx-v1'
    };

    const first = await orchestrator.submitJob(submitInput);
    expect(first.isNew).toBe(true);

    const initialEventCount = recordedEvents.length;

    // Resubmitting exact same job
    const second = await orchestrator.submitJob(submitInput);
    expect(second.isNew).toBe(false);
    expect(second.job.id).toBe(first.job.id);
    expect(recordedEvents.length).toBe(initialEventCount); // No duplicate events fired
  });

  it('handles retryable error by scheduling delayed retry and succeeding on next attempt', async () => {
    const { job } = await orchestrator.submitJob({
      referenceAssetId: 'ref_retry_001',
      type: 'scene_extraction',
      inputVersion: 'v1',
      processorVersion: 'scenedetect-v1'
    });

    let executionCount = 0;

    // First attempt: simulate transient timeout
    const firstExecResult = await orchestrator.pollAndExecuteNext('worker-alpha', async (j) => {
      executionCount++;
      return {
        status: 'retryable_error',
        error: {
          code: 'TIMEOUT',
          message: 'Worker execution timed out',
          classification: 'retryable',
          occurredAt: clock.nowIso()
        }
      };
    });

    expect(firstExecResult?.job.status).toBe('queued'); // Re-queued for delayed retry
    expect(firstExecResult?.job.attempt).toBe(2);
    expect(firstExecResult?.job.lastError?.code).toBe('TIMEOUT');
    expect(recordedEvents.some((e) => e.type === 'AuditJobRetryScheduled.v1')).toBe(true);

    // Immediate poll should yield null because availableAt is in the future (+5 seconds)
    const prematurePoll = await orchestrator.pollAndExecuteNext('worker-alpha');
    expect(prematurePoll).toBeNull();

    // Advance clock by 6 seconds
    clock.advanceMs(6_000);

    // Second attempt: succeeds
    const secondExecResult = await orchestrator.pollAndExecuteNext('worker-alpha', async (j, store) => {
      executionCount++;
      return fakeWorker.processJob(j);
    });

    expect(secondExecResult).not.toBeNull();
    expect(secondExecResult?.job.status).toBe('succeeded');
    expect(secondExecResult?.job.attempt).toBe(2);
    expect(executionCount).toBe(2);
  });

  it('immediately fails permanently on non-retryable errors', async () => {
    await orchestrator.submitJob({
      referenceAssetId: 'ref_corrupt_001',
      type: 'ocr',
      inputVersion: 'v1',
      processorVersion: 'tesseract-v1'
    });

    const execResult = await orchestrator.pollAndExecuteNext('worker-alpha', async () => {
      return {
        status: 'permanent_error',
        error: {
          code: 'CORRUPT_MEDIA',
          message: 'Invalid video container format',
          classification: 'permanent',
          occurredAt: clock.nowIso()
        }
      };
    });

    expect(execResult?.job.status).toBe('permanent_error');
    expect(execResult?.job.lastError?.classification).toBe('permanent');
    expect(recordedEvents.some((e) => e.type === 'AuditJobFailed.v1')).toBe(true);

    // Should not be available for lease anymore
    const subsequentPoll = await orchestrator.pollAndExecuteNext('worker-alpha');
    expect(subsequentPoll).toBeNull();
  });

  it('reclaims expired worker leases during health reap cycle', async () => {
    const { job } = await orchestrator.submitJob({
      referenceAssetId: 'ref_expired_001',
      type: 'audio_analysis',
      inputVersion: 'v1',
      processorVersion: 'pyannote-v1'
    });

    // Worker leases job with 30s timeout
    await repository.leaseNext('crashed-worker', clock.nowIso(), 30);

    // Advance clock past lease expiration (e.g. 45s)
    clock.advanceMs(45_000);

    const reclaimedCount = await orchestrator.reclaimExpiredLeases();
    expect(reclaimedCount).toBe(1);

    // Job is available to be leased by a healthy worker
    const recoveredLease = await repository.leaseNext('healthy-worker', clock.nowIso(), 30);
    expect(recoveredLease).not.toBeNull();
    expect(recoveredLease?.id).toBe(job.id);
    expect(recoveredLease?.leasedBy).toBe('healthy-worker');
  });

  it('rejects unsupported schema versions in DTO mapping', () => {
    const invalidJobPayload = {
      schemaVersion: 'audit-job.v999',
      id: 'job-invalid',
      referenceAssetId: 'ref-1',
      type: 'transcription',
      status: 'queued',
      attempt: 1,
      maxAttempts: 5,
      idempotencyKey: 'key-invalid',
      inputArtifactKeys: [],
      outputArtifactKeys: [],
      createdAt: clock.nowIso(),
      availableAt: clock.nowIso()
    };

    expect(() => {
      toDomainJob(invalidJobPayload);
    }).toThrow(SchemaVersionMismatchError);

    const invalidManifestPayload = {
      schemaVersion: 'artifact-manifest.v999',
      key: 'key-1',
      referenceAssetId: 'ref-1',
      sha256: 'abc',
      byteSize: 100,
      mimeType: 'application/json',
      createdAt: clock.nowIso()
    };

    expect(() => {
      toDomainArtifactManifest(invalidManifestPayload);
    }).toThrow(SchemaVersionMismatchError);
  });
});
