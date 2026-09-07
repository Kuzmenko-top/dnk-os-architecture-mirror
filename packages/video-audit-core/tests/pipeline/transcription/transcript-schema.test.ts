/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/transcription/transcript-schema.test.ts"
# purpose: "Comprehensive Unit Test Suite for transcript.v1 Schema Validation Rules."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  createTranscriptDocument,
  TranscriptDocumentSchema,
  TranscriptSegmentSchema,
  TranscriptWordSchema
} from '../../../src/pipeline/domain/transcription/transcript.js';

describe('TranscriptDocument transcript.v1 Schema Rules', () => {
  it('validates a correct transcript document with segment and word timestamps', () => {
    const valid = createTranscriptDocument({
      id: 'tr_test_01',
      referenceAssetId: 'asset_01',
      language: 'uk',
      provider: 'whisperx',
      modelVersion: 'large-v3',
      segments: [
        {
          id: 'seg_0',
          ordinal: 0,
          startMs: 0,
          endMs: 2500,
          text: 'Привіт світ.',
          words: [
            { ordinal: 0, text: 'Привіт', startMs: 0, endMs: 1200, confidence: 0.98 },
            { ordinal: 1, text: 'світ.', startMs: 1300, endMs: 2500, confidence: 0.99 }
          ]
        }
      ],
      durationMs: 3000,
      confidence: 0.98,
      status: 'completed'
    });

    expect(valid.schemaVersion).toBe('transcript.v1');
    expect(valid.segments).toHaveLength(1);
    expect(valid.status).toBe('completed');
  });

  it('rejects word where endMs < startMs', () => {
    expect(() =>
      TranscriptWordSchema.parse({
        ordinal: 0,
        text: 'помилка',
        startMs: 1000,
        endMs: 500
      })
    ).toThrow(/Word endMs must be >= startMs/);
  });

  it('rejects segment where startMs > endMs', () => {
    expect(() =>
      createTranscriptDocument({
        id: 'tr_test_err',
        referenceAssetId: 'asset_01',
        language: 'uk',
        provider: 'whisperx',
        modelVersion: 'large-v3',
        segments: [
          {
            id: 'seg_0',
            ordinal: 0,
            startMs: 2000,
            endMs: 1000,
            text: 'Некоректний інтервал',
            words: []
          }
        ],
        durationMs: 5000,
        status: 'completed'
      })
    ).toThrow(/Segment endMs must be >= startMs/);
  });

  it('rejects word whose startMs is before segment startMs', () => {
    expect(() =>
      createTranscriptDocument({
        id: 'tr_test_err_2',
        referenceAssetId: 'asset_01',
        language: 'uk',
        provider: 'whisperx',
        modelVersion: 'large-v3',
        segments: [
          {
            id: 'seg_0',
            ordinal: 0,
            startMs: 1000,
            endMs: 3000,
            text: 'Вихід за межі',
            words: [
              { ordinal: 0, text: 'Вихід', startMs: 500, endMs: 2000 }
            ]
          }
        ],
        durationMs: 5000,
        status: 'completed'
      })
    ).toThrow(/All word timestamp intervals must fit inside segment/);
  });

  it('rejects empty transcript document marked as completed', () => {
    expect(() =>
      createTranscriptDocument({
        id: 'tr_empty_completed',
        referenceAssetId: 'asset_01',
        language: 'uk',
        provider: 'whisperx',
        modelVersion: 'large-v3',
        segments: [],
        durationMs: 5000,
        status: 'completed'
      })
    ).toThrow(/Empty transcript document cannot have status 'completed'/);
  });

  it('allows empty transcript document when marked as degraded with warnings', () => {
    const degraded = createTranscriptDocument({
      id: 'tr_empty_degraded',
      referenceAssetId: 'asset_01',
      language: 'uk',
      provider: 'whisperx',
      modelVersion: 'large-v3',
      segments: [],
      durationMs: 5000,
      status: 'degraded',
      warnings: ['No audio track found']
    });

    expect(degraded.status).toBe('degraded');
    expect(degraded.warnings).toHaveLength(1);
  });

  it('rejects durationMs smaller than the last word endMs', () => {
    expect(() =>
      createTranscriptDocument({
        id: 'tr_duration_err',
        referenceAssetId: 'asset_01',
        language: 'uk',
        provider: 'whisperx',
        modelVersion: 'large-v3',
        segments: [
          {
            id: 'seg_0',
            ordinal: 0,
            startMs: 0,
            endMs: 5000,
            text: 'Задовгий сегмент',
            words: [{ ordinal: 0, text: 'Задовгий', startMs: 0, endMs: 5000 }]
          }
        ],
        durationMs: 3000,
        status: 'completed'
      })
    ).toThrow(/durationMs must be >= maximum timestamp of any segment/);
  });
});
