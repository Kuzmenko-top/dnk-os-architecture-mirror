# --- DNK-MRH-HEADER ---
# mrh_id: "core/voice/ukrainian_acoustic.py"
# purpose: "Ukrainian Acoustic Processor & Phonetic Voice Command Intent Classifier for Gerych Swarm."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-VOICE-FLOW-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import re
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("dnk.voice.ukrainian_acoustic")


class VoiceCommandIntent(BaseModel):
    raw_text: str
    cleaned_text: str
    intent_action: str
    target_agent: str
    confidence: float
    parameters: Dict[str, Any] = Field(default_factory=dict)
    feedback_phrase_ua: str


class UkrainianVoiceProcessor:
    """
    Phonetic pre-processor, dialect normalizer, and Swarm Intent Classifier
    specifically tuned for Ukrainian spoken language with technical terminology.
    """

    # Common spoken Ukrainian filler prefixes
    FILLER_PREFIXES = [
        r"^герич[\s,]+",
        r"^слухай[\s,]+",
        r"^привіт[\s,]+герич[\s,]+",
        r"^будь[\s-]+ласка[\s,]+",
        r"^значить[\s,]+",
        r"^коротше[\s,]+",
        r"^ану[\s,]+",
        r"^ну[\s,]+",
        r"^слухай[\s,]+сюди[\s,]+",
    ]

    # Technical term mapping for typical Ukrainian spoken transliterations
    PHONETIC_REPLACEMENTS = [
        (r"\bлайкхаус\b", "лейкхаус"),
        (r"\bлакехаус\b", "лейкхаус"),
        (r"\bшопіфай\b", "shopify"),
        (r"\bшопіфайний\b", "shopify"),
        (r"\bрілс\b", "reels"),
        (r"\bрілси\b", "reels"),
        (r"\bтіктоки\b", "tiktok"),
        (r"\bтікток\b", "tiktok"),
        (r"\bремоушн\b", "remotion"),
        (r"\bремоушен\b", "remotion"),
        (r"\bлікуід\b", "liquid"),
        (r"\bліквід\b", "liquid"),
        (r"\bдакдб\b", "duckdb"),
        (r"\bдекдб\b", "duckdb"),
    ]

    def __init__(self) -> None:
        self.logger = logger

    def clean_ukrainian_transcript(self, raw_transcript: str) -> str:
        """
        Cleans filler words, standardizes dialectal patterns, and applies phonetic replacements.
        """
        if not raw_transcript:
            return ""

        text = raw_transcript.strip().lower()

        # Remove filler prefixes
        for pattern in self.FILLER_PREFIXES:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Apply technical phonetic replacements
        for pattern, replacement in self.PHONETIC_REPLACEMENTS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Normalize whitespace and punctuation
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def parse_voice_command(self, raw_transcript: str) -> VoiceCommandIntent:
        """
        Classifies Ukrainian voice command into a structured Swarm Intent.
        """
        cleaned = self.clean_ukrainian_transcript(raw_transcript)
        text_lower = cleaned.lower()

        # 1. Video & Remotion Generation
        if any(w in text_lower for w in ["відео", "reels", "tiktok", "ремоушн", "remotion", "ролик", "анімаці"]):
            return VoiceCommandIntent(
                raw_text=raw_transcript,
                cleaned_text=cleaned,
                intent_action="render_remotion_video",
                target_agent="dnk_video_ai_creator",
                confidence=0.92,
                parameters={"prompt": cleaned, "format": "9:16"},
                feedback_phrase_ua="Прийнято, Максиме! Передаю завдання агенту dnk_video_ai_creator для створення 9:16 Remotion ролика."
            )

        # 2. Lakehouse / BI Analytics
        if any(w in text_lower for w in ["лейкхаус", "duckdb", "дохід", "виручк", "статистик", "аналітик", "продаж", "замовленн"]):
            return VoiceCommandIntent(
                raw_text=raw_transcript,
                cleaned_text=cleaned,
                intent_action="query_lakehouse_analytics",
                target_agent="dnk_analytics",
                confidence=0.95,
                parameters={"question": cleaned},
                feedback_phrase_ua="Запускаю асинхронний запит у DuckDB Lakehouse для розрахунку аналітики."
            )

        # 3. Canvas & UI Screen Building
        if any(w in text_lower for w in ["екран", "дизайн", "інтерфейс", "кнопк", "скрін", "карточк", "canvas"]):
            return VoiceCommandIntent(
                raw_text=raw_transcript,
                cleaned_text=cleaned,
                intent_action="generate_canvas_screen",
                target_agent="gerych_builder",
                confidence=0.90,
                parameters={"design_prompt": cleaned},
                feedback_phrase_ua="Зрозумів! gerych_builder береться за генерацію нового вузла в Spatial Canvas."
            )

        # 4. Security & Adversarial Audit
        if any(w in text_lower for w in ["аудит", "безпек", "перевір", "тест", "скан"]):
            return VoiceCommandIntent(
                raw_text=raw_transcript,
                cleaned_text=cleaned,
                intent_action="run_adversarial_audit",
                target_agent="gerych_auditor",
                confidence=0.94,
                parameters={"scope": cleaned},
                feedback_phrase_ua="Запускаю червону команду gerych_auditor для перевірки безпеки та тестів."
            )

        # 5. Shopify E-Commerce
        if any(w in text_lower for w in ["shopify", "liquid", "магазин", "товар", "корзин", "чекаут"]):
            return VoiceCommandIntent(
                raw_text=raw_transcript,
                cleaned_text=cleaned,
                intent_action="build_shopify_theme",
                target_agent="dnk_shopify",
                confidence=0.91,
                parameters={"theme_prompt": cleaned},
                feedback_phrase_ua="Делегую агенту dnk_shopify для модифікації Liquid шаблонів та вітрини."
            )

        # Default: Prime Swarm Dispatch
        return VoiceCommandIntent(
            raw_text=raw_transcript,
            cleaned_text=cleaned,
            intent_action="general_swarm_dispatch",
            target_agent="gerych_prime",
            confidence=0.85,
            parameters={"prompt": cleaned},
            feedback_phrase_ua="Слухаю і виконую, Максиме! Розгортаю спільну координацію рою."
        )
