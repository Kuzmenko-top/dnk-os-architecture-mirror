/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/application/ingestion-service.ts"
# purpose: "Application Service for Secure Media Ingestion, SHA-256 Deduplication, and Telegram Idempotency."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import {
  DirectFileUploadInput,
  TelegramFileInput,
  UrlReferenceInput,
  ManualFallbackInput
} from '../domain/ingestion/input.js';
import {
  ReferenceAsset,
  RightsMetadata,
  deriveMediaCapabilities
} from '../domain/assets/reference-asset.js';
import { sanitizeFilename, UrlValidationResult } from '../domain/ingestion/security.js';
import { VideoAuditJob } from '../domain/jobs/job.js';
import { ArtifactKeyGenerators } from '../domain/artifacts/artifact.js';
import { ReferenceAssetRepository } from '../ports/reference-asset-repository.js';
import { ArtifactStore } from '../ports/artifact-store.js';
import { MediaProbePort } from '../ports/media-probe.js';
import { VideoAuditOrchestrator } from './orchestrator.js';
import { UrlSecurityValidatorPort } from '../ports/url-validator.js';
import { TelegramUpdateTrackerPort } from '../ports/telegram-update-tracker.js';
import { Clock } from '../ports/clock.js';
import { IdGenerator } from '../ports/id-generator.js';

export interface IngestResult {
  asset: ReferenceAsset;
  sourceArtifactKey: string;
  ingestionJob: VideoAuditJob;
  isDuplicate: boolean;
  isTelegramDuplicate?: boolean;
  warnings: string[];
}

export class MediaIngestionService {
  constructor(
    private readonly referenceAssetRepo: ReferenceAssetRepository,
    private readonly artifactStore: ArtifactStore,
    private readonly mediaProbe: MediaProbePort,
    private readonly orchestrator: VideoAuditOrchestrator,
    private readonly urlValidator: UrlSecurityValidatorPort,
    private readonly telegramTracker: TelegramUpdateTrackerPort,
    private readonly clock: Clock,
    private readonly idGenerator: IdGenerator
  ) {}

  /**
   * Ingests a media file from direct file upload.
   */
  async ingestDirectUpload(input: DirectFileUploadInput): Promise<IngestResult> {
    return this.processMediaBuffer({
      buffer: input.buffer,
      originalFilename: input.originalFilename,
      declaredMimeType: input.declaredMimeType,
      sourcePlatform: 'direct_upload',
      actorId: input.actorId,
      rightsMetadataInput: input.rightsMetadata,
      correlationId: input.correlationId
    });
  }

  /**
   * Ingests a media file received via Telegram update, with update_id idempotency.
   */
  async ingestTelegramFile(input: TelegramFileInput): Promise<IngestResult> {
    // 1. Check Telegram Update Idempotency
    const updateStatus = await this.telegramTracker.isUpdateProcessed(input.updateId);
    if (updateStatus.processed && updateStatus.referenceAssetId) {
      const existingAsset = await this.referenceAssetRepo.getById(updateStatus.referenceAssetId);
      if (existingAsset) {
        const { job } = await this.orchestrator.submitJob({
          referenceAssetId: existingAsset.id,
          type: 'ingestion',
          inputVersion: '1.0.0',
          processorVersion: '1.0.0',
          inputArtifactKeys: [existingAsset.storageKey],
          correlationId: input.correlationId,
          actorId: input.actorId
        });

        return {
          asset: existingAsset,
          sourceArtifactKey: existingAsset.storageKey,
          ingestionJob: job,
          isDuplicate: true,
          isTelegramDuplicate: true,
          warnings: ['Telegram update was previously processed. Returned existing ReferenceAsset.']
        };
      }
    }

    const result = await this.processMediaBuffer({
      buffer: input.buffer,
      originalFilename: input.originalFilename,
      declaredMimeType: input.declaredMimeType,
      sourcePlatform: 'telegram',
      telegramFileId: input.fileId,
      telegramFileUniqueId: input.fileUniqueId,
      actorId: input.actorId,
      rightsMetadataInput: input.rightsMetadata,
      correlationId: input.correlationId
    });

    // Record processed Telegram update
    await this.telegramTracker.recordUpdate(input.updateId, result.asset.id);

    return result;
  }

  /**
   * Validates a URL reference against SSRF security policies.
   */
  async validateUrlReference(input: UrlReferenceInput): Promise<UrlValidationResult> {
    return this.urlValidator.validateUrl(input.url);
  }

  /**
   * Processes manual text/screenshot fallback when video binary is unavailable.
   */
  async ingestManualFallback(input: ManualFallbackInput): Promise<IngestResult> {
    const sanitized = sanitizeFilename(input.originalFilename ?? 'manual_transcript.txt');
    const nowIso = this.clock.nowIso();
    const assetId = this.idGenerator.generate('asset');

    const encoder = new TextEncoder();
    const transcriptBytes = encoder.encode(input.transcriptText ?? '');

    const probeResult = await this.mediaProbe.probeBuffer(
      transcriptBytes.length > 0 ? transcriptBytes : new Uint8Array([0x66, 0x74, 0x79, 0x70]), // fallback
      { filename: sanitized }
    ).catch(() => ({
      mimeType: 'text/plain',
      container: 'unknown' as const,
      durationMs: 0,
      hasVideo: false,
      hasAudio: false,
      byteSize: transcriptBytes.byteLength,
      sha256: '0000000000000000000000000000000000000000000000000000000000000000',
      isCorrupted: false
    }));

    const storageKey = ArtifactKeyGenerators.source(assetId, probeResult.sha256, 'txt');
    await this.artifactStore.put({
      key: storageKey,
      referenceAssetId: assetId,
      data: transcriptBytes,
      mimeType: 'text/plain'
    });

    const rights: RightsMetadata = {
      status: input.rightsMetadata?.status ?? 'user_owned',
      confirmedAt: input.rightsMetadata?.confirmedAt ?? nowIso,
      confirmedBy: input.rightsMetadata?.confirmedBy ?? input.actorId,
      sourcePlatform: 'manual_fallback',
      usageIntent: input.rightsMetadata?.usageIntent ?? 'private_analysis'
    };

    const asset: ReferenceAsset = {
      id: assetId,
      sourcePlatform: 'manual_fallback',
      sanitizedFilename: sanitized,
      contentHash: probeResult.sha256,
      storageKey,
      rightsMetadata: rights,
      probeResult,
      capabilities: ['multimodal_audit'],
      degradationWarnings: ['Manual transcript fallback: binary media stream absent.'],
      schemaVersion: 'reference-asset.v1',
      createdAt: nowIso,
      createdBy: input.actorId
    };

    await this.referenceAssetRepo.create(asset);

    const { job } = await this.orchestrator.submitJob({
      referenceAssetId: asset.id,
      type: 'ingestion',
      inputVersion: '1.0.0',
      processorVersion: '1.0.0',
      inputArtifactKeys: [storageKey],
      correlationId: input.correlationId,
      actorId: input.actorId
    });

    return {
      asset,
      sourceArtifactKey: storageKey,
      ingestionJob: job,
      isDuplicate: false,
      warnings: asset.degradationWarnings
    };
  }

  private async processMediaBuffer(params: {
    buffer: Uint8Array;
    originalFilename?: string;
    declaredMimeType?: string;
    sourcePlatform: 'direct_upload' | 'telegram';
    telegramFileId?: string;
    telegramFileUniqueId?: string;
    actorId: string;
    rightsMetadataInput?: Partial<RightsMetadata>;
    correlationId?: string;
  }): Promise<IngestResult> {
    const sanitized = sanitizeFilename(params.originalFilename);

    // 1. Media Probing & Magic-Byte Verification (Throttles/rejects corrupt & spoofed buffers)
    const probe = await this.mediaProbe.probeBuffer(params.buffer, {
      filename: sanitized,
      declaredMimeType: params.declaredMimeType
    });

    // 2. Check Content-Level Deduplication via SHA-256
    const existingByHash = await this.referenceAssetRepo.getByContentHash(probe.sha256);

    if (existingByHash) {
      // Content already exists! Reuse asset and storage key to prevent duplication
      const { job } = await this.orchestrator.submitJob({
        referenceAssetId: existingByHash.id,
        type: 'ingestion',
        inputVersion: '1.0.0',
        processorVersion: '1.0.0',
        inputArtifactKeys: [existingByHash.storageKey],
        correlationId: params.correlationId,
        actorId: params.actorId
      });

      return {
        asset: existingByHash,
        sourceArtifactKey: existingByHash.storageKey,
        ingestionJob: job,
        isDuplicate: true,
        warnings: [
          `Identical content hash (${probe.sha256.substring(0, 8)}...) detected. Reused existing ReferenceAsset.`
        ]
      };
    }

    // 3. New Media Asset: Store artifact & Create ReferenceAsset
    const nowIso = this.clock.nowIso();
    const assetId = this.idGenerator.generate('asset');
    const extension = probe.container === 'unknown' ? 'mp4' : probe.container;
    const storageKey = ArtifactKeyGenerators.source(assetId, probe.sha256, extension);

    // Prepare Rights Metadata
    const rightsMetadata: RightsMetadata = {
      status: params.rightsMetadataInput?.status ?? 'user_owned',
      confirmedAt: params.rightsMetadataInput?.confirmedAt ?? nowIso,
      confirmedBy: params.rightsMetadataInput?.confirmedBy ?? params.actorId,
      sourcePlatform: params.sourcePlatform,
      usageIntent: params.rightsMetadataInput?.usageIntent ?? 'private_analysis'
    };

    // Derive domain capabilities & degradation warnings
    const { capabilities, degradationWarnings } = deriveMediaCapabilities(
      probe,
      rightsMetadata
    );

    // Persist media binary & manifest in ArtifactStore
    await this.artifactStore.put({
      key: storageKey,
      referenceAssetId: assetId,
      data: params.buffer,
      mimeType: probe.mimeType,
      metadata: {
        sourcePlatform: params.sourcePlatform,
        sha256: probe.sha256
      }
    });

    const newAsset: ReferenceAsset = {
      id: assetId,
      sourcePlatform: params.sourcePlatform,
      telegramFileId: params.telegramFileId,
      telegramFileUniqueId: params.telegramFileUniqueId,
      originalFilename: params.originalFilename,
      sanitizedFilename: sanitized,
      contentHash: probe.sha256,
      storageKey,
      rightsMetadata,
      probeResult: probe,
      capabilities,
      degradationWarnings,
      schemaVersion: 'reference-asset.v1',
      createdAt: nowIso,
      createdBy: params.actorId
    };

    await this.referenceAssetRepo.create(newAsset);

    // 4. Submit Ingestion Job
    const { job } = await this.orchestrator.submitJob({
      referenceAssetId: newAsset.id,
      type: 'ingestion',
      inputVersion: '1.0.0',
      processorVersion: '1.0.0',
      inputArtifactKeys: [storageKey],
      correlationId: params.correlationId,
      actorId: params.actorId
    });

    return {
      asset: newAsset,
      sourceArtifactKey: storageKey,
      ingestionJob: job,
      isDuplicate: false,
      warnings: degradationWarnings
    };
  }
}
