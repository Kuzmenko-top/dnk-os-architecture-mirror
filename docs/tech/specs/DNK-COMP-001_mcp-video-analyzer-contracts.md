# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tech_specs_DNK-COMP-001"
# purpose: "Component Contracts & Pydantic Schemas for mcp-video-analyzer assimilation"
# author: "Gerych (Hermes Prime)"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# --- END DNK-MRH-HEADER ---

# 📝 Component Contracts: mcp-video-analyzer (DNK-COMP-001)

- **System Context**: `services/dnk_video_ai_creator`
- **Specification Type**: Structural Component Port Specifications
- **Target Language**: Python 3.12 (Pydantic v2)

---

## 🧩 1. Data Transfer Objects (DTOs)

To assimilate `mcp-video-analyzer` patterns into our Python-based `dnk_video_ai_creator` service, we define the following Pydantic schemas:

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class TranscriptEntry(BaseModel):
    timestamp: str = Field(..., description="Timestamp in hh:mm:ss format or mm:ss format")
    text: str = Field(..., description="Transcribed spoken words at this segment")

class FrameMetadata(BaseModel):
    timestamp: float = Field(..., description="Precise time offset in seconds")
    frame_index: int = Field(..., description="Sequential index of the frame")
    file_path: str = Field(..., description="Local path to the optimized frame JPEG")
    dhash: str = Field(..., description="64-bit dHash string representing visual fingerprint")
    ocr_text: Optional[str] = Field(None, description="Extracted OCR text if applicable")

class LoomVideoMetadata(BaseModel):
    id: str = Field(..., description="Loom Video ID")
    title: str = Field(..., description="Title of the Loom video")
    duration: float = Field(..., description="Duration in seconds")
    captions_url: Optional[str] = Field(None, description="GraphQL URL pointing to WebVTT captions")
    stream_url: Optional[str] = Field(None, description="Direct CDN streaming URL for video segments")
```

---

## 🔌 2. Port Definitions (Abstract Service Interfaces)

We establish clear boundaries for the components we are assimilating. These interfaces act as Python abstract base classes (ABCs) that can be plugged into our FastAPI backend or orchestrator:

```python
from abc import ABC, abstractmethod

class VideoTranscriptionPort(ABC):
    @abstractmethod
    def extract_audio(self, video_path: str) -> str:
        """Extract audio track from video and save as a high-fidelity WAV file."""
        pass

    @abstractmethod
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> List[TranscriptEntry]:
        """Transcribe audio track using the optimal local or API-based model."""
        pass


class FrameAnalysisPort(ABC):
    @abstractmethod
    def extract_keyframes(self, video_path: str, threshold: float = 0.4) -> List[FrameMetadata]:
        """Extract high-interest frames matching scene change threshold using FFmpeg select filters."""
        pass

    @abstractmethod
    def extract_frame_at(self, video_path: str, timestamp_s: float) -> FrameMetadata:
        """Extract a high-fidelity frame at a precise timestamp using rapid seek (-ss)."""
        pass

    @abstractmethod
    def deduplicate_frames(self, frames: List[FrameMetadata], max_distance: int = 10) -> List[FrameMetadata]:
        """Filter out visually similar frames using Hamming distance on dHash values."""
        pass


class LoomScraperPort(ABC):
    @abstractmethod
    def fetch_loom_metadata(self, video_id: str) -> LoomVideoMetadata:
        """Retrieve video details and WebVTT transcript URL directly from Loom GraphQL."""
        pass

    @abstractmethod
    def parse_webvtt_transcript(self, webvtt_url: str) -> List[TranscriptEntry]:
        """Download and parse a WebVTT file into standard TranscriptEntry objects."""
        pass
```
