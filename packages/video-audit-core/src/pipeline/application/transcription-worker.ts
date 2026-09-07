/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/application/transcription-worker.ts"
# purpose: "Production Application Worker for Executing Transcription Jobs, Cache-Validation and Persisting Transcript Artifacts."
# canonical_source: true
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditJob } from '../domain/jobs/job.js';
import { ArtifactStore } from '../ports/artifact-store.js';
import { AuditEventBus } from '../ports/event-bus.js';
import { TranscriptionProviderPort } from '../ports/transcription-provider.js';
import { TranscriptDocument, TranscriptDocumentSchema } from '../domain/transcription/transcript.js';
import { createHash } from 'node:crypto';

export interface TranscriptionWorkerOptions {
  provider: TranscriptionProviderPort;
  eventBus?: AuditEventBus;
}

export interface TranscriptionWorkerProcessResult {
  status: 'succeeded' | 'retryable_error' | 'permanent_error';
  outputArtifactKeys?: string[];
  transcript?: TranscriptDocument;
  error?: {
    code: string;
    message: string;
    classification: 'retryable' | 'permanent';
  };
}

export class TranscriptionWorker {
  private provider: TranscriptionProviderPort;
  private eventBus?: AuditEventBus;

  constructor(options: TranscriptionWorkerOptions) {
    this.provider = options.provider;
    this.eventBus = options.eventBus;
  }

  async processJob(
    job: VideoAuditJob,
    artifactStore: ArtifactStore
  ): Promise<TranscriptionWorkerProcessResult> {
    const payload = job.payload ?? {};
    const sourceArtifactKey = (payload.sourceArtifactKey as string) ?? `sources/${job.referenceAssetId}.mp4`;
    const languageHint = (payload.languageHint as string) ?? 'uk';

    // 1. Verify source artifact exists
    const isPresent = await artifactStore.exists(sourceArtifactKey);
    if (!isPresent) {
      return {
        status: 'permanent_error',
        error: {
          code: 'SOURCE_ARTIFACT_NOT_FOUND',
          message: `Source media artifact '${sourceArtifactKey}' not found in artifact store`,
          classification: 'permanent'
        }
      };
    }

    try {
      // 2. Sidecar Caching Logic
      const providerId = this.provider.providerId.toLowerCase();
      const modelVersion = (payload.modelVersion as string ?? 'large-v3').toLowerCase();
      const schemaVersion = 'v1';
      const providerModelVersion = `${providerId}-${modelVersion}-${schemaVersion}-${languageHint}`.replace(/[^a-z0-9-_]/g, '-');

      // Retrieve source sha256 to ensure hash/schema validation
      const sourceManifest = await artifactStore.getManifest(sourceArtifactKey);
      let sourceHash = sourceManifest?.sha256;
      if (!sourceHash) {
        try {
          const sourceData = await artifactStore.get(sourceArtifactKey);
          sourceHash = createHash('sha256').update(sourceData).digest('hex');
        } catch {
          sourceHash = 'unknown-source-hash';
        }
      }

      // Versioned Cache Keys
      const cacheKeyJson = `references/${job.referenceAssetId}/transcript/${providerModelVersion}.json`;
      const cacheKeyVtt = `references/${job.referenceAssetId}/transcript/${providerModelVersion}.vtt`;
      const cacheKeyTxt = `references/${job.referenceAssetId}/transcript/${providerModelVersion}.txt`;
      const legacyKey = `transcripts/${job.referenceAssetId}_v1.json`;

      const hasCachedJson = await artifactStore.exists(cacheKeyJson);
      if (hasCachedJson) {
        try {
          const cachedDoc = await artifactStore.getJson<any>(cacheKeyJson);
          
          // Schema and Hash validation check
          if (cachedDoc && cachedDoc.metadata?.sourceHash === sourceHash) {
            const validatedTranscript = TranscriptDocumentSchema.parse(cachedDoc);
            
            if (validatedTranscript.referenceAssetId === job.referenceAssetId) {
              // Cache hit! Return cached artifacts without calling provider
              // Re-inject metadata so it is returned to caller
              (validatedTranscript as any).metadata = cachedDoc.metadata;
              return {
                status: 'succeeded',
                outputArtifactKeys: [cacheKeyJson, cacheKeyVtt, cacheKeyTxt, legacyKey],
                transcript: validatedTranscript
              };
            }
          }
        } catch {
          // If cached content fails verification, bypass cache and re-transcribe
        }
      }

      // 3. Execute transcription via provider port
      const result = await this.provider.transcribe(
        {
          artifactKey: sourceArtifactKey,
          mimeType: 'video/mp4',
          languageHint,
          referenceAssetId: job.referenceAssetId
        },
        {
          jobId: job.id,
          traceId: job.idempotencyKey
        }
      );

      // 4. Validate output transcript document
      const validatedTranscript = TranscriptDocumentSchema.parse(result.transcript);

      // Inject source hash into custom metadata fields
      (validatedTranscript as any).metadata = {
        ...(validatedTranscript as any).metadata,
        sourceHash,
      };

      // 5. Serialize and persist artifact outputs (JSON, VTT, TXT)
      const transcriptJson = JSON.stringify(validatedTranscript, null, 2);
      const dataBuffer = Buffer.from(transcriptJson, 'utf-8');
      const sha256 = createHash('sha256').update(dataBuffer).digest('hex');

      const vttContent = this.convertToVtt(validatedTranscript);
      const txtContent = this.convertToTxt(validatedTranscript);

      // Store JSON Cache
      const manifest = await artifactStore.put({
        key: cacheKeyJson,
        data: dataBuffer,
        mimeType: 'application/json',
        referenceAssetId: job.referenceAssetId,
        jobId: job.id,
        jobType: job.type,
        metadata: {
          schemaVersion: 'transcript.v1',
          sha256,
          sourceHash,
          provider: providerId,
          modelVersion,
          wordCount: result.metadata.wordCount,
          segmentCount: result.metadata.segmentCount,
          status: validatedTranscript.status
        }
      });

      // Store VTT Cache
      await artifactStore.put({
        key: cacheKeyVtt,
        data: Buffer.from(vttContent, 'utf-8'),
        mimeType: 'text/vtt',
        referenceAssetId: job.referenceAssetId,
        jobId: job.id,
        jobType: job.type,
        metadata: {
          sha256: createHash('sha256').update(vttContent).digest('hex'),
          sourceHash,
        }
      });

      // Store TXT Cache
      await artifactStore.put({
        key: cacheKeyTxt,
        data: Buffer.from(txtContent, 'utf-8'),
        mimeType: 'text/plain',
        referenceAssetId: job.referenceAssetId,
        jobId: job.id,
        jobType: job.type,
        metadata: {
          sha256: createHash('sha256').update(txtContent).digest('hex'),
          sourceHash,
        }
      });

      // Store Legacy Path for backward-compatibility
      await artifactStore.put({
        key: legacyKey,
        data: dataBuffer,
        mimeType: 'application/json',
        referenceAssetId: job.referenceAssetId,
        jobId: job.id,
        jobType: job.type,
        metadata: {
          schemaVersion: 'transcript.v1',
          sha256,
          provider: providerId,
          modelVersion,
          status: validatedTranscript.status
        }
      });

      // 6. Emit ArtifactCreated.v1 event if eventBus present
      if (this.eventBus) {
        await this.eventBus.publish({
          eventId: `evt_art_${job.id}_${Date.now()}`,
          eventType: 'ArtifactCreated.v1',
          timestamp: new Date().toISOString(),
          correlationId: job.idempotencyKey,
          actorId: `worker_${this.provider.providerId}`,
          payload: { manifest }
        });
      }

      return {
        status: 'succeeded',
        outputArtifactKeys: [cacheKeyJson, cacheKeyVtt, cacheKeyTxt, legacyKey],
        transcript: validatedTranscript
      };
    } catch (err: any) {
      const isPermanent = err.classification === 'permanent' || err.code === 'INVALID_TRANSCRIPT_SCHEMA';
      return {
        status: isPermanent ? 'permanent_error' : 'retryable_error',
        error: {
          code: err.code ?? 'TRANSCRIPTION_FAILED',
          message: err.message ?? 'Unknown transcription failure',
          classification: isPermanent ? 'permanent' : 'retryable'
        }
      };
    }
  }

  private convertToVtt(transcript: TranscriptDocument): string {
    let vtt = 'WEBVTT\n\n';
    for (const seg of transcript.segments) {
      const start = this.formatMsToVttTime(seg.startMs);
      const end = this.formatMsToVttTime(seg.endMs);
      const speaker = seg.speakerId ? `<v ${seg.speakerId}>` : '';
      vtt += `${start} --> ${end}\n${speaker}${seg.text}\n\n`;
    }
    return vtt;
  }

  private convertToTxt(transcript: TranscriptDocument): string {
    return transcript.segments.map(s => s.text).join('\n');
  }

  private formatMsToVttTime(ms: number): string {
    const totalSecs = Math.floor(ms / 1000);
    const hrs = Math.floor(totalSecs / 3600);
    const mins = Math.floor((totalSecs % 3600) / 60);
    const secs = totalSecs % 60;
    const millis = ms % 1000;

    const pad = (num: number, size = 2) => String(num).padStart(size, '0');
    return `${pad(hrs)}:${pad(mins)}:${pad(secs)}.${pad(millis, 3)}`;
  }
}
