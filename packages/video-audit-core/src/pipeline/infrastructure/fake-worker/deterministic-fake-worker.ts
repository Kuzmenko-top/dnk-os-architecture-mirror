/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/fake-worker/deterministic-fake-worker.ts"
# purpose: "Deterministic Fake Worker for Zero-AI Video Audit Pipeline Testing."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditJob, JobError } from '../../domain/jobs/job.js';
import { generateDeterministicArtifactKey } from '../../domain/artifacts/artifact.js';
import { ArtifactStore } from '../../ports/artifact-store.js';

export interface FakeWorkerResult {
  status: 'succeeded' | 'retryable_error' | 'permanent_error';
  outputArtifactKeys?: string[];
  error?: JobError;
}

export type JobProcessorFn = (
  job: VideoAuditJob,
  store: ArtifactStore
) => Promise<FakeWorkerResult>;

export class DeterministicFakeWorker {
  constructor(
    public readonly workerId: string,
    public readonly artifactStore: ArtifactStore
  ) {}

  async processJob(
    job: VideoAuditJob,
    customProcessor?: JobProcessorFn
  ): Promise<FakeWorkerResult> {
    if (customProcessor) {
      return customProcessor(job, this.artifactStore);
    }

    // Default Deterministic Fake Processing
    const defaultOutputKey = generateDeterministicArtifactKey(
      job.type,
      job.referenceAssetId,
      'v1-fake'
    );

    const payload = JSON.stringify({
      referenceAssetId: job.referenceAssetId,
      jobId: job.id,
      jobType: job.type,
      attempt: job.attempt,
      status: 'simulated_success',
      data: {
        text: `Simulated output for ${job.type} job ${job.id}`
      }
    });

    await this.artifactStore.put({
      key: defaultOutputKey,
      referenceAssetId: job.referenceAssetId,
      jobId: job.id,
      jobType: job.type,
      data: payload,
      mimeType: 'application/json'
    });

    return {
      status: 'succeeded',
      outputArtifactKeys: [defaultOutputKey]
    };
  }
}
