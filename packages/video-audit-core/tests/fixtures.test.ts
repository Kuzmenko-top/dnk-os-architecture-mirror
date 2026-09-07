/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/fixtures.test.ts"
# purpose: "Unit Tests verifying all built-in Fixtures against Schema Validators."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  talkingHeadAuditFixture,
  productDemoAuditFixture,
  educationalShortAuditFixture,
  reburnAdaptationFixture,
  validateVideoAuditReport,
  validateAdaptationResult,
  validateScriptDocument,
  validateProsodyDocument,
  validateShotList,
} from '../src/index.js';

describe('Built-in Reference & Adaptation Fixture Validation', () => {
  it('should validate talking-head audit fixture', () => {
    const validated = validateVideoAuditReport(talkingHeadAuditFixture);
    expect(validated.id).toBe('audit-talking-head-001');
  });

  it('should validate product-demo audit fixture', () => {
    const validated = validateVideoAuditReport(productDemoAuditFixture);
    expect(validated.id).toBe('audit-product-demo-001');
  });

  it('should validate educational-short audit fixture', () => {
    const validated = validateVideoAuditReport(educationalShortAuditFixture);
    expect(validated.id).toBe('audit-educational-short-001');
  });

  it('should validate reburn-reference end-to-end adaptation result fixture and its sub-contracts', () => {
    const validatedAdaptation = validateAdaptationResult(reburnAdaptationFixture);
    expect(validatedAdaptation.id).toBe('adapt-reburn-001');

    const validatedScript = validateScriptDocument(reburnAdaptationFixture.script);
    expect(validatedScript.schemaVersion).toBe('script.v1');

    const validatedProsody = validateProsodyDocument(reburnAdaptationFixture.prosody);
    expect(validatedProsody.schemaVersion).toBe('prosody.v1');

    const validatedShotList = validateShotList(reburnAdaptationFixture.shotList);
    expect(validatedShotList.schemaVersion).toBe('shot-list.v1');
  });
});
