/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/analyzers/ocr-schema.test.ts"
# purpose: "Unit Tests for ocr.v1 Canonical Contract, Bounding Box Normalization, and Region Rules."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  OCRDocumentSchema,
  normalizeOCRText
} from '../../../src/pipeline/domain/analyzers/ocr.js';

describe('ocr.v1 Schema & Normalization', () => {
  it('validates a valid OCRDocument with frames and regions', () => {
    const doc = {
      schemaVersion: 'ocr.v1',
      referenceAssetId: 'asset-202',
      provider: 'tesseract-ocr',
      modelVersion: '5.3.0',
      languageHints: ['uk', 'en'],
      frames: [
        {
          frameId: 'frame_0',
          timestampMs: 1000,
          width: 1080,
          height: 1920,
          regions: [
            {
              text: 'ReBurn -20%',
              normalizedText: 'reburn -20%',
              confidence: 0.95,
              boundingBox: { x: 0.1, y: 0.2, width: 0.8, height: 0.1 },
              language: 'uk'
            }
          ]
        }
      ]
    };

    const parsed = OCRDocumentSchema.parse(doc);
    expect(parsed.schemaVersion).toBe('ocr.v1');
    expect(parsed.frames[0].regions[0].normalizedText).toBe('reburn -20%');
  });

  it('normalizes raw OCR text stripping whitespace and noise', () => {
    expect(normalizeOCRText('  Купити   зараз!  ')).toBe('купити зараз!');
    expect(normalizeOCRText('Shopify\nIntegration')).toBe('shopify integration');
  });
});
