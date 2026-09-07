/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/serialization.test.ts"
# purpose: "Unit Tests for Contract Serialization & Deserialization."
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
  reburnAdaptationFixture,
  serializeContract,
  deserializeVideoAuditReport,
  deserializeAdaptationResult,
} from '../src/index.js';

describe('Contract Serialization & Deserialization', () => {
  it('should round-trip serialize and deserialize VideoAuditReport', () => {
    const jsonStr = serializeContract(talkingHeadAuditFixture);
    const restored = deserializeVideoAuditReport(jsonStr);

    expect(restored.id).toBe(talkingHeadAuditFixture.id);
    expect(restored.schemaVersion).toBe('video-audit.v1');
    expect(restored.transcript.segments.length).toBe(1);
  });

  it('should round-trip serialize and deserialize AdaptationResult with nested contracts', () => {
    const jsonStr = serializeContract(reburnAdaptationFixture);
    const restored = deserializeAdaptationResult(jsonStr);

    expect(restored.id).toBe(reburnAdaptationFixture.id);
    expect(restored.script.schemaVersion).toBe('script.v1');
    expect(restored.prosody.schemaVersion).toBe('prosody.v1');
    expect(restored.shotList.schemaVersion).toBe('shot-list.v1');
    expect(restored.similarity.overallRisk).toBe('low');
  });
});
