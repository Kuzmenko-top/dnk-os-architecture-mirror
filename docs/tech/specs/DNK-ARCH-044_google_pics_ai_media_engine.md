# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-044_google_pics_ai_media_engine.md"
# purpose: "Technical Architecture Specification & Implementation Blueprint for DNK OS Google Pics Media & Image Generation Engine."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-GOOGLE-PICS-ASSIMILATION"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

# 🏗️ DNK-ARCH-044: DNK OS Google Pics AI Media Engine Specification

## 📌 1. Scope & System Goals
Специфікація **DNK-ARCH-044** визначає технічну архітектуру та контракт впровадження можливостей **Google Pics** (Nano Banana / Gemini 3.1 Flash Image) усередину екосистеми **DNK OS**:
1. **Інтеграція в DNK Open Canvas / Stitch** (`visual_shell/open_design`): Додавання плаваючого відростка та модального вікна `StitchPicsModal` для генерації, маскування (inpainting) та редагування типографіки на полотні.
2. **Гексагональний адаптер `DNKPicsAdapter`** (`core/adapters/dnk_pics_adapter.py`): Уніфікований Python-порт для роботи з Google Vertex AI / Gemini Developer API з підтримкою GCP аккаунт-ротації та офлайн-мок режиму для тестів.
3. **Зв'язок із Swarm агентами** (`dnk_shopify`, `dnk_video_ai_creator`): Автоматичне генерування товарних банерів, рекламних креативів та відео-кадрів.

---

## 🏛️ 2. Топологія Компонентів
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DNK OS PICS MEDIA ENGINE ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. VISUAL CANVAS OVERLAY (StitchCanvasContainer + StitchPicsModal)          │
│    - Object Segmentation & Mask Selection (SAM-like client grounding)        │
│    - Typography & Translation Editor (OCR text box swap)                    │
│    - Multi-Image Composer (Up to 14 asset reference dragging)               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. HEXAGONAL PYTHON ADAPTER (DNKPicsAdapter)                                │
│    - generate_image(prompt, aspect_ratio, person_generation)                │
│    - edit_image(base_image, prompt, mask_image)                             │
│    - edit_typography(base_image, target_text, replacement_text)             │
│    - composite_images(images, prompt)                                       │
│    - upscale_image(base_image, factor)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. GCP VERTEX AI & POOL ROTATION LAYER                                      │
│    - Dynamic Service Account Rotation from DnkModelGcpQuickBar pool         │
│    - Hermetic Mock Mode for CI Test Isolation                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 3. Data Contracts & Pydantic Schemas
```python
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class PicsGenerationRequest(BaseModel):
    prompt: str = Field(description="Text prompt for image creation")
    aspect_ratio: str = Field(default="16:9", description="1:1, 16:9, 9:16, 4:3")
    person_generation: str = Field(default="allow_adult", description="dont_allow, allow_adult")
    model_name: str = Field(default="gemini-3.1-flash-image")

class PicsEditRequest(BaseModel):
    base_image_b64: str = Field(description="Base64 encoded input image")
    prompt: str = Field(description="Editing instructions")
    mask_image_b64: Optional[str] = Field(default=None, description="Optional mask for selective inpainting")

class PicsTypographyEditRequest(BaseModel):
    base_image_b64: str = Field(description="Base64 encoded image with text")
    target_text: str = Field(description="Text to locate via OCR")
    replacement_text: str = Field(description="New text maintaining style & font")

class PicsResponseDTO(BaseModel):
    image_b64: str
    mime_type: str = "image/png"
    metadata: Dict[str, Any] = Field(default_factory=dict)
```
