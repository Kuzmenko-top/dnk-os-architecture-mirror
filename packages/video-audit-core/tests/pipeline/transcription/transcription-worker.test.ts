/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/transcription/transcription-worker.test.ts"
# purpose: "Integration Test Suite for TranscriptionWorker Application Pipeline Execution."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import { TranscriptionWorker } from '../../../src/pipeline/application/transcription-worker.js';
import { DeterministicFakeTranscriptionProvider } from '../../../src/pipeline/infrastructure/transcription/deterministic-transcription-provider.js';
import { InMemoryArtifactStore } from '../../../src/pipeline/infrastructure/in-memory/in-memory-artifact-store.js';
import { InMemoryEventBus } from '../../../src/pipeline/infrastructure/in-memory/in-memory-event-bus.js';
import { createAuditJob } from '../../../src/pipeline/domain/jobs/job.js';

describe('TranscriptionWorker Orchestration Integration', () => {
  it('successfully processes transcription job, stores artifact, and emits event', async () => {
    const provider = new DeterministicFakeTranscriptionProvider();
    const eventBus = new InMemoryEventBus();
    const store = new InMemoryArtifactStore();
    const worker = new TranscriptionWorker({ provider, eventBus });

    const sourceKey = 'sources/asset_01.mp4';
    await store.put({
      key: sourceKey,
      data: Buffer.from('fake mp4 video bytes'),
      mimeType: 'video/mp4',
      referenceAssetId: 'asset_01'
    });

    const job = createAuditJob({
      referenceAssetId: 'asset_01',
      type: 'transcription',
      payload: { sourceArtifactKey: sourceKey, languageHint: 'uk' }
    });

    const result = await worker.processJob(job, store);

    expect(result.status).toBe('succeeded');
    expect(result.outputArtifactKeys).toBeDefined();
    expect(result.outputArtifactKeys![0]).toContain('references/asset_01/transcript/');
    expect(result.transcript).toBeDefined();
    expect(result.transcript?.schemaVersion).toBe('transcript.v1');

    // Verify artifact store has saved transcript
    const artifactJson = await store.getText(result.outputArtifactKeys![0]);
    expect(artifactJson).toContain('ReBurn');

    // Verify event bus received ArtifactCreated.v1
    const published = eventBus.getPublishedEvents();
    expect(published).toHaveLength(1);
    expect(published[0].eventType).toBe('ArtifactCreated.v1');
  });

  it('fails with permanent_error when source media artifact is missing', async () => {
    const provider = new DeterministicFakeTranscriptionProvider();
    const store = new InMemoryArtifactStore();
    const worker = new TranscriptionWorker({ provider });

    const job = createAuditJob({
      referenceAssetId: 'asset_missing',
      type: 'transcription',
      payload: { sourceArtifactKey: 'sources/missing.mp4' }
    });

    const result = await worker.processJob(job, store);

    expect(result.status).toBe('permanent_error');
    expect(result.error?.code).toBe('SOURCE_ARTIFACT_NOT_FOUND');
  });

  describe('Sidecar Caching', () => {
    it('achieves cache hit when source hash and params match', async () => {
      const provider = new DeterministicFakeTranscriptionProvider();
      const eventBus = new InMemoryEventBus();
      const store = new InMemoryArtifactStore();
      const worker = new TranscriptionWorker({ provider, eventBus });

      const sourceKey = 'sources/asset_02.mp4';
      await store.put({
        key: sourceKey,
        data: Buffer.from('video version A'),
        mimeType: 'video/mp4',
        referenceAssetId: 'asset_02'
      });

      const job = createAuditJob({
        referenceAssetId: 'asset_02',
        type: 'transcription',
        payload: { sourceArtifactKey: sourceKey, languageHint: 'uk', modelVersion: 'large-v3' }
      });

      // 1st run - Cache miss, transcribes
      const result1 = await worker.processJob(job, store);
      expect(result1.status).toBe('succeeded');
      expect(eventBus.getPublishedEvents()).toHaveLength(1);

      // Reset event bus to track cache hit events
      eventBus.clearPublishedEvents();

      // 2nd run - Cache hit
      const result2 = await worker.processJob(job, store);
      expect(result2.status).toBe('succeeded');
      expect(result2.transcript?.id).toBe(result1.transcript?.id);
      expect(eventBus.getPublishedEvents()).toHaveLength(0); // Cache hit does not publish new events
    });

    it('triggers cache miss when model version changes', async () => {
      const provider = new DeterministicFakeTranscriptionProvider();
      const store = new InMemoryArtifactStore();
      const worker = new TranscriptionWorker({ provider });

      const sourceKey = 'sources/asset_02.mp4';
      await store.put({
        key: sourceKey,
        data: Buffer.from('video version A'),
        mimeType: 'video/mp4',
        referenceAssetId: 'asset_02'
      });

      const jobV3 = createAuditJob({
        referenceAssetId: 'asset_02',
        type: 'transcription',
        payload: { sourceArtifactKey: sourceKey, languageHint: 'uk', modelVersion: 'large-v3' }
      });

      const jobV2 = createAuditJob({
        referenceAssetId: 'asset_02',
        type: 'transcription',
        payload: { sourceArtifactKey: sourceKey, languageHint: 'uk', modelVersion: 'large-v2' }
      });

      const resultV3 = await worker.processJob(jobV3, store);
      const resultV2 = await worker.processJob(jobV2, store);

      expect(resultV3.status).toBe('succeeded');
      expect(resultV2.status).toBe('succeeded');
      // Different model version means different keys, so different transcripts generated
      expect(resultV2.outputArtifactKeys![0]).not.toBe(resultV3.outputArtifactKeys![0]);
    });

    it('triggers cache miss when source hash changes', async () => {
      const provider = new DeterministicFakeTranscriptionProvider();
      const eventBus = new InMemoryEventBus();
      const store = new InMemoryArtifactStore();
      const worker = new TranscriptionWorker({ provider, eventBus });

      const sourceKey = 'sources/asset_02.mp4';
      
      // Put initial video bytes
      await store.put({
        key: sourceKey,
        data: Buffer.from('video version A'),
        mimeType: 'video/mp4',
        referenceAssetId: 'asset_02'
      });

      const job = createAuditJob({
        referenceAssetId: 'asset_02',
        type: 'transcription',
        payload: { sourceArtifactKey: sourceKey, languageHint: 'uk' }
      });

      const result1 = await worker.processJob(job, store);
      expect(result1.status).toBe('succeeded');
      expect(eventBus.getPublishedEvents()).toHaveLength(1);

      // Reset event bus
      eventBus.clearPublishedEvents();

      // Update source bytes (different content -> different hash)
      await store.put({
        key: sourceKey,
        data: Buffer.from('video version B - modified bytes'),
        mimeType: 'video/mp4',
        referenceAssetId: 'asset_02'
      });

      const result2 = await worker.processJob(job, store);
      expect(result2.status).toBe('succeeded');
      // Should result in a fresh transcription and publish an event
      expect(eventBus.getPublishedEvents()).toHaveLength(1);
    });

    it('handles schema validation failure for corrupted cache by bypassing cache', async () => {
      const provider = new DeterministicFakeTranscriptionProvider();
      const eventBus = new InMemoryEventBus();
      const store = new InMemoryArtifactStore();
      const worker = new TranscriptionWorker({ provider, eventBus });

      const sourceKey = 'sources/asset_03.mp4';
      await store.put({
        key: sourceKey,
        data: Buffer.from('video version C'),
        mimeType: 'video/mp4',
        referenceAssetId: 'asset_03'
      });

      const job = createAuditJob({
        referenceAssetId: 'asset_03',
        type: 'transcription',
        payload: { sourceArtifactKey: sourceKey, languageHint: 'uk' }
      });

      const result1 = await worker.processJob(job, store);
      const jsonKey = result1.outputArtifactKeys![0];
      expect(eventBus.getPublishedEvents()).toHaveLength(1);

      // Reset event bus
      eventBus.clearPublishedEvents();

      // Corrupt the cached JSON file in store by removing a mandatory field
      const corruptDoc = {
        schemaVersion: 'transcript.v1',
        id: 'some-id',
        referenceAssetId: 'asset_03',
        // 'language' is required but we omit it to force validation failure
        provider: 'fake',
        modelVersion: 'large-v3',
        metadata: {
          sourceHash: (await store.getManifest(sourceKey))?.sha256
        }
      };
      await store.put({
        key: jsonKey,
        data: JSON.stringify(corruptDoc),
        mimeType: 'application/json',
        referenceAssetId: 'asset_03'
      });

      const result2 = await worker.processJob(job, store);
      expect(result2.status).toBe('succeeded');
      // Should bypass the corrupted cache, re-transcribe, and publish an event
      expect(eventBus.getPublishedEvents()).toHaveLength(1);
    });

    it('generates artifact manifest with correct sha256 metadata', async () => {
      const provider = new DeterministicFakeTranscriptionProvider();
      const store = new InMemoryArtifactStore();
      const worker = new TranscriptionWorker({ provider });

      const sourceKey = 'sources/asset_04.mp4';
      await store.put({
        key: sourceKey,
        data: Buffer.from('video version D'),
        mimeType: 'video/mp4',
        referenceAssetId: 'asset_04'
      });

      const job = createAuditJob({
        referenceAssetId: 'asset_04',
        type: 'transcription',
        payload: { sourceArtifactKey: sourceKey, languageHint: 'uk' }
      });

      const result = await worker.processJob(job, store);
      const jsonKey = result.outputArtifactKeys![0];

      const manifest = await store.getManifest(jsonKey);
      expect(manifest).toBeDefined();
      expect(manifest?.sha256).toBeDefined();
      expect(manifest?.mimeType).toBe('application/json');
    });
  });
});
