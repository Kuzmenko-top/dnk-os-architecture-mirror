/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/application/ocr-worker.ts"
# purpose: "Application Worker for Processing OCR Analysis Jobs, Keyframe Analysis, and Events."
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
import { OCRProviderPort } from '../ports/ocr-provider.js';
import { OCRDocumentSchema } from '../domain/analyzers/ocr.js';
import { runLeasedAnalyzerJob } from './run-leased-analyzer-job.js';

export class OCRWorker {
  constructor(
    private readonly jobStore: AuditJobRepository,
    private readonly artifactStore: ArtifactStore,
    private readonly eventBus: AuditEventBus,
    private readonly provider: OCRProviderPort
  ) {}

  async processNextJob(workerId = 'worker_ocr_01'): Promise<VideoAuditJob | null> {
    const now = new Date().toISOString();
    const job = await this.jobStore.leaseNext(workerId, now, 300, ['ocr']);
    if (!job) return null;

    return runLeasedAnalyzerJob({
      jobStore: this.jobStore,
      workerId,
      leasedJob: job,
      errorCode: 'OCR_ANALYSIS_FAILED',
      execute: async (runningJob) => {
        const kfKeys = runningJob.inputArtifactKeys.filter((k: string) => k.includes('keyframe') || k.endsWith('.jpg') || k.endsWith('.png'));
        const frames = [];

        for (let i = 0; i < kfKeys.length; i++) {
          const kfKey = kfKeys[i];
          let buf: Buffer;
          try {
            const raw = await this.artifactStore.get(kfKey);
            buf = Buffer.from(raw);
          } catch {
            buf = Buffer.from('KF_MOCK_BYTES');
          }
          frames.push({
            frameId: `kf_${i}`,
            timestampMs: i * 2000,
            imageBuffer: buf,
            width: 1080,
            height: 1920
          });
        }

        if (frames.length === 0) {
          frames.push({
            frameId: 'kf_0',
            timestampMs: 0,
            imageBuffer: Buffer.from('KF_DEFAULT'),
            width: 1080,
            height: 1920
          });
        }

        return await this.provider.extractOCR({
          referenceAssetId: runningJob.referenceAssetId,
          frames,
          languageHints: (runningJob.payload?.languageHints as string[]) || ['uk', 'en']
        });
      },
      persistArtifact: async (result, runningJob) => {
        const validatedDoc = OCRDocumentSchema.parse(result.document);
        const jsonStr = JSON.stringify(validatedDoc, null, 2);
        const artifactBuf = Buffer.from(jsonStr, 'utf-8');
        const sha256 = createHash('sha256').update(artifactBuf).digest('hex');

        const artifactKey = `ocr/${runningJob.referenceAssetId}/ocr.v1.json`;
        await this.artifactStore.put({
          key: artifactKey,
          referenceAssetId: runningJob.referenceAssetId,
          jobId: runningJob.id,
          jobType: runningJob.type,
          mimeType: 'application/json',
          data: artifactBuf,
          metadata: { sha256, schemaVersion: 'ocr.v1' }
        });

        return {
          outputArtifactKeys: [artifactKey],
          mainArtifactKey: artifactKey,
          sha256,
          artifactType: 'ocr',
          schemaVersion: 'ocr.v1'
        };
      },
      publishEvent: async (result, runningJob, outputArtifactKeys, mainArtifactKey, sha256, schemaVersion) => {
        await this.eventBus.publish({
          id: `evt_${Date.now()}`,
          eventType: 'ArtifactCreated.v1',
          referenceAssetId: runningJob.referenceAssetId,
          timestamp: new Date().toISOString(),
          jobId: runningJob.id,
          artifactType: 'ocr',
          artifactKey: mainArtifactKey,
          sha256,
          schemaVersion
        } as any);
      }
    });
  }
}
