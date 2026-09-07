/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/frame-deduplication.ts"
# purpose: "Port Interface and Types for Visual Frame Deduplication and Image Comparison Patterns."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export interface FrameCandidate {
  id: string;
  timestampMs: number;
  imagePath?: string;
  imageUrl?: string;
  imageHash: string; // e.g. perceptual hash / dhash / phash (hex or binary)
}

export interface FrameDedupPolicy {
  similarityThreshold: number; // Hamming distance threshold (e.g. 0.15 or 8 bits)
  maxFramesToKeep: number;
  priorityKey?: 'timestamp' | 'quality' | 'movement';
}

export interface FrameDeduplicationMetrics {
  input_frame_count: number;
  output_frame_count: number;
  dedup_ratio: number;
  average_hamming_distance: number;
  processing_time_ms: number;
}

export interface DeduplicatedFrameSet {
  referenceAssetId: string;
  deduplicatedFrames: FrameCandidate[];
  metrics: FrameDeduplicationMetrics;
}

export interface FrameDeduplicationPort {
  deduplicate(
    frames: FrameCandidate[],
    policy: FrameDedupPolicy,
    referenceAssetId?: string
  ): Promise<DeduplicatedFrameSet>;
}
