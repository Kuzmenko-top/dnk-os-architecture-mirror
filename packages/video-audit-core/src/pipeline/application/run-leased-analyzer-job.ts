/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/application/run-leased-analyzer-job.ts"
# purpose: "Generic Application Helper for Atomic VideoAuditJob Lifecycle Transitions (leased -> running -> succeeded/failed)."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditJob, JobErrorClassification } from '../domain/jobs/job.js';
import { AuditJobRepository } from '../ports/job-repository.js';

export interface RunLeasedAnalyzerJobInput<TResult> {
  jobStore: AuditJobRepository;
  workerId: string;
  leasedJob: VideoAuditJob;
  execute: (job: VideoAuditJob) => Promise<TResult>;
  persistArtifact: (result: TResult, job: VideoAuditJob) => Promise<{ outputArtifactKeys: string[]; mainArtifactKey?: string; sha256?: string; artifactType?: string; schemaVersion?: string }>;
  publishEvent?: (result: TResult, job: VideoAuditJob, outputArtifactKeys: string[], mainArtifactKey: string, sha256: string, schemaVersion: string) => Promise<void>;
  errorCode?: string;
}

export async function runLeasedAnalyzerJob<TResult>(
  input: RunLeasedAnalyzerJobInput<TResult>
): Promise<VideoAuditJob> {
  const { jobStore, workerId, leasedJob, execute, persistArtifact, publishEvent, errorCode = 'ANALYZER_JOB_FAILED' } = input;

  // 1. Transition from 'leased' to 'running'
  const runningJob = await jobStore.transition({
    jobId: leasedJob.id,
    toStatus: 'running',
    actorId: workerId,
    timestamp: new Date().toISOString()
  });

  try {
    // 2. Execute the actual work using the updated runningJob
    const result = await execute(runningJob);

    // 3. Persist the generated artifact
    const persistResult = await persistArtifact(result, runningJob);
    const { outputArtifactKeys, mainArtifactKey, sha256, artifactType, schemaVersion } = persistResult;

    // 4. Transition from 'running' to 'succeeded'
    const completedJob = await jobStore.transition({
      jobId: runningJob.id,
      toStatus: 'succeeded',
      actorId: workerId,
      timestamp: new Date().toISOString(),
      outputArtifactKeys
    });

    // 5. Optionally publish the event
    if (publishEvent && mainArtifactKey && sha256 && artifactType && schemaVersion) {
      await publishEvent(result, runningJob, outputArtifactKeys, mainArtifactKey, sha256, schemaVersion);
    }

    return completedJob;
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    const classification: JobErrorClassification = errorMsg.includes('permanent') ? 'permanent' : 'retryable';

    return await jobStore.transition({
      jobId: runningJob.id,
      toStatus: classification === 'permanent' ? 'permanent_error' : 'retryable_error',
      actorId: workerId,
      timestamp: new Date().toISOString(),
      lastError: {
        code: errorCode,
        message: errorMsg,
        classification,
        occurredAt: new Date().toISOString()
      }
    });
  }
}
