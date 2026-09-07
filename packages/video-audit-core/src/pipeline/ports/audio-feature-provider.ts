/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/audio-feature-provider.ts"
# purpose: "Provider-Agnostic Audio Feature Extraction Port and DTO Contracts."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { AudioFeaturesDocument } from '../domain/analyzers/audio-features.js';

export interface AudioFeatureInput {
  referenceAssetId: string;
  mediaFilePath: string;
  durationMs: number;
  hasAudioTrack?: boolean;
}

export interface AudioFeatureResult {
  document: AudioFeaturesDocument;
}

export interface AudioFeatureProviderPort {
  extractAudioFeatures(input: AudioFeatureInput): Promise<AudioFeatureResult>;
}
