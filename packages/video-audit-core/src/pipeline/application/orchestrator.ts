/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/application/orchestrator.ts"
# purpose: "High-Reliability Application Orchestrator for Video Audit Job Lifecycles."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { AuditJobRepository } from '../ports/job-repository.js';
import { ArtifactStore } from '../ports/artifact-store.js';
import { AuditEventBus } from '../ports/event-bus.js';
import { Clock } from '../ports/clock.js';
import { IdGenerator } from '../ports/id-generator.js';
import { VideoAuditJob, SubmitAuditJobInput, createAuditJob, JobError, AuditJobType } from '../domain/jobs/job.js';
import { calculateBackoffMs } from '../domain/retry-policy.js';

export interface OrchestratorOptions {
  workerId?: string;
  leaseDurationSeconds?: number;
  eventBus?: AuditEventBus;
  clock?: Clock;
  idGenerator?: IdGenerator;
  nowFn?: () => string;
}

export interface OrchestratorConstructorObject extends OrchestratorOptions {
  jobRepository: AuditJobRepository;
  artifactStore: ArtifactStore;
}

export class VideoAuditOrchestrator {
  private jobRepo: AuditJobRepository;
  private artifactStore: ArtifactStore;
  private eventBus?: AuditEventBus;
  private clock?: Clock;
  private idGenerator?: IdGenerator;
  private options: OrchestratorOptions;

  constructor(
    jobRepoOrConfig: AuditJobRepository | OrchestratorConstructorObject,
    artifactStore?: ArtifactStore,
    options: OrchestratorOptions = {}
  ) {
    if (jobRepoOrConfig && typeof (jobRepoOrConfig as any).create === 'function') {
      this.jobRepo = jobRepoOrConfig as AuditJobRepository;
      this.artifactStore = artifactStore!;
      this.options = options;
      this.eventBus = options.eventBus;
      this.clock = options.clock;
      this.idGenerator = options.idGenerator;
    } else {
      const config = jobRepoOrConfig as OrchestratorConstructorObject;
      this.jobRepo = config.jobRepository;
      this.artifactStore = config.artifactStore;
      this.options = config;
      this.eventBus = config.eventBus;
      this.clock = config.clock;
      this.idGenerator = config.idGenerator;
    }
  }

  private now(): string {
    if (this.clock) return this.clock.nowIso();
    if (this.options.nowFn) return this.options.nowFn();
    return new Date().toISOString();
  }

  private async publishEvent(type: string, aggregateId: string, payload: Record<string, any>): Promise<void> {
    if (this.eventBus && typeof (this.eventBus as any).publish === 'function') {
      await (this.eventBus as any).publish({
        id: `evt_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
        type,
        aggregateId,
        timestamp: this.now(),
        payload
      });
    }
  }

  async submitJob(
    input: SubmitAuditJobInput
  ): Promise<{ job: VideoAuditJob; isNew: boolean }> {
    const nowIso = this.now();
    const idempotencyKey =
      input.idempotencyKey ??
      `${input.referenceAssetId}:${input.type}:${input.inputVersion ?? 'v1'}:${input.processorVersion ?? 'default-v1'}`;

    const existing = await this.jobRepo.getByIdempotencyKey(idempotencyKey);
    if (existing) {
      return { job: existing, isNew: false };
    }

    const job = createAuditJob({ ...input, idempotencyKey }, nowIso);
    const created = await this.jobRepo.create(job);

    await this.publishEvent('AuditJobCreated.v1', created.id, { job: created });

    return { job: created, isNew: true };
  }

  async enqueueJob(
    input: SubmitAuditJobInput
  ): Promise<{ job: VideoAuditJob; isNew: boolean }> {
    return this.submitJob(input);
  }

  async getJobByIdempotencyKey(key: string): Promise<VideoAuditJob | null> {
    return this.jobRepo.getByIdempotencyKey(key);
  }

  async releaseExpiredLeases(): Promise<number> {
    const nowIso = this.now();
    return this.jobRepo.releaseExpiredLeases(nowIso);
  }

  async reclaimExpiredLeases(): Promise<number> {
    return this.releaseExpiredLeases();
  }

  async pollAndExecuteNext(
    workerFnOrTypesOrConfig?: any,
    workerFnOrTypes2?: any
  ): Promise<{ executed: boolean; job: VideoAuditJob; error?: JobError } | null> {
    let workerFn: ((job: VideoAuditJob, store: ArtifactStore) => Promise<any>) | undefined;
    let jobTypes: AuditJobType[] | undefined;
    let customWorkerId: string | undefined;

    if (typeof workerFnOrTypesOrConfig === 'string') {
      customWorkerId = workerFnOrTypesOrConfig;
      if (typeof workerFnOrTypes2 === 'function') {
        workerFn = workerFnOrTypes2;
      }
    } else if (typeof workerFnOrTypesOrConfig === 'function') {
      workerFn = workerFnOrTypesOrConfig;
      if (Array.isArray(workerFnOrTypes2)) {
        jobTypes = workerFnOrTypes2;
      }
    } else if (typeof workerFnOrTypes2 === 'function') {
      workerFn = workerFnOrTypes2;
      if (Array.isArray(workerFnOrTypesOrConfig)) {
        jobTypes = workerFnOrTypesOrConfig;
      } else if (workerFnOrTypesOrConfig && typeof workerFnOrTypesOrConfig === 'object') {
        jobTypes = workerFnOrTypesOrConfig.jobTypes ?? workerFnOrTypesOrConfig.types;
      }
    } else if (workerFnOrTypesOrConfig && typeof workerFnOrTypesOrConfig === 'object') {
      workerFn = workerFnOrTypesOrConfig.workerFn ?? workerFnOrTypesOrConfig.processor ?? workerFnOrTypesOrConfig.execute;
      jobTypes = workerFnOrTypesOrConfig.jobTypes ?? workerFnOrTypesOrConfig.types;
    }

    if (!workerFn) {
      return null;
    }

    const nowIso = this.now();
    const workerId = customWorkerId ?? this.options.workerId ?? 'orchestrator-worker';
    const leaseDuration = this.options.leaseDurationSeconds ?? 30;

    const leasedJob = await this.jobRepo.leaseNext(
      workerId,
      nowIso,
      leaseDuration,
      jobTypes
    );

    if (!leasedJob) {
      return null;
    }

    await this.publishEvent('AuditJobLeased.v1', leasedJob.id, { job: leasedJob, workerId });

    const runningJob = await this.jobRepo.transition({
      jobId: leasedJob.id,
      toStatus: 'running',
      actorId: workerId,
      timestamp: nowIso,
      reason: 'Leased and executing worker function'
    });

    await this.publishEvent('AuditJobRunning.v1', runningJob.id, { job: runningJob, workerId });

    try {
      const rawResult = await workerFn(runningJob, this.artifactStore);

      if (rawResult && typeof rawResult === 'object' && 'status' in rawResult) {
        const workerRes = rawResult as {
          status: string;
          outputArtifactKeys?: string[];
          error?: any;
        };

        if (workerRes.status === 'succeeded') {
          const finishedJob = await this.jobRepo.transition({
            jobId: runningJob.id,
            toStatus: 'succeeded',
            actorId: workerId,
            timestamp: this.now(),
            outputArtifactKeys: (workerRes.outputArtifactKeys as string[]) ?? [],
            reason: 'Worker succeeded'
          });

          await this.publishEvent('AuditJobSucceeded.v1', finishedJob.id, { job: finishedJob });

          return { executed: true, job: finishedJob };
        } else if (workerRes.status === 'retryable_error') {
          const errCode = (workerRes.error as any)?.code ?? 'WORKER_RETRYABLE_ERROR';
          const errMsg = (workerRes.error as any)?.message ?? String(workerRes.error ?? 'Retryable error');
          const err: JobError = {
            code: errCode,
            message: errMsg,
            classification: 'retryable',
            occurredAt: this.now()
          };
          const updatedJob = await this.handleJobFailure(runningJob, err, workerId);
          return { executed: true, job: updatedJob, error: err };
        } else {
          const errCode = (workerRes.error as any)?.code ?? 'WORKER_PERMANENT_ERROR';
          const errMsg = (workerRes.error as any)?.message ?? String(workerRes.error ?? 'Permanent error');
          const err: JobError = {
            code: errCode,
            message: errMsg,
            classification: 'permanent',
            occurredAt: this.now()
          };
          const updatedJob = await this.handleJobFailure(runningJob, err, workerId);
          return { executed: true, job: updatedJob, error: err };
        }
      }

      const outputArtifacts = Array.isArray(rawResult) ? rawResult : [];
      const keys = outputArtifacts.map((m: any) => m.key ?? m.id ?? String(m));

      const finishedJob = await this.jobRepo.transition({
        jobId: runningJob.id,
        toStatus: 'succeeded',
        actorId: workerId,
        timestamp: this.now(),
        outputArtifactKeys: keys,
        reason: 'Worker function completed'
      });

      await this.publishEvent('AuditJobSucceeded.v1', finishedJob.id, { job: finishedJob });

      return { executed: true, job: finishedJob };
    } catch (unhandledErr: any) {
      const err: JobError = {
        code: unhandledErr?.code ?? 'UNHANDLED_WORKER_EXCEPTION',
        message: unhandledErr?.message ?? String(unhandledErr),
        classification: 'retryable',
        occurredAt: this.now()
      };
      const updatedJob = await this.handleJobFailure(runningJob, err, workerId);
      return { executed: true, job: updatedJob, error: err };
    }
  }

  private async handleJobFailure(
    job: VideoAuditJob,
    error: JobError,
    workerId: string
  ): Promise<VideoAuditJob> {
    const nowIso = this.now();
    const isRetryable =
      error.classification === 'retryable' && job.attempt < job.maxAttempts;

    if (isRetryable) {
      const delayMs = calculateBackoffMs(job.attempt);
      const nextTime = new Date(new Date(nowIso).getTime() + delayMs).toISOString();

      const updated = await this.jobRepo.transition({
        jobId: job.id,
        toStatus: 'retryable_error',
        actorId: workerId,
        timestamp: nowIso,
        availableAt: nextTime,
        attempt: job.attempt + 1,
        reason: `Retryable failure on attempt ${job.attempt}: ${error.message}`,
        lastError: error
      });

      await this.publishEvent('AuditJobRetryScheduled.v1', updated.id, { job: updated, retryAt: nextTime, error });

      return updated;
    }

    const updated = await this.jobRepo.transition({
      jobId: job.id,
      toStatus: 'permanent_error',
      actorId: workerId,
      timestamp: nowIso,
      reason: `Job permanently failed: ${error.message}`,
      lastError: error
    });

    await this.publishEvent('AuditJobFailed.v1', updated.id, { job: updated, error });

    return updated;
  }
}
