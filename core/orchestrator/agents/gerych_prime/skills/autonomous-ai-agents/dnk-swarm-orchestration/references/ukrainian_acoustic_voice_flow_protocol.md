# --- DNK-MRH-HEADER ---
# mrh_id: "references/ukrainian_acoustic_voice_flow_protocol.md"
# purpose: "Ukrainian Acoustic Voice Processing, Phonetic Normalization & Swarm Intent Routing Protocol."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🎙️ Ukrainian Acoustic Voice Flow & Swarm Intent Routing Protocol

## 🎯 Architecture & Objective
Voice interaction in DNK OS allows Maxim to command swarms directly using natural Ukrainian speech from browser UI (`StitchPromptDock`) or mobile devices. However, spoken Ukrainian often contains phonetic variations, surzhyk, colloquial filler words, and Ukrainian transliterations of English engineering terms (e.g. "шопіфай", "лайкхаус", "ремоушн", "субагенти").

This protocol standardizes:
1. **Phonetic Normalization**: Cleaning filler particles ("слухай", "герич", "будь ласка", "коротше") and mapping phonetic variants to canonical terms.
2. **Deterministic Intent Classification**: Fast keyword & regex-based mapping to target Swarm workers (`gerych_builder`, `dnk_shopify`, `dnk_video_ai_creator`, `dnk_analytics`, `gerych_auditor`).
3. **Web Speech API Browser Dock**: Zero-latency client-side capture (`lang = 'uk-UA'`) with visual pulsing indicator and direct prompt auto-fill.
4. **Natural Ukrainian Audio Confirmation**: Generating conversational, concise feedback acknowledging the dispatch.

---

## 🛠️ Implementation Architecture

```python
from typing import Dict, Any, List

class UkrainianAcousticProcessor:
    PHONETIC_MAP = {
        "лайкхаус": "лейкхаус",
        "duckdb": "дакдб",
        "шопіфай": "shopify",
        "ремоушн": "remotion",
        "відео": "відео",
        "аудит": "аудит",
        "деплой": "деплой",
        "білд": "білд"
    }

    INTENT_ROUTING = {
        "video": {"agent": "dnk_video_ai_creator", "action": "generate_composition"},
        "analytics": {"agent": "dnk_analytics", "action": "lakehouse_bi_query"},
        "shopify": {"agent": "dnk_shopify", "action": "theme_ast_mutation"},
        "code": {"agent": "gerych_builder", "action": "scaffold_or_build"},
        "audit": {"agent": "gerych_auditor", "action": "run_quality_gate"}
    }
```

---

## ⚠️ Pitfalls & Invariants
- **Dialect False Positives**: Do not strip words that alter semantic command meaning (e.g. "не", "без", "тільки").
- **Browser Compatibility**: Safari and Chromium implement Web Speech differently (`SpeechRecognition` vs `webkitSpeechRecognition`). Always check `window.SpeechRecognition || window.webkitSpeechRecognition` with graceful fallback to server-side audio upload.
