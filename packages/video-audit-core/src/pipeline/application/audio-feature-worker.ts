/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/application/audio-feature-worker.ts"
# purpose: "Application Worker for Processing Audio Feature Extraction Jobs, Persistence, and Events."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.1"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { createHash } from 'node:crypto';
import { VideoAuditJob } from '../domain/jobs/job.js';
import { AuditJobRepository } from '../ports/job-repository.js';
import { ArtifactStore } from '../ports/artifact-store.js';
import { AuditEventBus } from '../ports/event-bus.js';
import { AudioFeatureProviderPort } from '../ports/audio-feature-provider.js';
import { AudioFeaturesDocumentSchema } from '../domain/analyzers/audio-features.js';
import { runLeasedAnalyzerJob } from './run-leased-analyzer-job.js';

export class AudioFeatureWorker {
  constructor(
    private readonly jobStore: AuditJobRepository,
    private readonly artifactStore: ArtifactStore,
    private readonly eventBus: AuditEventBus,
    private readonly provider: AudioFeatureProviderPort
  ) {}

  async processNextJob(workerId = 'worker_audio_01'): Promise<VideoAuditJob | null> {
    const now = new Date().toISOString();
    const job = await this.jobStore.leaseNext(workerId, now, 300, ['audio_analysis']);
    if (!job) return null;

    return runLeasedAnalyzerJob({
      jobStore: this.jobStore,
      workerId,
      leasedJob: job,
      errorCode: 'AUDIO_FEATURE_EXTRACTION_FAILED',
      execute: async (runningJob) => {
        const mediaKey = runningJob.inputArtifactKeys.find((k: string) => k.endsWith('.mp4') || k.includes('media') || k.includes('source'));
        const durationMs = (runningJob.payload?.durationMs as number) || 10000;
        const hasAudioTrack = runningJob.payload?.hasAudioTrack as boolean | undefined;

        return await this.provider.extractAudioFeatures({
          referenceAssetId: runningJob.referenceAssetId,
          mediaFilePath: mediaKey || 'sources/default/media.mp4',
          durationMs,
          hasAudioTrack
        });
      },
      persistArtifact: async (result, runningJob) => {
        const validatedDoc = AudioFeaturesDocumentSchema.parse(result.document);
        const jsonStr = JSON.stringify(validatedDoc, null, 2);
        const artifactBuf = Buffer.from(jsonStr, 'utf-8');
        const sha256 = createHash('sha256').update(artifactBuf).digest('hex');

        // FIXED: Using audio-features with dash to align with test assertion expectation
        const artifactKey = `audio-features/${runningJob.referenceAssetId}/audio-features.v1.json`;
        await this.artifactStore.put({
          key: artifactKey,
          referenceAssetId: runningJob.referenceAssetId,
          jobId: runningJob.id,
          jobType: runningJob.type,
          mimeType: 'application/json',
          data: artifactBuf,
          metadata: { sha256, schemaVersion: 'audio-features.v1' }
        });

        return {
          outputArtifactKeys: [artifactKey],
          mainArtifactKey: artifactKey,
          sha256,
          artifactType: 'audio_analysis',
          schemaVersion: 'audio-features.v1'
        };
      },
      publishEvent: async (result, runningJob, outputArtifactKeys, mainArtifactKey, sha256, schemaVersion) => {
        await this.eventBus.publish({
          id: `evt_${Date.now()}`,
          eventType: 'ArtifactCreated.v1',
          referenceAssetId: runningJob.referenceAssetId,
          timestamp: new Date().toISOString(),
          jobId: runningJob.id,
          artifactType: 'audio_analysis',
          artifactKey: mainArtifactKey,
          sha256,
          schemaVersion
        } as any);
      }
    });
  }
}
