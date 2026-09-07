/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/adaptation/domain/script-writer/script-writer.ts"
# purpose: "Script Writer Interface and Deterministic Generator for Brand-Safe Niche Adaptation."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { ScriptDocument, ScriptScene, ScriptParagraph } from '../../../schemas/script.js';
import { AdaptationRequest } from '../../../schemas/adaptation.js';
import { BrandProfile, ApprovedBrandFact } from '../../../schemas/brand.js';
import { ExtractedMechanisms } from '../mechanism-extractor.js';

export interface ScriptWriter {
  generate(
    request: AdaptationRequest,
    mechanisms: ExtractedMechanisms,
    profile: BrandProfile
  ): Promise<ScriptDocument> | ScriptDocument;
}

export class DeterministicScriptWriter implements ScriptWriter {
  public generate(
    request: AdaptationRequest,
    mechanisms: ExtractedMechanisms,
    profile: BrandProfile
  ): ScriptDocument {
    const scriptId = `script-adapt-${request.sourceAuditId}-${Math.floor(Math.random() * 10000)}`;

    // 1. Select approved facts to integrate
    const approvedFacts: ApprovedBrandFact[] = request.approvedFactIds.length > 0
      ? profile.approvedFacts.filter(f => request.approvedFactIds.includes(f.id) && f.status === 'approved')
      : profile.approvedFacts.filter(f => f.status === 'approved');

    const materialFact = approvedFacts.find(f => f.category === 'material') ?? profile.approvedFacts[0];
    const processFact = approvedFacts.find(f => f.category === 'process') ?? profile.approvedFacts[1];
    const safetyFact = approvedFacts.find(f => f.category === 'safety') ?? profile.approvedFacts[4];

    // 2. Generate 3–5 Hook Variants
    const hookVariants = this.generateHookVariants(mechanisms, request.audience);

    // 3. Assemble Scenes
    const targetSec = Math.round(request.targetDurationMs / 1000);
    const hookDurationMs = 3500;
    const ctaDurationMs = 4500;
    const remainingMs = Math.max(5000, request.targetDurationMs - hookDurationMs - ctaDurationMs);
    const problemDurationMs = Math.round(remainingMs * 0.4);
    const solutionDurationMs = Math.round(remainingMs * 0.6);

    const scenes: ScriptScene[] = [
      {
        id: 'scene-1-hook',
        title: 'Гачок (Hook)',
        role: 'hook',
        paragraphs: [
          {
            id: 'p-1',
            speakerRole: 'host',
            text: hookVariants[0],
            estimatedDurationMs: hookDurationMs,
          },
        ],
        targetTimeRange: { startMs: 0, endMs: hookDurationMs },
      },
      {
        id: 'scene-2-problem',
        title: 'Біль та типова помилка',
        role: 'problem_statement',
        paragraphs: [
          {
            id: 'p-2',
            speakerRole: 'host',
            text: `Якщо ви коптили у звичайній бочці або кустарному ящику, то знаєте головний біль: кислий конденсат і гіркий чорний наліт на м’ясі.`,
            estimatedDurationMs: problemDurationMs,
          },
        ],
        targetTimeRange: { startMs: hookDurationMs, endMs: hookDurationMs + problemDurationMs },
      },
      {
        id: 'scene-3-solution',
        title: 'Інженерне вирішення ReBurn',
        role: 'demonstration',
        paragraphs: [
          {
            id: 'p-3',
            speakerRole: 'host',
            text: `В установках ReBurn дим проходить крізь циклонний конденсатовідвідник, а примусова конвекція та сталь AISI 304 тримають температуру з точністю до півтора градуса.`,
            estimatedDurationMs: solutionDurationMs,
          },
        ],
        targetTimeRange: {
          startMs: hookDurationMs + problemDurationMs,
          endMs: hookDurationMs + problemDurationMs + solutionDurationMs,
        },
      },
      {
        id: 'scene-4-cta',
        title: 'Заклик до дії (CTA)',
        role: 'call_to_action',
        paragraphs: [
          {
            id: 'p-4',
            speakerRole: 'host',
            text: request.ctaType
              ? `Пишіть у директ слово "${request.ctaType}" для консультації з нашим інженером.`
              : profile.defaultCtaPatterns[0] ?? 'Пишіть у директ "КОПТИЛЬНЯ" для розрахунку моделі.',
            estimatedDurationMs: ctaDurationMs,
          },
        ],
        targetTimeRange: {
          startMs: hookDurationMs + problemDurationMs + solutionDurationMs,
          endMs: request.targetDurationMs,
        },
      },
    ];

    return {
      schemaVersion: 'script.v1',
      id: scriptId,
      language: request.language || 'uk',
      title: `Сценарій ReBurn для ${request.audience} (${request.niche})`,
      estimatedDurationMs: request.targetDurationMs,
      source: {
        type: 'adapted',
        auditId: request.sourceAuditId,
      },
      scenes,
      metadata: {
        hookVariants,
        targetAudience: request.audience,
        tone: request.tone,
        usedFactIds: [materialFact?.id, processFact?.id, safetyFact?.id].filter(Boolean),
        preservedMechanisms: mechanisms.keyInsights,
      },
    };
  }

  private generateHookVariants(mechanisms: ExtractedMechanisms, audience: string): string[] {
    switch (mechanisms.hookMechanism) {
      case 'contrarian_hook':
        return [
          'Чому 90% майстрів псують першу копчену партію ще до запалювання тріски?',
          'Перестаньте додавати цукор і селітру в коптильню — це фатальна помилка!',
          'Справжній дим не повинен бути білим і густим: ось чому.',
        ];
      case 'curiosity_gap':
        return [
          'Один секретний вузол у коптильні, який назавжди позбавляє м’ясо гіркоти.',
          'Що приховують професійні коптильні цехи від домашніх майстрів?',
          'Як отримати бурштиновий глянець без жодної краплі хімії?',
        ];
      case 'demonstration_hook':
      case 'bold_claim':
        return [
          'Зліва — м’ясо з кустарної бочки, справа — з камери ReBurn: відчуйте різницю!',
          'Ось як змінюється копчена грудинка, якщо контролювати точку роси.',
          'До і після: 4 години правильної конвекції творять дива.',
        ];
      case 'question_hook':
      default:
        return [
          'Дивіться, як працює шнековий димогенератор ReBurn при 18 градусах морозу.',
          'Перевіряємо точність температури в камері ReBurn тепловізором!',
          'Чи витримає харчова нержавійка AISI 304 цілодобове навантаження?',
        ];
    }
  }
}
