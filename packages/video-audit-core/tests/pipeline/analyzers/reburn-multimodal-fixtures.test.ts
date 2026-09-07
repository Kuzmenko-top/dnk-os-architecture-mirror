/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/analyzers/reburn-multimodal-fixtures.test.ts"
# purpose: "Integration & Benchmark Tests with Ukrainian ReBurn Multi-modal Fixtures."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.3"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import { DeterministicOCRProvider } from '../../../src/pipeline/infrastructure/analyzers/deterministic-ocr-provider.js';
import { DeterministicAudioFeatureProvider } from '../../../src/pipeline/infrastructure/analyzers/deterministic-audio-feature-provider.js';
import { DeterministicSceneProvider } from '../../../src/pipeline/infrastructure/analyzers/deterministic-scene-provider.js';
import { buildMultimodalEvidence } from '../../../src/pipeline/domain/analyzers/multimodal-evidence.js';

describe('Ukrainian ReBurn Multimodal Fixtures Benchmark', () => {
  it('correctly processes Ukrainian OCR overlays & audio silence pauses', async () => {
    const ocrProvider = new DeterministicOCRProvider();
    const audioProvider = new DeterministicAudioFeatureProvider();
    const sceneProvider = new DeterministicSceneProvider();

    const ocrRes = await ocrProvider.extractOCR({
      referenceAssetId: 'reburn-short-001',
      frames: [
        { frameId: 'f0', timestampMs: 0, imageBuffer: Buffer.from('KF0'), width: 1080, height: 1920 },
        { frameId: 'f1', timestampMs: 2000, imageBuffer: Buffer.from('KF1'), width: 1080, height: 1920 }
      ]
    });

    const audioRes = await audioProvider.extractAudioFeatures({
      referenceAssetId: 'reburn-short-001',
      mediaFilePath: 'dummy.mp4',
      durationMs: 5000,
      hasAudioTrack: true
    });

    const sceneRes = await sceneProvider.extractScenes({
      referenceAssetId: 'reburn-short-001',
      mediaFilePath: 'dummy.mp4',
      durationMs: 5000
    });

    const multimodal = buildMultimodalEvidence({
      referenceAssetId: 'reburn-short-001',
      scenes: sceneRes.document,
      ocr: ocrRes.document,
      audioFeatures: audioRes.document,
      transcript: {
        schemaVersion: 'transcript.v1',
        id: 'tx_reburn_001',
        referenceAssetId: 'reburn-short-001',
        language: 'uk',
        provider: 'deterministic-fake-transcription-provider',
        modelVersion: 'whisper-large-v3',
        durationMs: 5000,
        confidence: 0.99,
        status: 'completed',
        warnings: [],
        segments: [
          { id: 'seg_0', ordinal: 0, startMs: 0, endMs: 5000, text: 'Тестовий транскрипт', confidence: 0.99, words: [] }
        ]
      }
    });

    expect(multimodal.aggregateStatus).toBe('completed');
    expect(multimodal.ocr?.frames[1].regions[0].normalizedText).toContain('shopify');
    expect(multimodal.audioFeatures?.features.some((f) => f.silence)).toBe(true);
  });
});
