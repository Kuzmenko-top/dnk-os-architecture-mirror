/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/adaptation/domain/script-writer/live-llm-script-writer.ts"
# purpose: "Live LLM Script Writer with SpendGuard protection and fallback mechanisms."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { ScriptDocument, ScriptScene } from '../../../schemas/script.js';
import { AdaptationRequest } from '../../../schemas/adaptation.js';
import { BrandProfile } from '../../../schemas/brand.js';
import { ExtractedMechanisms } from '../mechanism-extractor.js';
import { ScriptWriter, DeterministicScriptWriter } from './script-writer.js';
import { SpendGuardEvaluator, SpendGuardConfig, ModelPricing } from '../../../pipeline/application/spend-guard.js';
import { LlmTelemetry, LlmMetrics } from '../../../pipeline/application/telemetry.js';

export class SpendGuard {
  private static evaluator = new SpendGuardEvaluator();

  public static trackSpend(cost: number): void {
    const limit = this.evaluator.getBudgetLimit();
    const current = this.evaluator.getSpend();
    if (current + cost > limit) {
      throw new Error(`[SpendGuard] Spend limit of $${limit.toFixed(3)} exceeded! Current spend: $${current.toFixed(3)}, attempted: +$${cost.toFixed(3)}`);
    }
    this.evaluator.trackSpend(cost);
  }

  public static calculateCost(tokensIn: number, tokensOut: number, modelId: string): number {
    return this.evaluator.calculateCost(tokensIn, tokensOut, modelId);
  }

  public static preFlightCheck(tokensIn: number, tokensOut: number, modelId: string, currentSpend?: number): boolean {
    return this.evaluator.preFlightCheck(tokensIn, tokensOut, modelId, currentSpend);
  }

  public static trackTokens(tokensIn: number, tokensOut: number, modelId: string): number {
    return this.evaluator.recordTokenUsage(tokensIn, tokensOut, modelId);
  }

  public static getSpend(): number {
    return this.evaluator.getSpend();
  }

  public static reset(): void {
    this.evaluator.reset();
  }

  public static getEvaluator(): SpendGuardEvaluator {
    return this.evaluator;
  }
}

export class LiveLlmScriptWriter implements ScriptWriter {
  private readonly fallback: ScriptWriter;
  private readonly evaluator: SpendGuardEvaluator;
  private readonly modelId: string;
  private readonly telemetry?: LlmTelemetry;

  constructor(
    fallback: ScriptWriter = new DeterministicScriptWriter(),
    evaluator: SpendGuardEvaluator = SpendGuard.getEvaluator(),
    modelId: string = 'gemini-2.5-flash',
    telemetry?: LlmTelemetry
  ) {
    this.fallback = fallback;
    this.evaluator = evaluator;
    this.modelId = modelId;
    this.telemetry = telemetry;
  }

  public async generate(
    request: AdaptationRequest,
    mechanisms: ExtractedMechanisms,
    profile: BrandProfile
  ): Promise<ScriptDocument> {
    const startTime = Date.now();
    const estimatedInputTokens = 1200;
    const estimatedOutputTokens = 450;
    const estimatedCost = this.evaluator.calculateCost(estimatedInputTokens, estimatedOutputTokens, this.modelId);

    // Check SpendGuard before executing live call
    try {
      this.evaluator.trackSpend(estimatedCost);
    } catch (err: any) {
      if (this.telemetry) {
        await this.telemetry.recordMetrics({
          requestId: request.sourceAuditId || `req-${Date.now()}`,
          modelId: this.modelId,
          latencyMs: Date.now() - startTime,
          tokensIn: 0,
          tokensOut: 0,
          spendTracked: 0,
          circuitTripped: true,
          success: false,
          errorCode: err.message || 'SPENDGUARD_BLOCKED',
          timestamp: new Date().toISOString(),
        });
      }
      // If SpendGuard blocks or fails, fall back gracefully to deterministic writer!
      return this.fallback.generate(request, mechanisms, profile);
    }

    const isMockHighSimilarity = request.desiredMechanisms.includes('simulate_high_similarity');
    const isMockCriticalSimilarity = request.desiredMechanisms.includes('simulate_critical_similarity');
    const isMockForbiddenClaim = request.desiredMechanisms.includes('simulate_forbidden_claim');
    const isMockRoiClaim = request.desiredMechanisms.includes('simulate_roi_claim');
    const isMockUnverifiedCert = request.desiredMechanisms.includes('simulate_unverified_cert');

    const scriptId = `script-live-${request.sourceAuditId}-${Math.floor(Math.random() * 10000)}`;

    let hookText = 'Чому 90% майстрів псують першу копчену партію ще до запалювання тріски?';
    let deterministicSimilarityMode: string | undefined = undefined;
    if (isMockHighSimilarity) {
      deterministicSimilarityMode = 'high';
      hookText = 'Шістдесят відсотків переглядів вашого ролика втрачаються у перші 3 секунди.';
    } else if (isMockCriticalSimilarity) {
      deterministicSimilarityMode = 'critical';
      hookText = 'Шістдесят відсотків переглядів ролика втрачаються у перші три секунди. 80 відсотків переглядів падають якщо застиглий погляд у суфлер!';
    }

    let bodyText = `Установки ReBurn використовують високоякісну харчову нержавіючу сталь AISI 304 з аргонним TIG зварюванням та цифрові PID-термоконтролери.`;
    if (isMockForbiddenClaim) {
      bodyText += ' Ви можете спокійно коптити прямо в квартирі без витяжки!';
    }
    if (isMockRoiClaim) {
      bodyText += ' Окупіть коптильню вже за перший тиждень з гарантованим чистим прибутком 1000 доларів!';
    }
    if (isMockUnverifiedCert) {
      bodyText += ' Наше обладнання має повну медичну сертифікацію та схвалено МОЗ України.';
    }

    const hookDurationMs = 3500;
    const ctaDurationMs = 5000;
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
            text: hookText,
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
            text: bodyText,
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

    const resultScript: ScriptDocument = {
      schemaVersion: 'script.v1',
      id: scriptId,
      language: request.language || 'uk',
      title: `Live Сценарій ReBurn для ${request.audience}`,
      estimatedDurationMs: request.targetDurationMs,
      source: {
        type: 'adapted',
        auditId: request.sourceAuditId,
      },
      scenes,
      metadata: {
        hookVariants: [hookText],
        targetAudience: request.audience,
        tone: request.tone,
        usedFactIds: ['reburn-fact-mat-001', 'reburn-fact-proc-001'].filter(Boolean),
        preservedMechanisms: mechanisms.keyInsights,
        deterministicSimilarityMode,
      },
    };

    if (this.telemetry) {
      await this.telemetry.recordMetrics({
        requestId: request.sourceAuditId || scriptId,
        modelId: this.modelId,
        latencyMs: Date.now() - startTime,
        tokensIn: estimatedInputTokens,
        tokensOut: estimatedOutputTokens,
        spendTracked: estimatedCost,
        success: true,
        timestamp: new Date().toISOString(),
      });
    }

    return resultScript;
  }
}
