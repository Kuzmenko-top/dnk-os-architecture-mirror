/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/analyzers/multimodal-evidence.ts"
# purpose: "Canonical Multimodal Evidence Aggregator & Temporal Correlation Layer for 001D/001E."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';
import { SceneDocumentSchema, SceneDocument } from './scenes.js';
import { OCRDocumentSchema, OCRDocument } from './ocr.js';
import { AudioFeaturesDocumentSchema, AudioFeaturesDocument } from './audio-features.js';
import { TranscriptDocumentSchema, TranscriptDocument } from '../transcription/transcript.js';
import {
  computeAnalysisAggregateStatus,
  AnalysisAggregateStatus,
  AnalysisRequirements,
  DEFAULT_ANALYSIS_REQUIREMENTS,
  AnalysisStreams
} from './aggregate-status.js';

export const EvidenceReferenceSchema = z.object({
  transcriptSegmentIds: z.array(z.string()).optional(),
  transcriptWordIndexes: z.array(z.number().int().nonnegative()).optional(),
  sceneIds: z.array(z.string()).optional(),
  ocrFrameIds: z.array(z.string()).optional(),
  audioSegmentIndexes: z.array(z.number().int().nonnegative()).optional()
});

export type EvidenceReference = z.infer<typeof EvidenceReferenceSchema>;

export const TemporalCorrelationItemSchema = z.object({
  timestampMs: z.number().nonnegative(),
  sceneId: z.string().optional(),
  spokenWord: z.string().optional(),
  ocrText: z.string().optional(),
  silenceDetected: z.boolean().optional(),
  reference: EvidenceReferenceSchema.optional()
});

export type TemporalCorrelationItem = z.infer<typeof TemporalCorrelationItemSchema>;

export const MultimodalEvidenceDocumentSchema = z.object({
  schemaVersion: z.literal('multimodal-evidence.v1'),
  referenceAssetId: z.string().min(1),
  generatedAt: z.string().datetime(),
  aggregateStatus: z.enum(['completed', 'partial', 'failed', 'manual_review']),
  transcript: TranscriptDocumentSchema.optional(),
  scenes: SceneDocumentSchema.optional(),
  ocr: OCRDocumentSchema.optional(),
  audioFeatures: AudioFeaturesDocumentSchema.optional(),
  temporalCorrelations: z.array(TemporalCorrelationItemSchema)
});

export type MultimodalEvidenceDocument = z.infer<typeof MultimodalEvidenceDocumentSchema>;

export interface MultimodalInput {
  referenceAssetId: string;
  transcript?: TranscriptDocument;
  scenes?: SceneDocument;
  ocr?: OCRDocument;
  audioFeatures?: AudioFeaturesDocument;
  statuses?: {
    transcriptionStatus?: string;
    sceneExtractionStatus?: string;
    ocrStatus?: string;
    audioFeatureStatus?: string;
  };
  requirements?: AnalysisRequirements;
}

export function buildMultimodalEvidence(input: MultimodalInput): MultimodalEvidenceDocument {
  // Determine structured streams
  const streams: AnalysisStreams = {
    scenes: {
      state: input.scenes
        ? (input.scenes.scenes.length === 0 ? 'empty' : 'completed')
        : (input.statuses?.sceneExtractionStatus === 'failed' ? 'failed' : 'missing')
    },
    ocr: {
      state: input.ocr
        ? (input.ocr.frames.length === 0 || input.ocr.frames.every(f => f.regions.length === 0 || f.regions.every(r => !r.text.trim())) ? 'empty' : 'completed')
        : (input.statuses?.ocrStatus === 'failed' ? 'failed' : 'missing')
    },
    audio: {
      state: input.audioFeatures
        ? (input.audioFeatures.features.length === 0 ? 'empty' : 'completed')
        : (input.statuses?.audioFeatureStatus === 'failed' ? 'failed' : 'missing'),
      isDegraded: input.audioFeatures?.isDegraded || input.statuses?.audioFeatureStatus === 'degraded'
    },
    transcript: {
      state: input.transcript
        ? (input.transcript.segments.length === 0 ? 'empty' : 'completed')
        : (input.statuses?.transcriptionStatus === 'failed' ? 'failed' : 'missing')
    }
  };

  const aggregateStatus: AnalysisAggregateStatus = computeAnalysisAggregateStatus(
    streams,
    input.requirements || DEFAULT_ANALYSIS_REQUIREMENTS
  );

  const timestampsMsSet = new Set<number>();
  input.scenes?.scenes.forEach((s) => {
    timestampsMsSet.add(Math.round(s.startMs));
  });
  input.ocr?.frames.forEach((f) => {
    timestampsMsSet.add(Math.round(f.timestampMs));
  });
  input.transcript?.segments.forEach((seg) => {
    timestampsMsSet.add(Math.round(seg.startMs));
  });
  input.audioFeatures?.features.forEach((af) => {
    timestampsMsSet.add(Math.round(af.startMs));
  });

  const sortedTimestamps = Array.from(timestampsMsSet).sort((a, b) => a - b);

  const temporalCorrelations: TemporalCorrelationItem[] = sortedTimestamps.map((tsMs) => {
    // Determine scene: strictly [startMs, endMs) unless it's the last point of the final scene
    const matchingScenes = input.scenes?.scenes.filter((s) => tsMs >= s.startMs && tsMs < s.endMs) || [];
    const scene = matchingScenes.length > 0 ? matchingScenes[0] : undefined;

    // OCR frame within 1000ms
    const matchingOcrFrames = input.ocr?.frames.filter((f) => Math.abs(f.timestampMs - tsMs) < 1000) || [];
    const ocrFrame = matchingOcrFrames.length > 0 ? matchingOcrFrames[0] : undefined;

    // Transcript segment
    const matchingSegments = input.transcript?.segments.filter((seg) => tsMs >= seg.startMs && tsMs < seg.endMs) || [];
    const segment = matchingSegments.length > 0 ? matchingSegments[0] : undefined;

    // Audio features
    const audioFeatIdx = input.audioFeatures?.features.findIndex((af) => tsMs >= af.startMs && tsMs < af.endMs) ?? -1;
    const audioFeat = audioFeatIdx >= 0 && input.audioFeatures ? input.audioFeatures.features[audioFeatIdx] : undefined;

    const reference: EvidenceReference = {
      transcriptSegmentIds: segment ? [segment.id] : undefined,
      sceneIds: scene ? [scene.id] : undefined,
      ocrFrameIds: ocrFrame ? [ocrFrame.frameId] : undefined,
      audioSegmentIndexes: audioFeatIdx >= 0 ? [audioFeatIdx] : undefined
    };

    return {
      timestampMs: tsMs,
      sceneId: scene?.id,
      spokenWord: segment?.text,
      ocrText: ocrFrame?.regions.map((r) => r.text).join(' | '),
      silenceDetected: audioFeat?.silence,
      reference
    };
  });

  return MultimodalEvidenceDocumentSchema.parse({
    schemaVersion: 'multimodal-evidence.v1',
    referenceAssetId: input.referenceAssetId,
    generatedAt: new Date().toISOString(),
    aggregateStatus,
    transcript: input.transcript ? JSON.parse(JSON.stringify(input.transcript)) : undefined,
    scenes: input.scenes ? JSON.parse(JSON.stringify(input.scenes)) : undefined,
    ocr: input.ocr ? JSON.parse(JSON.stringify(input.ocr)) : undefined,
    audioFeatures: input.audioFeatures ? JSON.parse(JSON.stringify(input.audioFeatures)) : undefined,
    temporalCorrelations
  });
}
