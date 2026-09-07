# --- DNK-MRH-HEADER ---
# mrh_id: "core/voice/__init__.py"
# purpose: "Package entrypoint for DNK OS Ukrainian Voice Flow & Acoustic Command Processor."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-VOICE-FLOW-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

from .ukrainian_acoustic import UkrainianVoiceProcessor, VoiceCommandIntent

__all__ = ["UkrainianVoiceProcessor", "VoiceCommandIntent"]
