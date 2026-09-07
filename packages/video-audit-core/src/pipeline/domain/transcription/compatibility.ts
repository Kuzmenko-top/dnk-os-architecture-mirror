/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/transcription/compatibility.ts"
# purpose: "Compatibility Mappers between transcript.v1 and VideoAuditReport Legacy Schema."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { TranscriptDocument as CanonicalTranscriptDocument } from './transcript.js';
import { TranscriptDocument as LegacyReportTranscript } from '../../../schemas/audit.js';

/**
 * Maps a canonical transcript.v1 document to the VideoAuditReport legacy transcript schema.
 */
export function toLegacyReportTranscript(
  canonical: CanonicalTranscriptDocument
): LegacyReportTranscript {
  const fullText = canonical.segments.map(s => s.text).join(' ');

  const segments = canonical.segments.map(s => ({
    id: s.id,
    startMs: s.startMs,
    endMs: s.endMs,
    text: s.text,
    speakerTag: s.speakerId,
    words: s.words.map(w => ({
      word: w.text,
      startMs: w.startMs,
      endMs: w.endMs,
      confidence: w.confidence ?? 0.9,
      speakerTag: w.speakerId ?? s.speakerId
    }))
  }));

  return {
    language: canonical.language,
    fullText,
    segments,
    overallConfidence: canonical.confidence
  };
}
