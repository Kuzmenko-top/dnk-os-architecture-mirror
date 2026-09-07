/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/transcription/ukrainian-benchmark.test.ts"
# purpose: "Benchmark Test Suite for Ukrainian Speech, ReBurn Technical Terms & RTF Precision."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import { DeterministicFakeTranscriptionProvider } from '../../../src/pipeline/infrastructure/transcription/deterministic-transcription-provider.js';

describe('Ukrainian Benchmark & ReBurn Domain Verification', () => {
  const provider = new DeterministicFakeTranscriptionProvider();

  it('evaluates ReBurn technical terms recall (>= 90%)', async () => {
    const res = await provider.transcribe(
      {
        artifactKey: 'sources/uk_reburn_demo.mp4',
        mimeType: 'video/mp4',
        languageHint: 'uk'
      },
      { jobId: 'job_benchmark_01' }
    );

    expect(res.transcript.status).toBe('completed');
    expect(res.metadata.qualityFlags.technicalTermAccuracy).toBeGreaterThanOrEqual(0.90);

    const fullText = res.transcript.segments.map(s => s.text).join(' ');
    // Check key ReBurn terms in sample output
    expect(fullText).toContain('ReBurn');
    expect(fullText).toContain('Teleprompter');
    expect(fullText).toContain('Shopify');
  });

  it('validates word timestamp coverage (>= 95%) and strict ordering', async () => {
    const res = await provider.transcribe(
      {
        artifactKey: 'sources/uk_reburn_demo.mp4',
        mimeType: 'video/mp4',
        languageHint: 'uk'
      },
      { jobId: 'job_benchmark_02' }
    );

    const segments = res.transcript.segments;
    let totalWords = 0;
    let validWordTimestamps = 0;

    segments.forEach(seg => {
      seg.words.forEach(word => {
        totalWords++;
        if (word.startMs >= seg.startMs && word.endMs <= seg.endMs && word.endMs > word.startMs) {
          validWordTimestamps++;
        }
      });
    });

    const coverage = totalWords > 0 ? validWordTimestamps / totalWords : 0;
    expect(coverage).toBeGreaterThanOrEqual(0.95);
  });

  it('supports degraded visual-only benchmark without throwing errors', async () => {
    const degradedProvider = new DeterministicFakeTranscriptionProvider({ emptyAudioMode: true });
    const res = await degradedProvider.transcribe(
      {
        artifactKey: 'sources/silent_video.mp4',
        mimeType: 'video/mp4',
        languageHint: 'uk'
      },
      { jobId: 'job_benchmark_degraded' }
    );

    expect(res.transcript.status).toBe('degraded');
    expect(res.transcript.segments).toHaveLength(0);
    expect(res.transcript.warnings[0]).toContain('No audio track detected');
  });
});
