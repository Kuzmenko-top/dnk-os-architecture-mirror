/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/video-analysis/in-memory-frame-deduplicator.ts"
# purpose: "In-Memory Implementation of FrameDeduplicationPort with Hamming Distance comparison."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import {
  FrameDeduplicationPort,
  FrameCandidate,
  FrameDedupPolicy,
  DeduplicatedFrameSet
} from '../../ports/frame-deduplication.js';

export class InMemoryFrameDeduplicator implements FrameDeduplicationPort {
  public async deduplicate(
    frames: FrameCandidate[],
    policy: FrameDedupPolicy,
    referenceAssetId = 'unknown-asset'
  ): Promise<DeduplicatedFrameSet> {
    const startTime = Date.now();
    
    if (frames.length === 0) {
      return {
        referenceAssetId,
        deduplicatedFrames: [],
        metrics: {
          input_frame_count: 0,
          output_frame_count: 0,
          dedup_ratio: 0,
          average_hamming_distance: 0,
          processing_time_ms: Date.now() - startTime
        }
      };
    }

    const kept: FrameCandidate[] = [];
    let totalHammingDistance = 0;
    let comparisons = 0;

    for (const candidate of frames) {
      let isDuplicate = false;
      for (const existing of kept) {
        const dist = this.calculateHammingDistance(candidate.imageHash, existing.imageHash);
        totalHammingDistance += dist;
        comparisons++;

        const normDist = dist / Math.max(1, candidate.imageHash.length);
        if (normDist < policy.similarityThreshold) {
          isDuplicate = true;
          break;
        }
      }

      if (!isDuplicate && kept.length < policy.maxFramesToKeep) {
        kept.push(candidate);
      }
    }

    const input_frame_count = frames.length;
    const output_frame_count = kept.length;
    const dedup_ratio = input_frame_count > 0 ? (input_frame_count - output_frame_count) / input_frame_count : 0;
    const average_hamming_distance = comparisons > 0 ? totalHammingDistance / comparisons : 0;

    return {
      referenceAssetId,
      deduplicatedFrames: kept,
      metrics: {
        input_frame_count,
        output_frame_count,
        dedup_ratio,
        average_hamming_distance,
        processing_time_ms: Date.now() - startTime
      }
    };
  }

  private calculateHammingDistance(hash1: string, hash2: string): number {
    let distance = 0;
    const len = Math.min(hash1.length, hash2.length);
    for (let i = 0; i < len; i++) {
      if (hash1[i] !== hash2[i]) {
        distance++;
      }
    }
    distance += Math.abs(hash1.length - hash2.length);
    return distance;
  }
}
