/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/adaptation/domain/guards/human-review-policy.ts"
# purpose: "Fail-closed Human Review Decision Engine for Adaptation Results."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { AdaptationStatus } from '../../../schemas/adaptation.js';
import { BrandComplianceReport } from '../../../schemas/brand.js';
import { SimilarityReport } from '../../../schemas/similarity.js';
import { ScriptDocument } from '../../../schemas/script.js';
import { ProsodyDocument } from '../../../schemas/prosody.js';
import { ShotList } from '../../../schemas/shotlist.js';

export interface HumanReviewEvaluationInput {
  targetDurationMs: number;
  script: ScriptDocument;
  prosody?: ProsodyDocument;
  shotList?: ShotList;
  brandCompliance: BrandComplianceReport;
  similarity: SimilarityReport;
  rightsStatus?: 'cleared' | 'unknown' | 'flagged';
  safetyFlagged?: boolean;
}

export interface HumanReviewDecision {
  status: AdaptationStatus;
  reasons: string[];
  requiresManualReview: boolean;
}

export class HumanReviewPolicy {
  public evaluate(input: HumanReviewEvaluationInput): HumanReviewDecision {
    const reasons: string[] = [];

    // 1. REJECTION CRITERIA (Hard fails)
    // 3.2 Missing Prosody or ShotList Policy:
    // missing prosody   → rejected (cannot execute teleprompter)
    // missing shotlist  → rejected (cannot produce video)
    if (!input.prosody || !input.prosody.tokens || input.prosody.tokens.length === 0) {
      return {
        status: 'rejected',
        reasons: ['Відсутній або неповний документ просодії (ProsodyDocument): неможливо виконати суфлер (cannot execute teleprompter).'],
        requiresManualReview: false,
      };
    }

    if (!input.shotList || !input.shotList.shots || input.shotList.shots.length === 0) {
      return {
        status: 'rejected',
        reasons: ['Відсутній або неповний список планів (ShotList): неможливо виробити відео (cannot produce video).'],
        requiresManualReview: false,
      };
    }

    if (input.similarity.overallRisk === 'critical_plagiarism') {
      return {
        status: 'rejected',
        reasons: [
          'Критичний ризик плагіату (CRITICAL_LEXICAL_SIMILARITY / критичний ризик плагіату): пряме копіювання тексту першоджерела.',
          ...input.similarity.notes
        ],
        requiresManualReview: false,
      };
    }

    if (input.brandCompliance.status === 'rejected') {
      return {
        status: 'rejected',
        reasons: [
          'Виявлено порушення заборонених заяв бренду або небезпечні рекомендації:',
          ...input.brandCompliance.forbiddenViolations,
        ],
        requiresManualReview: false,
      };
    }

    // 2. MANUAL REVIEW CRITERIA (Checkpoints requiring human sign-off)
    if (input.similarity.overallRisk === 'high') {
      reasons.push('Висока лексична схожість із першоджерелом (HIGH_LEXICAL_SIMILARITY / висока лексична схожість): сценарій занадто схожий на оригінал.');
    }

    if (input.brandCompliance.unverifiedClaims.length > 0) {
      reasons.push(
        `Згадуються непідтверджені технічні факти або сертифікація: ${input.brandCompliance.unverifiedClaims.join('; ')}`
      );
    }

    if (input.brandCompliance.commercialViolations.length > 0) {
      reasons.push(
        `Використано фінансові або окупнісні обіцянки: ${input.brandCompliance.commercialViolations.join('; ')}`
      );
    }

    if (input.rightsStatus === 'unknown' || input.rightsStatus === 'flagged') {
      reasons.push(`Статус авторських прав матеріалу не підтверджено (невідомі права, RIGHTS_STATUS_UNKNOWN, rightsStatus = ${input.rightsStatus}).`);
    }

    if (input.safetyFlagged) {
      reasons.push('Сценарій містить потенційно чутливі до безпеки інструкції з експлуатації.');
    }

    // Check duration tolerance (±25%)
    const totalWords = input.script.scenes
      .flatMap(s => s.paragraphs.map(p => p.text))
      .join(' ')
      .split(/\s+/)
      .filter(w => w.length > 0).length;
    const actualDurationMs = Math.round((totalWords / 130) * 60000);
    const diffRatio = Math.abs(actualDurationMs - input.targetDurationMs) / input.targetDurationMs;
    if (diffRatio > 0.25) {
      reasons.push(
        `Невідповідність хронометражу (DURATION_OUT_OF_BOUNDS): тривалість сценарію (${Math.round(actualDurationMs / 1000)}с) відхиляється від цільової (${Math.round(
          input.targetDurationMs / 1000
        )}с) більш ніж на 25%.`
      );
    }

    if (reasons.length > 0) {
      return {
        status: 'manual_review',
        reasons,
        requiresManualReview: true,
      };
    }

    // 3. ACCEPTED (All guards passed cleanly)
    return {
      status: 'accepted',
      reasons: ['Усі перевірки бренду, безпеки, схожості та тривалості пройдені успішно.'],
      requiresManualReview: false,
    };
  }
}
