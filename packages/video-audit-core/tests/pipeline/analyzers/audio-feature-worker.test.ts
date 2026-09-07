/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/analyzers/audio-feature-worker.test.ts"
# purpose: "Integration Tests for AudioFeatureWorker, Feature Extraction, and Acoustic Degraded Mode."
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
import { AudioFeatureWorker } from '../../../src/pipeline/application/audio-feature-worker.js';
import { DeterministicAudioFeatureProvider } from '../../../src/pipeline/infrastructure/analyzers/deterministic-audio-feature-provider.js';
import { InMemoryJobRepository } from '../../../src/pipeline/infrastructure/in-memory/in-memory-job-repository.js';
import { InMemoryArtifactStore } from '../../../src/pipeline/infrastructure/in-memory/in-memory-artifact-store.js';
import { InMemoryEventBus } from '../../../src/pipeline/infrastructure/in-memory/in-memory-event-bus.js';
import { createAuditJob } from '../../../src/pipeline/domain/jobs/job.js';

describe('AudioFeatureWorker Integration', () => {
  let jobStore: InMemoryJobRepository;
  let artifactStore: InMemoryArtifactStore;
  let eventBus: InMemoryEventBus;
  let provider: DeterministicAudioFeatureProvider;
  let worker: AudioFeatureWorker;

  beforeEach(() => {
    jobStore = new InMemoryJobRepository();
    artifactStore = new InMemoryArtifactStore();
    eventBus = new InMemoryEventBus();
    provider = new DeterministicAudioFeatureProvider();
    worker = new AudioFeatureWorker(jobStore, artifactStore, eventBus, provider);
  });

  it('leases, runs audio feature extraction, persists audio-features.v1.json, and publishes event', async () => {
    await artifactStore.put({
      key: 'sources/asset-audio-1/media.mp4',
      referenceAssetId: 'asset-audio-1',
      data: Buffer.from('FAKE_AUDIO_BYTES'),
      mimeType: 'video/mp4'
    });

    const job = createAuditJob({
      referenceAssetId: 'asset-audio-1',
      type: 'audio_analysis',
      payload: {
        sourceArtifactKey: 'sources/asset-audio-1/media.mp4',
        durationMs: 8000,
        hasAudioTrack: true
      }
    });
    await jobStore.create(job);

    const completed = await worker.processNextJob();
    expect(completed).not.toBeNull();
    expect(completed?.status).toBe('succeeded');
    expect(completed?.outputArtifactKeys).toContain('audio-features/asset-audio-1/audio-features.v1.json');

    const artifactBuf = await artifactStore.get('audio-features/asset-audio-1/audio-features.v1.json');
    const doc = JSON.parse(artifactBuf.toString('utf-8'));
    expect(doc.schemaVersion).toBe('audio-features.v1');
    expect(doc.hasAudioTrack).toBe(true);
    expect(doc.isDegraded).toBe(false);

    expect(eventBus.publishedEvents).toHaveLength(1);
    expect(eventBus.publishedEvents[0].eventType).toBe('ArtifactCreated.v1');
  });

  it('handles degraded mode when hasAudioTrack is false without crashing', async () => {
    await artifactStore.put({
      key: 'sources/asset-no-audio/media.mp4',
      referenceAssetId: 'asset-no-audio',
      data: Buffer.from('FAKE_BYTES'),
      mimeType: 'video/mp4'
    });

    const job = createAuditJob({
      referenceAssetId: 'asset-no-audio',
      type: 'audio_analysis',
      payload: {
        sourceArtifactKey: 'sources/asset-no-audio/media.mp4',
        durationMs: 4000,
        hasAudioTrack: false
      }
    });
    await jobStore.create(job);

    const completed = await worker.processNextJob();
    expect(completed).not.toBeNull();
    expect(completed?.status).toBe('succeeded');

    const artifactBuf = await artifactStore.get('audio-features/asset-no-audio/audio-features.v1.json');
    const doc = JSON.parse(artifactBuf.toString('utf-8'));
    expect(doc.hasAudioTrack).toBe(false);
    expect(doc.isDegraded).toBe(true);
    expect(doc.features).toHaveLength(0);
  });
});
