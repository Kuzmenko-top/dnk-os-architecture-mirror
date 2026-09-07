/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/analyzers/frame-deduplication.test.ts"
# purpose: "Unit tests for InMemoryFrameDeduplicator and FrameDeduplicationPort interface."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import { InMemoryFrameDeduplicator } from '../../../src/pipeline/infrastructure/video-analysis/in-memory-frame-deduplicator.js';
import { FrameCandidate, FrameDedupPolicy } from '../../../src/pipeline/ports/frame-deduplication.js';

describe('InMemoryFrameDeduplicator', () => {
  const deduplicator = new InMemoryFrameDeduplicator();

  it('keeps all frames when they are highly distinct (high Hamming Distance)', async () => {
    const frames: FrameCandidate[] = [
      { id: 'f1', timestampMs: 100, imageHash: '1111111111111111' },
      { id: 'f2', timestampMs: 200, imageHash: '2222222222222222' },
      { id: 'f3', timestampMs: 300, imageHash: '3333333333333333' }
    ];

    const policy: FrameDedupPolicy = {
      similarityThreshold: 0.1, // very strict matching required
      maxFramesToKeep: 10
    };

    const result = await deduplicator.deduplicate(frames, policy, 'asset_123');
    expect(result.referenceAssetId).toBe('asset_123');
    expect(result.deduplicatedFrames).toHaveLength(3);
    expect(result.metrics.input_frame_count).toBe(3);
    expect(result.metrics.output_frame_count).toBe(3);
    expect(result.metrics.dedup_ratio).toBe(0);
  });

  it('deduplicates frames that are very similar (low Hamming Distance)', async () => {
    // f2 differs by only 1 character out of 16 from f1
    const frames: FrameCandidate[] = [
      { id: 'f1', timestampMs: 100, imageHash: '1111111111111111' },
      { id: 'f2', timestampMs: 200, imageHash: '1111111111111112' }, 
      { id: 'f3', timestampMs: 300, imageHash: '2222222222222222' }
    ];

    const policy: FrameDedupPolicy = {
      similarityThreshold: 0.15, // threshold of 15% distance
      maxFramesToKeep: 10
    };

    const result = await deduplicator.deduplicate(frames, policy, 'asset_123');
    expect(result.deduplicatedFrames).toHaveLength(2); // f2 should be discarded as duplicate of f1
    expect(result.deduplicatedFrames[0].id).toBe('f1');
    expect(result.deduplicatedFrames[1].id).toBe('f3');
    expect(result.metrics.dedup_ratio).toBeCloseTo(0.33, 1);
  });

  it('enforces maxFramesToKeep limit', async () => {
    const frames: FrameCandidate[] = [
      { id: 'f1', timestampMs: 100, imageHash: '1111111111111111' },
      { id: 'f2', timestampMs: 200, imageHash: '2222222222222222' },
      { id: 'f3', timestampMs: 300, imageHash: '3333333333333333' }
    ];

    const policy: FrameDedupPolicy = {
      similarityThreshold: 0.1,
      maxFramesToKeep: 2
    };

    const result = await deduplicator.deduplicate(frames, policy, 'asset_123');
    expect(result.deduplicatedFrames).toHaveLength(2); // strictly limited to 2
    expect(result.deduplicatedFrames[0].id).toBe('f1');
    expect(result.deduplicatedFrames[1].id).toBe('f2');
  });

  it('handles empty frame arrays gracefully', async () => {
    const policy: FrameDedupPolicy = {
      similarityThreshold: 0.1,
      maxFramesToKeep: 5
    };

    const result = await deduplicator.deduplicate([], policy, 'asset_empty');
    expect(result.deduplicatedFrames).toHaveLength(0);
    expect(result.metrics.input_frame_count).toBe(0);
    expect(result.metrics.output_frame_count).toBe(0);
    expect(result.metrics.dedup_ratio).toBe(0);
  });
});
