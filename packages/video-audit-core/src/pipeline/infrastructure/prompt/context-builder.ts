/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/prompt/context-builder.ts"
# purpose: "Canonical Context Builder to Serialize Multimodal Input Deterministically."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.2"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { MultimodalAuditInput, MultimodalAuditContext } from '../../ports/multimodal-audit-provider.js';

export interface BuiltContext {
  contextString: string;
  inputArtifactHashes: Record<string, string>;
  warnings: string[];
}

export class MultimodalContextBuilder {
  build(input: MultimodalAuditInput, context: MultimodalAuditContext): BuiltContext {
    const warnings: string[] = [];
    const sections: string[] = [];

    // Header info
    sections.push(`[VIDEO METADATA]
Asset ID: ${input.referenceAssetId}
Duration: ${input.metadata.durationMs}ms
Dimensions: ${input.metadata.width ?? 'N/A'}x${input.metadata.height ?? 'N/A'}
Has Audio: ${input.metadata.hasAudio}
Has Video: ${input.metadata.hasVideo}
`);

    // Transcript Section
    if (input.transcript && input.transcript.segments.length > 0) {
      const transcriptLines = input.transcript.segments.map(seg => {
        return `  - [seg_id: ${seg.id}] [${seg.startMs}ms - ${seg.endMs}ms] (confidence: ${seg.confidence}): "${seg.text}"`;
      }).join('\n');
      sections.push(`[TRANSCRIPT]
Language: ${input.transcript.language}
Segments:
${transcriptLines}`);
    } else {
      warnings.push('PARTIAL_INPUT_MISSING_TRANSCRIPT');
      sections.push(`[TRANSCRIPT]
Status: Missing/Empty`);
    }

    // Scenes Section
    if (input.scenes && input.scenes.scenes.length > 0) {
      const sceneLines = input.scenes.scenes.map(sc => {
        return `  - [scene_id: ${sc.id}] [${sc.startMs}ms - ${sc.endMs}ms] (${sc.durationMs}ms) shot_type: ${sc.shotType ?? 'unknown'}, boundary_confidence: ${sc.boundaryConfidence}`;
      }).join('\n');
      sections.push(`[VISUAL SCENES]
Scenes:
${sceneLines}`);
    } else {
      warnings.push('PARTIAL_INPUT_MISSING_SCENES');
      sections.push(`[VISUAL SCENES]
Status: Missing/Empty`);
    }

    // OCR Section
    if (input.ocr && input.ocr.frames.length > 0) {
      const ocrLines = input.ocr.frames.map(frame => {
        const textRegions = frame.regions.map(r => {
          const b = r.boundingBox;
          return `"${r.normalizedText}" [box: x=${b.x},y=${b.y},w=${b.width},h=${b.height}]`;
        }).join(', ');
        return `  - [frame_id: ${frame.frameId}] [${frame.timestampMs}ms] regions: ${textRegions}`;
      }).join('\n');
      sections.push(`[OCR ONSCREEN TEXT]
Frames:
${ocrLines}`);
    } else {
      warnings.push('PARTIAL_INPUT_MISSING_OCR');
      sections.push(`[OCR ONSCREEN TEXT]
Status: Missing/Empty`);
    }

    // Audio Features Section
    if (input.audioFeatures && input.audioFeatures.features.length > 0) {
      const audioLines = input.audioFeatures.features.map((feat, index) => {
        return `  - [idx: ${index}] [${feat.startMs}ms - ${feat.endMs}ms] silence: ${feat.silence}, speechProb: ${feat.speechProbability ?? 'N/A'}, musicProb: ${feat.musicProbability ?? 'N/A'}, rmsDb: ${feat.rmsDb ?? 'N/A'}, clipping: ${feat.clippingDetected}`;
      }).join('\n');
      sections.push(`[AUDIO FEATURES]
Features:
${audioLines}`);
    } else {
      warnings.push('PARTIAL_INPUT_MISSING_AUDIO_FEATURES');
      sections.push(`[AUDIO FEATURES]
Status: Missing/Empty`);
    }

    // Map input artifact hashes safely
    const inputArtifactHashes: Record<string, string> = {};
    if (input.artifactRefs) {
      for (const [key, ref] of Object.entries(input.artifactRefs)) {
        if (ref && ref.sha256) {
          inputArtifactHashes[key] = ref.sha256;
        }
      }
    }

    // Target niches
    if (context.targetNiches && context.targetNiches.length > 0) {
      sections.push(`[TARGET NICHES]
${context.targetNiches.join(', ')}`);
    }

    return {
      contextString: sections.join('\n\n'),
      inputArtifactHashes,
      warnings
    };
  }
}
