/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/ingestion/direct-upload-and-telegram.test.ts"
# purpose: "Integration Tests for Direct Upload, Telegram Ingestion, and Rights Intent."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect, beforeEach } from 'vitest';
import { MediaIngestionService } from '../../../src/pipeline/application/ingestion-service.js';
import { InMemoryReferenceAssetRepository } from '../../../src/pipeline/infrastructure/in-memory/in-memory-reference-asset-repository.js';
import { InMemoryArtifactStore } from '../../../src/pipeline/infrastructure/in-memory/in-memory-artifact-store.js';
import { InMemoryAuditJobRepository } from '../../../src/pipeline/infrastructure/in-memory/in-memory-job-repository.js';
import { InMemoryAuditEventBus } from '../../../src/pipeline/infrastructure/in-memory/in-memory-event-bus.js';
import { InMemoryTelegramTracker } from '../../../src/pipeline/infrastructure/in-memory/in-memory-telegram-tracker.js';
import { DeterministicMediaProbe } from '../../../src/pipeline/infrastructure/media-probe/deterministic-media-probe.js';
import { SsrfUrlValidator } from '../../../src/pipeline/infrastructure/security/ssrf-url-validator.js';
import { VideoAuditOrchestrator } from '../../../src/pipeline/application/orchestrator.js';
import { SystemClock } from '../../../src/pipeline/infrastructure/system/system-clock.js';
import { UuidIdGenerator } from '../../../src/pipeline/infrastructure/system/uuid-id-generator.js';

describe('Media Ingestion Integration Workflows', () => {
  let service: MediaIngestionService;
  let artifactStore: InMemoryArtifactStore;
  let jobRepo: InMemoryAuditJobRepository;

  beforeEach(() => {
    const assetRepo = new InMemoryReferenceAssetRepository();
    artifactStore = new InMemoryArtifactStore();
    jobRepo = new InMemoryAuditJobRepository();
    const eventBus = new InMemoryAuditEventBus();
    const clock = new SystemClock();
    const idGen = new UuidIdGenerator();

    const orchestrator = new VideoAuditOrchestrator(
      jobRepo,
      artifactStore,
      eventBus,
      clock,
      idGen
    );

    service = new MediaIngestionService(
      assetRepo,
      artifactStore,
      new DeterministicMediaProbe(),
      orchestrator,
      new SsrfUrlValidator(),
      new InMemoryTelegramTracker(),
      clock,
      idGen
    );
  });

  it('successfully processes direct upload and submits ingestion job', async () => {
    const mediaBytes = new TextEncoder().encode('....ftypisom....SAMPLE_DIRECT_UPLOAD_01....');

    const result = await service.ingestDirectUpload({
      type: 'file_upload',
      buffer: mediaBytes,
      originalFilename: 'my_reel.mp4',
      actorId: 'creator_123',
      rightsMetadata: {
        status: 'user_owned',
        usageIntent: 'commercial_adaptation'
      }
    });

    expect(result.asset.id).toBeDefined();
    expect(result.asset.sanitizedFilename).toBe('my_reel.mp4');
    expect(result.asset.rightsMetadata.status).toBe('user_owned');
    expect(result.asset.rightsMetadata.usageIntent).toBe('commercial_adaptation');

    // Verify binary storage
    const storedBytes = await artifactStore.get(result.sourceArtifactKey);
    expect(storedBytes).not.toBeNull();

    // Verify created job in orchestrator job repo
    const createdJob = await jobRepo.getById(result.ingestionJob.id);
    expect(createdJob).not.toBeNull();
    expect(createdJob?.type).toBe('ingestion');
    expect(createdJob?.status).toBe('queued');
  });

  it('processes manual transcript fallback ingestion', async () => {
    const result = await service.ingestManualFallback({
      type: 'manual_fallback',
      transcriptText: 'Hello world, this is a manual transcript fallback for analysis.',
      originalFilename: 'script_text.txt',
      actorId: 'editor_456'
    });

    expect(result.asset.sourcePlatform).toBe('manual_fallback');
    expect(result.asset.capabilities).toContain('multimodal_audit');
    expect(result.asset.degradationWarnings.some((w) => w.includes('Manual transcript fallback'))).toBe(true);
  });
});
