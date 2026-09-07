/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/governance/evidence.ts"
# purpose: "Evidence Classification, Confidence Bounds & Evidence Governance Engine."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { EvidenceItem, EvidenceType } from '../schemas/audit.js';

export interface CreateEvidenceParams {
  id: string;
  type?: EvidenceType;
  claim: string;
  confidence: number;
  source: string;
  timeRange?: { startMs: number; endMs: number };
  modelVersion?: string;
  evidenceRefs?: string[];
}

export function validateEvidenceConfidence(confidence: number): number {
  if (typeof confidence !== 'number' || isNaN(confidence) || confidence < 0 || confidence > 1) {
    throw new Error(`Invalid confidence score: ${confidence}. Must be a float between 0.0 and 1.0.`);
  }
  return confidence;
}

export function createEvidenceItem(params: CreateEvidenceParams): EvidenceItem {
  const confidence = validateEvidenceConfidence(params.confidence);

  let classifiedType = params.type;

  if (!classifiedType) {
    // Auto-infer evidence type when not explicitly supplied
    const deterministicSources = ['whisperx', 'ffmpeg', 'rule_engine', 'whisperx_v3_ffmpeg', 'ffmpeg_scene_detect'];
    if (deterministicSources.includes(params.source) && confidence >= 0.7) {
      classifiedType = 'observed';
    } else if (confidence >= 0.4) {
      classifiedType = 'inferred';
    } else {
      classifiedType = 'hypothesized';
    }
  } else {
    // Enforce confidence bounds when type is explicitly supplied
    if (classifiedType === 'observed' && confidence < 0.7) {
      classifiedType = 'inferred';
    } else if (classifiedType === 'inferred' && confidence < 0.4) {
      classifiedType = 'hypothesized';
    }
  }

  return {
    id: params.id,
    type: classifiedType,
    claim: params.claim,
    confidence,
    source: params.source,
    timeRange: params.timeRange,
    modelVersion: params.modelVersion,
    evidenceRefs: params.evidenceRefs || [],
  };
}

export function validateEvidenceClassification(item: EvidenceItem): { valid: boolean; reason?: string } {
  if (item.type === 'observed' && item.confidence < 0.7) {
    return {
      valid: false,
      reason: `Observed evidence item '${item.id}' has confidence ${item.confidence} (< 0.7 bound). Must be classified as 'inferred' or 'hypothesized'.`,
    };
  }

  if (item.type === 'inferred' && item.confidence < 0.4) {
    return {
      valid: false,
      reason: `Inferred evidence item '${item.id}' has confidence ${item.confidence} (< 0.4 bound). Must be classified as 'hypothesized'.`,
    };
  }

  return { valid: true };
}
