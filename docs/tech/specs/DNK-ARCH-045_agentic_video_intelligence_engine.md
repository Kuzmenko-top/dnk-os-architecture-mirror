# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-045_agentic_video_intelligence_engine.md"
# purpose: "Technical Architecture Specification for DNK OS Agentic Video Understanding Engine."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-AGENTIC-VIDEO-ENGINE"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

# 📐 DNK-ARCH-045: Agentic Video Intelligence Engine Specification

## 1. Scope & Objective
This specification formalizes the incorporation of Google's Gemini Agentic Video Understanding (`gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.6-flash`) into the DNK OS ecosystem. The objective is to replace brute-force static video frame sampling with dynamic, self-navigating visual intelligence across all video processing pipelines.

## 2. Architecture & Domain Topology

### 2.1 Hexagonal Architecture Ports & Adapters
```
+-------------------------------------------------------------+
|                      Domain Layer                           |
|  - VideoCompositionService (services/dnk_video_ai_creator)   |
|  - StitchCanvasVideoInspector (visual_shell/open_design)    |
|  - ShopifyUgcAuditor (services/dnk_shopify)                 |
+-------------------------------------------------------------+
                              |
                     [Uses Abstract Port]
                              v
+-------------------------------------------------------------+
|                 DNKAgenticVideoPort (Core)                  |
|  + analyze_video(uri, prompt, mode) -> VideoAnalysisResult   |
|  + retrieve_moments(uri, targets) -> list[MomentReference]  |
|  + generate_smart_chapters(uri) -> list[VideoChapter]       |
|  + detect_anomalies(uri, rules) -> list[AnomalyDetection]   |
+-------------------------------------------------------------+
                              |
                    [Implements Adapter]
                              v
+-------------------------------------------------------------+
|               DNKAgenticVideoAdapter                        |
|  (core/adapters/dnk_agentic_video_adapter.py)               |
|  - Connects to Google GenAI Interactions API                |
|  - Handles URI resolution (gs://, youtube, files API)       |
|  - Supports transparent trace streaming (thoughts/calls)     |
|  - Built-in Mock Mode for Zero-Cost Hermetic CI Testing     |
+-------------------------------------------------------------+
```

## 3. Data Transfer Objects (DTOs)

```python
class ProcessingMode(str, Enum):
    AGENTIC = "agentic"
    STATIC = "static"

class VideoSegmentRef(BaseModel):
    start_timestamp: str  # "MM:SS" or "HH:MM:SS"
    end_timestamp: str
    description: str
    confidence: float = 1.0

class VideoChapter(BaseModel):
    title: str
    start_time: str
    summary: str

class VideoStepTrace(BaseModel):
    step_type: str  # thought | processing_call | processing_result | model_output
    summary: Optional[str] = None
    signature: Optional[str] = None

class VideoAnalysisResult(BaseModel):
    summary: str
    processing_mode: ProcessingMode
    tokens_consumed: int
    steps_trace: list[VideoStepTrace] = []
    moments: list[VideoSegmentRef] = []
    chapters: list[VideoChapter] = []
```

## 4. Operational Invariants
1. **Adaptive Mode Selection**:
   - Short clips (< 180s) or uniform temporal scans -> Static mode (1 FPS).
   - Long-form lectures, streams, podcasts, unboxings (> 180s) -> Agentic mode (token savings up to 88%).
2. **Grounded Timestamp Integrity**:
   - Every identified moment or chapter MUST cite a valid temporal interval (`MM:SS`).
3. **Trace Streamability**:
   - The UI must be able to visualize the agent's internal reasoning loop (`thought` -> `processing_call` -> `processing_result`).
4. **Hermetic CI Execution**:
   - When no Google API Key is provided, the adapter operates in deterministic mock mode without network calls.
