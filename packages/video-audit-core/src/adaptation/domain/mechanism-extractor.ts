/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/adaptation/domain/mechanism-extractor.ts"
# purpose: "Deterministic Content Mechanism Extractor using mapped input structures."
# canonical_source: true
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditReport, SceneRole } from '../../schemas/audit.js';
import { TimeRange } from '../../schemas/common.js';

export type HookMechanism =
  | 'contrarian_hook'
  | 'curiosity_gap'
  | 'bold_claim'
  | 'negative_framing'
  | 'problem_hook'
  | 'demonstration_hook'
  | 'question_hook';

export type NarrativePattern =
  | 'problem_solution'
  | 'educational_listicle'
  | 'before_after'
  | 'technical_explainer'
  | 'founder_story'
  | 'proof_demo'
  | 'offer_cta';

export type ShotRhythm = 'fast_paced' | 'steady_cadence' | 'deliberate_slow';
export type PausePattern = 'emphatic_punch' | 'conversational_flow' | 'rhythmic_rapid';
export type CtaPattern = 'direct_commercial' | 'educational_comment' | 'consultation_lead' | 'profile_link';

export interface ExtractedMechanisms {
  hookMechanism: HookMechanism;
  narrativePattern: NarrativePattern;
  shotRhythm: ShotRhythm;
  pausePattern: PausePattern;
  ctaPattern: CtaPattern;
  keyInsights: string[];
  recommendedPacingWpm: number;
}

export interface MechanismExtractionInput {
  reportId: string;
  hookType: string;
  hookDurationMs: number;
  narrativeArc: string;
  keyTakeaways: string[];
  ctaType?: string;
  pacingStructure: string;
  scenes: Array<{
    id: string;
    role: SceneRole;
    timeRange: TimeRange;
    summary: string;
    shotCount: number;
  }>;
  audioFeatures: {
    speakingWpm?: number;
    pauseCount: number;
    averagePauseDurationMs: number;
  };
  visuals: {
    cutFrequencyPerMin: number;
  };
  observedClaims: string[];
}

export function mapAuditReportToExtractionInput(report: VideoAuditReport): MechanismExtractionInput {
  const observedClaims = report.evidence
    .filter(e => e.type === 'observed')
    .map(e => e.claim);

  return {
    reportId: report.id,
    hookType: report.structure.hookType,
    hookDurationMs: report.structure.hookDurationMs,
    narrativeArc: report.structure.narrativeArc,
    keyTakeaways: report.structure.keyTakeaways ?? [],
    ctaType: report.structure.ctaType,
    pacingStructure: report.structure.pacingStructure,
    scenes: report.scenes.map(s => ({
      id: s.id,
      role: s.role,
      timeRange: s.timeRange,
      summary: s.summary,
      shotCount: s.shots?.length ?? 0,
    })),
    audioFeatures: {
      speakingWpm: report.audioFeatures.speakingWpm,
      pauseCount: report.audioFeatures.pauseCount,
      averagePauseDurationMs: report.audioFeatures.averagePauseDurationMs,
    },
    visuals: {
      cutFrequencyPerMin: report.visuals.cutFrequencyPerMin,
    },
    observedClaims,
  };
}

export class MechanismExtractor {
  public extract(input: MechanismExtractionInput): ExtractedMechanisms {
    const hookScene = input.scenes.find(s => s.role === 'hook');
    const hookText = (hookScene?.summary ?? '').toLowerCase();

    // 1. Classify Hook Mechanism
    let hookMechanism: HookMechanism = 'problem_hook';
    if (hookText.includes('не') || hookText.includes('помилк') || hookText.includes('ніколи') || hookText.includes('дарма')) {
      hookMechanism = 'contrarian_hook';
    } else if (hookText.includes('як') || hookText.includes('чому') || hookText.includes('секрет')) {
      hookMechanism = 'curiosity_gap';
    } else if (hookText.includes('до') && hookText.includes('після')) {
      hookMechanism = 'demonstration_hook';
    } else if (hookText.includes('?') || hookText.includes('чи ви знаєте')) {
      hookMechanism = 'question_hook';
    } else if (hookText.includes('100%') || hookText.includes('найкращ') || hookText.includes('гарант')) {
      hookMechanism = 'bold_claim';
    }

    // 2. Classify Narrative Pattern
    const sceneRoles = input.scenes.map(s => s.role);
    const fullText = input.scenes.map(s => s.summary).join(' ').toLowerCase();

    let narrativePattern: NarrativePattern = 'problem_solution';
    if (sceneRoles.includes('demonstration') && (fullText.includes('до') && fullText.includes('після'))) {
      narrativePattern = 'before_after';
    } else if (fullText.includes('правил') || fullText.includes('помилк') || fullText.includes('1.') || fullText.includes('2.')) {
      narrativePattern = 'educational_listicle';
    } else if (fullText.includes('температур') || fullText.includes('конвекц') || fullText.includes('датчик') || fullText.includes('pid')) {
      narrativePattern = 'technical_explainer';
    } else if (fullText.includes('ми почали') || fullText.includes('майстерн') || fullText.includes('бренд') || fullText.includes('історі')) {
      narrativePattern = 'founder_story';
    } else if (sceneRoles.includes('demonstration') && !sceneRoles.includes('problem_statement')) {
      narrativePattern = 'proof_demo';
    }

    // 3. Classify Shot Rhythm
    let shotRhythm: ShotRhythm = 'steady_cadence';
    if (input.visuals.cutFrequencyPerMin > 20) {
      shotRhythm = 'fast_paced';
    } else if (input.visuals.cutFrequencyPerMin < 8) {
      shotRhythm = 'deliberate_slow';
    }

    // 4. Classify Pause Pattern
    const audio = input.audioFeatures;
    let pausePattern: PausePattern = 'conversational_flow';
    if (audio.pauseCount > 5 && audio.averagePauseDurationMs > 400) {
      pausePattern = 'emphatic_punch';
    } else if (audio.speakingWpm && audio.speakingWpm > 160) {
      pausePattern = 'rhythmic_rapid';
    }

    // 5. Classify CTA Pattern
    const ctaScene = input.scenes.find(s => s.role === 'call_to_action');
    const ctaText = (ctaScene?.summary ?? '').toLowerCase();
    let ctaPattern: CtaPattern = 'profile_link';
    if (ctaText.includes('консульт') || ctaText.includes('прорах') || ctaText.includes('інженер')) {
      ctaPattern = 'consultation_lead';
    } else if (ctaText.includes('ціна') || ctaText.includes('купити') || ctaText.includes('замов')) {
      ctaPattern = 'direct_commercial';
    } else if (ctaText.includes('пишіть') || ctaText.includes('коментар') || ctaText.includes('слово')) {
      ctaPattern = 'educational_comment';
    }

    // 6. Pacing recommendation
    const recommendedPacingWpm = audio.speakingWpm && audio.speakingWpm >= 110 && audio.speakingWpm <= 170
      ? audio.speakingWpm
      : 140;

    const keyInsights: string[] = [
      `Hook format: ${hookMechanism} across initial ${Math.round(input.hookDurationMs / 1000)}s`,
      `Core structural flow: ${narrativePattern} with ${input.scenes.length} narrative scenes`,
      `Visual shot rhythm: ${shotRhythm} (cut rate ${input.visuals.cutFrequencyPerMin}/min)`,
      `Vocal delivery style: ${pausePattern} around ${recommendedPacingWpm} WPM`,
    ];

    return {
      hookMechanism,
      narrativePattern,
      shotRhythm,
      pausePattern,
      ctaPattern,
      keyInsights,
      recommendedPacingWpm,
    };
  }
}
