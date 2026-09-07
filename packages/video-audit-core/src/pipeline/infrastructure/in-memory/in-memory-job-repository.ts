/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/in-memory/in-memory-job-repository.ts"
# purpose: "In-Memory Thread-Safe Implementation of AuditJobRepository with State Machine Transitions."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditJob, AuditJobType, AuditJobStatus } from '../../domain/jobs/job.js';
import { validateJobTransition } from '../../domain/jobs/state-machine.js';
import { AuditJobRepository, JobTransitionInput, JobTransitionRecord } from '../../ports/job-repository.js';

export class InMemoryAuditJobRepository implements AuditJobRepository {
  private jobs: Map<string, VideoAuditJob> = new Map();
  private transitions: JobTransitionRecord[] = [];

  async create(job: VideoAuditJob): Promise<VideoAuditJob> {
    if (this.jobs.has(job.id)) {
      throw new Error(`Audit job '${job.id}' already exists.`);
    }
    const cloned = { ...job };
    this.jobs.set(job.id, cloned);
    this.transitions.push({
      jobId: job.id,
      fromStatus: 'none' as any,
      toStatus: 'queued',
      actorId: 'system',
      timestamp: job.createdAt,
      reason: 'Job created',
      attempt: job.attempt
    });
    return { ...cloned };
  }

  async getById(id: string): Promise<VideoAuditJob | null> {
    const found = this.jobs.get(id);
    return found ? { ...found } : null;
  }

  async getByIdempotencyKey(key: string): Promise<VideoAuditJob | null> {
    for (const j of this.jobs.values()) {
      if (j.idempotencyKey === key) {
        return { ...j };
      }
    }
    return null;
  }

  async leaseNext(
    workerId: string,
    now: string,
    leaseDurationSeconds: number = 30,
    jobTypes?: AuditJobType[]
  ): Promise<VideoAuditJob | null> {
    const nowDate = new Date(now).getTime();
    for (const job of this.jobs.values()) {
      if (job.status !== 'queued') continue;
      if (jobTypes && jobTypes.length > 0 && !jobTypes.includes(job.type)) continue;

      const availableAtTime = new Date(job.availableAt).getTime();
      if (availableAtTime > nowDate) continue;

      const leaseExpiresAt = new Date(nowDate + leaseDurationSeconds * 1000).toISOString();
      const fromStatus = job.status;
      job.status = 'leased';
      job.leasedBy = workerId;
      job.leasedUntil = leaseExpiresAt;

      this.transitions.push({
        jobId: job.id,
        fromStatus,
        toStatus: 'leased',
        actorId: workerId,
        timestamp: now,
        reason: 'Leased by worker',
        attempt: job.attempt
      });

      return { ...job };
    }
    return null;
  }

  async transition(input: JobTransitionInput): Promise<VideoAuditJob> {
    const job = this.jobs.get(input.jobId);
    if (!job) {
      throw new Error(`Job '${input.jobId}' not found for transition.`);
    }

    const fromStatus = job.status;
    validateJobTransition(job.id, fromStatus, input.toStatus, input.reason);

    if (input.attempt !== undefined) {
      job.attempt = input.attempt;
    }

    if (input.toStatus === 'running') {
      job.status = 'running';
      job.startedAt = input.timestamp;
    } else if (
      input.toStatus === 'succeeded' ||
      input.toStatus === 'permanent_error' ||
      input.toStatus === 'cancelled'
    ) {
      job.status = input.toStatus;
      job.finishedAt = input.timestamp;
      job.leasedUntil = undefined;
      job.leasedBy = undefined;
    } else if (input.toStatus === 'retryable_error') {
      job.status = 'queued';
      job.leasedUntil = undefined;
      job.leasedBy = undefined;
    } else if (input.toStatus === 'queued') {
      job.status = 'queued';
      job.leasedUntil = undefined;
      job.leasedBy = undefined;
    } else {
      job.status = input.toStatus;
    }

    if (input.availableAt !== undefined) {
      job.availableAt = input.availableAt;
    }
    if (input.lastError !== undefined) {
      job.lastError = input.lastError;
    }
    if (input.outputArtifactKeys !== undefined) {
      job.outputArtifactKeys = [...input.outputArtifactKeys];
    }

    const record: JobTransitionRecord = {
      jobId: job.id,
      fromStatus,
      toStatus: job.status,
      actorId: input.actorId,
      timestamp: input.timestamp,
      reason: input.reason,
      attempt: job.attempt
    };
    this.transitions.push(record);

    return { ...job };
  }

  async releaseExpiredLeases(now: string): Promise<number> {
    const nowDate = new Date(now).getTime();
    let releasedCount = 0;

    for (const job of this.jobs.values()) {
      if (job.status === 'leased' || job.status === 'running') {
        if (job.leasedUntil && new Date(job.leasedUntil).getTime() < nowDate) {
          const fromStatus = job.status;
          job.status = 'queued';
          job.leasedBy = undefined;
          job.leasedUntil = undefined;
          releasedCount++;

          this.transitions.push({
            jobId: job.id,
            fromStatus,
            toStatus: 'queued',
            actorId: 'system',
            timestamp: now,
            reason: 'Lease expired and reclaimed',
            attempt: job.attempt
          });
        }
      }
    }

    return releasedCount;
  }

  async getTransitionsForJob(jobId: string): Promise<JobTransitionRecord[]> {
    return this.transitions.filter((t) => t.jobId === jobId).map((t) => ({ ...t }));
  }

  async listJobs(filter?: {
    status?: AuditJobStatus;
    referenceAssetId?: string;
    type?: AuditJobType;
  }): Promise<VideoAuditJob[]> {
    let result = Array.from(this.jobs.values());
    if (filter?.status) {
      result = result.filter((j) => j.status === filter.status);
    }
    if (filter?.referenceAssetId) {
      result = result.filter((j) => j.referenceAssetId === filter.referenceAssetId);
    }
    if (filter?.type) {
      result = result.filter((j) => j.type === filter.type);
    }
    return result.map((j) => ({ ...j }));
  }
}

export { InMemoryAuditJobRepository as InMemoryJobRepository };
