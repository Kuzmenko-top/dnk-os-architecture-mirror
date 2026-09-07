# Gemini 3.5 Transcribe & Auto-Cut Video Asset Pipeline

# --- DNK-MRH-HEADER ---
# mrh_id: "media/programmatic-video-engine/references/gemini-transcribe-media-pipeline.md"
# purpose: "Technical Reference for Gemini 3.5 Transcribe, Word-Timestamps Auto-Cut & Multimodal Video Indexing."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

## 1. High-Efficiency Audio Extraction & Pre-Processing
- **Problem**: Ingesting 1000+ GB of raw video directly into cloud AI services is bandwidth-prohibitive and slow.
- **Solution**: Pre-process video locally using FFmpeg to extract compressed 16kHz mono audio (Opus / MP3).
- **Ratio**: Reduces 1000 GB video archive down to ~15-20 GB audio (98% reduction), preserving full speech fidelity.
- **Command Vector**:
  ```bash
  ffmpeg -i "raw_video.mp4" -vn -acodec libopus -b:a 32k -ar 16000 -ac 1 "extracted_audio.opus"
  ```

## 2. Gemini 3.5 Transcribe Integration Spec
- **SDK**: `google-genai` (v2.0.0+) via Interactions API.
- **Model**: `gemini-3.5-transcribe` (Batch) or `gemini-3.5-transcribe-live` (Streaming).
- **Core Parameters**:
  - `mode`: `"smart"` (filters disfluencies while keeping exact word-level timing) or `"verbatim"`.
  - `word_timestamps`: `True` (delivers millisecond-accurate word boundaries).
  - `diarization`: `True` (speaker identification).
  - `custom_vocabulary`: Custom domain terms list to prevent STT hallucinations.

- **Python Interaction Pattern**:
  ```python
  from google import genai
  from google.genai import types

  client = genai.Client()
  audio_file = client.files.upload(file="extracted_audio.opus")

  response = client.interactions.create(
      model="gemini-3.5-transcribe",
      input={"file": audio_file},
      config=types.TranscriptionConfig(
          mode="smart",
          language_codes=["uk-UA", "en-US"],
          word_timestamps=True,
          diarization=True,
          custom_vocabulary=["FastAPI", "SCONES", "TaskDNA", "DNK OS", "Gerych"]
      )
  )
  ```

## 3. Disfluency & Silence Auto-Cut Algorithm
- **Word Gap Analysis**: Calculate $\Delta t = \text{word}_{i+1}.\text{start} - \text{word}_i.\text{end}$.
- **Silence Threshold**: If $\Delta t > 1.2\text{s}$ (configurable), mark the interval $(\text{word}_i.\text{end}, \text{word}_{i+1}.\text{start})$ as a pause cut range. Check leading silence ($0 \to \text{word}_0.\text{start}$) and trailing silence ($\text{word}_{-1}.\text{end} \to \text{duration}$).
- **Filler Word Filter**: Match transcript words against disfluency lists (UKR/ENG: `"um"`, `"uh"`, `"ну"`, `"типу"`, `"е-е"`, `"коротше"`, `"значить"`, `"отже"`).
- **Cut Range Merging**: Sort all cut ranges and merge adjacent intervals if $\text{cut}_{i+1}.\text{start} \le \text{cut}_i.\text{end} + \text{merge\_threshold\_sec}$ (default 0.5s).
- **Keep Ranges Computation**: Invert merged cut ranges across `[0, total_duration]` to generate `[{"start": float, "end": float, "duration": float}]` segments for non-destructive FFmpeg trim/concat or AST timeline composition.

## 4. Ingestion Data Models (Pydantic V2)
```python
class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float
    confidence: float = 1.0

class SpeakerSegment(BaseModel):
    speaker_id: str
    start: float
    end: float
    text: str

class TranscriptResult(BaseModel):
    audio_path: str
    duration_sec: float
    text: str
    words: List[WordTimestamp] = []
    speakers: List[SpeakerSegment] = []

class CutRange(BaseModel):
    start: float
    end: float
    reason: Literal["filler_word", "pause", "duplicate", "merged_cut"]
    text: Optional[str] = None
```

## 5. Long-Form Audio Chunking (30-45 min Slices)
- For raw video files > 45 minutes, split extracted audio into chunk intervals (e.g. 2700s) using FFmpeg `-f segment` or timestamp slicing (`-ss / -to`) before batching to `GeminiTranscriber.transcribe_batch_async` with a semaphore concurrency limiter (`max_concurrent=5`).

## 6. Multimodal SCONES Vector Indexing (Video Asset DAM)
- **Segment Chunking**: Group contiguous words into 30-90s logical topic segments.
- **Metadata**: Attach `footage_id`, `start_time`, `end_time`, `speaker_id`, `raw_text`.
- **Vector Embedding**: Store text embeddings in SCONES Memory (`pgvector`).
- **Semantic Retrieval**: Query "find footage where I debug code or explain DAG architecture" to retrieve exact frame timestamps for B-Roll substitution.
