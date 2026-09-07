/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/jobs/state-machine.ts"
# purpose: "Deterministic Finite State Machine & Transition Rules for Video Audit Jobs."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { AuditJobStatus, VideoAuditJob } from './job.js';

export class InvalidJobTransitionError extends Error {
  public readonly fromStatus: AuditJobStatus;
  public readonly toStatus: AuditJobStatus;
  public readonly jobId: string;

  constructor(jobId: string, fromStatus: AuditJobStatus, toStatus: AuditJobStatus, reason?: string) {
    const msg = `Invalid state transition for job '${jobId}': cannot transition from '${fromStatus}' to '${toStatus}'.${
      reason ? ` Reason: ${reason}` : ''
    }`;
    super(msg);
    this.name = 'InvalidJobTransitionError';
    this.jobId = jobId;
    this.fromStatus = fromStatus;
    this.toStatus = toStatus;
    Object.setPrototypeOf(this, InvalidJobTransitionError.prototype);
  }
}

export interface JobTransitionRecord {
  jobId: string;
  fromStatus: AuditJobStatus;
  toStatus: AuditJobStatus;
  actorId: string;
  timestamp: string;
  reason?: string;
  attempt: number;
}

/**
 * Strict state transition matrix:
 *
 * QUEUED         -> LEASED
 * LEASED         -> RUNNING
 * LEASED         -> QUEUED (lease expired / reclaimed)
 * RUNNING        -> SUCCEEDED
 * RUNNING        -> RETRYABLE_ERROR
 * RUNNING        -> PERMANENT_ERROR
 * RUNNING        -> CANCELLED
 * RETRYABLE_ERROR-> QUEUED (scheduled retry)
 *
 * Terminal states (no outgoing transitions allowed):
 * SUCCEEDED
 * PERMANENT_ERROR
 * CANCELLED
 */
export const ALLOWED_JOB_TRANSITIONS: Readonly<Record<AuditJobStatus, readonly AuditJobStatus[]>> = {
  queued: ['leased'],
  leased: ['running', 'queued'],
  running: ['succeeded', 'retryable_error', 'permanent_error', 'cancelled'],
  retryable_error: ['queued', 'permanent_error'],
  succeeded: [],
  permanent_error: [],
  cancelled: []
};

export function canTransition(from: AuditJobStatus, to: AuditJobStatus): boolean {
  const allowed = ALLOWED_JOB_TRANSITIONS[from];
  return Boolean(allowed && allowed.includes(to));
}

export function validateTransition(
  jobId: string,
  from: AuditJobStatus,
  to: AuditJobStatus,
  reason?: string
): void {
  if (!canTransition(from, to)) {
    throw new InvalidJobTransitionError(jobId, from, to, reason);
  }
}

export const validateJobTransition = validateTransition;

export function applyJobTransition(
  job: VideoAuditJob,
  toStatus: AuditJobStatus,
  actorId: string,
  timestamp: string,
  reason?: string
): { updatedJob: VideoAuditJob; transitionRecord: JobTransitionRecord } {
  validateTransition(job.id, job.status, toStatus, reason);

  const transitionRecord: JobTransitionRecord = {
    jobId: job.id,
    fromStatus: job.status,
    toStatus,
    actorId,
    timestamp,
    reason,
    attempt: job.attempt
  };

  const updatedJob: VideoAuditJob = {
    ...job,
    status: toStatus
  };

  if (toStatus === 'leased') {
    updatedJob.leasedBy = actorId;
  } else if (toStatus === 'running') {
    if (!updatedJob.startedAt) {
      updatedJob.startedAt = timestamp;
    }
  } else if (toStatus === 'succeeded' || toStatus === 'permanent_error' || toStatus === 'cancelled') {
    updatedJob.finishedAt = timestamp;
    updatedJob.leasedUntil = undefined;
    updatedJob.leasedBy = undefined;
  } else if (toStatus === 'queued') {
    updatedJob.leasedUntil = undefined;
    updatedJob.leasedBy = undefined;
  }

  return { updatedJob, transitionRecord };
}
