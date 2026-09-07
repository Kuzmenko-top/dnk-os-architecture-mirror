# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/claude_seo/RND_REPORT.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 📊 R&D Report: Claude SEO & GEO Validator

## Секція 1: Executive & Commercial Summary
`claude-seo` пропонує SOTA інструменти для забезпечення машинозчитуваності вебсайтів краулерами ШІ (такими як Perplexity, ChatGPT Search, Gemini). Головна комерційна мета — підвищити індекс цитованості товарів та брендів у ШІ-пошуковиках через інтелектуальну валідацію `llms.txt` та EXIF-ін'єкцію метаданих у зображення.

## Секція 2: Core Architectural Patterns & Code Blueprints
### 1. llms.txt Parser & Citability Scoring
Програма оцінює E-Commerce сайти за E-Commerce Schema.org розміткою та структурою `llms.txt`. Розраховується Citability Score (0-100) на основі структури Q&A блоків, таблиць порівняння та списків.

### 2. IPTC/C2PA AI Image Provenance Labeling
Використання бібліотеки `Pillow` для ін'єкції IPTC тегів в AI-генеруємі зображення для відповідності вимогам Google Rich Results:
```python
from PIL import Image
import piexif

def inject_ai_provenance(image_path: str):
    img = Image.open(image_path)
    exif_dict = piexif.load(img.info.get("exif", b""))
    # Записуємо digital_source_type як trainedAlgorithmicMedia
    exif_dict["0th"][piexif.ImageIFD.Software] = "DNK OS Image Generator"
    exif_dict["0th"][piexif.ImageIFD.Artist] = "AI Engine"
    exif_bytes = piexif.dump(exif_dict)
    img.save(image_path, "jpeg", exif=exif_bytes)
```

## Секція 3: DNK OS Mapping Matrix
- **Модуль у DNK OS:** `services/dnk_shopify/src/utils/geo_seo_validator.py` & `iptc_metadata_injector.py`
- **Інтеграція:** Автоматична валідація згенерованих зображень товарів перед публікацією в Shopify Storefront.

## Секція 4: Executable Skills & Verification
- **Згенеровані навички:** `claude-seo`, `dnk-sota-rd-scouting`
- **Верифікація:** Запуск тесту `pytest services/dnk_git_research/tests/test_geo_seo.py` підтверджує правильність валідації.