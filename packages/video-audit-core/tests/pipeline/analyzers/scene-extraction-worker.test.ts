/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/analyzers/scene-extraction-worker.test.ts"
# purpose: "Integration Tests for SceneExtractionWorker, Lifecycle, Keyframes, and Artifact Persistence."
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
import { SceneExtractionWorker } from '../../../src/pipeline/application/scene-extraction-worker.js';
import { DeterministicSceneProvider } from '../../../src/pipeline/infrastructure/analyzers/deterministic-scene-provider.js';
import { InMemoryJobRepository } from '../../../src/pipeline/infrastructure/in-memory/in-memory-job-repository.js';
import { InMemoryArtifactStore } from '../../../src/pipeline/infrastructure/in-memory/in-memory-artifact-store.js';
import { InMemoryEventBus } from '../../../src/pipeline/infrastructure/in-memory/in-memory-event-bus.js';
import { createAuditJob } from '../../../src/pipeline/domain/jobs/job.js';

describe('SceneExtractionWorker Integration', () => {
  let jobStore: InMemoryJobRepository;
  let artifactStore: InMemoryArtifactStore;
  let eventBus: InMemoryEventBus;
  let provider: DeterministicSceneProvider;
  let worker: SceneExtractionWorker;

  beforeEach(() => {
    jobStore = new InMemoryJobRepository();
    artifactStore = new InMemoryArtifactStore();
    eventBus = new InMemoryEventBus();
    provider = new DeterministicSceneProvider();
    worker = new SceneExtractionWorker(jobStore, artifactStore, eventBus, provider);
  });

  it('leases, extracts scenes, saves scenes.v1 artifact, and publishes event', async () => {
    await artifactStore.put({
      key: 'sources/asset-1/media.mp4',
      referenceAssetId: 'asset-1',
      data: Buffer.from('FAKE_VIDEO_BYTES'),
      mimeType: 'video/mp4'
    });

    const job = createAuditJob({
      referenceAssetId: 'asset-1',
      type: 'scene_extraction',
      payload: {
        sourceArtifactKey: 'sources/asset-1/media.mp4',
        durationMs: 6000
      }
    });
    await jobStore.create(job);

    const completed = await worker.processNextJob();
    expect(completed).not.toBeNull();
    expect(completed?.status).toBe('succeeded');
    expect(completed?.outputArtifactKeys).toContain('scenes/asset-1/scenes.v1.json');

    const artifactBuf = await artifactStore.get('scenes/asset-1/scenes.v1.json');
    const doc = JSON.parse(artifactBuf.toString('utf-8'));
    expect(doc.schemaVersion).toBe('scenes.v1');
    expect(doc.scenes).toHaveLength(2);

    expect(eventBus.publishedEvents).toHaveLength(1);
    expect(eventBus.publishedEvents[0].eventType).toBe('ArtifactCreated.v1');
  });
});
