/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/prompt/templates.ts"
# purpose: "Versioned Prompt Templates & Registry for Multimodal Audit Pipeline."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export interface PromptTemplate {
  version: string;
  template: string;
}

export class PromptTemplateRegistry {
  private templates: Map<string, string> = new Map();

  constructor() {
    // Register default multimodal audit template (v1.0.0)
    this.registerTemplate('1.0.0', `
You are an expert video analyst. You will be provided with multi-modal artifacts of a video.
Your task is to analyze these artifacts and output a JSON document strictly adhering to the "multimodal-audit.v1" schema.

### Core Rules:
- Use only supplied artifacts.
- Do not invent scenes, words, metrics, engagement data, or audio events.
- Mark every claim as observed, inferred, or hypothesized.
- Every observed claim must contain evidenceRefs (at least one non-empty reference list).
- Every time-bound claim must contain timeRange with startMs and endMs.
- If evidence is absent, return unknown or warning.
- Never state that a video is viral without actual performance data.
- Retention conclusions are hypotheses unless external analytics are supplied.
- Do not reproduce original wording in adaptation recommendations.
- Return JSON only according to multimodal-audit.v1.
- Make sure that all scene IDs, transcript segment IDs, and OCR frame IDs referenced in claims or facts ACTUALLY exist in the provided input. Do not invent IDs.

### Input Context:
{{INPUT_CONTEXT}}

### JSON Output Format (multimodal-audit.v1):
Return ONLY a valid JSON object matching the following structure without any surrounding conversational text or prose.

\`\`\`json
{
  "schemaVersion": "multimodal-audit.v1",
  "referenceAssetId": "{{REFERENCE_ASSET_ID}}",
  "inputArtifacts": {
    "transcript": {{TRANSCRIPT_REF}},
    "scenes": {{SCENES_REF}},
    "ocr": {{OCR_REF}},
    "audioFeatures": {{AUDIO_FEATURES_REF}},
    "evidence": {{EVIDENCE_REF}}
  },
  "observedFacts": [
    {
      "id": "fact_...",
      "category": "visual" | "speech" | "text_ocr" | "audio" | "pacing",
      "description": "...",
      "confidence": 0.0 to 1.0,
      "timeRange": { "startMs": 0, "endMs": 1000 },
      "evidenceRefs": {
        "transcriptSegmentIds": [],
        "transcriptWordIndexes": [],
        "sceneIds": [],
        "ocrFrameIds": [],
        "audioSegmentIndexes": []
      }
    }
  ],
  "claims": [
    {
      "id": "claim_...",
      "text": "...",
      "classification": "observed" | "inferred" | "hypothesized",
      "confidence": 0.0 to 1.0,
      "evidenceRefs": {
        "transcriptSegmentIds": [],
        "transcriptWordIndexes": [],
        "sceneIds": [],
        "ocrFrameIds": [],
        "audioSegmentIndexes": []
      },
      "timeRange": { "startMs": 0, "endMs": 1000 } // optional
    }
  ],
  "structure": {
    "hookType": "negative_frame" | "bold_claim" | "curiosity_gap" | "story_origin" | "visual_shock" | "question_prompt" | "problem_agitation" | "other",
    "hookDurationMs": 0,
    "narrativeArc": "...",
    "narrativeBeats": [],
    "keyTakeaways": [],
    "ctaType": "...",
    "ctaStructure": "...",
    "pacingStructure": "..."
  },
  "visual": {
    "dominantColorPalette": [],
    "cutFrequencyPerMin": 0.0,
    "faceVisibilityRatio": 0.0 to 1.0,
    "hasCaptions": true,
    "captionStyle": "...",
    "visualGrammar": "...",
    "shotPacing": "...",
    "motionEnergyScore": 0.0 to 1.0
  },
  "audio": {
    "hasBackgroundMusic": false,
    "musicGenre": "...",
    "musicBpm": 120,
    "speechToMusicRatioDb": 12,
    "averageLoudnessLufs": -14,
    "pauseCount": 0,
    "averagePauseDurationMs": 0,
    "speakingWpm": 140,
    "audioPacing": "...",
    "clippingDetected": false
  },
  "retentionHypotheses": [
    {
      "id": "hyp_...",
      "estimatedRetentionScore": 0 to 100,
      "hypothesisType": "hook_dropoff" | "pacing_lull" | "cta_abandonment" | "engagement_peak" | "content_fatigue" | "general",
      "description": "...",
      "timeRange": { "startMs": 0, "endMs": 1000 },
      "severity": "low" | "medium" | "high",
      "evidenceRefs": {},
      "confidence": 0.0 to 1.0
    }
  ],
  "adaptationRecommendations": [
    {
      "id": "rec_...",
      "targetNiche": "...",
      "opportunity": "...",
      "suggestedHook": "...",
      "suggestedAngle": "...",
      "recommendedShotList": [
        {
          "shotIndex": 0,
          "shotType": "...",
          "description": "...",
          "durationMs": 1000
        }
      ],
      "riskFlags": []
    }
  ],
  "confidence": 0.0 to 1.0,
  "warnings": [],
  "modelSet": {
    "provider": "{{PROVIDER}}",
    "model": "{{MODEL}}",
    "modelSetVersion": "{{MODEL_SET_VERSION}}",
    "promptTemplateVersion": "1.0.0",
    "inputArtifactHashes": {},
    "outputSchemaVersion": "multimodal-audit.v1",
    "processingDurationMs": 0
  }
}
\`\`\`
`);
  }

  registerTemplate(version: string, template: string): void {
    this.templates.set(version, template);
  }

  getTemplate(version: string): string {
    const template = this.templates.get(version);
    if (!template) {
      throw new Error(`Prompt template for version ${version} not found in registry.`);
    }
    return template;
  }
}

export class PromptRenderer {
  render(template: string, variables: Record<string, any>): string {
    let result = template;
    for (const [key, value] of Object.entries(variables)) {
      const placeholder = `{{${key}}}`;
      const stringValue = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value);
      result = result.split(placeholder).join(stringValue);
    }
    return result;
  }
}
