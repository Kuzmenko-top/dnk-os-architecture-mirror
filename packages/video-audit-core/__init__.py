# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/__init__.py"
# purpose: "Unified public entry point for @dnk/video-audit-core containing all workers and the orchestrator."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any
from .transcription_adapter import WhisperXAdapter
from .scene_extraction_worker import SceneExtractionWorker
from .ocr_worker import OCRWorker
from .audio_feature_worker import AudioFeatureWorker
from .hook_retention_analysis import HookRetentionAnalyzer
from .claim_verification import ClaimVerificationEngine

__all__ = [
    "WhisperXAdapter",
    "SceneExtractionWorker",
    "OCRWorker",
    "AudioFeatureWorker",
    "HookRetentionAnalyzer",
    "ClaimVerificationEngine",
    "VideoAuditOrchestrator"
]

class VideoAuditOrchestrator:
    """
    Main orchestrator for @dnk/video-audit-core, running transcription, scene extraction,
    OCR text overlays, audio feature metrics, hook analysis, and claim verification in tandem.
    """
    def __init__(self):
        self.transcriber = WhisperXAdapter()
        self.scenes = SceneExtractionWorker()
        self.ocr = OCRWorker()
        self.audio = AudioFeatureWorker()
        self.hook = HookRetentionAnalyzer()
        self.claims = ClaimVerificationEngine()

    async def execute_full_audit(self, video_source: str, language: str = "uk") -> Dict[str, Any]:
        """
        Executes a complete multimodal video audit across all layers of the creative.
        """
        # Run all pipeline stages
        trans_res = await self.transcriber.transcribe_video(video_source, language=language)
        scenes_res = await self.scenes.extract_scenes(video_source)
        ocr_res = await self.ocr.extract_screen_text(video_source)
        audio_res = await self.audio.analyze_audio(video_source)
        
        # Analyze Hook and Claims using outputs of prior stages
        hook_res = await self.hook.analyze_hook(trans_res, scenes_res, ocr_res, audio_res)
        claims_res = await self.claims.verify_claims(trans_res, ocr_res)

        return {
            "success": True,
            "video_source": video_source,
            "language": language,
            "transcription": trans_res,
            "scenes": scenes_res,
            "ocr": ocr_res,
            "audio": audio_res,
            "hook_analysis": hook_res,
            "claim_verification": claims_res
        }
