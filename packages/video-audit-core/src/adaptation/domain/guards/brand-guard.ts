/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/adaptation/domain/guards/brand-guard.ts"
# purpose: "Brand Safety, Approved Fact Alignment and Forbidden Claims Guard."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { BrandProfile, BrandComplianceReport, BrandComplianceStatus } from '../../../schemas/brand.js';
import { ScriptDocument } from '../../../schemas/script.js';

export interface BrandGuardOptions {
  strictMode?: boolean;
}

export class BrandGuard {
  constructor(private readonly options: BrandGuardOptions = {}) {}

  public evaluate(
    script: ScriptDocument,
    profile: BrandProfile,
    approvedFactIds: string[] = []
  ): BrandComplianceReport {
    const fullText = script.scenes
      .flatMap(s => s.paragraphs.map(p => p.text))
      .join(' ')
      .toLowerCase();

    const paragraphs = script.scenes.flatMap(s => s.paragraphs.map(p => p.text));
    const sentences = paragraphs.flatMap(p => {
      return p.split(/(?<=[.!?])\s+/).map(s => s.trim()).filter(Boolean);
    });

    const usedFactIds: string[] = [];
    const unverifiedClaims: string[] = [];
    const forbiddenViolations: string[] = [];
    const commercialViolations: string[] = [];
    const notes: string[] = [];

    // 1. Check Forbidden Claims & Additional safety heuristics
    for (const sentence of sentences) {
      const sLower = sentence.toLowerCase();
      for (const forbidden of profile.forbiddenClaims) {
        if (sLower.includes(forbidden.toLowerCase())) {
          forbiddenViolations.push(sentence);
        }
      }
      if (sLower.includes('в квартирі без') || sLower.includes('без витяжк') || sLower.includes('без димоходу')) {
        forbiddenViolations.push(sentence);
      }
    }

    // 2. Commercial & ROI Claims Check
    const roiPatterns = [
      /окупність за \d+ (дн|тиж)/i,
      /гарантований прибуток/i,
      /100% прибуток/i,
      /заробите \d+ (грн|\$|євро)/i,
      /окупіть коптильню/i,
      /чистим прибутком/i,
      /окуп/i,
    ];
    for (const sentence of sentences) {
      const sLower = sentence.toLowerCase();
      for (const pat of roiPatterns) {
        if (pat.test(sLower)) {
          commercialViolations.push(sentence);
          if (!unverifiedClaims.includes(sentence)) {
            unverifiedClaims.push(sentence);
          }
          if (!notes.some(n => n.includes('UNVERIFIED_COMMERCIAL_CLAIM'))) {
            notes.push('УВАГА: UNVERIFIED_COMMERCIAL_CLAIM - Непідтверджена фінансова або окупнісна обіцянка у тексті сценарію');
          }
        }
      }
    }

    // 3. Match and verify referenced brand facts
    for (const fact of profile.approvedFacts) {
      if (fact.status !== 'approved') continue;

      // Check keywords from the fact with stem/prefix support
      const factKeywords = this.extractSignificantKeywords(fact.text);
      const matchCount = factKeywords.filter(kw => {
        const kwLower = kw.toLowerCase();
        return fullText.includes(kwLower) || (kwLower.length > 5 && fullText.includes(kwLower.slice(0, 5)));
      }).length;
      const ratio = factKeywords.length > 0 ? matchCount / factKeywords.length : 0;

      if (ratio >= 0.4 || fullText.includes(fact.id.toLowerCase())) {
        usedFactIds.push(fact.id);

        if (approvedFactIds && !approvedFactIds.includes(fact.id)) {
          for (const sentence of sentences) {
            const sLower = sentence.toLowerCase();
            const sMatchCount = factKeywords.filter(kw => {
              const kwLower = kw.toLowerCase();
              return sLower.includes(kwLower) || (kwLower.length > 5 && sLower.includes(kwLower.slice(0, 5)));
            }).length;
            const sRatio = factKeywords.length > 0 ? sMatchCount / factKeywords.length : 0;
            if (sRatio >= 0.3 || sLower.includes(fact.id.toLowerCase())) {
              if (!unverifiedClaims.includes(sentence)) {
                unverifiedClaims.push(sentence);
              }
            }
          }
        }
      }
    }

    // Check if explicitly requested facts are present
    for (const requestedId of approvedFactIds) {
      const fact = profile.approvedFacts.find(f => f.id === requestedId);
      if (!fact) {
        unverifiedClaims.push(`Запитаний ID факту не знайдено в базі бренду: ${requestedId}`);
      } else if (fact.status === 'deprecated') {
        unverifiedClaims.push(`Запитаний факт застарів (deprecated): ${requestedId}`);
      }
    }

    // 4. Unverified claims detection (e.g. certificates without sources)
    for (const sentence of sentences) {
      const sLower = sentence.toLowerCase();
      if (sLower.includes('сертифік') || sLower.includes('європейськ') || sLower.includes('iso')) {
        const hasCertFact = usedFactIds.some(id => {
          const f = profile.approvedFacts.find(x => x.id === id);
          return f && (f.source.includes('cert') || f.text.toLowerCase().includes('сертифік'));
        });
        if (!hasCertFact) {
          if (!unverifiedClaims.includes(sentence)) {
            unverifiedClaims.push(sentence);
          }
        }
      }
    }

    // 5. Tone analysis
    let toneScore = 1.0;
    const spamWords = ['шок', 'сенсація', 'неймовірно дешево', 'дарма', 'халява', 'бомба'];
    for (const spam of spamWords) {
      if (fullText.includes(spam)) {
        toneScore -= 0.15;
        notes.push(`Знижено бал тону через клікбейтне або агресивне слово: "${spam}"`);
      }
    }
    toneScore = Math.max(0.1, Math.min(1.0, toneScore));

    // 6. Decide Compliance Status
    let status: BrandComplianceStatus = 'approved';
    if (forbiddenViolations.length > 0) {
      status = 'rejected';
      notes.push('КРИТИЧНО: Виявлено прямі порушення безпеки або заборонених заяв.');
    } else if (commercialViolations.length > 0 || unverifiedClaims.length > 0 || toneScore < 0.7) {
      status = 'flagged';
      notes.push('УВАГА: Сценарій містить твердження, які вимагають додаткової перевірки модератором.');
    } else {
      notes.push('Сценарій відповідає затвердженим фактам бренду ReBurn.');
    }

    return {
      status,
      usedFactIds: Array.from(new Set(usedFactIds)),
      unverifiedClaims,
      forbiddenViolations,
      commercialViolations,
      toneScore: Math.round(toneScore * 100) / 100,
      notes,
    };
  }

  private extractSignificantKeywords(text: string): string[] {
    const stopWords = new Set(['і', 'в', 'на', 'з', 'до', 'для', 'та', 'по', 'що', 'як', 'це', 'за', 'від', 'але']);
    return text
      .split(/[\s,.-]+/)
      .map(w => w.trim().toLowerCase())
      .filter(w => w.length > 3 && !stopWords.has(w));
  }
}
