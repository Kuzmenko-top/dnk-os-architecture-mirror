/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/transcription/whisperx-adapter.test.ts"
# purpose: "Unit Test Suite for WhisperX Adapter Execution Boundary and Error Mapping."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  WhisperXTranscriptionAdapter,
  WhisperXTranscriptionError,
  RawWhisperXOutput
} from '../../../src/pipeline/infrastructure/transcription/whisperx-transcription-adapter.js';

describe('WhisperXTranscriptionAdapter Execution & Parsing Boundary', () => {
  it('parses valid WhisperX stdout and converts timestamps to milliseconds', async () => {
    const rawOutput: RawWhisperXOutput = {
      language: 'uk',
      segments: [
        {
          start: 0.5,
          end: 2.1,
          text: 'Вітаю у системі',
          speaker: 'SPEAKER_00',
          words: [
            { word: 'Вітаю', start: 0.5, end: 1.1, score: 0.98, speaker: 'SPEAKER_00' },
            { word: 'у', start: 1.2, end: 1.4, score: 0.95, speaker: 'SPEAKER_00' },
            { word: 'системі', start: 1.5, end: 2.1, score: 0.99, speaker: 'SPEAKER_00' }
          ]
        }
      ]
    };

    const adapter = new WhisperXTranscriptionAdapter({
      executor: async (cmd, args) => ({
        stdout: JSON.stringify(rawOutput),
        stderr: '',
        exitCode: 0
      })
    });

    const res = await adapter.transcribe(
      {
        artifactKey: 'sources/sample.mp4',
        mimeType: 'video/mp4',
        languageHint: 'uk',
        durationMs: 3000
      },
      { jobId: 'job_wx_01' }
    );

    expect(res.transcript.provider).toBe('whisperx');
    expect(res.transcript.language).toBe('uk');
    expect(res.transcript.segments).toHaveLength(1);

    const seg = res.transcript.segments[0];
    expect(seg.startMs).toBe(500);
    expect(seg.endMs).toBe(2100);
    expect(seg.words).toHaveLength(3);
    expect(seg.words[0].startMs).toBe(500);
    expect(seg.words[0].endMs).toBe(1100);
    expect(seg.words[0].text).toBe('Вітаю');
  });

  it('classifies CUDA/OOM hardware error as retryable failure', async () => {
    const adapter = new WhisperXTranscriptionAdapter({
      executor: async () => ({
        stdout: '',
        stderr: 'OutOfMemoryError: CUDA out of memory. Tried to allocate 2.00 GiB',
        exitCode: 1
      })
    });

    try {
      await adapter.transcribe(
        { artifactKey: 'sources/sample.mp4', mimeType: 'video/mp4' },
        { jobId: 'job_wx_oom' }
      );
      expect.fail('Should have thrown WhisperXTranscriptionError');
    } catch (err: any) {
      expect(err).toBeInstanceOf(WhisperXTranscriptionError);
      expect(err.classification).toBe('retryable');
      expect(err.code).toBe('WHISPERX_RESOURCE_FAILURE');
    }
  });

  it('classifies media corruption as permanent failure', async () => {
    const adapter = new WhisperXTranscriptionAdapter({
      executor: async () => ({
        stdout: '',
        stderr: 'InvalidData: corrupt mp4 file header',
        exitCode: 1
      })
    });

    try {
      await adapter.transcribe(
        { artifactKey: 'sources/corrupt.mp4', mimeType: 'video/mp4' },
        { jobId: 'job_wx_corrupt' }
      );
      expect.fail('Should have thrown WhisperXTranscriptionError');
    } catch (err: any) {
      expect(err).toBeInstanceOf(WhisperXTranscriptionError);
      expect(err.classification).toBe('permanent');
      expect(err.code).toBe('WHISPERX_MEDIA_CORRUPT');
    }
  });
});
