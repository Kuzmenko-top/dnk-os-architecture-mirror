/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/analyzers/scene-schema.test.ts"
# purpose: "Unit Tests for scenes.v1 Canonical Contract, Time Invariants, and Policy Validation."
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
  SceneDocumentSchema,
  SceneSchema,
  validateScenesNonOverlapping,
  SceneExtractionPolicySchema
} from '../../../src/pipeline/domain/analyzers/scenes.js';

describe('scenes.v1 Schema & Time Invariants', () => {
  it('validates a valid SceneDocument with non-overlapping scenes', () => {
    const doc = {
      schemaVersion: 'scenes.v1',
      referenceAssetId: 'asset-101',
      extractor: {
        provider: 'deterministic-scene-provider',
        version: '1.0.0',
        method: 'time_slice'
      },
      durationMs: 5000,
      scenes: [
        {
          id: 'scene_0',
          ordinal: 0,
          startMs: 0,
          endMs: 2500,
          durationMs: 2500,
          boundaryConfidence: 0.9,
          shotType: 'talking_head'
        },
        {
          id: 'scene_1',
          ordinal: 1,
          startMs: 2500,
          endMs: 5000,
          durationMs: 2500,
          boundaryConfidence: 0.88,
          shotType: 'product'
        }
      ]
    };

    const parsed = SceneDocumentSchema.parse(doc);
    expect(parsed.schemaVersion).toBe('scenes.v1');
    expect(parsed.scenes).toHaveLength(2);
    expect(validateScenesNonOverlapping(parsed.scenes)).toBe(true);
  });

  it('rejects scenes with endMs <= startMs', () => {
    expect(() =>
      SceneSchema.parse({
        id: 'scene_bad',
        ordinal: 0,
        startMs: 1000,
        endMs: 1000,
        durationMs: 0,
        boundaryConfidence: 0.5
      })
    ).toThrow();
  });

  it('rejects overlapping scenes', () => {
    const scenes = [
      SceneSchema.parse({
        id: 'scene_0',
        ordinal: 0,
        startMs: 0,
        endMs: 3000,
        durationMs: 3000,
        boundaryConfidence: 0.9
      }),
      SceneSchema.parse({
        id: 'scene_1',
        ordinal: 1,
        startMs: 2500,
        endMs: 5000,
        durationMs: 2500,
        boundaryConfidence: 0.9
      })
    ];

    expect(validateScenesNonOverlapping(scenes)).toBe(false);
  });

  it('validates SceneExtractionPolicy defaults', () => {
    const policy = SceneExtractionPolicySchema.parse({
      threshold: 0.35,
      minSceneDurationMs: 1200,
      keyframeStrategy: 'middle',
      maxScenes: 15
    });

    expect(policy.threshold).toBe(0.35);
    expect(policy.maxScenes).toBe(15);
  });
});
