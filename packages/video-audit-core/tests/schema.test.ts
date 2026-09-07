/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/schema.test.ts"
# purpose: "Unit Tests for Zod Schema Validation & Version Mismatch Checks."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  validateVideoAuditReport,
  validateScriptDocument,
  validateProsodyDocument,
  validateShotList,
  validateAdaptationResult,
  ValidationError,
  SchemaVersionMismatchError,
} from '../src/index.js';

describe('Video Intelligence Schema Validation', () => {
  it('should reject invalid schema versions', () => {
    const invalidVersionDoc = {
      schemaVersion: 'script.v99',
      id: 'script-01',
      language: 'uk',
      scenes: [],
      estimatedDurationMs: 1000,
      source: { type: 'original' },
    };

    expect(() => validateScriptDocument(invalidVersionDoc)).toThrow(SchemaVersionMismatchError);
  });

  it('should reject invalid payload structure missing required fields', () => {
    const badAuditPayload = {
      schemaVersion: 'video-audit.v1',
      id: 'audit-001',
      status: 'READY',
      // missing referenceAsset, transcript, scenes, etc.
    };

    expect(() => validateVideoAuditReport(badAuditPayload)).toThrow(ValidationError);
  });

  it('should validate valid ScriptDocument', () => {
    const validScript = {
      schemaVersion: 'script.v1',
      id: 'script-valid-01',
      language: 'uk',
      title: 'Тестовий сценарій',
      estimatedDurationMs: 15000,
      source: { type: 'original' },
      scenes: [
        {
          id: 'sc-1',
          title: 'Вступ',
          role: 'hook',
          paragraphs: [
            {
              id: 'p-1',
              text: 'Привіт усім!',
              speakerRole: 'main_speaker',
              estimatedDurationMs: 3000,
            },
          ],
        },
      ],
    };

    const validated = validateScriptDocument(validScript);
    expect(validated.id).toBe('script-valid-01');
    expect(validated.scenes.length).toBe(1);
  });
});
