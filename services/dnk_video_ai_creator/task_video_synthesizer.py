# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/task_video_synthesizer.py"
# purpose: "Grounded 1-Click Marketing Video & Remotion 9:16 Schema Synthesizer for Completed Tasks"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("dnk.video.task_synthesizer")


class MarketingVideoScene(BaseModel):
    id: str = Field(..., description="Unique scene identifier")
    title: str = Field(..., description="Headline of the scene")
    subtitle: str = Field(..., description="Supporting caption or script fragment")
    duration_frames: int = Field(..., description="Duration of scene in frames (30fps)")
    bg_gradient: str = Field(..., description="CSS linear-gradient background")
    accent_color: str = Field(..., description="Hex accent color for typography and highlights")


class MarketingVideoPayload(BaseModel):
    composition_id: str = Field(..., description="Remotion composition ID")
    aspect_ratio: str = Field(default="9:16", description="Video aspect ratio (vertical 9:16)")
    duration_in_frames: int = Field(default=480, description="Total duration in frames (16s at 30fps)")
    fps: int = Field(default=30, description="Frames per second")
    scenes: List[MarketingVideoScene] = Field(default_factory=list, description="Ordered scene timeline")
    voiceover_script: str = Field(..., description="Cohesive TTS narration script")
    grounded_diffs_summary: List[str] = Field(default_factory=list, description="List of altered files grounded in git artifacts")


class TaskVideoSynthesizer:
    """
    Synthesizes grounded 9:16 vertical marketing videos for completed tasks.
    Extracts structured 4-scene storyboards (Hook -> Problem -> Solution -> CTA)
    directly from Task acceptance criteria, descriptions, and code artifacts.
    """

    def __init__(self) -> None:
        pass

    def synthesize_task_marketing_script(
        self,
        node_id: str,
        node: Any,
        artifacts: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes a 16-second (480 frames at 30 fps) 9:16 vertical video storyboard
        for a task node.
        
        Timeline:
          1. Hook (0-3s, 90 frames): Grabs attention with the breakthrough/feature.
          2. Problem (3-7s, 120 frames): Details user/business pain point.
          3. Solution (7-13s, 180 frames): Concrete solution grounded in acceptance criteria & files.
          4. CTA (13-16s, 90 frames): Call to action to test or launch.
        """
        node_title = getattr(node, "title", "Feature Update")
        node_desc = getattr(node, "description", "").strip()
        acceptance_criteria = list(getattr(node, "acceptance_criteria", []) or [])
        target_files = list(getattr(node, "target_files", []) or [])

        def _extract_file_path(item: Any) -> str:
            if isinstance(item, str):
                return item
            if isinstance(item, dict):
                return str(item.get("path") or item.get("file_path") or "")
            for attr in ("path", "file_path", "filename", "name"):
                val = getattr(item, attr, None)
                if val and isinstance(val, str):
                    return val
            return ""

        # Extract files from artifacts if available
        grounded_files: List[str] = []
        if artifacts is not None:
            files_list = []
            if hasattr(artifacts, "files"):
                files_list = getattr(artifacts, "files", []) or []
            elif isinstance(artifacts, dict) and "files" in artifacts:
                files_list = artifacts.get("files", []) or []
            grounded_files = [_extract_file_path(f) for f in files_list]

        if not grounded_files:
            grounded_files = [_extract_file_path(f) for f in target_files]

        grounded_files = [f for f in grounded_files if f]

        # 1. Hook Scene (0-3s, 90 frames)
        hook_title = f"🚀 {node_title}"
        hook_sub = "Big update just landed in DNK OS!" if not node_desc else f"Stop wasting hours: {node_title} is here."

        # 2. Problem Scene (3-7s, 120 frames)
        problem_title = "The Bottleneck"
        if node_desc:
            # Clean up and shorten description for vertical card
            clean_desc = node_desc.split("\n")[0]
            problem_sub = clean_desc if len(clean_desc) <= 120 else f"{clean_desc[:117]}..."
        else:
            problem_sub = "Manual workflows and fragmented tools were holding back progress."

        # 3. Solution Scene (7-13s, 180 frames)
        solution_title = "The Solution"
        if acceptance_criteria:
            criteria_summary = " • " + " • ".join(acceptance_criteria[:3])
            if len(criteria_summary) > 160:
                criteria_summary = f"{criteria_summary[:157]}..."
            solution_sub = f"Delivered: {criteria_summary}"
        else:
            solution_sub = f"Automated execution completed with certified code changes across {len(grounded_files)} files."

        if grounded_files and len(solution_sub) < 120:
            file_sample = ", ".join([f.split("/")[-1] for f in grounded_files[:3]])
            solution_sub += f" (Files: {file_sample})"

        # 4. CTA Scene (13-16s, 90 frames)
        cta_title = "Ready to Ship?"
        cta_sub = "Experience autonomous high-velocity execution live on DNK OS!"

        # Build 4 Scenes
        scenes = [
            MarketingVideoScene(
                id="scene_hook",
                title=hook_title,
                subtitle=hook_sub,
                duration_frames=90,
                bg_gradient="linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)",
                accent_color="#6366f1",
            ),
            MarketingVideoScene(
                id="scene_problem",
                title=problem_title,
                subtitle=problem_sub,
                duration_frames=120,
                bg_gradient="linear-gradient(135deg, #2e1065 0%, #3b0764 100%)",
                accent_color="#a855f7",
            ),
            MarketingVideoScene(
                id="scene_solution",
                title=solution_title,
                subtitle=solution_sub,
                duration_frames=180,
                bg_gradient="linear-gradient(135deg, #064e3b 0%, #065f46 100%)",
                accent_color="#10b981",
            ),
            MarketingVideoScene(
                id="scene_cta",
                title=cta_title,
                subtitle=cta_sub,
                duration_frames=90,
                bg_gradient="linear-gradient(135deg, #7c2d12 0%, #9a3412 100%)",
                accent_color="#f97316",
            ),
        ]

        # Build Voiceover Script
        voiceover_parts = [
            f"Attention builders! {hook_sub}",
            f"Here is the challenge: {problem_sub}",
            f"Here is our breakthrough: {solution_sub}.",
            f"Verified and certified across {len(grounded_files)} components.",
            f"{cta_sub}",
        ]
        voiceover_script = " ".join(voiceover_parts)

        payload = MarketingVideoPayload(
            composition_id=f"comp_task_{node_id}",
            aspect_ratio="9:16",
            duration_in_frames=480,
            fps=30,
            scenes=scenes,
            voiceover_script=voiceover_script,
            grounded_diffs_summary=grounded_files,
        )

        return payload.model_dump()
