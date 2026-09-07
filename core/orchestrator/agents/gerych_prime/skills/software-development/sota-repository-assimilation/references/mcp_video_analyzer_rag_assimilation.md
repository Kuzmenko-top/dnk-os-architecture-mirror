# 🧬 SOTA Reference: MCP Video Analyzer RAG Assimilation

## 👑 1. Scope & Core Patterns
This reference outlines high-fidelity architectural patterns and integration-ready algorithms extracted from `guimatheus92/mcp-video-analyzer` for implementing advanced media deconstruction and Agentic Video Understanding in **DNK OS** (`services/dnk_video_ai_creator`).

### 🌟 High-Value Architectural Pillars:
1. **Loom GraphQL Meta-Scraper Invariant**: Direct serverless query pattern to extract captions and raw streaming URLs without browser automation or video downloads.
2. **Visual dHash & Hamming Deduplication**: Perceptual difference hashing to eliminate duplicate video frames (slides, static UI) from LLM visual context.
3. **OCR Enhancing Preprocessing Pipeline**: Sharp-like image tuning (2x scale, grayscale, contrast normalization) to boost OCR accuracy by up to 15%.
4. **Hybrid Agentic Navigation Toolkit**: Providing granular micro-tools (`get_transcript`, `get_frame_at`, `get_frame_burst`) to power the Gemini Agentic Video Exploration Loop.

---

## ⚡ 2. Technical Implementations & Schemas

### 🔗 2.1. Loom GraphQL Extraction Query
Instead of downloading screen recordings, query Loom's GraphQL endpoint directly to get the WebVTT transcript file and stream CDN source URL instantly:

```graphql
# POST to https://www.loom.com/graphql
query GetLoomVideoData($videoId: ID!) {
  video(id: $videoId) {
    id
    title
    duration
    captions {
      sourceUrl # Direct WebVTT link
      language
    }
    sourceUrl # Direct CDN mp4/webm stream
  }
}
```

### 🖼️ 2.2. dHash Perceptual Image Fingerprinting
A Python equivalent of `sharp`'s perceptual image comparison for frame-level deduplication:

### 🖼️ 2.2.1. TypeScript Port & Deduplication Interface
In TypeScript monorepos (e.g. `video_audit_core`), frame deduplication is decoupled via a clear Port/Adapter architecture:

```typescript
export interface FrameCandidate {
  id: string;
  timestampMs: number;
  imagePath?: string;
  imageUrl?: string;
  imageHash: string; // Perceptual hash (hex representation)
}

export interface FrameDedupPolicy {
  similarityThreshold: number; // Hamming distance percentage / threshold (e.g. 0.15)
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
```

```python
import cv2
import numpy as np

def calculate_dhash(image: np.ndarray, hash_size: int = 8) -> str:
    """
    Computes a 64-bit difference hash (dHash) for an image.
    Compares the relative brightness of adjacent pixels in a 9x8 grid.
    """
    # Resize to 9x8 and convert to grayscale
    resized = cv2.resize(image, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    
    # Compute horizontal gradients
    diff = gray[:, 1:] > gray[:, :-1]
    
    # Pack boolean bits into a hexadecimal string
    bits = diff.flatten()
    hex_string = "".join(f"{b:02x}" for b in np.packbits(bits))
    return hex_string

def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculates the Hamming distance (differing bits) between two dHashes."""
    h1_bytes = bytes.fromhex(hash1)
    h2_bytes = bytes.fromhex(hash2)
    return sum(bin(b1 ^ b2).count("1") for b1, b2 in zip(h1_bytes, h2_bytes))
```

### 📝 2.3. OCR Image Optimization Preprocessing
Applying advanced image enhancements before OCR processing yields an 11-15% gain in optical character recognition accuracy for text-dense software screen shares:

```python
def optimize_for_ocr(image_path: str, output_path: str) -> None:
    """
    Optimizes a frame image for Tesseract OCR:
    - Grayscale conversion
    - 2x linear upscaling
    - Histogram contrast normalization
    """
    img = cv2.imread(image_path)
    
    # 1. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. 2x Upscale
    upscaled = cv2.resize(gray, (0, 0), fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    
    # 3. Contrast Equalization (CLAHE - Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    optimized = clahe.apply(upscaled)
    
    cv2.imwrite(output_path, optimized)
```

---

## 🚦 3. Implementation of the Agentic Video Exploration Loop

Rather than extracting all frames at 1 FPS and flooding the LLM context, the orchestrator utilizes granular toolports in a feedback loop:

```python
# SOTA Agentic timeline navigation algorithm
def agentic_video_search(video_path: str, target_query: str) -> dict:
    # Step 1: Query the low-token audio transcript first
    transcript = video_transcriber.transcribe(video_path)
    
    # Step 2: Agent analyzes text timeline to propose candidate timestamps
    candidate_timestamps = llm_propose_visual_targets(transcript, target_query)
    
    results = []
    # Step 3: Target Frame Retrieval
    for timestamp in candidate_timestamps:
        # Rapid seek frame extraction (-ss)
        frame = frame_analyzer.extract_frame_at(video_path, timestamp)
        
        # Fast local OCR on the target frame
        ocr_text = run_local_ocr(frame.file_path)
        
        results.append({
            "timestamp": timestamp,
            "ocr_text": ocr_text,
            "frame_path": frame.file_path
        })
        
    # Step 4: Final mult-modal fusion
    return llm_synthesize_visuals_with_audio(transcript, results, target_query)
```
