/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/ingestion/idempotency-dedup.test.ts"
# purpose: "Unit Tests for Content Deduplication (SHA-256) and Telegram Update Idempotency."
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

describe('Ingestion Content Deduplication & Telegram Idempotency', () => {
  let service: MediaIngestionService;
  let assetRepo: InMemoryReferenceAssetRepository;
  let artifactStore: InMemoryArtifactStore;
  let telegramTracker: InMemoryTelegramTracker;

  beforeEach(() => {
    assetRepo = new InMemoryReferenceAssetRepository();
    artifactStore = new InMemoryArtifactStore();
    telegramTracker = new InMemoryTelegramTracker();
    const jobRepo = new InMemoryAuditJobRepository();
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
      telegramTracker,
      clock,
      idGen
    );
  });

  it('performs content-level deduplication on identical SHA-256 binary upload', async () => {
    const videoBuffer = new TextEncoder().encode('....ftypisom....VIDEO_BINARY_DATA_001....');

    // 1st Upload
    const res1 = await service.ingestDirectUpload({
      type: 'file_upload',
      buffer: videoBuffer,
      originalFilename: 'video_v1.mp4',
      actorId: 'user_1'
    });

    expect(res1.isDuplicate).toBe(false);
    expect(res1.asset.id).toBeDefined();

    // 2nd Upload of identical content
    const res2 = await service.ingestDirectUpload({
      type: 'file_upload',
      buffer: videoBuffer,
      originalFilename: 'renamed_copy.mp4',
      actorId: 'user_2'
    });

    expect(res2.isDuplicate).toBe(true);
    expect(res2.asset.id).toBe(res1.asset.id);
    expect(res2.sourceArtifactKey).toBe(res1.sourceArtifactKey);
    expect(res2.warnings.some((w) => w.includes('Identical content hash'))).toBe(true);
  });

  it('ensures Telegram update_id idempotency', async () => {
    const telegramBuffer = new TextEncoder().encode('....ftypisom....TELEGRAM_VIDEO_002....');

    const tgInput = {
      type: 'telegram_file' as const,
      buffer: telegramBuffer,
      updateId: 987654,
      fileId: 'tg_file_001',
      fileUniqueId: 'tg_uniq_001',
      chatId: 112233,
      userId: 445566,
      originalFilename: 'telegram_video.mp4',
      actorId: 'tg_bot'
    };

    // 1st Delivery of Telegram Update
    const res1 = await service.ingestTelegramFile(tgInput);
    expect(res1.isDuplicate).toBe(false);
    expect(res1.asset.telegramFileId).toBe('tg_file_001');

    // 2nd Duplicate Delivery of same Telegram update_id
    const res2 = await service.ingestTelegramFile(tgInput);
    expect(res2.isTelegramDuplicate).toBe(true);
    expect(res2.isDuplicate).toBe(true);
    expect(res2.asset.id).toBe(res1.asset.id);
    expect(res2.warnings.some((w) => w.includes('Telegram update was previously processed'))).toBe(true);
  });
});
