/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/fixtures/reburn/fixture-builder.ts"
# purpose: "Helper Factory for Deterministic and Schema-Compliant ReBurn Audit Fixtures."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { ReferenceAsset } from './types.js';
import { TranscriptDocument } from '../../pipeline/domain/transcription/transcript.js';
import { SceneDocument } from '../../pipeline/domain/analyzers/scenes.js';
import { OCRDocument } from '../../pipeline/domain/analyzers/ocr.js';
import { AudioFeaturesDocument } from '../../pipeline/domain/analyzers/audio-features.js';
import { MultimodalEvidenceDocument } from '../../pipeline/domain/analyzers/multimodal-evidence.js';
import {
  MultimodalAuditResult,
  AuditedClaim,
  ObservedFact,
  HookType,
  MultimodalRetentionHypothesis,
  AdaptationRecommendation
} from '../../schemas/multimodal-audit.js';

export function buildReferenceAsset(opts: {
  id: string;
  sourceUrl?: string;
  durationMs: number;
  width?: number;
  height?: number;
  fps?: number;
}): ReferenceAsset {
  return {
    id: opts.id,
    sourceType: 'url_tiktok',
    url: opts.sourceUrl ?? `https://storage.dnk-reburn.com/fixtures/${opts.id}.mp4`,
    mediaMetadata: {
      durationMs: opts.durationMs,
      width: opts.width ?? 1080,
      height: opts.height ?? 1920,
      fps: opts.fps ?? 30,
      aspectRatio: '9:16'
    },
    platformMetadata: {
      hashtags: ['reburn', 'smoking', 'bbq']
    },
    createdAt: '2026-09-03T09:00:00.000Z'
  };
}

export function buildTranscriptDoc(opts: {
  referenceAssetId: string;
  durationMs: number;
  segments: Array<{ id: string; startMs: number; endMs: number; text: string; confidence?: number }>;
  language?: string;
}): TranscriptDocument {
  const isCompleted = opts.segments.length > 0;
  return {
    schemaVersion: 'transcript.v1',
    id: `transcript_${opts.referenceAssetId}`,
    referenceAssetId: opts.referenceAssetId,
    language: opts.language ?? 'uk',
    durationMs: opts.durationMs,
    provider: 'whisper-reburn-v2',
    modelVersion: 'whisper-large-v3-uk',
    confidence: 0.95,
    status: isCompleted ? 'completed' : 'degraded',
    segments: opts.segments.map((s, segIdx) => {
      const words = s.text.split(' ').filter(Boolean);
      const segDur = s.endMs - s.startMs;
      return {
        id: s.id,
        ordinal: segIdx,
        startMs: s.startMs,
        endMs: s.endMs,
        text: s.text,
        confidence: s.confidence ?? 0.95,
        words: words.map((w, wIdx) => {
          const wStart = Math.floor(s.startMs + (segDur * wIdx) / (words.length || 1));
          const wEnd = Math.floor(s.startMs + (segDur * (wIdx + 1)) / (words.length || 1));
          return {
            ordinal: wIdx,
            text: w,
            startMs: wStart,
            endMs: wEnd,
            confidence: s.confidence ?? 0.95
          };
        })
      };
    }),
    warnings: []
  };
}

export function buildSceneDoc(opts: {
  referenceAssetId: string;
  scenes: Array<{ id: string; startMs: number; endMs: number; description: string; score?: number }>;
}): SceneDocument {
  const maxEndMs = opts.scenes.length > 0 ? Math.max(...opts.scenes.map(s => s.endMs)) : 0;
  return {
    schemaVersion: 'scenes.v1',
    referenceAssetId: opts.referenceAssetId,
    extractor: {
      provider: 'pyscenedetect-reburn',
      version: 'v1.0',
      method: 'content_aware'
    },
    durationMs: maxEndMs,
    scenes: opts.scenes.map((s, idx) => ({
      id: s.id,
      ordinal: idx,
      startMs: s.startMs,
      endMs: s.endMs,
      durationMs: s.endMs - s.startMs,
      boundaryConfidence: s.score ?? 0.92,
      shotType: 'product',
      keyframeArtifactKey: `keyframes/${s.id}.jpg`
    })),
    warnings: []
  };
}

export function buildOcrDoc(opts: {
  referenceAssetId: string;
  frames: Array<{
    frameId: string;
    timestampMs: number;
    regions: Array<{ text: string; confidence?: number }>;
  }>;
}): OCRDocument {
  return {
    schemaVersion: 'ocr.v1',
    referenceAssetId: opts.referenceAssetId,
    provider: 'tesseract-reburn-uk',
    modelVersion: 'v5.3',
    frames: opts.frames.map((f) => ({
      frameId: f.frameId,
      timestampMs: f.timestampMs,
      width: 1080,
      height: 1920,
      regions: f.regions.map((r) => ({
        text: r.text,
        normalizedText: r.text.toLowerCase().trim(),
        confidence: r.confidence ?? 0.94,
        boundingBox: { x: 0.1, y: 0.2, width: 0.8, height: 0.1 }
      }))
    })),
    languageHints: ['uk', 'en'],
    warnings: []
  };
}

export function buildAudioFeaturesDoc(opts: {
  referenceAssetId: string;
  durationMs: number;
  hasAudioTrack?: boolean;
  segments?: Array<{ startMs: number; endMs: number; speechProb?: number; musicProb?: number; silence?: boolean }>;
}): AudioFeaturesDocument {
  const hasAudio = opts.hasAudioTrack ?? true;
  return {
    schemaVersion: 'audio-features.v1',
    referenceAssetId: opts.referenceAssetId,
    sampleRate: 44100,
    durationMs: opts.durationMs,
    provider: 'librosa-reburn-audio',
    hasAudioTrack: hasAudio,
    isDegraded: !hasAudio,
    features: hasAudio
      ? (opts.segments ?? [
          { startMs: 0, endMs: Math.floor(opts.durationMs / 2), speechProb: 0.9, musicProb: 0.2, silence: false },
          { startMs: Math.floor(opts.durationMs / 2), endMs: opts.durationMs, speechProb: 0.85, musicProb: 0.3, silence: false }
        ]).map((seg) => ({
          startMs: seg.startMs,
          endMs: seg.endMs,
          rmsDb: -18.5,
          peakDb: -3.2,
          speechProbability: seg.speechProb ?? 0.9,
          musicProbability: seg.musicProb ?? 0.25,
          silence: seg.silence ?? false,
          noiseScore: 0.05,
          clippingDetected: false
        }))
      : [],
    warnings: hasAudio ? [] : ['Video contains no audio stream or empty audio track']
  };
}

export function buildEvidenceDoc(opts: {
  referenceAssetId: string;
  durationMs: number;
  aggregateStatus?: 'completed' | 'partial' | 'failed' | 'manual_review';
}): MultimodalEvidenceDocument {
  return {
    schemaVersion: 'multimodal-evidence.v1',
    referenceAssetId: opts.referenceAssetId,
    generatedAt: '2026-09-03T09:01:00.000Z',
    aggregateStatus: opts.aggregateStatus ?? 'completed',
    temporalCorrelations: [
      {
        timestampMs: 0,
        sceneId: 'sc_01',
        spokenWord: 'Коптильня',
        ocrText: 'ReBurn',
        silenceDetected: false
      }
    ]
  };
}

export function buildMultimodalAuditResult(opts: {
  referenceAssetId: string;
  durationMs: number;
  hookType?: HookType;
  hookDurationMs?: number;
  claims: AuditedClaim[];
  observedFacts?: ObservedFact[];
  keyTakeaways?: string[];
  ctaType?: string;
  ctaStructure?: string;
  retentionHypotheses?: MultimodalRetentionHypothesis[];
  adaptationRecommendations?: AdaptationRecommendation[];
  inputArtifacts?: MultimodalAuditResult['inputArtifacts'];
  modelSetVersion?: string;
  confidence?: number;
  warnings?: string[];
}): MultimodalAuditResult {
  return {
    schemaVersion: 'multimodal-audit.v1',
    referenceAssetId: opts.referenceAssetId,
    inputArtifacts: opts.inputArtifacts ?? {},
    observedFacts: opts.observedFacts ?? [],
    claims: opts.claims,
    structure: {
      hookType: opts.hookType ?? 'bold_claim',
      hookDurationMs: opts.hookDurationMs ?? 2500,
      narrativeArc: 'Hook -> Problem Demonstration -> Technical Solution -> Call to Action',
      narrativeBeats: [
        { name: 'Hook', startMs: 0, endMs: opts.hookDurationMs ?? 2500, description: 'Visual & verbal hook' },
        { name: 'Core Solution', startMs: opts.hookDurationMs ?? 2500, endMs: Math.floor(opts.durationMs * 0.8), description: 'Detailed demonstration' },
        { name: 'CTA', startMs: Math.floor(opts.durationMs * 0.8), endMs: opts.durationMs, description: 'Direct call to action' }
      ],
      keyTakeaways: opts.keyTakeaways ?? ['High engineering standard', 'Proven smoking results'],
      ctaType: opts.ctaType ?? 'consultation',
      ctaStructure: opts.ctaStructure ?? 'Direct offer with inquiry prompt',
      pacingStructure: 'Dynamic rhythm with clear emphasis on core equipment specs'
    },
    visual: {
      dominantColorPalette: ['#1A1A1A', '#C0C0C0', '#D4AF37'],
      cutFrequencyPerMin: 18,
      faceVisibilityRatio: 0.65,
      hasCaptions: true,
      captionStyle: 'Dynamic yellow on dark background',
      visualGrammar: 'Cinematic equipment b-roll alternating with expert presentation',
      shotPacing: 'Fast hook followed by detailed macro inspection',
      motionEnergyScore: 0.75
    },
    audio: {
      hasBackgroundMusic: true,
      musicGenre: 'Industrial acoustic rhythm',
      musicBpm: 110,
      speechToMusicRatioDb: 12.5,
      averageLoudnessLufs: -14.2,
      pauseCount: 4,
      averagePauseDurationMs: 450,
      speakingWpm: 135,
      audioPacing: 'Steady, deliberate professional cadence',
      clippingDetected: false
    },
    retentionHypotheses: opts.retentionHypotheses ?? [
      {
        id: `ret_${opts.referenceAssetId}_01`,
        estimatedRetentionScore: 78,
        hypothesisType: 'hook_dropoff',
        description: 'Strong initial visual hook retains up to 70% of viewers past 3 seconds (hypothesized based on visual pacing)',
        severity: 'low',
        confidence: 0.65
      }
    ],
    adaptationRecommendations: opts.adaptationRecommendations ?? [
      {
        id: `adapt_rec_${opts.referenceAssetId}_01`,
        targetNiche: 'B2B/B2C Food Processing & Smoking Equipment',
        opportunity: 'Highlight ReBurn AISI 304 food-grade stainless steel & automated temperature management',
        suggestedHook: 'Чому 90% домашніх коптилень псують м’ясо гіркотою?',
        suggestedAngle: 'Technical mastery and defect prevention',
        recommendedShotList: [
          { shotIndex: 1, shotType: 'extreme_macro', description: 'Macro shot of welded AISI 304 seams', durationMs: 2000 },
          { shotIndex: 2, shotType: 'action_medium', description: 'Clean smoke flow through deflector', durationMs: 3000 }
        ],
        riskFlags: []
      }
    ],
    confidence: opts.confidence ?? 0.94,
    warnings: opts.warnings ?? [],
    modelSet: {
      provider: 'vertex-gemini',
      model: 'gemini-2.5-pro',
      modelSnapshot: '2026-09-01',
      modelSetVersion: opts.modelSetVersion ?? 'multimodal-audit-model.v1',
      promptTemplateVersion: 'reburn-audit-prompt.v1',
      inputArtifactHashes: {
        transcript: 'sha256_mock_transcript',
        scenes: 'sha256_mock_scenes'
      },
      outputSchemaVersion: 'multimodal-audit.v1',
      processingDurationMs: 1450,
      tokenUsage: {
        promptTokens: 3200,
        completionTokens: 850,
        totalTokens: 4050
      }
    }
  };
}
