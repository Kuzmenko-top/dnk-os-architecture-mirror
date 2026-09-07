/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/fixtures/reburn/semantic-validator.ts"
# purpose: "Semantic Assertions and Invariants Engine for ReBurn Video Audit Fixtures."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import {
  ReBurnFixtureData,
  SemanticAssertionResult,
  SemanticAssertionViolation
} from './types.js';

export class ReBurnSemanticValidator {
  public static validate(fixture: ReBurnFixtureData): SemanticAssertionResult {
    const violations: SemanticAssertionViolation[] = [];
    const { manifest, transcript, scenes, ocr, audioFeatures, multimodalAudit } = fixture;
    const duration = manifest.durationMs;

    // 1. Hook Claim Invariant: Hook exists and starts near zero
    if (manifest.invariants.hookMustStartNearZero) {
      const hookClaim = multimodalAudit.claims.find(
        (c) => c.text.toLowerCase().includes('hook') || c.text.toLowerCase().includes('хук') || (c.timeRange && c.timeRange.startMs <= 3000)
      );
      if (!hookClaim && multimodalAudit.structure.hookType === undefined) {
        violations.push({
          code: 'HOOK_CLAIM_MISSING',
          message: `Fixture ${manifest.fixtureId} must have an explicit hook claim or defined hookType in structure`,
        });
      }
      if (hookClaim?.timeRange && hookClaim.timeRange.startMs > 3000) {
        violations.push({
          code: 'HOOK_TIMESTAMP_INVALID',
          message: `Hook claim startMs (${hookClaim.timeRange.startMs}) must start near zero (<= 3000ms)`,
          context: { startMs: hookClaim.timeRange.startMs }
        });
      }
    }

    // 2. Virality Invariant: Virality & retention conclusions are NEVER 'observed' without engagement data
    if (manifest.invariants.viralityNeverObservedWithoutEngagement) {
      const viralityKeywords = ['віральн', 'viral', 'retention', 'утримання', 'ctr', 'конверсі', 'перегляд'];
      for (const claim of multimodalAudit.claims) {
        const lower = claim.text.toLowerCase();
        const mentionsVirality = viralityKeywords.some((k) => lower.includes(k));
        if (mentionsVirality && claim.classification === 'observed') {
          violations.push({
            code: 'VIRALITY_CANNOT_BE_OBSERVED',
            message: `Claim "${claim.text}" discusses virality/retention but is classified as 'observed'. Must be 'hypothesized' or 'inferred'.`,
            context: { claimId: claim.id, text: claim.text, classification: claim.classification }
          });
        }
      }
    }

    // 3. Evidence Reference Invariant: Observed claims MUST have evidence refs
    for (const claim of multimodalAudit.claims) {
      if (claim.classification === 'observed') {
        const hasRefs =
          (claim.evidenceRefs?.transcriptSegmentIds && claim.evidenceRefs.transcriptSegmentIds.length > 0) ||
          (claim.evidenceRefs?.sceneIds && claim.evidenceRefs.sceneIds.length > 0) ||
          (claim.evidenceRefs?.ocrFrameIds && claim.evidenceRefs.ocrFrameIds.length > 0) ||
          (claim.evidenceRefs?.audioSegmentIndexes && claim.evidenceRefs.audioSegmentIndexes.length > 0);

        if (!hasRefs) {
          violations.push({
            code: 'OBSERVED_CLAIM_MISSING_EVIDENCE',
            message: `Claim "${claim.id}" is marked 'observed' but lacks concrete evidence references`,
            context: { claimId: claim.id, text: claim.text }
          });
        }
      }
    }

    // 4. Timestamp Sanity: Invariants on media boundary
    for (const claim of multimodalAudit.claims) {
      if (claim.timeRange) {
        if (claim.timeRange.startMs < 0 || claim.timeRange.endMs > duration || claim.timeRange.startMs > claim.timeRange.endMs) {
          violations.push({
            code: 'CLAIM_TIMESTAMP_OUT_OF_BOUNDS',
            message: `Claim "${claim.id}" timeRange [${claim.timeRange.startMs}, ${claim.timeRange.endMs}] exceeds duration [0, ${duration}]`,
            context: { claimId: claim.id, timeRange: claim.timeRange, duration }
          });
        }
      }
    }

    // 5. Scene Count Invariant
    if (scenes) {
      if (scenes.scenes.length !== manifest.expectedScenes) {
        violations.push({
          code: 'SCENE_COUNT_MISMATCH',
          message: `Expected ${manifest.expectedScenes} scenes, but extracted ${scenes.scenes.length}`,
          context: { expected: manifest.expectedScenes, actual: scenes.scenes.length }
        });
      }
    }

    // 6. No Hallucinated IDs Invariant
    if (manifest.invariants.noHallucinatedIds) {
      const knownSegmentIds = new Set(transcript?.segments.map((s) => s.id) ?? []);
      const knownSceneIds = new Set(scenes?.scenes.map((s) => s.id) ?? []);
      const knownOcrFrameIds = new Set(ocr?.frames.map((f) => f.frameId) ?? []);

      for (const claim of multimodalAudit.claims) {
        if (claim.evidenceRefs?.transcriptSegmentIds) {
          for (const segId of claim.evidenceRefs.transcriptSegmentIds) {
            if (transcript && !knownSegmentIds.has(segId)) {
              violations.push({
                code: 'HALLUCINATED_SEGMENT_ID',
                message: `Claim "${claim.id}" references non-existent transcriptSegmentId "${segId}"`,
                context: { claimId: claim.id, segmentId: segId }
              });
            }
          }
        }

        if (claim.evidenceRefs?.sceneIds) {
          for (const sId of claim.evidenceRefs.sceneIds) {
            if (scenes && !knownSceneIds.has(sId)) {
              violations.push({
                code: 'HALLUCINATED_SCENE_ID',
                message: `Claim "${claim.id}" references non-existent sceneId "${sId}"`,
                context: { claimId: claim.id, sceneId: sId }
              });
            }
          }
        }

        if (claim.evidenceRefs?.ocrFrameIds) {
          for (const fId of claim.evidenceRefs.ocrFrameIds) {
            if (ocr && !knownOcrFrameIds.has(fId)) {
              violations.push({
                code: 'HALLUCINATED_OCR_FRAME_ID',
                message: `Claim "${claim.id}" references non-existent ocrFrameId "${fId}"`,
                context: { claimId: claim.id, frameId: fId }
              });
            }
          }
        }
      }
    }

    // 7. OCR Provenance Check
    if (manifest.expectedOcrTerms.length > 0 && ocr && !manifest.invariants.allowEmptyOcr) {
      const allOcrText = ocr.frames.flatMap((f) => f.regions.map((r) => r.text)).join(' ').toLowerCase();
      for (const term of manifest.expectedOcrTerms) {
        if (!allOcrText.includes(term.toLowerCase())) {
          violations.push({
            code: 'EXPECTED_OCR_TERM_NOT_FOUND',
            message: `Expected OCR term "${term}" not found in extracted OCR frames`,
            context: { term }
          });
        }
      }
    }

    // 8. Ukrainian Technical Terms Check
    if (manifest.expectedTechnicalTerms.length > 0) {
      const transcriptText = transcript?.segments.map((s) => s.text).join(' ') ?? '';
      const ocrText = ocr?.frames.flatMap((f) => f.regions.map((r) => r.text)).join(' ') ?? '';
      const claimsText = multimodalAudit.claims.map((c) => c.text).join(' ');
      const combinedText = [transcriptText, ocrText, claimsText].join(' ').toLowerCase();

      for (const term of manifest.expectedTechnicalTerms) {
        if (!combinedText.includes(term.toLowerCase())) {
          violations.push({
            code: 'TECHNICAL_TERM_MISSING',
            message: `Key technical term "${term}" missing from fixture corpus`,
            context: { term }
          });
        }
      }
    }

    return {
      valid: violations.length === 0,
      fixtureId: manifest.fixtureId,
      violations
    };
  }
}
