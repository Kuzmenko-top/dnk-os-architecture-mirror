# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/video_composition_schema.py"
# purpose: "AST DSL schema definition for Video Composition, Tracks, Clips, Keyframes and Transitions."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

"""
Video Composition Schema AST DSL for dnk_video_ai_creator.
Pydantic V2 definitions for video compositions.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class EasingType(str, Enum):
    """Supported easing types for keyframe interpolation and transitions."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BEZIER = "bezier"
    SPRING = "spring"
    QUAD_IN = "quad_in"
    QUAD_OUT = "quad_out"
    QUAD_IN_OUT = "quad_in_out"
    CUBIC_IN = "cubic_in"
    CUBIC_OUT = "cubic_out"
    CUBIC_IN_OUT = "cubic_in_out"


class ClipType(str, Enum):
    """Types of media or renderable clips on a track."""
    TEXT = "text"
    CANVAS = "canvas"
    SVG = "svg"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"


class TransitionType(str, Enum):
    """Supported transition effects between clips."""
    NONE = "none"
    FADE = "fade"
    CROSSFADE = "crossfade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    GLITCH = "glitch"
    KINETIC_ZOOM = "kinetic_zoom"


class Keyframe(BaseModel):
    """Individual keyframe for property animation."""
    model_config = ConfigDict(extra="forbid")

    frame: int = Field(..., ge=0, description="0-based relative frame number within clip")
    value: Union[float, int, str, List[Union[float, int]], Dict[str, Any]] = Field(
        ..., description="Value at this keyframe (number, string/hex color, list, or dict)"
    )
    easing: EasingType = Field(default=EasingType.LINEAR, description="Easing function to target keyframe")
    easing_params: Optional[Dict[str, float]] = Field(
        default=None, description="Optional parameters for bezier (x1, y1, x2, y2) or spring (stiffness, damping, mass)"
    )


class AnimatedProperty(BaseModel):
    """Collection of keyframes animating a single property."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Property name (e.g. position_x, opacity, scale, rotation)")
    keyframes: List[Keyframe] = Field(..., min_length=1, description="List of keyframes sorted by frame")


class Clip(BaseModel):
    """Renderable or playable element placed on a track."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique clip identifier")
    clip_type: ClipType = Field(..., description="Clip media/render type")
    start_frame: int = Field(..., ge=0, description="Start frame relative to timeline start")
    duration_frames: int = Field(..., gt=0, description="Clip duration in frames")
    layer: int = Field(default=0, ge=0, description="Z-index layer order for rendering")
    src: Optional[str] = Field(default=None, description="Source URL or relative file path for media/svg/fonts")
    content: Optional[str] = Field(default=None, description="Text string, raw SVG XML, or kinetic payload")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Static property key-values (e.g. x, y, width, height, color, font_family)"
    )
    animated_properties: Dict[str, AnimatedProperty] = Field(
        default_factory=dict, description="Animated properties keyed by property name"
    )
    volume: float = Field(default=1.0, ge=0.0, le=2.0, description="Audio volume multiplier for audio/video clips")


class Transition(BaseModel):
    """Transition effect connecting two clips on the same track or overlay."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique transition identifier")
    transition_type: TransitionType = Field(..., description="Type of visual transition effect")
    from_clip_id: str = Field(..., description="Source clip ID")
    to_clip_id: str = Field(..., description="Target clip ID")
    duration_frames: int = Field(..., gt=0, description="Duration of transition overlap in frames")
    easing: EasingType = Field(default=EasingType.LINEAR, description="Transition blend curve easing")
    params: Dict[str, Any] = Field(default_factory=dict, description="Effect specific parameter overrides")


class Track(BaseModel):
    """Ordered sequence of clips of a common media kind."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique track identifier")
    name: str = Field(..., description="Human readable track label")
    kind: str = Field(default="video", description="Kind of track: video, audio, or overlay")
    clips: List[Clip] = Field(default_factory=list, description="List of clips assigned to this track")


class VideoCompositionSchema(BaseModel):
    """Root AST DSL for a complete video composition project."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique composition ID")
    title: str = Field(default="Untitled Video", description="Composition title")
    width: int = Field(default=1920, gt=0, description="Canvas width in pixels")
    height: int = Field(default=1080, gt=0, description="Canvas height in pixels")
    fps: int = Field(default=30, description="Target frame rate (must be 24, 30, or 60)")
    duration_frames: int = Field(..., gt=0, description="Total composition duration in frames")
    background_color: str = Field(default="#000000", description="Canvas background color hex")
    tracks: List[Track] = Field(default_factory=list, description="Ordered list of timeline tracks")
    transitions: List[Transition] = Field(default_factory=list, description="Active transitions between clips")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata and render settings")
