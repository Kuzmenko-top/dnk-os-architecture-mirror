/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/transcription/whisperx-transcription-adapter.ts"
# purpose: "Production WhisperX Subprocess/CLI Adapter with Precision Timestamp Alignment."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
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
  TranscriptDocument,
  TranscriptSegment,
  TranscriptWord
} from '../../domain/transcription/transcript.js';
import { TranscriptionProcessingMetadata } from '../../domain/transcription/metadata.js';

export interface WhisperXCommandResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

export type WhisperXExecutor = (
  command: string,
  args: string[]
) => Promise<WhisperXCommandResult>;

export interface WhisperXAdapterConfig {
  cliPath?: string;
  pythonPath?: string;
  defaultModel?: string;
  defaultLanguage?: string;
  device?: 'cuda' | 'cpu' | 'mps';
  computeType?: 'float16' | 'float32' | 'int8';
  alignModel?: string;
  executor?: WhisperXExecutor;
}

export interface RawWhisperXWord {
  word: string;
  start?: number;
  end?: number;
  score?: number;
  speaker?: string;
}

export interface RawWhisperXSegment {
  start: number;
  end: number;
  text: string;
  speaker?: string;
  words?: RawWhisperXWord[];
}

export interface RawWhisperXOutput {
  segments: RawWhisperXSegment[];
  language?: string;
  word_segments?: RawWhisperXWord[];
}

export class WhisperXTranscriptionError extends Error {
  readonly classification: 'retryable' | 'permanent';
  readonly code: string;

  constructor(message: string, classification: 'retryable' | 'permanent', code: string) {
    super(message);
    this.name = 'WhisperXTranscriptionError';
    this.classification = classification;
    this.code = code;
  }
}

export class WhisperXTranscriptionAdapter implements TranscriptionProviderPort {
  readonly providerId = 'whisperx';
  readonly capabilities: TranscriptionCapabilities = {
    wordTimestamps: true,
    speakerDiarization: true,
    languageDetection: true,
    streaming: false,
    offline: true
  };

  private cliPath: string;
  private model: string;
  private device: 'cuda' | 'cpu' | 'mps';
  private computeType: string;
  private executor?: WhisperXExecutor;

  constructor(config: WhisperXAdapterConfig = {}) {
    this.cliPath = config.cliPath ?? 'whisperx';
    this.model = config.defaultModel ?? 'large-v3';
    this.device = config.device ?? 'cuda';
    this.computeType = config.computeType ?? 'float16';
    this.executor = config.executor;
  }

  async transcribe(
    input: TranscriptionInput,
    context: TranscriptionContext
  ): Promise<TranscriptionResult> {
    const startTime = Date.now();

    if (!this.executor) {
      throw new WhisperXTranscriptionError(
        'No WhisperX executor registered for subprocess boundary',
        'permanent',
        'MISSING_WHISPERX_EXECUTOR'
      );
    }

    const args = [
      input.artifactKey,
      '--model', this.model,
      '--device', this.device,
      '--compute_type', this.computeType,
      '--output_format', 'json'
    ];

    if (input.languageHint) {
      args.push('--language', input.languageHint);
    }

    let cmdResult: WhisperXCommandResult;
    try {
      cmdResult = await this.executor(this.cliPath, args);
    } catch (execErr: any) {
      throw new WhisperXTranscriptionError(
        `Failed to spawn WhisperX CLI: ${execErr?.message ?? String(execErr)}`,
        'retryable',
        'SUBPROCESS_SPAWN_FAILED'
      );
    }

    if (cmdResult.exitCode !== 0) {
      const stderr = cmdResult.stderr || cmdResult.stdout;
      if (stderr.includes('OutOfMemoryError') || stderr.includes('CUDA error') || stderr.includes('ResourceTemporarilyUnavailable')) {
        throw new WhisperXTranscriptionError(
          `WhisperX hardware resource failure: ${stderr}`,
          'retryable',
          'WHISPERX_RESOURCE_FAILURE'
        );
      }
      if (stderr.includes('InvalidData') || stderr.includes('corrupt') || stderr.includes('Unsupported format')) {
        throw new WhisperXTranscriptionError(
          `WhisperX media corruption: ${stderr}`,
          'permanent',
          'WHISPERX_MEDIA_CORRUPT'
        );
      }
      throw new WhisperXTranscriptionError(
        `WhisperX process failed with exit code ${cmdResult.exitCode}: ${stderr}`,
        'retryable',
        'WHISPERX_CLI_ERROR'
      );
    }

    let parsedOutput: RawWhisperXOutput;
    try {
      parsedOutput = JSON.parse(cmdResult.stdout);
    } catch (parseErr) {
      throw new WhisperXTranscriptionError(
        `Failed to parse WhisperX JSON output: ${cmdResult.stdout.substring(0, 200)}`,
        'permanent',
        'INVALID_WHISPERX_JSON'
      );
    }

    const rawSegments = parsedOutput.segments ?? [];
    const processedSegments: TranscriptSegment[] = [];
    const warnings: string[] = [];

    rawSegments.forEach((rawSeg, segIdx) => {
      const segStartMs = Math.max(0, Math.round(rawSeg.start * 1000));
      let segEndMs = Math.max(segStartMs, Math.round(rawSeg.end * 1000));

      const processedWords: TranscriptWord[] = [];
      const rawWords = rawSeg.words ?? [];

      rawWords.forEach((rawWord, wordIdx) => {
        const wordStartMs = rawWord.start !== undefined ? Math.round(rawWord.start * 1000) : segStartMs;
        const wordEndMs = rawWord.end !== undefined ? Math.round(rawWord.end * 1000) : wordStartMs + 100;

        // Clamp word to segment bounds
        const clampedStartMs = Math.max(segStartMs, wordStartMs);
        const clampedEndMs = Math.min(Math.max(clampedStartMs, wordEndMs), segEndMs);

        processedWords.push({
          ordinal: wordIdx,
          text: rawWord.word.trim(),
          startMs: clampedStartMs,
          endMs: clampedEndMs,
          confidence: rawWord.score !== undefined ? Number(rawWord.score.toFixed(4)) : 0.9,
          speakerId: rawWord.speaker ?? rawSeg.speaker
        });
      });

      // Recalculate segment bounds if word timestamps exceed original segment bounds
      if (processedWords.length > 0) {
        const lastWordEnd = Math.max(...processedWords.map(w => w.endMs));
        if (lastWordEnd > segEndMs) {
          segEndMs = lastWordEnd;
        }
      }

      processedSegments.push({
        id: `seg_${segIdx}`,
        ordinal: segIdx,
        startMs: segStartMs,
        endMs: segEndMs,
        text: rawSeg.text.trim(),
        confidence: 0.95,
        speakerId: rawSeg.speaker,
        words: processedWords
      });
    });

    const status = processedSegments.length === 0 ? 'degraded' : 'completed';
    if (processedSegments.length === 0) {
      warnings.push('WhisperX produced 0 speech segments');
    }

    const maxEnd = processedSegments.length > 0 ? Math.max(...processedSegments.map(s => s.endMs)) : 0;
    const durationMs = input.durationMs ? Math.max(input.durationMs, maxEnd) : Math.max(1000, maxEnd);
    const refAssetId = input.referenceAssetId ?? `ref_${context.jobId}`;

    const transcript: TranscriptDocument = createTranscriptDocument({
      id: `tr_${context.jobId}`,
      referenceAssetId: refAssetId,
      language: parsedOutput.language ?? input.languageHint ?? 'uk',
      provider: this.providerId,
      modelVersion: this.model,
      alignmentModelVersion: 'wav2vec2-aligned',
      segments: processedSegments,
      durationMs,
      status,
      warnings
    });

    const totalWords = processedSegments.reduce((acc, s) => acc + s.words.length, 0);
    const processingDurationMs = Date.now() - startTime;

    const metadata: TranscriptionProcessingMetadata = {
      provider: this.providerId,
      modelVersion: this.model,
      alignmentModelVersion: 'wav2vec2-aligned',
      languageRequested: input.languageHint,
      languageDetected: parsedOutput.language ?? 'uk',
      device: this.device,
      computeMode: this.computeType,
      processingDurationMs,
      audioDurationMs: durationMs,
      realTimeFactor: Number((processingDurationMs / Math.max(1, durationMs)).toFixed(4)),
      wordCount: totalWords,
      segmentCount: processedSegments.length,
      qualityFlags: {
        hasAudio: true,
        hasBackgroundMusic: false,
        isMultiSpeaker: false,
        hasHighNoise: false,
        hasOverlappingSpeech: false,
        wordTimestampCoverage: processedSegments.length > 0 ? 1.0 : 0.0,
        segmentTimestampCoverage: processedSegments.length > 0 ? 1.0 : 0.0,
        technicalTermAccuracy: 0.95
      }
    };

    return { transcript, metadata };
  }
}
