/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/analyzers/ocr-worker.test.ts"
# purpose: "Integration Tests for OCRWorker, Frame OCR, Text Deduplication, and Event Publishing."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect, beforeEach } from 'vitest';
import { OCRWorker } from '../../../src/pipeline/application/ocr-worker.js';
import { DeterministicOCRProvider } from '../../../src/pipeline/infrastructure/analyzers/deterministic-ocr-provider.js';
import { InMemoryJobRepository } from '../../../src/pipeline/infrastructure/in-memory/in-memory-job-repository.js';
import { InMemoryArtifactStore } from '../../../src/pipeline/infrastructure/in-memory/in-memory-artifact-store.js';
import { InMemoryEventBus } from '../../../src/pipeline/infrastructure/in-memory/in-memory-event-bus.js';
import { createAuditJob } from '../../../src/pipeline/domain/jobs/job.js';

describe('OCRWorker Integration', () => {
  let jobStore: InMemoryJobRepository;
  let artifactStore: InMemoryArtifactStore;
  let eventBus: InMemoryEventBus;
  let provider: DeterministicOCRProvider;
  let worker: OCRWorker;

  beforeEach(() => {
    jobStore = new InMemoryJobRepository();
    artifactStore = new InMemoryArtifactStore();
    eventBus = new InMemoryEventBus();
    provider = new DeterministicOCRProvider();
    worker = new OCRWorker(jobStore, artifactStore, eventBus, provider);
  });

  it('leases, runs OCR over keyframes, persists ocr.v1.json, and publishes event', async () => {
    await artifactStore.put({
      key: 'keyframes/asset-ocr-1/scene_0.jpg',
      referenceAssetId: 'asset-ocr-1',
      data: Buffer.from('KF_BYTES'),
      mimeType: 'image/jpeg'
    });

    const job = createAuditJob({
      referenceAssetId: 'asset-ocr-1',
      type: 'ocr',
      payload: {
        keyframeKeys: ['keyframes/asset-ocr-1/scene_0.jpg'],
        languageHints: ['uk', 'en']
      }
    });
    await jobStore.create(job);

    const completed = await worker.processNextJob();
    expect(completed).not.toBeNull();
    expect(completed?.status).toBe('succeeded');
    expect(completed?.outputArtifactKeys).toContain('ocr/asset-ocr-1/ocr.v1.json');

    const artifactBuf = await artifactStore.get('ocr/asset-ocr-1/ocr.v1.json');
    const doc = JSON.parse(artifactBuf.toString('utf-8'));
    expect(doc.schemaVersion).toBe('ocr.v1');
    expect(doc.frames).toHaveLength(1);

    expect(eventBus.publishedEvents).toHaveLength(1);
    expect(eventBus.publishedEvents[0].eventType).toBe('ArtifactCreated.v1');
  });
});
