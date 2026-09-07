/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/application/scene-extraction-worker.ts"
# purpose: "Application Worker for Processing Scene Extraction Jobs, Keyframe Persistence, and Events."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { createHash } from 'node:crypto';
import { VideoAuditJob } from '../domain/jobs/job.js';
import { AuditJobRepository } from '../ports/job-repository.js';
import { ArtifactStore } from '../ports/artifact-store.js';
import { AuditEventBus } from '../ports/event-bus.js';
import { SceneExtractionProviderPort } from '../ports/scene-extraction-provider.js';
import { SceneDocumentSchema } from '../domain/analyzers/scenes.js';
import { runLeasedAnalyzerJob } from './run-leased-analyzer-job.js';

export class SceneExtractionWorker {
  constructor(
    private readonly jobStore: AuditJobRepository,
    private readonly artifactStore: ArtifactStore,
    private readonly eventBus: AuditEventBus,
    private readonly provider: SceneExtractionProviderPort
  ) {}

  async processNextJob(workerId = 'worker_scene_01'): Promise<VideoAuditJob | null> {
    const now = new Date().toISOString();
    const job = await this.jobStore.leaseNext(workerId, now, 300, ['scene_extraction']);
    if (!job) return null;

    return runLeasedAnalyzerJob({
      jobStore: this.jobStore,
      workerId,
      leasedJob: job,
      errorCode: 'SCENE_EXTRACTION_FAILED',
      execute: async (runningJob) => {
        const mediaKey = runningJob.inputArtifactKeys.find((k: string) => k.endsWith('.mp4') || k.includes('media') || k.includes('source'));
        const durationMs = (runningJob.payload?.durationMs as number) || 10000;

        return await this.provider.extractScenes({
          referenceAssetId: runningJob.referenceAssetId,
          mediaFilePath: mediaKey || 'sources/default/media.mp4',
          durationMs
        });
      },
      persistArtifact: async (result, runningJob) => {
        const validatedDoc = SceneDocumentSchema.parse(result.document);
        const jsonStr = JSON.stringify(validatedDoc, null, 2);
        const artifactBuf = Buffer.from(jsonStr, 'utf-8');
        const sha256 = createHash('sha256').update(artifactBuf).digest('hex');

        const artifactKey = `scenes/${runningJob.referenceAssetId}/scenes.v1.json`;
        await this.artifactStore.put({
          key: artifactKey,
          referenceAssetId: runningJob.referenceAssetId,
          jobId: runningJob.id,
          jobType: runningJob.type,
          mimeType: 'application/json',
          data: artifactBuf,
          metadata: { sha256, schemaVersion: 'scenes.v1' }
        });

        const outputArtifactKeys = [artifactKey];

        if (result.keyframeArtifacts) {
          for (const [kfName, kfBuf] of Object.entries(result.keyframeArtifacts)) {
            const kfPath = `scenes/${runningJob.referenceAssetId}/keyframes/${kfName}`;
            await this.artifactStore.put({
              key: kfPath,
              referenceAssetId: runningJob.referenceAssetId,
              jobId: runningJob.id,
              jobType: runningJob.type,
              mimeType: 'image/jpeg',
              data: kfBuf,
              metadata: { schemaVersion: 'keyframe.v1' }
            });
            outputArtifactKeys.push(kfPath);
          }
        }

        return {
          outputArtifactKeys,
          mainArtifactKey: artifactKey,
          sha256,
          artifactType: 'scenes',
          schemaVersion: 'scenes.v1'
        };
      },
      publishEvent: async (result, runningJob, outputArtifactKeys, mainArtifactKey, sha256, schemaVersion) => {
        await this.eventBus.publish({
          id: `evt_${Date.now()}`,
          eventType: 'ArtifactCreated.v1',
          referenceAssetId: runningJob.referenceAssetId,
          timestamp: new Date().toISOString(),
          jobId: runningJob.id,
          artifactType: 'scenes',
          artifactKey: mainArtifactKey,
          sha256,
          schemaVersion
        } as any);
      }
    });
  }
}
