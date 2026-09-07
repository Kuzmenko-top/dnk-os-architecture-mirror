/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/analyzers/prompt-pipeline.test.ts"
# purpose: "Adversarial & Governance contract tests for the versioned Prompt Pipeline."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.3"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import { PromptPipeline } from '../../../src/pipeline/infrastructure/prompt/index.js';
import { MultimodalAuditInput, MultimodalAuditContext } from '../../../src/pipeline/ports/multimodal-audit-provider.js';

// Reusable mocks matching exact domain models
const mockInput: MultimodalAuditInput = {
  referenceAssetId: 'asset_123',
  metadata: {
    durationMs: 10000,
    width: 1920,
    height: 1080,
    hasAudio: true,
    hasVideo: true
  },
  artifactRefs: {
    transcript: {
      key: 'transcript_ref',
      sha256: 'a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j01234',
      schemaVersion: 'transcript.v1'
    },
    scenes: {
      key: 'scenes_ref',
      sha256: 'b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0123456',
      schemaVersion: 'scenes.v1'
    }
  },
  evidence: {
    schemaVersion: 'multimodal-evidence.v1',
    referenceAssetId: 'asset_123',
    generatedAt: new Date().toISOString(),
    aggregateStatus: 'completed' as const,
    temporalCorrelations: []
  },
  transcript: {
    schemaVersion: 'transcript.v1',
    id: 'tx_123',
    referenceAssetId: 'asset_123',
    language: 'en',
    provider: 'whisper',
    modelVersion: 'v3',
    segments: [
      { id: 'seg_01', ordinal: 1, startMs: 0, endMs: 5000, text: 'Hello world', words: [], confidence: 0.95 },
      { id: 'seg_02', ordinal: 2, startMs: 5000, endMs: 10000, text: 'Subscribe now', words: [], confidence: 0.99 }
    ],
    durationMs: 10000,
    confidence: 0.97,
    status: 'completed' as const,
    warnings: []
  },
  scenes: {
    schemaVersion: 'scenes.v1',
    referenceAssetId: 'asset_123',
    extractor: {
      provider: 'ffmpeg',
      version: '1.0.0',
      method: 'scndetect'
    },
    scenes: [
      { id: 'scene_01', ordinal: 1, startMs: 0, endMs: 4000, durationMs: 4000, boundaryConfidence: 0.95, shotType: 'wide' },
      { id: 'scene_02', ordinal: 2, startMs: 4000, endMs: 10000, durationMs: 6000, boundaryConfidence: 0.99, shotType: 'close_up' }
    ],
    durationMs: 10000,
    warnings: []
  },
  ocr: {
    schemaVersion: 'ocr.v1',
    referenceAssetId: 'asset_123',
    provider: 'tesseract',
    modelVersion: 'v5',
    frames: [
      {
        frameId: 'frame_01',
        timestampMs: 1000,
        width: 1920,
        height: 1080,
        regions: [
          {
            text: 'OFFER',
            normalizedText: 'OFFER',
            boundingBox: { x: 10, y: 10, width: 100, height: 50 },
            confidence: 0.99
          }
        ]
      }
    ],
    languageHints: ['en'],
    warnings: []
  },
  audioFeatures: {
    schemaVersion: 'audio-features.v1',
    referenceAssetId: 'asset_123',
    sampleRate: 44100,
    durationMs: 10000,
    provider: 'pyannote',
    hasAudioTrack: true,
    isDegraded: false,
    features: [
      {
        startMs: 0,
        endMs: 5000,
        silence: false,
        speechProbability: 0.9,
        musicProbability: 0.1,
        rmsDb: -15,
        clippingDetected: false
      }
    ],
    warnings: []
  }
};

const mockContext: MultimodalAuditContext = {
  targetNiches: ['lifestyle', 'fitness']
};

const buildBaseValidResult = () => ({
  schemaVersion: 'multimodal-audit.v1',
  referenceAssetId: 'asset_123',
  inputArtifacts: {
    transcript: {
      key: 'transcript_ref',
      sha256: 'a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j01234',
      schemaVersion: 'transcript.v1'
    },
    scenes: {
      key: 'scenes_ref',
      sha256: 'b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0123456',
      schemaVersion: 'scenes.v1'
    }
  },
  observedFacts: [
    {
      id: 'fact_01',
      category: 'speech' as const,
      description: 'Speaker mentioned Hello world',
      confidence: 0.99,
      timeRange: { startMs: 0, endMs: 5000 },
      evidenceRefs: { transcriptSegmentIds: ['seg_01'] }
    }
  ],
  claims: [
    {
      id: 'claim_01',
      text: 'Visual of close up at 4s',
      classification: 'observed' as any,
      confidence: 0.98,
      evidenceRefs: { sceneIds: ['scene_02'] },
      timeRange: { startMs: 4000, endMs: 10000 }
    }
  ],
  structure: {
    hookType: 'bold_claim' as const,
    hookDurationMs: 4000,
    narrativeArc: 'Introduction to climax',
    narrativeBeats: [
      { name: 'Intro', startMs: 0, endMs: 4000, description: 'Opening setup' }
    ],
    keyTakeaways: ['Good hook'],
    pacingStructure: 'Fast'
  },
  visual: {
    dominantColorPalette: ['#ffffff'],
    cutFrequencyPerMin: 12,
    faceVisibilityRatio: 0.8,
    hasCaptions: true,
    visualGrammar: 'Cinematic'
  },
  audio: {
    hasBackgroundMusic: true,
    audioPacing: 'Upbeat'
  },
  retentionHypotheses: [
    {
      id: 'ret_01',
      estimatedRetentionScore: 85,
      hypothesisType: 'hook_dropoff' as const,
      description: 'Risk at intro transition',
      severity: 'medium' as const,
      confidence: 0.8,
      evidenceRefs: { sceneIds: ['scene_01'] },
      timeRange: { startMs: 0, endMs: 4000 }
    }
  ],
  adaptationRecommendations: [
    {
      id: 'rec_01',
      opportunity: 'Make hook punchier'
    }
  ],
  confidence: 0.9,
  warnings: [] as string[],
  modelSet: {
    provider: 'test-provider',
    model: 'test-model',
    modelSetVersion: '1.0.0',
    promptTemplateVersion: '1.0.0',
    inputArtifactHashes: {
      transcript: 'a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j01234',
      scenes: 'b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j0a1b2c3d4e5f6g7h8i9j012345'
    },
    outputSchemaVersion: 'multimodal-audit.v1' as const,
    processingDurationMs: 1500
  }
});

describe('PromptPipeline and Adversarial Fixture Acceptance', () => {
  const pipeline = new PromptPipeline();

  it('1. should accept a fully valid clean JSON response', () => {
    const validResult = buildBaseValidResult();
    const rawResponse = JSON.stringify(validResult);

    const check = pipeline.evaluateResponse(rawResponse, mockInput);
    expect(check.status).toBe('accepted');
    expect(check.errors).toHaveLength(0);
    expect(check.result).toBeDefined();
    expect(check.result?.schemaVersion).toBe('multimodal-audit.v1');
  });

  it('2. should safely extract JSON wrapped in a markdown fence', () => {
    const validResult = buildBaseValidResult();
    const rawResponse = `
Some intro text that is extra prose.
\`\`\`json
${JSON.stringify(validResult, null, 2)}
\`\`\`
Some footer text.
`;

    const check = pipeline.evaluateResponse(rawResponse, mockInput);
    expect(check.status).toBe('accepted');
    expect(check.errors).toHaveLength(0);
  });

  it('3. should extract and parse JSON with extra prose around it but no fence', () => {
    const validResult = buildBaseValidResult();
    const rawResponse = `
Here is your requested audit payload:
${JSON.stringify(validResult)}
Hope you find it useful.
`;

    const check = pipeline.evaluateResponse(rawResponse, mockInput);
    expect(check.status).toBe('accepted');
    expect(check.errors).toHaveLength(0);
  });

  it('4. should reject an invalid enum in claims classification', () => {
    const badResult = buildBaseValidResult();
    (badResult.claims[0] as any).classification = 'super-hallucinated-type';
    const rawResponse = JSON.stringify(badResult);

    const check = pipeline.evaluateResponse(rawResponse, mockInput);
    expect(check.status).toBe('rejected');
    expect(check.errors[0]).toContain('classification');
  });

  it('5. should reject observed claims/facts with missing or empty evidence refs', () => {
    const badResult = buildBaseValidResult();
    // Empty evidenceRefs
    badResult.claims[0].evidenceRefs = {} as any;
    const rawResponse = JSON.stringify(badResult);

    const check = pipeline.evaluateResponse(rawResponse, mockInput);
    expect(check.status).toBe('manual_review');
    expect(check.errors.some((e: string) => e.includes('must contain at least one evidence reference'))).toBe(true);
  });

  it('6. should issue a warning for hypothesized claims with no evidence refs', () => {
    const validResult = buildBaseValidResult();
    validResult.claims.push({
      id: 'claim_hypo',
      text: 'We hypothesize a high dropoff at the start',
      classification: 'hypothesized' as any,
      confidence: 0.99, // Decoupled confidence: high confidence in hypothesis is allowed
      evidenceRefs: {} as any,
      timeRange: { startMs: 0, endMs: 2000 }
    });
    const rawResponse = JSON.stringify(validResult);

    const check = pipeline.evaluateResponse(rawResponse, mockInput);
    expect(check.status).toBe('accepted');
    expect(check.warnings.some((w: string) => w.includes('has no evidence references/context'))).toBe(true);
  });

  it('7. should reject invalid timeRange (startMs > endMs)', () => {
    const badResult = buildBaseValidResult();
    badResult.claims[0].timeRange = { startMs: 5000, endMs: 2000 };
    const rawResponse = JSON.stringify(badResult);

    const check = pipeline.evaluateResponse(rawResponse, mockInput);
    // Since startMs > endMs is refined on the AuditedClaimSchema, it fails zod schema validation
    expect(check.status).toBe('rejected');
  });

  it('8. should reject hallucinated scene IDs that do not exist in input', () => {
    const badResult = buildBaseValidResult();
    badResult.claims[0].evidenceRefs = { sceneIds: ['scene_non_existent'] };
    const rawResponse = JSON.stringify(badResult);

    const check = pipeline.evaluateResponse(rawResponse, mockInput);
    expect(check.status).toBe('manual_review');
    expect(check.errors.some((e: string) => e.includes('Hallucinated scene ID found'))).toBe(true);
  });

  it('9. should reject wrong schemaVersion', () => {
    const validResult = buildBaseValidResult();
    (validResult as any).schemaVersion = 'multimodal-audit.v2';
    const rawResponse = JSON.stringify(validResult);

    const check = pipeline.evaluateResponse(rawResponse, mockInput);
    expect(check.status).toBe('rejected');
    expect(check.errors[0]).toContain('schemaVersion');
  });

  it('10. should safely repair malformed JSON (trailing comma) and parse it', () => {
    const validResult = buildBaseValidResult();
    const rawWithTrailingComma = JSON.stringify(validResult).replace(
      '"expectedImpact":"Increase retention"}',
      '"expectedImpact":"Increase retention",}'
    ); // causes a valid trailing comma before }

    const check = pipeline.evaluateResponse(rawWithTrailingComma, mockInput);
    expect(check.status).toBe('accepted');
    expect(check.errors).toHaveLength(0);
  });

  it('11. should reject severe malformed JSON that cannot be safely repaired', () => {
    const RawTrash = '{ "schemaVersion": "multimodal-audit.v1", "referenceAssetId": "some_asset_id", and some unclosed string';

    const check = pipeline.evaluateResponse(RawTrash, mockInput);
    expect(check.status).toBe('rejected');
    expect(check.errors[0]).toContain('Failed to parse response JSON even after repair');
  });

  it('12. should reject oversized response', () => {
    const validResult = buildBaseValidResult();
    let massiveProse = 'A'.repeat(1050000); // Exceeds 1MB
    const rawResponse = JSON.stringify(validResult) + massiveProse;

    const check = pipeline.evaluateResponse(rawResponse, mockInput);
    expect(check.status).toBe('rejected');
    expect(check.errors[0]).toContain('Response oversized');
  });

  it('13. should handle partial input with warning and accepted status', () => {
    // Input missing transcript entirely
    const partialInput = { ...mockInput, transcript: undefined };
    const promptBuild = pipeline.generatePrompt(partialInput, mockContext);

    expect(promptBuild.warnings).toContain('PARTIAL_INPUT_MISSING_TRANSCRIPT');

    // Result without transcript artifact refs
    const validResult = buildBaseValidResult();
    (validResult.inputArtifacts as any).transcript = undefined;
    const rawResponse = JSON.stringify(validResult);

    const check = pipeline.evaluateResponse(rawResponse, partialInput, promptBuild.warnings);
    expect(check.status).toBe('accepted');
    expect(check.warnings).toContain('PARTIAL_INPUT_MISSING_TRANSCRIPT');
  });
});
