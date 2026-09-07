/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/multimodal-audit-provider.ts"
# purpose: "Provider-Agnostic Multimodal Audit Port and Input/Output Contracts."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { TranscriptDocument } from '../domain/transcription/transcript.js';
import { SceneDocument } from '../domain/analyzers/scenes.js';
import { OCRDocument } from '../domain/analyzers/ocr.js';
import { AudioFeaturesDocument } from '../domain/analyzers/audio-features.js';
import { MultimodalEvidenceDocument } from '../domain/analyzers/multimodal-evidence.js';
import { ReferenceAsset } from '../domain/assets/reference-asset.js';
import { MultimodalAuditResult, ArtifactRef } from '../../schemas/multimodal-audit.js';

export interface ReferenceMetadata {
  durationMs: number;
  width?: number;
  height?: number;
  hasAudio: boolean;
  hasVideo: boolean;
  sourcePlatform?: string;
  originalFilename?: string;
}

export interface MultimodalAuditInput {
  referenceAssetId: string;
  transcript?: TranscriptDocument;
  scenes?: SceneDocument;
  ocr?: OCRDocument;
  audioFeatures?: AudioFeaturesDocument;
  evidence: MultimodalEvidenceDocument;
  metadata: ReferenceMetadata;
  artifactRefs?: {
    transcript?: ArtifactRef;
    scenes?: ArtifactRef;
    ocr?: ArtifactRef;
    audioFeatures?: ArtifactRef;
    evidence?: ArtifactRef;
  };
}

export interface MultimodalAuditContext {
  promptTemplateVersion?: string;
  temperature?: number;
  maxTokens?: number;
  correlationId?: string;
  targetNiches?: string[];
}

export interface MultimodalAuditProviderResult {
  result: MultimodalAuditResult;
  rawResponse?: string;
  durationMs: number;
  tokenUsage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export interface MultimodalAuditProviderPort {
  readonly providerId: string;
  readonly modelSetVersion: string;

  analyze(
    input: MultimodalAuditInput,
    context: MultimodalAuditContext
  ): Promise<MultimodalAuditProviderResult>;
}
