/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/analyzers/deterministic-audio-feature-provider.ts"
# purpose: "Deterministic Fake Audio Feature Provider for Acoustic Metrics Testing & Degraded Audio Modes."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import {
  AudioFeatureProviderPort,
  AudioFeatureInput,
  AudioFeatureResult
} from '../../ports/audio-feature-provider.js';
import { AudioFeaturesDocumentSchema } from '../../domain/analyzers/audio-features.js';

export class DeterministicAudioFeatureProvider implements AudioFeatureProviderPort {
  async extractAudioFeatures(input: AudioFeatureInput): Promise<AudioFeatureResult> {
    const hasAudio = input.hasAudioTrack !== false;
    const durationMs = Math.max(input.durationMs, 1000);

    if (!hasAudio) {
      const degradedDocument = AudioFeaturesDocumentSchema.parse({
        schemaVersion: 'audio-features.v1',
        referenceAssetId: input.referenceAssetId,
        sampleRate: 44100,
        durationMs,
        provider: 'deterministic-fake-audio-provider',
        hasAudioTrack: false,
        isDegraded: true,
        features: [],
        warnings: ['No audio track detected in source media artifact. Degraded capability to visual-only analysis.']
      });

      return { document: degradedDocument };
    }

    const seg0End = Math.floor(durationMs * 0.45);
    const silenceEnd = seg0End + Math.min(600, Math.floor(durationMs * 0.1));

    const document = AudioFeaturesDocumentSchema.parse({
      schemaVersion: 'audio-features.v1',
      referenceAssetId: input.referenceAssetId,
      sampleRate: 44100,
      durationMs,
      provider: 'deterministic-fake-audio-provider',
      hasAudioTrack: true,
      isDegraded: false,
      features: [
        {
          startMs: 0,
          endMs: seg0End,
          rmsDb: -16.5,
          peakDb: -1.2,
          speechProbability: 0.94,
          silence: false,
          musicProbability: 0.12,
          noiseScore: 0.04,
          clippingDetected: false
        },
        {
          startMs: seg0End,
          endMs: silenceEnd,
          rmsDb: -62.0,
          peakDb: -55.0,
          speechProbability: 0.01,
          silence: true,
          musicProbability: 0.0,
          noiseScore: 0.02,
          clippingDetected: false
        },
        {
          startMs: silenceEnd,
          endMs: durationMs,
          rmsDb: -15.8,
          peakDb: -0.5,
          speechProbability: 0.96,
          silence: false,
          musicProbability: 0.18,
          noiseScore: 0.06,
          clippingDetected: false
        }
      ]
    });

    return { document };
  }
}
