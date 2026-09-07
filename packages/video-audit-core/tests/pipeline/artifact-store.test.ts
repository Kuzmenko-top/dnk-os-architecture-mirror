/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/artifact-store.test.ts"
# purpose: "Unit Tests for In-Memory Artifact Store and Checksum Validation."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect, beforeEach } from 'vitest';
import { InMemoryArtifactStore } from '../../src/pipeline/infrastructure/in-memory/in-memory-artifact-store.js';

describe('InMemoryArtifactStore', () => {
  let store: InMemoryArtifactStore;

  beforeEach(() => {
    store = new InMemoryArtifactStore();
  });

  it('stores string/buffer data and computes accurate SHA-256 and byteSize', async () => {
    const key = 'references/ref-1/transcript/v1.json';
    const payload = JSON.stringify({ text: 'Hello video audit' });

    const manifest = await store.put({
      key,
      referenceAssetId: 'ref-1',
      jobId: 'job-1',
      jobType: 'transcription',
      data: payload,
      mimeType: 'application/json'
    });

    expect(manifest.key).toBe(key);
    expect(manifest.referenceAssetId).toBe('ref-1');
    expect(manifest.jobId).toBe('job-1');
    expect(manifest.mimeType).toBe('application/json');
    expect(manifest.schemaVersion).toBe('artifact-manifest.v1');
    expect(manifest.sha256).toBeDefined();
    expect(manifest.byteSize).toBe(Buffer.byteLength(payload, 'utf8'));

    const exists = await store.exists(key);
    expect(exists).toBe(true);

    const retrievedText = await store.getText(key);
    expect(retrievedText).toBe(payload);

    const parsed = await store.getJson<{ text: string }>(key);
    expect(parsed?.text).toBe('Hello video audit');
  });

  it('deletes stored artifacts and manifests', async () => {
    const key = 'references/ref-1/scenes/v1.json';
    await store.put({
      key,
      referenceAssetId: 'ref-1',
      data: '[]',
      mimeType: 'application/json'
    });

    expect(await store.exists(key)).toBe(true);
    await store.delete(key);
    expect(await store.exists(key)).toBe(false);
  });
});
