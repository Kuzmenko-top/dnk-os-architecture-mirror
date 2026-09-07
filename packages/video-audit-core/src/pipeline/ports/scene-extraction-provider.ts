/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/scene-extraction-provider.ts"
# purpose: "Provider-Agnostic Scene Extraction Port and DTO Contracts."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { SceneDocument, SceneExtractionPolicy } from '../domain/analyzers/scenes.js';

export interface SceneExtractionInput {
  referenceAssetId: string;
  mediaFilePath: string;
  durationMs?: number;
  policy?: Partial<SceneExtractionPolicy>;
}

export interface SceneExtractionResult {
  document: SceneDocument;
  keyframeArtifacts?: Record<string, Buffer>;
}

export interface SceneExtractionProviderPort {
  readonly providerName: string;
  readonly version: string;
  extractScenes(input: SceneExtractionInput): Promise<SceneExtractionResult>;
}
