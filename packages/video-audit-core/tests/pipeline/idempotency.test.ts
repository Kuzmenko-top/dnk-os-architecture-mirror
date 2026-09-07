/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/idempotency.test.ts"
# purpose: "Unit Tests for Deterministic Idempotency Keys and Key Formats."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  generateIdempotencyKey,
  parseIdempotencyKey
} from '../../src/pipeline/domain/idempotency/key.js';
import {
  ArtifactKeyGenerators,
  generateDeterministicArtifactKey
} from '../../src/pipeline/domain/artifacts/artifact.js';

describe('Idempotency & Deterministic Key Management', () => {
  it('generates canonical format {referenceAssetId}:{jobType}:{inputVersion}:{processorVersion}', () => {
    const key = generateIdempotencyKey({
      referenceAssetId: 'ref_123',
      jobType: 'transcription',
      inputVersion: 'asset-v2',
      processorVersion: 'whisperx-v1'
    });

    expect(key).toBe('ref_123:transcription:asset-v2:whisperx-v1');
  });

  it('correctly parses valid idempotency keys into components', () => {
    const key = 'ref_888:scene_extraction:v3:scenedetect-v2.1';
    const parsed = parseIdempotencyKey(key);

    expect(parsed).toEqual({
      referenceAssetId: 'ref_888',
      jobType: 'scene_extraction',
      inputVersion: 'v3',
      processorVersion: 'scenedetect-v2.1'
    });
  });

  it('throws when building idempotency key with empty components', () => {
    expect(() => {
      generateIdempotencyKey({
        referenceAssetId: '',
        jobType: 'transcription',
        inputVersion: 'v1',
        processorVersion: 'v1'
      });
    }).toThrow();
  });

  it('generates deterministic artifact keys matching storage specifications', () => {
    const refId = 'ref_test_001';
    const sha = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';

    expect(ArtifactKeyGenerators.source(refId, sha, 'mp4')).toBe(
      `references/${refId}/source/${sha}.mp4`
    );
    expect(ArtifactKeyGenerators.transcription(refId, 'whisperx-v1')).toBe(
      `references/${refId}/transcript/whisperx-v1.json`
    );
    expect(ArtifactKeyGenerators.scene_extraction(refId, 'scenedetect-v2')).toBe(
      `references/${refId}/scenes/scenedetect-v2.json`
    );
    expect(ArtifactKeyGenerators.multimodal_audit(refId, 'gemini-2.5-pro')).toBe(
      `references/${refId}/audit/gemini-2.5-pro.json`
    );

    expect(generateDeterministicArtifactKey('transcription', refId, 'whisperx-v1')).toBe(
      `references/${refId}/transcript/whisperx-v1.json`
    );
  });
});
