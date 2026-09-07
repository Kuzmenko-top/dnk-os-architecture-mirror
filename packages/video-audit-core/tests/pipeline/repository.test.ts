/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/repository.test.ts"
# purpose: "Unit Tests for In-Memory Audit Job Repository Atomic Leases and Expiry."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect, beforeEach } from 'vitest';
import { InMemoryJobRepository } from '../../src/pipeline/infrastructure/in-memory/in-memory-job-repository.js';
import { VideoAuditJob } from '../../src/pipeline/domain/jobs/job.js';

describe('InMemoryJobRepository', () => {
  let repo: InMemoryJobRepository;

  beforeEach(() => {
    repo = new InMemoryJobRepository();
  });

  const createSampleJob = (id: string, key: string, availableAt = '2026-09-02T12:00:00.000Z'): VideoAuditJob => ({
    id,
    referenceAssetId: 'ref-001',
    type: 'transcription',
    status: 'queued',
    attempt: 1,
    maxAttempts: 3,
    idempotencyKey: key,
    inputArtifactKeys: [],
    outputArtifactKeys: [],
    schemaVersion: 'audit-job.v1',
    createdAt: '2026-09-02T12:00:00.000Z',
    availableAt
  });

  it('prevents two workers from leasing the same job simultaneously', async () => {
    const job = createSampleJob('job-1', 'key-1');
    await repo.create(job);

    const now = '2026-09-02T12:00:00.000Z';
    const lease1 = await repo.leaseNext('worker-A', now, 30);
    expect(lease1).not.toBeNull();
    expect(lease1?.id).toBe('job-1');
    expect(lease1?.status).toBe('leased');
    expect(lease1?.leasedBy).toBe('worker-A');

    // Worker B tries to lease at the same time
    const lease2 = await repo.leaseNext('worker-B', now, 30);
    expect(lease2).toBeNull(); // No jobs available to lease
  });

  it('reclaims expired leases and returns them to queued status', async () => {
    const job = createSampleJob('job-1', 'key-1');
    await repo.create(job);

    const leaseTime = '2026-09-02T12:00:00.000Z';
    await repo.leaseNext('worker-A', leaseTime, 30); // leasedUntil = 12:00:30

    // After 40 seconds, worker hasn't updated the job -> lease expired
    const checkTime = '2026-09-02T12:00:40.000Z';
    const reclaimedCount = await repo.releaseExpiredLeases(checkTime);
    expect(reclaimedCount).toBe(1);

    const updatedJob = await repo.getById('job-1');
    expect(updatedJob?.status).toBe('queued');
    expect(updatedJob?.leasedBy).toBeUndefined();
    expect(updatedJob?.leasedUntil).toBeUndefined();

    // Now worker B can successfully lease it
    const leaseB = await repo.leaseNext('worker-B', checkTime, 30);
    expect(leaseB).not.toBeNull();
    expect(leaseB?.id).toBe('job-1');
    expect(leaseB?.leasedBy).toBe('worker-B');
  });

  it('records full audit transition history', async () => {
    const job = createSampleJob('job-1', 'key-1');
    await repo.create(job);

    await repo.leaseNext('worker-A', '2026-09-02T12:00:00.000Z', 30);
    await repo.transition({
      jobId: 'job-1',
      toStatus: 'running',
      actorId: 'worker-A',
      timestamp: '2026-09-02T12:00:05.000Z'
    });
    await repo.transition({
      jobId: 'job-1',
      toStatus: 'succeeded',
      actorId: 'worker-A',
      timestamp: '2026-09-02T12:00:20.000Z',
      outputArtifactKeys: ['references/ref-001/transcript/v1.json']
    });

    const transitions = await repo.getTransitionsForJob('job-1');
    expect(transitions.length).toBe(4);
    expect(transitions[0].toStatus).toBe('queued');
    expect(transitions[1].toStatus).toBe('leased');
    expect(transitions[2].toStatus).toBe('running');
    expect(transitions[3].toStatus).toBe('succeeded');
  });
});
