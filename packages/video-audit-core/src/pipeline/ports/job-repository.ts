/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/job-repository.ts"
# purpose: "Port Interface for VideoAuditJob Persistence and Atomic Lease Operations."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditJob, AuditJobStatus, AuditJobType, JobError } from '../domain/jobs/job.js';
import { JobTransitionRecord } from '../domain/jobs/state-machine.js';

export type { JobTransitionRecord };

export interface JobTransitionInput {
  jobId: string;
  toStatus: AuditJobStatus;
  actorId: string;
  timestamp: string;
  reason?: string;
  leasedUntil?: string;
  leasedBy?: string;
  outputArtifactKeys?: string[];
  lastError?: JobError;
  availableAt?: string;
  incrementAttempt?: boolean;
  attempt?: number;
}

export interface AuditJobRepository {
  create(job: VideoAuditJob): Promise<VideoAuditJob>;
  getById(id: string): Promise<VideoAuditJob | null>;
  getByIdempotencyKey(key: string): Promise<VideoAuditJob | null>;
  leaseNext(workerId: string, now: string, leaseDurationSeconds?: number, jobTypes?: AuditJobType[]): Promise<VideoAuditJob | null>;
  transition(input: JobTransitionInput): Promise<VideoAuditJob>;
  releaseExpiredLeases(now: string): Promise<number>;
  getTransitionsForJob(jobId: string): Promise<JobTransitionRecord[]>;
  listJobs(filter?: {
    referenceAssetId?: string;
    type?: AuditJobType;
    status?: AuditJobStatus;
  }): Promise<VideoAuditJob[]>;
}
