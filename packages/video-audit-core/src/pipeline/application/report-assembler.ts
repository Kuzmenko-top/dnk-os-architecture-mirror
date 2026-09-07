/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/application/report-assembler.ts"
# purpose: "Deterministic VideoAuditReport Assembler, Validation, and Immutable Persistence."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { createHash } from 'node:crypto';
import { z } from 'zod';
import { VideoAuditReport, VideoAuditReportSchema, AuditStatus } from '../../schemas/audit.js';
import { MultimodalAuditResult, MultimodalAuditResultSchema } from '../../schemas/multimodal-audit.js';
import { TranscriptDocumentSchema, TranscriptDocument } from '../domain/transcription/transcript.js';
import { toLegacyReportTranscript } from '../domain/transcription/compatibility.js';
import { SceneDocumentSchema, SceneDocument } from '../domain/analyzers/scenes.js';
import { OCRDocumentSchema, OCRDocument } from '../domain/analyzers/ocr.js';
import { AudioFeaturesDocumentSchema, AudioFeaturesDocument } from '../domain/analyzers/audio-features.js';
import { MultimodalEvidenceDocumentSchema, MultimodalEvidenceDocument } from '../domain/analyzers/multimodal-evidence.js';
import { ArtifactStore } from '../ports/artifact-store.js';
import { AuditEventBus } from '../ports/event-bus.js';
import { ArtifactKeyGenerators } from '../domain/artifacts/artifact.js';
import { ReferenceAsset, ReferenceAssetSchema } from '../../schemas/reference.js';

export interface AssembleReportInput {
  referenceAssetId: string;
  referenceAsset: ReferenceAsset;
  reportVersion: string;
  
  // Serialized string or Buffer contents of each artifact
  transcriptArtifact: { data: string; sha256: string };
  multimodalAuditArtifact: { data: string; sha256: string };
  
  // Optional artifacts for partial/degraded handling
  scenesArtifact?: { data: string; sha256: string };
  ocrArtifact?: { data: string; sha256: string };
  audioFeaturesArtifact?: { data: string; sha256: string };
  multimodalEvidenceArtifact?: { data: string; sha256: string };
  
  actorId?: string;
  correlationId?: string;
  promptVersion?: string;
  modelVersion?: string;
  reportSchemaVersion?: string;
  adaptationPolicyVersion?: string;
}

export class VideoAuditReportAssembler {
  constructor(
    private readonly artifactStore: ArtifactStore,
    private readonly eventBus: AuditEventBus
  ) {}

  private calculateSha256(data: string): string {
    return createHash('sha256').update(data, 'utf-8').digest('hex');
  }

  async assembleAndPersist(input: AssembleReportInput): Promise<{ report: VideoAuditReport; key: string; isNew: boolean }> {
    const { referenceAssetId, referenceAsset, reportVersion, actorId = 'system', correlationId = `corr_${Date.now()}` } = input;

    // Generujeme immutable report key
    const reportKey = ArtifactKeyGenerators.report_assembly(referenceAssetId, reportVersion);

    const promptVersion = input.promptVersion ?? 'multimodal-audit-prompt.v1';
    const adaptationPolicyVersion = input.adaptationPolicyVersion ?? 'default.v1';
    const reportSchemaVersion = input.reportSchemaVersion ?? 'video-audit.v1';

    const currentInputHashes: Record<string, string> = {
      transcript: input.transcriptArtifact.sha256,
      multimodalAudit: input.multimodalAuditArtifact.sha256,
      ...(input.scenesArtifact ? { scenes: input.scenesArtifact.sha256 } : {}),
      ...(input.ocrArtifact ? { ocr: input.ocrArtifact.sha256 } : {}),
      ...(input.audioFeaturesArtifact ? { audioFeatures: input.audioFeaturesArtifact.sha256 } : {}),
      ...(input.multimodalEvidenceArtifact ? { multimodalEvidence: input.multimodalEvidenceArtifact.sha256 } : {}),
    };

    // Idempotency check: skontrolujeme ci uz report existuje a ci sa zhoduje kompletny composite fingerprint
    try {
      const existingData = await this.artifactStore.get(reportKey);
      if (existingData) {
        const manifest = await this.artifactStore.getManifest(reportKey);
        const meta = manifest?.metadata as Record<string, any> | undefined;

        // Overime ze sa zhoduje referenceAssetId, input hashes, prompt, model, schema a adaptation policy
        const inputHashesMatch =
          meta?.inputArtifactHashes &&
          JSON.stringify(meta.inputArtifactHashes) === JSON.stringify(currentInputHashes);
        const schemaMatch = meta?.schemaVersion === reportSchemaVersion;
        const promptMatch = meta?.promptVersion === promptVersion;
        const adaptationMatch = meta?.adaptationPolicyVersion === adaptationPolicyVersion;
        const refMatch = manifest?.referenceAssetId === referenceAssetId;
        const targetModelVersion = input.modelVersion ?? (() => {
          try {
            return JSON.parse(input.multimodalAuditArtifact.data)?.modelSet?.modelSetVersion ?? 'multimodal-audit-model.v1';
          } catch {
            return 'multimodal-audit-model.v1';
          }
        })();
        const modelMatch = meta?.modelVersion === targetModelVersion;

        if (inputHashesMatch && schemaMatch && promptMatch && adaptationMatch && refMatch && modelMatch) {
          const report = VideoAuditReportSchema.parse(JSON.parse(existingData.toString('utf-8')));
          return { report, key: reportKey, isNew: false };
        }
      }
    } catch (e) {
      // Not found or mismatch is fine, continue assembling
    }

    const warnings: string[] = [];

    // 1. Verify and parse required Transcript Artifact
    const transcriptData = input.transcriptArtifact.data;
    const transcriptSha = this.calculateSha256(transcriptData);
    if (transcriptSha !== input.transcriptArtifact.sha256) {
      throw new Error(`SHA-256 mismatch for transcript artifact: expected ${input.transcriptArtifact.sha256}, got ${transcriptSha}`);
    }
    const transcriptParsed = JSON.parse(transcriptData);
    if (transcriptParsed.schemaVersion !== 'transcript.v1') {
      throw new Error(`Incompatible transcript schema version: expected 'transcript.v1', got '${transcriptParsed.schemaVersion}'`);
    }
    const transcriptDoc = TranscriptDocumentSchema.parse(transcriptParsed);
    if (transcriptDoc.referenceAssetId !== referenceAssetId) {
      throw new Error(`referenceAssetId mismatch in transcript artifact: expected ${referenceAssetId}, got ${transcriptDoc.referenceAssetId}`);
    }

    // 2. Verify and parse required Multimodal Audit Artifact
    const auditData = input.multimodalAuditArtifact.data;
    const auditSha = this.calculateSha256(auditData);
    if (auditSha !== input.multimodalAuditArtifact.sha256) {
      throw new Error(`SHA-256 mismatch for multimodal audit artifact: expected ${input.multimodalAuditArtifact.sha256}, got ${auditSha}`);
    }
    const auditParsed = JSON.parse(auditData);
    if (auditParsed.schemaVersion !== 'multimodal-audit.v1') {
      throw new Error(`Incompatible multimodal-audit schema version: expected 'multimodal-audit.v1', got '${auditParsed.schemaVersion}'`);
    }
    const auditDoc = MultimodalAuditResultSchema.parse(auditParsed);
    if (auditDoc.referenceAssetId !== referenceAssetId) {
      throw new Error(`referenceAssetId mismatch in multimodal audit artifact: expected ${referenceAssetId}, got ${auditDoc.referenceAssetId}`);
    }
    if (!auditDoc.modelSet || !auditDoc.modelSet.modelSetVersion) {
      throw new Error(`report assembly failed: missing modelSetVersion in multimodal-audit artifact`);
    }

    // 3. Verify and parse optional Scenes Artifact
    let scenesDoc: SceneDocument | undefined;
    if (input.scenesArtifact) {
      const scenesData = input.scenesArtifact.data;
      const scenesSha = this.calculateSha256(scenesData);
      if (scenesSha !== input.scenesArtifact.sha256) {
        throw new Error(`SHA-256 mismatch for scenes artifact: expected ${input.scenesArtifact.sha256}, got ${scenesSha}`);
      }
      const parsed = JSON.parse(scenesData);
      if (parsed.schemaVersion !== 'scenes.v1') {
        throw new Error(`Incompatible scenes schema version: expected 'scenes.v1', got '${parsed.schemaVersion}'`);
      }
      scenesDoc = SceneDocumentSchema.parse(parsed);
      if (scenesDoc.referenceAssetId !== referenceAssetId) {
        throw new Error(`referenceAssetId mismatch in scenes artifact: expected ${referenceAssetId}, got ${scenesDoc.referenceAssetId}`);
      }
    } else {
      warnings.push(`Scenes artifact is missing. Report assembled with degraded scene data.`);
    }

    // 4. Verify and parse optional OCR Artifact
    let ocrDoc: OCRDocument | undefined;
    if (input.ocrArtifact) {
      const ocrData = input.ocrArtifact.data;
      const ocrSha = this.calculateSha256(ocrData);
      if (ocrSha !== input.ocrArtifact.sha256) {
        throw new Error(`SHA-256 mismatch for ocr artifact: expected ${input.ocrArtifact.sha256}, got ${ocrSha}`);
      }
      const parsed = JSON.parse(ocrData);
      if (parsed.schemaVersion !== 'ocr.v1') {
        throw new Error(`Incompatible ocr schema version: expected 'ocr.v1', got '${parsed.schemaVersion}'`);
      }
      ocrDoc = OCRDocumentSchema.parse(parsed);
      if (ocrDoc.referenceAssetId !== referenceAssetId) {
        throw new Error(`referenceAssetId mismatch in ocr artifact: expected ${referenceAssetId}, got ${ocrDoc.referenceAssetId}`);
      }
    } else {
      warnings.push(`OCR artifact is missing. Report assembled with degraded OCR data.`);
    }

    // 5. Verify and parse optional Audio Features Artifact
    let audioDoc: AudioFeaturesDocument | undefined;
    if (input.audioFeaturesArtifact) {
      const audioData = input.audioFeaturesArtifact.data;
      const audioSha = this.calculateSha256(audioData);
      if (audioSha !== input.audioFeaturesArtifact.sha256) {
        throw new Error(`SHA-256 mismatch for audio features artifact: expected ${input.audioFeaturesArtifact.sha256}, got ${audioSha}`);
      }
      const parsed = JSON.parse(audioData);
      if (parsed.schemaVersion !== 'audio-features.v1') {
        throw new Error(`Incompatible audio-features schema version: expected 'audio-features.v1', got '${parsed.schemaVersion}'`);
      }
      audioDoc = AudioFeaturesDocumentSchema.parse(parsed);
      if (audioDoc.referenceAssetId !== referenceAssetId) {
        throw new Error(`referenceAssetId mismatch in audio features artifact: expected ${referenceAssetId}, got ${audioDoc.referenceAssetId}`);
      }
    } else {
      warnings.push(`Audio features artifact is missing. Report assembled with degraded audio data.`);
    }

    // 6. Verify and parse optional Multimodal Evidence Artifact
    let evidenceDoc: MultimodalEvidenceDocument | undefined;
    if (input.multimodalEvidenceArtifact) {
      const evidenceData = input.multimodalEvidenceArtifact.data;
      const evidenceSha = this.calculateSha256(evidenceData);
      if (evidenceSha !== input.multimodalEvidenceArtifact.sha256) {
        throw new Error(`SHA-256 mismatch for multimodal evidence artifact: expected ${input.multimodalEvidenceArtifact.sha256}, got ${evidenceSha}`);
      }
      const parsed = JSON.parse(evidenceData);
      if (parsed.schemaVersion !== 'multimodal-evidence.v1') {
        throw new Error(`Incompatible multimodal-evidence schema version: expected 'multimodal-evidence.v1', got '${parsed.schemaVersion}'`);
      }
      evidenceDoc = MultimodalEvidenceDocumentSchema.parse(parsed);
      if (evidenceDoc.referenceAssetId !== referenceAssetId) {
        throw new Error(`referenceAssetId mismatch in multimodal evidence artifact: expected ${referenceAssetId}, got ${evidenceDoc.referenceAssetId}`);
      }
    } else {
      warnings.push(`Multimodal evidence artifact is missing. Report assembled with degraded evidence references.`);
    }

    // Validate claim evidence references
    if (auditDoc.claims) {
      for (const claim of auditDoc.claims) {
        if (claim.evidenceRefs) {
          const refs = claim.evidenceRefs;
          
          // Verify transcript segment ids if they exist
          if (refs.transcriptSegmentIds) {
            for (const id of refs.transcriptSegmentIds) {
              const exists = transcriptDoc.segments.some(s => s.id === id);
              if (!exists) {
                throw new Error(`Invalid evidence reference: transcript segment "${id}" not found`);
              }
            }
          }

          // Verify scene ids if they exist
          if (refs.sceneIds && scenesDoc) {
            for (const id of refs.sceneIds) {
              const exists = scenesDoc.scenes.some(s => s.id === id);
              if (!exists) {
                throw new Error(`Invalid evidence reference: scene "${id}" not found`);
              }
            }
          }

          // Verify ocr frame ids if they exist
          if (refs.ocrFrameIds && ocrDoc) {
            for (const id of refs.ocrFrameIds) {
              const exists = ocrDoc.frames.some(f => f.frameId === id);
              if (!exists) {
                throw new Error(`Invalid evidence reference: OCR frame "${id}" not found`);
              }
            }
          }
        }
      }
    }

    // 7. Map to Legacy Report Transcript format
    const mappedTranscript = toLegacyReportTranscript(transcriptDoc);

    // 8. Map to Scene structure (from narrativeBeats)
    const mappedScenes = auditDoc.structure.narrativeBeats.map((beat: any, idx: number) => ({
      id: beat.id ?? `scene_${idx + 1}`,
      title: beat.title ?? beat.name ?? `Scene ${idx + 1}`,
      role: (['hook', 'problem_statement', 'core_value', 'demonstration', 'social_proof', 'call_to_action', 'outro'].includes(beat.role)
        ? beat.role
        : 'demonstration') as any,
      timeRange: beat.timeRange ?? { startMs: beat.startMs ?? 0, endMs: beat.endMs ?? 1000 },
      summary: beat.summary ?? beat.description ?? '',
      shots: []
    }));

    // 9. Map Audio Features
    const audioAny = audioDoc as any;
    const mappedAudioFeatures = {
      hasBackgroundMusic: audioAny?.features?.hasBackgroundMusic ?? auditDoc.audio?.hasBackgroundMusic ?? false,
      musicGenre: audioAny?.features?.musicGenre ?? auditDoc.audio?.musicGenre,
      musicBpm: audioAny?.features?.musicBpm ?? auditDoc.audio?.musicBpm,
      speechToMusicRatioDb: audioAny?.features?.speechToMusicRatioDb ?? auditDoc.audio?.speechToMusicRatioDb,
      averageLoudnessLufs: audioAny?.features?.averageLoudnessLufs ?? auditDoc.audio?.averageLoudnessLufs,
      pauseCount: audioAny?.features?.pauseCount ?? auditDoc.audio?.pauseCount ?? 0,
      averagePauseDurationMs: audioAny?.features?.averagePauseDurationMs ?? auditDoc.audio?.averagePauseDurationMs ?? 0,
      speakingWpm: audioAny?.features?.speakingWpm ?? auditDoc.audio?.speakingWpm,
    };

    // 10. Map Retention Hypotheses
    const firstScore = auditDoc.retentionHypotheses?.[0]?.estimatedRetentionScore ?? 80.0;
    const mappedRetention = {
      estimatedRetentionScore: firstScore,
      dropoffRisks: auditDoc.retentionHypotheses
        ?.filter(h => ['hook_dropoff', 'pacing_lull', 'cta_abandonment', 'content_fatigue'].includes(h.hypothesisType))
        .map(h => ({
          timeRange: h.timeRange ?? { startMs: 0, endMs: 0 },
          reason: h.description,
          severity: (h.severity ?? 'medium') as 'low' | 'medium' | 'high'
        })) ?? [],
      engagementDrivers: auditDoc.retentionHypotheses
        ?.filter(h => h.hypothesisType === 'engagement_peak')
        .map(h => ({
          timeRange: h.timeRange ?? { startMs: 0, endMs: 0 },
          driver: h.description
        })) ?? []
    };

    // 11. Map Evidence Items
    const mappedEvidence: any[] = [];
    
    // Add observed facts
    if (auditDoc.observedFacts) {
      for (const fact of auditDoc.observedFacts) {
        const refs: string[] = [];
        if (fact.evidenceRefs?.transcriptSegmentIds) refs.push(...fact.evidenceRefs.transcriptSegmentIds);
        if (fact.evidenceRefs?.sceneIds) refs.push(...fact.evidenceRefs.sceneIds);
        if (fact.evidenceRefs?.ocrFrameIds) refs.push(...fact.evidenceRefs.ocrFrameIds);
        if (fact.evidenceRefs?.audioSegmentIndexes) refs.push(...fact.evidenceRefs.audioSegmentIndexes.map(String));

        mappedEvidence.push({
          id: fact.id,
          type: 'observed',
          claim: fact.description,
          confidence: fact.confidence,
          source: fact.category,
          timeRange: fact.timeRange,
          modelVersion: auditDoc.modelSet.modelSetVersion,
          evidenceRefs: refs
        });
      }
    }

    // Add claims
    if (auditDoc.claims) {
      for (const claim of auditDoc.claims) {
        const refs: string[] = [];
        if (claim.evidenceRefs?.transcriptSegmentIds) refs.push(...claim.evidenceRefs.transcriptSegmentIds);
        if (claim.evidenceRefs?.sceneIds) refs.push(...claim.evidenceRefs.sceneIds);
        if (claim.evidenceRefs?.ocrFrameIds) refs.push(...claim.evidenceRefs.ocrFrameIds);
        if (claim.evidenceRefs?.audioSegmentIndexes) refs.push(...claim.evidenceRefs.audioSegmentIndexes.map(String));

        mappedEvidence.push({
          id: claim.id,
          type: claim.classification,
          claim: claim.text,
          confidence: claim.confidence,
          source: 'multimodal-audit',
          timeRange: claim.timeRange,
          modelVersion: auditDoc.modelSet.modelSetVersion,
          evidenceRefs: refs
        });
      }
    }

    // Map hook type to compatible values
    const rawHookType = auditDoc.structure.hookType;
    let mappedHookType: 'negative_frame' | 'bold_claim' | 'curiosity_gap' | 'story_origin' | 'visual_shock' | 'question_prompt' = 'curiosity_gap';
    if (['negative_frame', 'bold_claim', 'curiosity_gap', 'story_origin', 'visual_shock', 'question_prompt'].includes(rawHookType)) {
      mappedHookType = rawHookType as any;
    }

    // Determine aggregate status
    const aggregateStatus = 'READY';
    const auditWarnings = [...warnings, ...(auditDoc.warnings ?? [])];

    // Assemble the final VideoAuditReport
    const report: VideoAuditReport = {
      schemaVersion: 'video-audit.v1',
      id: `report_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      status: aggregateStatus,
      createdAt: new Date().toISOString(),
      referenceAsset,
      transcript: mappedTranscript,
      scenes: mappedScenes,
      audioFeatures: mappedAudioFeatures,
      structure: {
        hookType: mappedHookType,
        hookDurationMs: auditDoc.structure.hookDurationMs,
        narrativeArc: auditDoc.structure.narrativeArc,
        keyTakeaways: auditDoc.structure.keyTakeaways,
        ctaType: auditDoc.structure.ctaType as any,
        pacingStructure: auditDoc.structure.pacingStructure
      },
      visuals: {
        dominantColorPalette: auditDoc.visual.dominantColorPalette,
        cutFrequencyPerMin: auditDoc.visual.cutFrequencyPerMin,
        faceVisibilityRatio: auditDoc.visual.faceVisibilityRatio,
        hasCaptions: auditDoc.visual.hasCaptions,
        captionStyle: auditDoc.visual.captionStyle
      },
      retention: mappedRetention,
      evidence: mappedEvidence
    };

    // Parse and validate the final report schema
    const validatedReport = VideoAuditReportSchema.parse(report);

    // Save report to the ArtifactStore
    const serializedReport = JSON.stringify(validatedReport, null, 2);
    const reportBuf = Buffer.from(serializedReport, 'utf-8');
    const finalReportSha = createHash('sha256').update(reportBuf).digest('hex');

    const modelVersion = input.modelVersion ?? auditDoc.modelSet.modelSetVersion;

    await this.artifactStore.put({
      key: reportKey,
      referenceAssetId,
      mimeType: 'application/json',
      data: reportBuf,
      metadata: {
        sha256: finalReportSha,
        schemaVersion: reportSchemaVersion,
        modelVersion,
        promptVersion,
        adaptationPolicyVersion,
        inputArtifactHashes: currentInputHashes,
        warnings: auditWarnings
      }
    });

    // 12. Publish AuditReportCreated.v1 event after successful persistence
    await this.eventBus.publish({
      id: `evt_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      eventType: 'AuditReportCreated.v1',
      referenceAssetId,
      timestamp: new Date().toISOString(),
      correlationId,
      actorId,
      payload: {
        referenceAssetId,
        reportId: validatedReport.id,
        reportKey,
        aggregateStatus,
        sha256: finalReportSha,
        createdAt: validatedReport.createdAt,
        metadata: {
          modelVersion,
          promptVersion,
          adaptationPolicyVersion,
          inputArtifactHashes: currentInputHashes,
          warnings: auditWarnings
        }
      }
    } as any);

    return { report: validatedReport, key: reportKey, isNew: true };
  }
}
