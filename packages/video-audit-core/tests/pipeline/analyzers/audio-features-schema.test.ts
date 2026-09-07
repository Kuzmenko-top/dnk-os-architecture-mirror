/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/analyzers/audio-features-schema.test.ts"
# purpose: "Unit Tests for audio-features.v1 Canonical Contract, Acoustic Metrics, and Degraded Audio."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  AudioFeaturesDocumentSchema
} from '../../../src/pipeline/domain/analyzers/audio-features.js';

describe('audio-features.v1 Schema & Degraded Modes', () => {
  it('validates a complete AudioFeaturesDocument with acoustic segments', () => {
    const doc = {
      schemaVersion: 'audio-features.v1',
      referenceAssetId: 'asset-303',
      sampleRate: 44100,
      durationMs: 4000,
      provider: 'ffmpeg-audio-analyzer',
      hasAudioTrack: true,
      isDegraded: false,
      features: [
        {
          startMs: 0,
          endMs: 2000,
          rmsDb: -16.2,
          peakDb: -1.0,
          speechProbability: 0.95,
          silence: false,
          musicProbability: 0.1,
          clippingDetected: false
        },
        {
          startMs: 2000,
          endMs: 2600,
          rmsDb: -64.0,
          peakDb: -55.0,
          speechProbability: 0.0,
          silence: true,
          clippingDetected: false
        }
      ]
    };

    const parsed = AudioFeaturesDocumentSchema.parse(doc);
    expect(parsed.schemaVersion).toBe('audio-features.v1');
    expect(parsed.features).toHaveLength(2);
    expect(parsed.features[1].silence).toBe(true);
  });

  it('supports degraded audio document when no audio track exists', () => {
    const degradedDoc = {
      schemaVersion: 'audio-features.v1',
      referenceAssetId: 'asset-no-audio',
      sampleRate: 44100,
      durationMs: 3000,
      provider: 'ffmpeg-audio-analyzer',
      hasAudioTrack: false,
      isDegraded: true,
      features: [],
      warnings: ['No audio track present in media file']
    };

    const parsed = AudioFeaturesDocumentSchema.parse(degradedDoc);
    expect(parsed.hasAudioTrack).toBe(false);
    expect(parsed.isDegraded).toBe(true);
  });
});
