/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/transcription/deterministic-transcription-provider.ts"
# purpose: "Deterministic Fake Transcription Provider with Ukrainian ReBurn Benchmark Presets and Degraded Capabilities."
# canonical_source: true
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import {
  TranscriptionCapabilities,
  TranscriptionContext,
  TranscriptionInput,
  TranscriptionProviderPort,
  TranscriptionResult
} from '../../ports/transcription-provider.js';
import {
  createTranscriptDocument,
  TranscriptSegment
} from '../../domain/transcription/transcript.js';
import { TranscriptionProcessingMetadata } from '../../domain/transcription/metadata.js';

export interface DeterministicProviderOptions {
  latencyMs?: number;
  simulatedError?: { code: string; message: string; classification: 'retryable' | 'permanent' };
  degradedCapabilities?: Partial<TranscriptionCapabilities>;
  emptyAudioMode?: boolean;
}

export class DeterministicFakeTranscriptionProvider implements TranscriptionProviderPort {
  readonly providerId = 'deterministic-fake-asr';
  readonly capabilities: TranscriptionCapabilities;
  private latencyMs: number;
  private simulatedError?: { code: string; message: string; classification: 'retryable' | 'permanent' };
  private emptyAudioMode: boolean;

  constructor(options: DeterministicProviderOptions = {}) {
    this.latencyMs = options.latencyMs ?? 0;
    this.simulatedError = options.simulatedError;
    this.emptyAudioMode = options.emptyAudioMode ?? false;
    this.capabilities = {
      wordTimestamps: true,
      speakerDiarization: true,
      languageDetection: true,
      streaming: false,
      offline: true,
      ...options.degradedCapabilities
    };
  }

  async transcribe(
    input: TranscriptionInput,
    context: TranscriptionContext
  ): Promise<TranscriptionResult> {
    if (this.latencyMs > 0) {
      await new Promise(resolve => setTimeout(resolve, this.latencyMs));
    }

    if (this.simulatedError) {
      const err = new Error(this.simulatedError.message) as any;
      err.code = this.simulatedError.code;
      err.classification = this.simulatedError.classification;
      throw err;
    }

    if (this.emptyAudioMode) {
      const doc = createTranscriptDocument({
        id: `tr_${context.jobId}_degraded`,
        referenceAssetId: input.referenceAssetId ?? 'asset_unknown',
        language: input.languageHint ?? 'uk',
        provider: this.providerId,
        modelVersion: 'degraded-v1',
        segments: [],
        durationMs: input.durationMs ?? 1000,
        confidence: 0.0,
        status: 'degraded',
        warnings: ['No audio track detected in source media artifact. Degrading capability to visual-only.']
      });

      return {
        transcript: doc,
        metadata: {
          provider: this.providerId,
          modelVersion: 'degraded-v1',
          languageRequested: input.languageHint ?? 'uk',
          languageDetected: 'none',
          device: 'fake',
          computeMode: 'cpu',
          processingDurationMs: this.latencyMs,
          audioDurationMs: input.durationMs ?? 1000,
          realTimeFactor: 0.01,
          wordCount: 0,
          segmentCount: 0,
          qualityFlags: {
            hasAudio: false,
            hasBackgroundMusic: false,
            isMultiSpeaker: false,
            hasHighNoise: false,
            hasOverlappingSpeech: false,
            wordTimestampCoverage: 0.0,
            segmentTimestampCoverage: 0.0,
            technicalTermAccuracy: 0.0
          }
        }
      };
    }

    // Default Ukrainian ReBurn benchmark transcript
    const segments: TranscriptSegment[] = [
      {
        id: 'seg_0',
        ordinal: 0,
        startMs: 0,
        endMs: 3500,
        text: 'Вітаємо в ReBurn ecosystem та DNK OS.',
        speakerId: 'SPEAKER_01',
        words: [
          { ordinal: 0, text: 'Вітаємо', startMs: 0, endMs: 700, confidence: 0.98 },
          { ordinal: 1, text: 'в', startMs: 750, endMs: 900, confidence: 0.99 },
          { ordinal: 2, text: 'ReBurn', startMs: 950, endMs: 1600, confidence: 0.96 },
          { ordinal: 3, text: 'ecosystem', startMs: 1650, endMs: 2400, confidence: 0.95 },
          { ordinal: 4, text: 'та', startMs: 2450, endMs: 2600, confidence: 0.99 },
          { ordinal: 5, text: 'DNK', startMs: 2650, endMs: 3000, confidence: 0.97 },
          { ordinal: 6, text: 'OS.', startMs: 3050, endMs: 3500, confidence: 0.98 }
        ]
      },
      {
        id: 'seg_1',
        ordinal: 1,
        startMs: 3600,
        endMs: 7200,
        text: 'Як за 60 секунд налаштувати Teleprompter та Shopify зйомки Shorts?',
        speakerId: 'SPEAKER_01',
        words: [
          { ordinal: 0, text: 'Як', startMs: 3600, endMs: 3800, confidence: 0.98 },
          { ordinal: 1, text: 'за', startMs: 3850, endMs: 4000, confidence: 0.99 },
          { ordinal: 2, text: '60', startMs: 4050, endMs: 4400, confidence: 0.95 },
          { ordinal: 3, text: 'секунд', startMs: 4450, endMs: 4900, confidence: 0.96 },
          { ordinal: 4, text: 'налаштувати', startMs: 4950, endMs: 5600, confidence: 0.94 },
          { ordinal: 5, text: 'Teleprompter', startMs: 5650, endMs: 6300, confidence: 0.97 },
          { ordinal: 6, text: 'та', startMs: 6350, endMs: 6450, confidence: 0.99 },
          { ordinal: 7, text: 'Shopify', startMs: 6500, endMs: 7000, confidence: 0.96 },
          { ordinal: 8, text: 'зйомки', startMs: 7050, endMs: 7100, confidence: 0.95 },
          { ordinal: 9, text: 'Shorts?', startMs: 7120, endMs: 7200, confidence: 0.95 }
        ]
      }
    ];

    const durationMs = input.durationMs ?? 8000;
    const doc = createTranscriptDocument({
      id: `tr_${context.jobId}`,
      referenceAssetId: input.referenceAssetId ?? 'asset_001',
      language: input.languageHint ?? 'uk',
      provider: this.providerId,
      modelVersion: 'large-v3-reburn-v1',
      alignmentModelVersion: 'wav2vec2-uk-v1',
      segments,
      durationMs,
      confidence: 0.97,
      status: 'completed',
      warnings: []
    });

    const totalWords = segments.reduce((sum, s) => sum + s.words.length, 0);

    const metadata: TranscriptionProcessingMetadata = {
      provider: this.providerId,
      modelVersion: 'large-v3-reburn-v1',
      alignmentModelVersion: 'wav2vec2-uk-v1',
      languageRequested: input.languageHint ?? 'uk',
      languageDetected: 'uk',
      device: 'fake',
      computeMode: 'gpu',
      processingDurationMs: this.latencyMs,
      audioDurationMs: durationMs,
      realTimeFactor: 0.05,
      wordCount: totalWords,
      segmentCount: segments.length,
      qualityFlags: {
        hasAudio: true,
        hasBackgroundMusic: false,
        isMultiSpeaker: false,
        hasHighNoise: false,
        hasOverlappingSpeech: false,
        wordTimestampCoverage: 1.0,
        segmentTimestampCoverage: 1.0,
        technicalTermAccuracy: 1.0
      }
    };

    return {
      transcript: doc,
      metadata
    };
  }
}
