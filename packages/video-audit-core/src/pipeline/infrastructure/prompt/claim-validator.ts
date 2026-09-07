/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/prompt/claim-validator.ts"
# purpose: "Evidence Governance & Claim Validator to detect hallucinations, invalid times, and empty references."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { MultimodalAuditResult } from '../../../schemas/multimodal-audit.js';
import { MultimodalAuditInput } from '../../ports/multimodal-audit-provider.js';

export interface ValidationIssue {
  type: 'error' | 'warning';
  message: string;
}

export class EvidenceClaimValidator {
  validate(result: MultimodalAuditResult, input: MultimodalAuditInput): ValidationIssue[] {
    const issues: ValidationIssue[] = [];

    // Gather valid IDs from input artifacts
    const validSceneIds = new Set<string>(input.scenes?.scenes.map(s => s.id) ?? []);
    const validSegmentIds = new Set<string>(input.transcript?.segments.map(s => s.id) ?? []);
    const validFrameIds = new Set<string>(input.ocr?.frames.map(f => f.frameId) ?? []);
    const totalDurationMs = input.metadata.durationMs;

    const hasScenes = !!input.scenes && input.scenes.scenes.length > 0;
    const hasTranscript = !!input.transcript && input.transcript.segments.length > 0;
    const hasOcr = !!input.ocr && input.ocr.frames.length > 0;
    const hasAudio = !!input.audioFeatures && input.audioFeatures.features.length > 0;

    // Helper to check if evidenceRefs has any references at all
    const hasAnyRef = (refs: any): boolean => {
      if (!refs) return false;
      const tSegs = Array.isArray(refs.transcriptSegmentIds) ? refs.transcriptSegmentIds.length : 0;
      const tWords = Array.isArray(refs.transcriptWordIndexes) ? refs.transcriptWordIndexes.length : 0;
      const sIds = Array.isArray(refs.sceneIds) ? refs.sceneIds.length : 0;
      const oIds = Array.isArray(refs.ocrFrameIds) ? refs.ocrFrameIds.length : 0;
      const aSegs = Array.isArray(refs.audioSegmentIndexes) ? refs.audioSegmentIndexes.length : 0;
      return tSegs > 0 || tWords > 0 || sIds > 0 || oIds > 0 || aSegs > 0;
    };

    // Helper to check for hallucinated IDs
    const checkHallucinations = (refs: any, contextName: string) => {
      if (!refs) return;

      if (refs.sceneIds && Array.isArray(refs.sceneIds)) {
        for (const id of refs.sceneIds) {
          if (hasScenes && !validSceneIds.has(id)) {
            issues.push({
              type: 'error',
              message: `Hallucinated scene ID found in ${contextName}: "${id}"`
            });
          }
        }
      }

      if (refs.transcriptSegmentIds && Array.isArray(refs.transcriptSegmentIds)) {
        for (const id of refs.transcriptSegmentIds) {
          if (hasTranscript && !validSegmentIds.has(id)) {
            issues.push({
              type: 'error',
              message: `Hallucinated transcript segment ID found in ${contextName}: "${id}"`
            });
          }
        }
      }

      if (refs.ocrFrameIds && Array.isArray(refs.ocrFrameIds)) {
        for (const id of refs.ocrFrameIds) {
          if (hasOcr && !validFrameIds.has(id)) {
            issues.push({
              type: 'error',
              message: `Hallucinated OCR frame ID found in ${contextName}: "${id}"`
            });
          }
        }
      }
    };

    // Helper to check timeRange
    const checkTimeRange = (range: any, contextName: string) => {
      if (!range) return;
      if (typeof range.startMs !== 'number' || typeof range.endMs !== 'number') {
        issues.push({
          type: 'error',
          message: `Invalid timeRange types in ${contextName}`
        });
        return;
      }
      if (range.startMs < 0 || range.endMs < 0) {
        issues.push({
          type: 'error',
          message: `Negative timestamps in timeRange for ${contextName}: [${range.startMs}ms - ${range.endMs}ms]`
        });
      }
      if (range.startMs > range.endMs) {
        issues.push({
          type: 'error',
          message: `Invalid timeRange for ${contextName}: startMs (${range.startMs}) cannot exceed endMs (${range.endMs})`
        });
      }
      if (range.endMs > totalDurationMs + 100) { // allow 100ms tolerance
        issues.push({
          type: 'error',
          message: `TimeRange in ${contextName} [${range.startMs}ms - ${range.endMs}ms] exceeds video duration (${totalDurationMs}ms)`
        });
      }
    };

    // 1. Validate Observed Facts
    if (result.observedFacts && Array.isArray(result.observedFacts)) {
      for (const fact of result.observedFacts) {
        const descName = `fact "${fact.id}"`;
        // Observed facts MUST have evidence references
        if (!hasAnyRef(fact.evidenceRefs)) {
          issues.push({
            type: 'error',
            message: `Observed fact "${fact.id}" must contain at least one evidence reference.`
          });
        }
        checkHallucinations(fact.evidenceRefs, descName);
        checkTimeRange(fact.timeRange, descName);
      }
    }

    // 2. Validate Claims
    if (result.claims && Array.isArray(result.claims)) {
      for (const claim of result.claims) {
        const descName = `claim "${claim.id}"`;

        // Classification-specific rules
        if (claim.classification === 'observed') {
          if (!hasAnyRef(claim.evidenceRefs)) {
            issues.push({
              type: 'error',
              message: `Observed claim "${claim.id}" must contain at least one evidence reference.`
            });
          }
        } else if (claim.classification === 'hypothesized') {
          if (!hasAnyRef(claim.evidenceRefs)) {
            issues.push({
              type: 'warning',
              message: `Hypothesized claim "${claim.id}" has no evidence references/context.`
            });
          }
        }

        checkHallucinations(claim.evidenceRefs, descName);
        checkTimeRange(claim.timeRange, descName);
      }
    }

    // 3. Validate Retention Hypotheses (they also have timeRanges and evidenceRefs)
    if (result.retentionHypotheses && Array.isArray(result.retentionHypotheses)) {
      for (const hyp of result.retentionHypotheses) {
        const descName = `retention hypothesis "${hyp.id}"`;
        checkHallucinations(hyp.evidenceRefs, descName);
        checkTimeRange(hyp.timeRange, descName);
      }
    }

    return issues;
  }
}
