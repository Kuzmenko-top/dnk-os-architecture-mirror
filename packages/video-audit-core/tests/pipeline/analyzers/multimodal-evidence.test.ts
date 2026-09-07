/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/analyzers/multimodal-evidence.test.ts"
# purpose: "Unit & Integration Tests for Multimodal Evidence Aggregation, Status Matrix, and Requirements."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  buildMultimodalEvidence
} from '../../../src/pipeline/domain/analyzers/multimodal-evidence.js';
import {
  computeAnalysisAggregateStatus,
  AnalysisRequirements
} from '../../../src/pipeline/domain/analyzers/aggregate-status.js';

describe('Multimodal Evidence Aggregator & Aggregate Status Matrix', () => {
  it('computes completed status when all analyzers complete', () => {
    const status = computeAnalysisAggregateStatus({
      scenes: { state: 'completed' },
      ocr: { state: 'completed' },
      audio: { state: 'completed' },
      transcript: { state: 'completed' }
    });
    expect(status).toBe('completed');
  });

  it('computes partial status when audio is degraded', () => {
    const status = computeAnalysisAggregateStatus({
      scenes: { state: 'completed' },
      ocr: { state: 'completed' },
      audio: { state: 'completed', isDegraded: true },
      transcript: { state: 'completed' }
    });
    expect(status).toBe('partial');
  });

  it('handles missing transcript, optional (should be partial)', () => {
    const status = computeAnalysisAggregateStatus({
      scenes: { state: 'completed' },
      ocr: { state: 'completed' },
      audio: { state: 'completed' },
      transcript: { state: 'missing' }
    }, {
      scenes: 'required',
      ocr: 'optional',
      audio: 'optional',
      transcript: 'optional'
    });
    expect(status).toBe('partial');
  });

  it('handles missing transcript, required (should be manual_review)', () => {
    const status = computeAnalysisAggregateStatus({
      scenes: { state: 'completed' },
      ocr: { state: 'completed' },
      audio: { state: 'completed' },
      transcript: { state: 'missing' }
    }, {
      scenes: 'required',
      ocr: 'optional',
      audio: 'optional',
      transcript: 'required'
    });
    expect(status).toBe('manual_review');
  });

  it('handles empty OCR, optional (should be completed)', () => {
    const status = computeAnalysisAggregateStatus({
      scenes: { state: 'completed' },
      ocr: { state: 'empty' },
      audio: { state: 'completed' },
      transcript: { state: 'completed' }
    }, {
      scenes: 'required',
      ocr: 'optional',
      audio: 'optional',
      transcript: 'optional'
    });
    expect(status).toBe('completed');
  });

  it('handles required stream failed (should be failed)', () => {
    const status = computeAnalysisAggregateStatus({
      scenes: { state: 'failed' },
      ocr: { state: 'completed' },
      audio: { state: 'completed' },
      transcript: { state: 'completed' }
    }, {
      scenes: 'required',
      ocr: 'optional',
      audio: 'optional',
      transcript: 'optional'
    });
    expect(status).toBe('failed');
  });

  it('guarantees source documents remain unchanged (immutability)', () => {
    const scenesDoc = {
      schemaVersion: 'scenes.v1' as const,
      referenceAssetId: 'asset-imm-1',
      extractor: { provider: 'test', version: '1.0', method: 'test' },
      durationMs: 4000,
      scenes: [
        { id: 'scene_0', ordinal: 0, startMs: 0, endMs: 4000, durationMs: 4000, boundaryConfidence: 0.9 }
      ]
    };
    const scenesDocStr = JSON.stringify(scenesDoc);

    const evidence = buildMultimodalEvidence({
      referenceAssetId: 'asset-imm-1',
      scenes: scenesDoc
    });

    expect(evidence.schemaVersion).toBe('multimodal-evidence.v1');
    expect(JSON.stringify(scenesDoc)).toBe(scenesDocStr); // verified immutability
  });

  it('builds multimodal evidence document with temporal correlation', () => {
    const evidence = buildMultimodalEvidence({
      referenceAssetId: 'asset-multi-1',
      scenes: {
        schemaVersion: 'scenes.v1',
        referenceAssetId: 'asset-multi-1',
        extractor: { provider: 'test', version: '1.0', method: 'test' },
        durationMs: 4000,
        scenes: [
          { id: 'scene_0', ordinal: 0, startMs: 0, endMs: 4000, durationMs: 4000, boundaryConfidence: 0.9 }
        ]
      },
      ocr: {
        schemaVersion: 'ocr.v1',
        referenceAssetId: 'asset-multi-1',
        provider: 'test',
        modelVersion: '1.0',
        languageHints: ['uk'],
        frames: [
          {
            frameId: 'f0',
            timestampMs: 1000,
            width: 1080,
            height: 1920,
            regions: [{ text: 'ReBurn Promo', normalizedText: 'reburn promo', confidence: 0.9, boundingBox: { x: 0, y: 0, width: 1, height: 1 } }]
          }
        ]
      }
    });

    expect(evidence.schemaVersion).toBe('multimodal-evidence.v1');
    expect(evidence.temporalCorrelations.length).toBeGreaterThan(0);
  });
});
