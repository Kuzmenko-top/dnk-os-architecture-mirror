/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/transcription/report-compatibility.test.ts"
# purpose: "Compatibility Test Suite between transcript.v1 Document and Legacy VideoAuditReport Schema."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import { createTranscriptDocument } from '../../../src/pipeline/domain/transcription/transcript.js';
import { toLegacyReportTranscript } from '../../../src/pipeline/domain/transcription/compatibility.js';
import { TranscriptDocumentSchema as LegacyTranscriptSchema } from '../../../src/schemas/audit.js';

describe('TranscriptDocument to VideoAuditReport Legacy Compatibility', () => {
  it('converts canonical transcript.v1 into valid legacy VideoAuditReport transcript structure', () => {
    const canonical = createTranscriptDocument({
      id: 'tr_compat_01',
      referenceAssetId: 'asset_compat',
      language: 'uk',
      provider: 'whisperx',
      modelVersion: 'large-v3',
      segments: [
        {
          id: 'seg_0',
          ordinal: 0,
          startMs: 0,
          endMs: 2000,
          text: 'Перше речення.',
          speakerId: 'SPEAKER_01',
          words: [
            { ordinal: 0, text: 'Перше', startMs: 0, endMs: 800, confidence: 0.95 },
            { ordinal: 1, text: 'речення.', startMs: 900, endMs: 2000, confidence: 0.98 }
          ]
        },
        {
          id: 'seg_1',
          ordinal: 1,
          startMs: 2100,
          endMs: 4000,
          text: 'Друге речення.',
          speakerId: 'SPEAKER_01',
          words: [
            { ordinal: 0, text: 'Друге', startMs: 2100, endMs: 2800, confidence: 0.92 },
            { ordinal: 1, text: 'речення.', startMs: 2900, endMs: 4000, confidence: 0.96 }
          ]
        }
      ],
      durationMs: 4500,
      confidence: 0.96,
      status: 'completed'
    });

    const legacy = toLegacyReportTranscript(canonical);

    // Verify it parses against legacy Zod schema
    const parsedLegacy = LegacyTranscriptSchema.parse(legacy);

    expect(parsedLegacy.language).toBe('uk');
    expect(parsedLegacy.fullText).toBe('Перше речення. Друге речення.');
    expect(parsedLegacy.segments).toHaveLength(2);
    expect(parsedLegacy.segments[0].words).toHaveLength(2);
    expect(parsedLegacy.segments[0].words[0].word).toBe('Перше');
    expect(parsedLegacy.segments[0].words[0].startMs).toBe(0);
    expect(parsedLegacy.segments[0].words[0].endMs).toBe(800);
    expect(parsedLegacy.overallConfidence).toBe(0.96);
  });
});
