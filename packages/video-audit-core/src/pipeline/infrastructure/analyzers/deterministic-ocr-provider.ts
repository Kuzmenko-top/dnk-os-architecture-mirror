/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/analyzers/deterministic-ocr-provider.ts"
# purpose: "Deterministic Fake OCR Provider for Reproducible Tests & Ukrainian ReBurn Fixtures."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import {
  OCRProviderPort,
  OCRInput,
  OCRResult
} from '../../ports/ocr-provider.js';
import { OCRDocumentSchema, OCRFrameSchema, normalizeOCRText } from '../../domain/analyzers/ocr.js';

export class DeterministicOCRProvider implements OCRProviderPort {
  async extractOCR(input: OCRInput): Promise<OCRResult> {
    const rawFrames = input.frames.map((frame, index) => {
      const isIntro = index === 0;
      const textOverlay = isIntro ? 'ReBurn Teleprompter - Демо' : 'Shopify - ЗНИЖКА -20% Купити зараз';
      const normalizedText = normalizeOCRText(textOverlay);

      return OCRFrameSchema.parse({
        frameId: frame.frameId,
        timestampMs: frame.timestampMs,
        width: frame.width || 1080,
        height: frame.height || 1920,
        regions: [
          {
            text: textOverlay,
            normalizedText,
            confidence: 0.94,
            boundingBox: {
              x: 0.1,
              y: isIntro ? 0.2 : 0.7,
              width: 0.8,
              height: 0.15
            },
            language: 'uk'
          }
        ]
      });
    });

    const document = OCRDocumentSchema.parse({
      schemaVersion: 'ocr.v1',
      referenceAssetId: input.referenceAssetId,
      provider: 'deterministic-fake-ocr-provider',
      modelVersion: '1.0.0',
      frames: rawFrames,
      languageHints: input.languageHints || ['uk', 'en']
    });

    return { document };
  }
}
