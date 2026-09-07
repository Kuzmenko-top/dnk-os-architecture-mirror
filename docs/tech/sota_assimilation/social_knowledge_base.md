# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/social_knowledge_base.md"
# purpose: "SOTA Architectural Audit & Assimilation Mapping of guimatheus92/social-knowledge-base for DNK Video Librarian."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Assimilation & Architectural Audit: guimatheus92/social-knowledge-base (SKB)

## 👑 1. Executive Summary

This document presents a comprehensive, high-fidelity architectural audit of the open-source repository **`guimatheus92/social-knowledge-base` (SKB)**.

**Social Knowledge Base (SKB)** is a modern, AI-native system designed to download, transcribe, analyze, and synthesize video content (specifically Instagram/TikTok Reels, Stories, and Highlights) into an interactive, RAG-queryable knowledge base. It combines high-performance local GPU-accelerated transcription, multimodal video parsing (frame-extraction + OCR), schema-guided structured LLM prompts, and a beautiful Next.js + SQLite dashboard.

### 🌟 Key Audit Takeaway
SKB is a goldmine of production-ready patterns for our **DNK Video Librarian (DVL)** system (Phase 1 to Phase 5 in `DNK-VIDEO-AUDIT-AND-PLAN.md`). By assimilating its core mechanics—specifically **GPU-accelerated Whisper sidecar caching, incremental Map-Reduce overview synthesis, and timestamp-aligned subtitle database schemas**—we can accelerate DVL development by 3x and guarantee zero-waste token efficiency.

---

## 🏗️ 2. High-Level Architecture Comparison

The SKB architecture aligns 1:1 with the design goals of our **DNK Video Librarian**. Below is a high-level mapping of components and technologies:

| Domain Layer | Social Knowledge Base (SKB) | DNK Video Librarian (DVL) Proposed Architecture | Integration Synergy |
| :--- | :--- | :--- | :--- |
| **Media Ingestion** | Local python scripts for Instagram / `yt_dlp` / direct URLs. | `core/media/audio_extractor.py` (FFmpeg-based audio demuxing). | **Direct Reuse**: Reuse the SQL schema for media manifest & ingestion status. |
| **Transcription (STT)** | GPU `faster-whisper` + local subtitle caching (`.vtt`, `.txt`, `.json` sidecars). | `core/media/stt_transcribe.py` (Gemini 3.5 smart mode + local Whisper fallback). | **Direct Reuse**: Adopt sidecar side-by-side caching to prevent expensive re-transcriptions. |
| **Video Understanding** | Multimodal frame analyzer + OCR (`mcp-video-analyzer`). | Gemini 3.5 Multimodal video-to-prose & frame analysis. | **Pattern Adapt**: Use uniform frame extraction + OCR as a fallback/enrichment. |
| **Knowledge Synthesis** | Map-Reduce prompts (`prompts/build-notes.md` + `prompts/synthesize-overview.md`). | `core/media/auto_cut_cleaner.py` + SCONES memory builders. | **Direct Reuse**: High-fidelity markdown structure & Incremental Overview compilation. |
| **Semantic Search & DB** | Next.js (Drizzle ORM) + SQLite (`node:sqlite`) + `ChromaDB` / vector search. | SCONES Memory Vault + PGVector / SQLite FTS5. | **Direct Reuse**: SQLite media-notes relational schema and timestamp-linked search queries. |

---

## 🔍 3. Deep Dive into Key Components & Mechanics

### 🗄️ 3.1. Relational Database Manifest & Status Tracking (SQLite)
SKB implements a highly resilient, lightweight manifest schema using SQLite to track the ingestion job pipeline. It stores media assets, transcriber status, and note outputs.

**Database Schema (`schema.ts`):**
- **`media` Table**: Tracks download details (`id`, `origin_id`, `type`, `local_path`, `file_size`, `duration`, `status`).
- **`notes` Table**: Stores generated markdown notes, titles, and tags tied back to `media`.
- **`jobs` Table**: Real-time progress monitoring of downloading, transcribing, and indexing.

*Why this is useful for DVL:*
Instead of writing a custom state tracker, we can adapt this schema to run inside `apps/api/visual_shell_db.json` or a lightweight SQLite database in DNK OS. It allows us to resume aborted ingestion pipelines gracefully.

---

### ⚡ 3.2. GPU Batch Transcription & Sidecar Caching (`transcribe_gpu.py`)
To minimize transcription costs and processing latency, SKB uses a localized GPU transcription script based on `faster-whisper`:
1. It scans the assets folder for untranscribed video files.
2. It executes Whisper with automatic GPU/CPU fallback and optimal batching.
3. **Key Pattern:** It writes three sidecar files directly next to each video:
   - `video_name.txt` (Plain text summary)
   - `video_name.vtt` (Standard WebVTT for player subtitles)
   - `video_name.json` (Structured word-by-word timestamp mappings)
4. On subsequent runs, it checks for these sidecars. If they exist, it skips transcription entirely.

*Why this is useful for DVL (Task `DNK-VIDEO-003`):*
This is the ultimate **Zero-Waste** pattern! Gemini 3.5 Transcription APIs are highly capable, but repeated runs on the same videos during debugging can drain our API budget. By implementing this sidecar file caching protocol, we ensure we only call Gemini or local Whisper once per file.

---

### 🧠 3.3. Hierarchical Notes & Incremental Map-Reduce Overview Synthesis
SKB contains two incredibly polished prompt templates designed to convert raw transcriptions and frame OCRs into a beautifully structured, categorized knowledge base:

#### A. One-Video Synthesis (`prompts/build-notes.md`)
Converts Whisper transcripts and extracted frame OCRs into a clean Markdown note containing:
- YAML Frontmatter: metadata (title, category, tags, duration, original link).
- Section 1: Executive Summary.
- Section 2: Core Takeaways & Insights (with precise timestamps).
- Section 3: Word-by-word text or frame descriptions.

#### B. Incremental Synthesizer (`prompts/synthesize-overview.md`)
When dealing with hundreds of videos, reading individual notes is tedious. SKB solves this by compiling a global `OVERVIEW.md` index through an **incremental Map-Reduce** pipeline:
1. It reads the YAML frontmatter and categories of all existing notes.
2. It prompts the LLM to categorize the files into structural themes.
3. It incrementally compiles/updates `docs/OVERVIEW.md` by writing deep analyses of each category, referencing individual notes with links (e.g., `[Title](notes/post_id.md)`).
4. If new videos are ingested, only the newly added frontmatters are mapped, and the existing `OVERVIEW.md` is updated in-place without rewriting everything from scratch.

*Why this is useful for DVL (Task `DNK-VIDEO-005`):*
We can directly adopt this map-reduce pattern to generate high-quality knowledge maps of Maxim's video archive in SCONES Memory, ensuring a single unified overview of all concepts, talks, or B-roll reels is always up to date.

---

### 🎨 3.4. Next.js 16 + Tailwind 4 Frontend Dashboard
The user interface of SKB is built using modern Next.js, featuring:
- A real-time Ingestion / Import queue showing active jobs, logs, and speeds.
- A semantic Search Bar with multilingual query matching.
- A **Note Reader Card** which renders the generated markdown note alongside a custom HTML5 Video Player.
- **Timestamp Jumping**: Clicking any timestamp in the markdown note (e.g., `01:23`) dynamically jumps the video player to that exact millisecond.

*Why this is useful for DVL:*
This exactly maps to the user experience needed for our `apps/web/` video dashboard in DNK OS. We can port the interactive markdown renderer with timestamp click-to-seek triggers directly into our Svelte/React components.

---

## ⚡ 4. Swarm Assimilation Mapping & Integration Blueprint

We can directly assimilate these open-source patterns into our workspace.

```
       [Raw Video Assets Ingested]
                   |
                   v
     [core/media/audio_extractor.py]
                   |  (Opus/MP3 audio extracted)
                   v
     [core/media/stt_transcribe.py] <---> [Check Local Sidecars (TXT/VTT/JSON)]
                   |  (New Transcription via Gemini / Whisper)
                   v
     [SCONES Memory / SQLite Manifest] <--- (Stores metadata & timestamps)
                   |
                   v
     [core/media/auto_cut_cleaner.py]
                   |  (Generates Keep Ranges & Removes Silence)
                   v
     [Map-Reduce Synthesizer Prompt] 
                   |
                   +---> Individual Video Notes (`docs/footage/`)
                   +---> Incremental `docs/footage/OVERVIEW.md`
```

### 💻 4.1. Actionable Code Assimilation Examples

We will build the DVL ingestion pipeline adopting SKB's sidecar-caching and state-manifest protocols.

#### A. Sidecar Check & Write Protocol
When `stt_transcribe.py` is invoked, it should first search for a local sidecar JSON. If found, it parses it instantly:

```python
# core/media/stt_transcribe.py (Proposed Implementation)
import os
import json
from pathlib import Path

class GeminiTranscriber:
    def __init__(self, cache_dir: str = "assets/transcripts/"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def transcribe(self, audio_path: str, media_hash: str) -> dict:
        """Transcribes audio, caching results in sidecar files to prevent redundant API bills."""
        sidecar_json = self.cache_dir / f"{media_hash}.json"
        
        # Check cache
        if sidecar_json.exists():
            print(f"[CACHE HIT] Loading cached transcription sidecar: {sidecar_json}")
            with open(sidecar_json, "r") as f:
                return json.load(f)
                
        # Cache Miss -> Execute API call (e.g., Gemini 3.5 or Whisper)
        print(f"[CACHE MISS] Executing transcription for {audio_path}")
        result = self._call_transcription_api(audio_path)
        
        # Write sidecars
        self._write_sidecars(media_hash, result)
        return result
        
    def _write_sidecars(self, media_hash: str, result: dict):
        sidecar_json = self.cache_dir / f"{media_hash}.json"
        sidecar_txt = self.cache_dir / f"{media_hash}.txt"
        sidecar_vtt = self.cache_dir / f"{media_hash}.vtt"
        
        # Write structured JSON
        with open(sidecar_json, "w") as f:
            json.dump(result, f, indent=2)
            
        # Write plain text
        with open(sidecar_txt, "w") as f:
            f.write(result.get("text", ""))
            
        # Generate VTT format subtitles
        vtt_content = self._to_vtt(result.get("segments", []))
        with open(sidecar_vtt, "w") as f:
            f.write(vtt_content)
```

#### B. Map-Reduce Incremental Synthesizer Schema
We can write a pipeline in `scripts/system/` that reads markdown notes frontmatters and compiles a beautiful structured roadmap index:

```python
# core/media/knowledge_synthesizer.py (Proposed Implementation)
import os
import yaml
from pathlib import Path

def synthesize_media_overview(notes_dir: str, output_path: str):
    """Parses frontmatter of all video notes and builds an incremental OVERVIEW.md."""
    notes_path = Path(notes_dir)
    collected_metadata = []
    
    for note_file in notes_path.glob("*.md"):
        if note_file.name == "OVERVIEW.md":
            continue
        try:
            with open(note_file, "r") as f:
                content = f.read()
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    meta = yaml.safe_load(parts[1])
                    meta["filename"] = note_file.name
                    collected_metadata.append(meta)
        except Exception as e:
            print(f"Error parsing {note_file}: {e}")
            
    # Decompose into LLM synthesis prompt
    prompt = f"""
    You are compiling a Master Overview for a Video Archive.
    Here is the catalog of currently ingested videos:
    {yaml.dump(collected_metadata)}
    
    Group them into logical themes and write a high-fidelity Markdown OVERVIEW.md index
    with backlinks referencing [Title](notes/filename.md) and summarizing key lessons.
    """
    
    # We call our LLM agent to synthesize and then write the output_path
    print(f"Synthesizing overview for {len(collected_metadata)} videos...")
```

---

## 🚀 5. Concrete Action Items for DNK Video Librarian

To maximize the benefits of this audit, Gerych Prime and the specialized subagents will execute the following integrations:

1. **Step 1: Manifest Alignment (Phase 1)**
   Adapt SKB's SQLite metadata tables as our baseline manifest. Integrate this schema directly into our ` footage` DB representation inside SCONES.
2. **Step 2: Dual-Backend Transcriber (Phase 2)**
   Implement `stt_transcribe.py` utilizing **Gemini 3.5 Transcribe API** as primary backend, with a fallback to SKB's localized **`faster-whisper` GPU container pipeline** for high-volume offline processing.
3. **Step 3: Sidecar Subtitle Caching (Phase 2 & 3)**
   Make sidecar files (`.vtt`, `.txt`, `.json`) a strict invariant in our audio pipeline. `auto_cut_cleaner.py` will read the JSON sidecar to construct silence-cut boundaries and keep_ranges.
4. **Step 4: Interactive Web Dashboard (Phase 5)**
   Use Next.js + Tailwind + HTML5 timestamp binding triggers in `apps/web/` to allow Maxim to search SCONES, view notes, and seek directly inside his raw recordings.
