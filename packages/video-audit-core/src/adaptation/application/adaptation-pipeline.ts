/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/adaptation/application/adaptation-pipeline.ts"
# purpose: "Niche Adaptation Engine Pipeline coordinating Guards, Prosody, ShotList & Decision."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import crypto from 'crypto';
import { AdaptationRequest, AdaptationResult, AdaptationResultSchema } from '../../schemas/adaptation.js';
import { VideoAuditReport } from '../../schemas/audit.js';
import { BrandProfile } from '../../schemas/brand.js';
import { MechanismExtractor, mapAuditReportToExtractionInput } from '../domain/mechanism-extractor.js';
import { BrandGuard } from '../domain/guards/brand-guard.js';
import { SimilarityGuard } from '../domain/guards/similarity-guard.js';
import { HumanReviewPolicy } from '../domain/guards/human-review-policy.js';
import { ProsodyTransformer } from '../domain/transformers/prosody-transformer.js';
import { ShotListGenerator } from '../domain/transformers/shotlist-generator.js';
import { ScriptWriter, DeterministicScriptWriter } from '../domain/script-writer/script-writer.js';
import { AdaptationRepository } from '../ports/adaptation-repository.js';
import { InMemoryAdaptationRepository } from '../infrastructure/persistence/in-memory-adaptation-repository.js';

export interface AdaptationPipelineConfig {
  promptVersion?: string;
  adaptationPolicyVersion?: string;
  repository?: AdaptationRepository;
  scriptWriter?: ScriptWriter;
}

export class NicheAdaptationPipeline {
  private readonly promptVersion: string;
  private readonly adaptationPolicyVersion: string;
  private readonly repository: AdaptationRepository;
  private readonly mechanismExtractor: MechanismExtractor;
  private readonly scriptWriter: ScriptWriter;
  private readonly brandGuard: BrandGuard;
  private readonly similarityGuard: SimilarityGuard;
  private readonly humanReviewPolicy: HumanReviewPolicy;
  private readonly prosodyTransformer: ProsodyTransformer;
  private readonly shotListGenerator: ShotListGenerator;

  constructor(config: AdaptationPipelineConfig = {}) {
    this.promptVersion = config.promptVersion ?? 'v1.0.0';
    this.adaptationPolicyVersion = config.adaptationPolicyVersion ?? 'v1.0.0';
    this.repository = config.repository ?? new InMemoryAdaptationRepository();
    this.scriptWriter = config.scriptWriter ?? new DeterministicScriptWriter();
    this.mechanismExtractor = new MechanismExtractor();
    this.brandGuard = new BrandGuard();
    this.similarityGuard = new SimilarityGuard();
    this.humanReviewPolicy = new HumanReviewPolicy();
    this.prosodyTransformer = new ProsodyTransformer();
    this.shotListGenerator = new ShotListGenerator();
  }

  public async adapt(
    request: AdaptationRequest,
    report: VideoAuditReport,
    profile: BrandProfile
  ): Promise<AdaptationResult> {
    const versions = {
      promptVersion: this.promptVersion,
      adaptationPolicyVersion: this.adaptationPolicyVersion,
    };

    // 1. Idempotency Check
    const idempotencyKey = this.repository.generateKey(request, versions);
    const cached = await this.repository.findByKey(idempotencyKey);
    if (cached) {
      return cached;
    }

    // 1.5 ID/Hash mismatch check
    if (request.sourceAuditId !== report.id) {
      const errorResult: AdaptationResult = {
        schemaVersion: 'adaptation.v1',
        id: `adapt-res-err-${crypto.randomUUID().slice(0, 8)}`,
        sourceAuditId: report.id,
        requestId: `req-${request.sourceAuditId}`,
        createdAt: new Date().toISOString(),
        script: {
          schemaVersion: 'script.v1',
          id: 'script-error',
          language: request.language || 'uk',
          title: 'Error: ID Mismatch',
          estimatedDurationMs: 0,
          source: { type: 'adapted', auditId: report.id },
          scenes: []
        },
        prosody: {
          schemaVersion: 'prosody.v1',
          scriptId: 'script-error',
          globalPacing: { targetWpm: 0, targetDurationMs: 0 },
          tokens: []
        },
        shotList: {
          schemaVersion: 'shot-list.v1',
          scriptId: 'script-error',
          shots: []
        },
        evidence: [],
        preservedMechanisms: [],
        changedElements: [],
        similarity: { overallRisk: 'low', lexical: 0, structural: 0, visual: 0, audio: 0, brand: 0, notes: [] },
        brandCompliance: {
          status: 'rejected',
          usedFactIds: [],
          unverifiedClaims: [],
          forbiddenViolations: ['Input report ID mismatch: request expects ' + request.sourceAuditId + ' but received ' + report.id],
          commercialViolations: [],
          toneScore: 0,
          notes: []
        },
        status: 'rejected',
        warnings: ['INPUT_REPORT_MISMATCH'],
        adaptationRationale: 'ID mismatch'
      };
      return errorResult;
    }

    // 2. Extract abstract mechanisms from the source audit
    const extractionInput = mapAuditReportToExtractionInput(report);
    const mechanisms = this.mechanismExtractor.extract(extractionInput);

    // 3. Generate brand-tailored script
    const script = await this.scriptWriter.generate(request, mechanisms, profile);

    // 4. Evaluate Brand Safety & Fact Alignment
    const brandCompliance = this.brandGuard.evaluate(script, profile, request.approvedFactIds);

    // 5. Evaluate Similarity (Lexical, Structural, Visual, Brand)
    const similarity = this.similarityGuard.evaluate(report, script);

    // 6. Generate Teleprompter-Ready Prosody Document
    const prosody = this.prosodyTransformer.transform(script, request.targetDurationMs);

    // 7. Generate Matching ShotList
    const shotList = this.shotListGenerator.generate(script);

    // 8. Human Review Decision Engine
    const decision = this.humanReviewPolicy.evaluate({
      targetDurationMs: request.targetDurationMs,
      script,
      prosody,
      shotList,
      brandCompliance,
      similarity,
      rightsStatus: (report.referenceAsset?.platformMetadata as any)?.rightsStatus ?? 'cleared',
    });

    const warnings: string[] = [
      ...brandCompliance.notes.filter(n => n.startsWith('УВАГА')),
      ...decision.reasons.filter(r => !r.includes('успішно')),
    ];

    const resultId = `adapt-res-${crypto.randomUUID().slice(0, 8)}`;

    const adaptationResult: AdaptationResult = {
      schemaVersion: 'adaptation.v1',
      id: resultId,
      sourceAuditId: report.id,
      requestId: `req-${request.sourceAuditId}`,
      createdAt: new Date().toISOString(),
      script,
      prosody,
      shotList,
      preservedMechanisms: mechanisms.keyInsights,
      changedElements: [
        `Адаптовано під нішу: ${request.niche}`,
        `Цільова аудиторія: ${request.audience}`,
        `Використано затверджені факти бренду: ${brandCompliance.usedFactIds.join(', ') || 'загальні інженерні факти'}`,
      ],
      similarity,
      brandCompliance,
      status: decision.status,
      warnings,
      adaptationRationale: `Перенесено хук типу "${mechanisms.hookMechanism}" та наративну модель "${mechanisms.narrativePattern}" у контекст обладнання ReBurn.`,
      evidence: [],
    };

    // 9. Schema Validation
    const validated = AdaptationResultSchema.parse(adaptationResult);

    // 10. Persist Idempotently
    await this.repository.save(idempotencyKey, validated);

    return validated;
  }
}
