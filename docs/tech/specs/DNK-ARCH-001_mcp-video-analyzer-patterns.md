# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tech_specs_DNK-ARCH-001"
# purpose: "SOTA Architectural Specification & Pattern Map of mcp-video-analyzer"
# author: "Gerych (Hermes Prime)"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# --- END DNK-MRH-HEADER ---

# 🗺️ Architecture Specification: mcp-video-analyzer (DNK-ARCH-001)

- **System Context**: `services/dnk_video_ai_creator`
- **Core Design Pattern**: Event-Driven Multi-Modal MCP Adapter
- **Revision**: 1.0.0

---

## 🏗️ 1. Processing Topology

The architecture of `mcp-video-analyzer` follows a classic layered adapter pattern, wrapping low-level media and network drivers into a unified MCP JSON-RPC interface:

```
                      +-------------------+
                      |   AI Client LLM   |
                      +---------+---------+
                                |
                    JSON-RPC    | (Stdio)
                                v
                      +-------------------+
                      |    MCP Server     |  (server.ts / index.ts)
                      +---------+---------+
                                |
         +----------------------+----------------------+
         |                                             |
         v                                             v
+------------------+                          +------------------+
|   Processors     |                          |     Adapters     |
+--------+---------+                          +--------+---------+
         |                                             |
         +--> AudioTranscriber (audio-transcriber.ts)  +--> LoomAdapter (loom.adapter.ts)
         +--> FrameExtractor   (frame-extractor.ts)   +--> YtDlpAdapter (ytdlp.adapter.ts)
         +--> FrameDedup       (frame-dedup.ts)       +--> TwelveLabsAdapter (twelvelabs.adapter.ts)
         +--> FrameOCR         (frame-ocr.ts)
         |
         v
+------------------+
|  Native Engines  |
+--------+---------+
         |
         +--> FFmpeg (ffmpeg-static)
         +--> Sharp (libvips)
         +--> Tesseract.js
```

---

## 🚦 2. The Paradigm Shift: Static vs Agentic Video Understanding

Our active development in `services/dnk_video_ai_creator` implements the SOTA **Gemini Agentic Video Understanding** model (released September 1, 2026). It is critical to compare how `mcp-video-analyzer`'s traditional approach compares to this next-generation paradigm:

### A. The Static Paradigm (mcp-video-analyzer default)
- **Concept**: Rigorous bulk parsing. Upon receiving a video, it runs ffmpeg to extract frames at a dense interval (e.g. 1 FPS) or extracts all scene-changes, dedupes them, runs OCR on every surviving frame, and compiles an "Annotated Timeline" which is dumped into the LLM context.
- **Pros**: Zero real-time model interaction during processing; completely deterministic.
- **Cons**: High token waste (floods context with OCR and images), expensive API spend (unnecessary Whisper and GPT-4o-mini calls), slow processing times (heavy image scaling and disk I/O).

### B. The Agentic Paradigm (Gemini-Agentic & DNK OS Hybrid)
- **Concept**: Timeline navigation loop. The AI model receives *only* the low-token audio transcript first. The agent then navigates the timeline dynamically, pinpointing timestamps of interest, and retrieves specific visual context on-the-fly.
- **Pros**: **88% reduction in token usage**, **66% cost reduction**, higher visual reasoning accuracy, much faster initial response.
- **Cons**: Requires active execution tools (`get_frame_at`, `get_frame_burst`) during the reasoning turn.

### 🌟 Synthesis: The Perfect Hybrid
By exposing granular tools like `get_transcript`, `get_frame_at`, and `get_frame_burst`, `mcp-video-analyzer` provides the exact toolkit we need. Rather than running the monolithic `analyze_video` tool (which uses the Static paradigm), we can program our swarm agents to use the granular tools to run a **highly optimized Agentic Video Exploration Loop**!

---

## ⚡ 3. Loom GraphQL Sequence Flow

The Loom integration is an architectural gem. It uses a secure, public-facing GraphQL API to gather video data with near-instant speeds:

```
[AI Client]            [Loom Adapter]           [Loom GraphQL API]         [Loom CDN]
     |                       |                          |                       |
     |--- Get Loom Info ---->|                          |                       |
     |    (Video ID)         |--- POST GraphQL Query -->|                       |
     |                       |    (GetVideo, etc.)      |                       |
     |                       |                          |                       |
     |                       |<-- Return Metadata ------|                       |
     |                       |    (Name, Captions URL)  |                       |
     |                       |                                                  |
     |                       |--- Download WebVTT (Zero-Cost Transcript) ------>|
     |                       |<-- Return WebVTT Content ------------------------|
     |                       |                                                  |
     |<-- Complete Context --|                                                  |
     |    (Metadata + Text)  |                                                  |
```

This bypasses all heavy machine learning costs for screen recordings hosted on Loom, providing instantaneous visual metadata and textual transcription.
