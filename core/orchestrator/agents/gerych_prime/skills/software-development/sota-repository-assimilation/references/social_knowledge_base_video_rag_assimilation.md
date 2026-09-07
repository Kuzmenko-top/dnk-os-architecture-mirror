# 🧬 SOTA Reference: Social Knowledge Base (SKB) Video RAG Assimilation

## 👑 1. Scope & Core Patterns
This reference details the high-performance architectural patterns extracted from `guimatheus92/social-knowledge-base` (SKB) for building the **DNK Video Librarian (DVL)** system in DNK OS.

### 🌟 High-Value Architectural Pillars:
1. **Zero-Waste Sidecar Caching Invariant**: Sidecar-based local STT caching to minimize API and compute overhead.
2. **Resilient SQLite pipeline state tracking**: State-machine-driven ingestion queue to guarantee fault tolerance and resume-on-failure.
3. **Incremental Map-Reduce Knowledge Synthesis**: Fast theme compilation of massive video sets using frontmatter-only lookups.
4. **Interactive Seek-to-Timestamp UI**: 1:1 binding between generated text timestamps and video playback.

---

## ⚡ 2. Technical Implementations & Schemas

### 🗄️ 2.1. Ingestion Pipeline Status Schema (SQLite)
Track progress of large media files via a status state machine:
```sql
CREATE TABLE media (
  id TEXT PRIMARY KEY,
  origin_id TEXT,
  type TEXT CHECK(type IN ('video', 'audio', 'short')),
  local_path TEXT NOT NULL,
  file_size INTEGER,
  duration_seconds REAL,
  status TEXT CHECK(status IN ('pending', 'processing', 'transcribed', 'notes_generated', 'indexed', 'error')) DEFAULT 'pending',
  error_message TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
```

### 💾 2.2. Zero-Waste Sidecar Caching Pattern
Always check for local sidecars before invoking expensive external STT (e.g. Gemini 3.5 Transcribe).
- **Sidecar Side-by-Side Invariant**:
  - `[media_hash].json` -> Full word-by-word timestamp alignments.
  - `[media_hash].vtt` -> Subtitles ready for the frontend HTML5 player.
  - `[media_hash].txt` -> Raw prose description for standard text indexing.

### 💾 2.2.1. TypeScript Port & Naming Convention Implementation
In production environments (e.g. `video_audit_core`), the naming convention for sidecars is structured under a reference asset path:
`references/{referenceAssetId}/transcript/{provider}-{model}-{version}.{json|vtt|txt}`

```typescript
export interface TranscriptSegment {
  startMs: number;
  endMs: number;
  text: string;
  speaker?: string;
}

export interface TranscriptDocument {
  id: string;
  sourceHash: string; // SHA-256 hash of source video/audio asset
  provider: string;
  model: string;
  version: string;
  segments: TranscriptSegment[];
}
```

```python
# Check local cache before calling API
def get_transcription(media_path: str, media_hash: str) -> dict:
    sidecar_json = Path(f"assets/transcripts/{media_hash}.json")
    if sidecar_json.exists():
        with open(sidecar_json, "r") as f:
            return json.load(f)
            
    # Cache Miss -> Execute API
    transcription = call_stt_api(media_path)
    
    # Save sidecars
    with open(sidecar_json, "w") as f:
        json.dump(transcription, f)
    return transcription
```

### 🧠 2.3. Incremental Map-Reduce Knowledge Synthesizer
Avoid passing entire video transcriptions to the LLM when summarizing archives. Use a two-stage **Map-Reduce** pipeline:

1. **Map Phase (`build-notes`)**: Process each raw transcription into an individual Markdown note with structured YAML frontmatter:
   ```markdown
   ---
   title: "How TaskDNA Works"
   category: "Architecture"
   tags: ["task-dna", "swarm", "dag"]
   duration: 345
   ---
   # Executive Summary
   ...
   ```

2. **Reduce Phase (`synthesize-overview`)**: Group and summarize notes by reading only the lightweight frontmatters of all notes, generating/updating a global theme-based `OVERVIEW.md` dynamically:
   ```python
   def compile_overview(notes_dir: str):
       frontmatters = []
       for note_file in Path(notes_dir).glob("*.md"):
           # Read YAML header only
           meta = parse_yaml_frontmatter(note_file)
           frontmatters.append(meta)
           
       # Prompt LLM to group metadata into themes and update OVERVIEW.md
       llm_update_overview(frontmatters)
   ```

### 🎨 2.4. Click-to-Seek Interactive Timestamps
On the frontend Markdown renderer, parse any timestamp matching `(HH:)?MM:SS` (e.g. `01:45` or `01:12:30`) and wrap it in a clickable element that fires a seek event on the HTML5 video tag:

```typescript
// Click handler in React / Svelte
const handleTimestampClick = (timestampString: string) => {
  const parts = timestampString.split(':').map(Number);
  let seconds = 0;
  if (parts.length === 3) {
    seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
  } else if (parts.length === 2) {
    seconds = parts[0] * 60 + parts[1];
  }
  
  const videoPlayer = document.querySelector('video');
  if (videoPlayer) {
    videoPlayer.currentTime = seconds;
    videoPlayer.play();
  }
};
```
