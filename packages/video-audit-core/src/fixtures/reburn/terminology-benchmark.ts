/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/fixtures/reburn/terminology-benchmark.ts"
# purpose: "Ukrainian Manufacturing & Smoking Equipment Terminology Benchmark for ReBurn."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export interface TerminologyBenchmarkResult {
  totalTerms: number;
  detectedTerms: number;
  recall: number;
  termOccurrences: Record<string, number>;
  brandIntegrityPassed: boolean;
}

export const REBURN_CANONICAL_TERMS = [
  'ReBurn',
  'димогенератор',
  'коптильна камера',
  'коптильня',
  'нержавіюча сталь',
  'AISI 304',
  'конвекція',
  'термоконтроль',
  'терморегулятор',
  'холодне копчення',
  'гаряче копчення',
  'тріска',
  'щепа',
  'конденсатовідвідник',
  'дефлектор',
  'охолоджувач диму',
  'температура ядра',
  'автоматика'
] as const;

export class ReBurnTerminologyBenchmark {
  public static evaluate(textCorpus: string): TerminologyBenchmarkResult {
    const occurrences: Record<string, number> = {};
    let detected = 0;

    for (const term of REBURN_CANONICAL_TERMS) {
      const regex = new RegExp(`\\b${term.replace('+', '\\+')}\\b`, 'gi');
      const matches = textCorpus.match(regex);
      const count = matches ? matches.length : 0;
      occurrences[term] = count;
      if (count > 0) {
        detected++;
      }
    }

    // Brand integrity: if 'reburn' is present, check that exact casing 'ReBurn' is used in title or brand mentions
    const brandMentions = textCorpus.match(/reburn/gi);
    const hasBrand = brandMentions !== null && brandMentions.length > 0;
    const exactBrandMatches = textCorpus.match(/\bReBurn\b/g);
    const brandIntegrityPassed = !hasBrand || (exactBrandMatches !== null && exactBrandMatches.length > 0);

    return {
      totalTerms: REBURN_CANONICAL_TERMS.length,
      detectedTerms: detected,
      recall: detected / REBURN_CANONICAL_TERMS.length,
      termOccurrences: occurrences,
      brandIntegrityPassed
    };
  }
}
