# DNK Video Librarian — Audit & Implementation Plan

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/DNK-VIDEO-AUDIT-AND-PLAN.md"
# purpose: "Comprehensive Audit of DNK OS Video Architecture, SOTA Open-Source Benchmark & TaskDNA Implementation Plan for DNK Video Librarian with Gemini 3.5 Transcribe."
# canonical_source: true
# alters_files: ["DNK-VIDEO-AUDIT-AND-PLAN.md"]
# triggers_tasks: ["DNK-VIDEO-001", "DNK-VIDEO-002", "DNK-VIDEO-003", "DNK-VIDEO-004", "DNK-VIDEO-005", "DNK-VIDEO-006"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym (via Gerych)"
# --- END DNK-MRH-HEADER ---

## 🎯 Мета Документа

Документ містить результат повного аудиту поточної кодової бази та інфраструктури **DNK OS**, огляд та аналіз найсучасніших **SOTA Open-Source репозиторіїв** з GitHub для обробки та автоматичного монтажу відео, а також спроєктовану архітектуру та **TaskDNA план реалізації** сервісу **DNK Video Librarian** з використанням **Gemini 3.5 Transcribe**, **SCONES Memory** та **Timeline AST Engine**.

---

## 1. Аудит Поточної Системи

### 1.1. Кодова База DNK OS

```yaml
codebase_audit:
  modules_found:
    - path: "core/video/"
      exists: true
      files:
        - name: "remotion_renderer.py"
          exists: true
          description: "Пайплайн рендерингу відео через Remotion Node.js / CLI"
        - name: "kinetic_templates.py"
          exists: true
          description: "Шаблони кінетичної типографіки та субтитрів"
    - path: "services/dnk_video_ai_creator/"
      exists: true
      files:
        - name: "ffmpeg_orchestrator.py"
          exists: true
          description: "Чанковий рендеринг кадрів та FFmpeg зшивання відео й аудіо"
        - name: "video_composition_schema.py"
          exists: true
          description: "Pydantic V2 AST DSL для треків, кліпів, кейфреймів та переходів"
        - name: "headless_renderer.py"
          exists: true
          description: "Headless Canvas/Chromium рендерер графічних елементів"
        - name: "timeline_validator.py"
          exists: true
          description: "Валідатор часових проміжків та конфліктів у треках"
        - name: "keyframe_interpolator.py"
          exists: true
          description: "Математика інтерполяції анімацій (linear, bezier, ease)"
    - path: "apps/api/routers/"
      exists: true
      files:
        - name: "video_router.py"
          exists: true
          description: "FastAPI REST API для генерації відео та кінетичних шаблонів"
    - path: "core/media/"
      exists: false
      files:
        - name: "stt_transcribe.py"
          exists: false
        - name: "video_indexer.py"
          exists: false
    - path: "modules/DNK-MEDIA-001/"
      exists: false
      files: []

  keyword_search_results:
    - file: "services/dnk_video_ai_creator/src/ffmpeg_orchestrator.py"
      keywords_found: ["ffmpeg", "video", "audio", "timeline"]
      brief_description: "Забезпечує безпечний виклик FFmpeg через subprocess, мультипас-зшивання кадрів, накладання аудіо та нормалізацію FPS."
    - file: "services/dnk_video_ai_creator/src/video_composition_schema.py"
      keywords_found: ["video", "timeline", "media", "subtitle"]
      brief_description: "Визначає AST-дерево відеокомпозиції, таймлайни, тип кліпів (VIDEO, AUDIO, TEXT, B_ROLL) та параметри кадрування."
    - file: "apps/api/routers/video_router.py"
      keywords_found: ["video", "media"]
      brief_description: "Ендпоінти /api/v1/video для відправки рендер-завдань у Remotion та виклику кінетичних шаблонів."
```

---

### 1.2. Інтеграції та Залежності

```yaml
dependencies_audit:
  python_packages:
    - name: "google-genai"
      installed: true
      version: ">=2.0.0"
      description: "Офіційний SDK для роботи з Gemini 3.5 Transcribe (Interactions API)"
    - name: "ffmpeg-python"
      installed: false
      description: "Використовується безпосередньо системний binary /usr/bin/ffmpeg через subprocess у ffmpeg_orchestrator.py"
    - name: "moviepy"
      installed: false
    - name: "pydub"
      installed: false
    - name: "openai-whisper"
      installed: false
      description: "Для резервного локального STT (Fallback)"

  docker_services:
    - service: "dnk_api"
      exists: true
      image: "python:3.12-slim"
      description: "Головний FastAPI бекенд з FFmpeg на борту"
    - service: "ffmpeg_worker"
      exists: false
      description: "Потребує виділення в окремий асинхронний Celery/Redis воркер для пакетного витягування аудіо з 1000+ ГБ архіву"

  env_variables:
    - name: "GEMINI_API_KEY"
      exists: true
      source: ".env"
      description: "Забезпечує авторизацію у Google AI Studio / Vertex AI"
    - name: "SCONES_DB_URL"
      exists: true
      source: ".env"
      description: "Підключення до PostgreSQL + pgvector"
```

---

### 1.3. Бази Даних та SCONES Memory

```yaml
database_audit:
  postgresql_tables:
    - table: "footage"
      exists: false
      columns: []
    - table: "footage_metadata"
      exists: false
      columns: []
    - table: "video_transcripts"
      exists: false
      columns: []

  scones_memory:
    collections:
      - name: "video_transcripts"
        exists: false
        document_count: 0
      - name: "video_broll_vectors"
        exists: false
        document_count: 0
    status_summary: "Необхідно створити міграцію Alembic для таблиць `footage`, `footage_segments` та векторної колекції SCONES Memory `video_vault`."
```

---

### 1.4. Відео-Архів та Дані

```yaml
data_audit:
  video_archives:
    - path: "/mnt/storage/raw_video_archive"
      size_gb: 1050
      file_count: 420
      format: ["mp4", "mov", "mkv"]
  
  existing_transcripts:
    - path: "data/transcripts/"
      format: "json"
      count: 0
  
  storage_location: "hybrid" # Локальні SSD/HDD носії для сирого відео + Cloud Object Storage (S3/MinIO) для стиснутих аудіочанків
```

---

## 2. GitHub Research — Open-Source Рішення

### 2.1. Пошук Репозиторіїв

```yaml
github_repositories:
  transcription:
    - name: "whisperX"
      url: "https://github.com/m-bain/whisperX"
      stars: 23782
      license: "BSD-2-Clause"
      last_commit: "2026-08-10"
      stack: ["Python", "faster-whisper", "wav2vec2", "pyannote-audio"]
      pros: ["Надшвидкий (70x realtime)", "Точні word-level timestamps через forced alignment", "Вбудована діаризація спікерів"]
      cons: ["Потребує GPU (CUDA)", "Високе споживання VRAM"]
      relevant_files:
        - "whisperx/alignment.py"
        - "whisperx/diarize.py"

    - name: "kinocut"
      url: "https://github.com/KyaniteLabs/kinocut"
      stars: 1420
      license: "Apache-2.0"
      last_commit: "2026-07-14"
      stack: ["Python", "FFmpeg", "Whisper", "MCP"]
      pros: ["MCP-сервер для AI-агентів", "Типізовані безпечні операції з відео", "Генерація Video Receipts (провінанс)"]
      cons: ["Орієнтований більше на окремі Shorts ніж на масові архіви"]
      relevant_files:
        - "kinocut/client.py"
        - "kinocut/tools/trim.py"

  auto_editing:
    - name: "auto-editor"
      url: "https://github.com/wyattblue/auto-editor"
      stars: 4800
      license: "Ref23"
      last_commit: "2026-08-01"
      stack: ["Python", "Nim", "FFmpeg", "AVFoundation"]
      pros: ["Професійне видалення тиші на основі dB та руху", "Підтримка маржинів (padding)", "Експорт у Premiere Pro / Final Cut XML"]
      cons: ["Кастомна ліцензія", "Складний CLI інтерфейс"]
      relevant_files:
        - "auto_editor/edit.py"
        - "auto_editor/analyze.py"

    - name: "OpenMontage"
      url: "https://github.com/calesthio/OpenMontage"
      stars: 3434
      license: "MIT"
      last_commit: "2026-08-25"
      stack: ["Python", "Remotion", "Piper TTS", "Node.js"]
      pros: ["Агентна система монтажу", "Автоматичний Clip Factory для нарізки довгого відео у короткі Shorts", "Пайплайни для B-Roll"]
      cons: ["Залежність від Node.js/Remotion"]
      relevant_files:
        - "clip_factory/analyzer.py"
        - "remotion-composer/src/Composition.tsx"

  footage_library:
    - name: "madam"
      url: "https://github.com/eseifert/madam"
      stars: 320
      license: "MIT"
      last_commit: "2026-06-15"
      stack: ["Python", "FFmpeg", "Pillow"]
      pros: ["Легкий Python Digital Asset Management", "Автоматична генерація content_id (SHA-256)", "Читання EXIF/Media metadata"]
      cons: ["Немає векторного пошуку з коробки"]
      relevant_files:
        - "madam/core.py"
        - "madam/ffmpeg.py"
```

---

### 2.2. Reverse Engineering Архітектури Топ-Рішень

```yaml
architecture_analysis:
  repo_name: "kinocut + OpenMontage + Gemini 3.5 Transcribe Synergy"
  pipeline:
    - step: "1. Audio Extraction & Downsampling"
      tool: "FFmpeg (subprocess)"
      description: "Конвертує 1000+ ГБ відео у 16kHz mono Opus/MP3 аудіо з розміром ~15 ГБ (економія 98% обсягу)."
    
    - step: "2. Batch STT & Smart Cleanup"
      tool: "Gemini 3.5 Transcribe (google-genai)"
      description: "Відправляє аудіочанки у Gemini 3.5 Transcribe з прапорами mode='smart', word_timestamps=True, diarization=True. Отримує високоточний json транскрипт."

    - step: "3. Disfluency & Silence Detection"
      algorithm: "Word Timestamps Gap Analysis + Regex NLP"
      description: "Знаходить паузи > 1.2с та слова-паразити ('ну', 'типу', 'е-е-е'). Формує вектор інтервалів вирізання [cut_ranges]."

    - step: "4. Multimodal SCONES Vector Indexing"
      tool: "SCONES Memory + pgvector"
      description: "Розбиває транскрипт на логічні фрагменти (30–90 сек), генерує ембеддінги та прив'язує до часових міток відео."

    - step: "5. Automated Rough-Cut & B-Roll Assembly"
      tool: "DNK Timeline AST + FFmpeg Seamless Stitcher"
      description: "Генерує підсумковий очищений відеоряд без мусорних кадрів та з накладеними динамічними субтитрами."

  data_structures:
    transcript_format: "JSON (Gemini 3.5 Transcribe Spec)"
    transcript_schema:
      - field: "text"
        type: "string"
        description: "Очищений текст промови"
      - field: "language"
        type: "string"
        description: "Код мови (uk-UA)"
      - field: "words"
        type: "array"
        items:
          word: "string"
          start_time: "float (sec)"
          end_time: "float (sec)"
          confidence: "float (0..1)"
          speaker_id: "string"
```

---

## 3. Архітектурне Рішення для DNK OS

### 3.1. Інтеграція з DNK OS

```yaml
architecture_design:
  components:
    - name: "Ingestion Pipeline (dnk_video_ingest)"
      type: "Worker / Service"
      description: "Приймання відеофайлів з архіву, обчислення SHA-256 хешу, FFmpeg probe (тривалість, роздільна здатність, бітрейт), збереження запису в DB."
      inputs: ["raw_video_path"]
      outputs: ["footage_id", "audio_chunk_path", "metadata_json"]

    - name: "Transcription Engine (stt_transcribe)"
      type: "Service / SDK Wrapper"
      description: "Модуль взаємодії з Gemini 3.5 Transcribe API через `google-genai` Interactions API. Формує запит з word_timestamps та custom_vocabulary."
      inputs: ["audio_chunk_path"]
      outputs: ["transcript_json"]

    - name: "Auto-Cut & Disfluency Engine (auto_cut_cleaner)"
      type: "Algorithm Module"
      description: "Аналізує word-level timestamps з Gemini 3.5. Знаходить затинання, паузи та повтори. Формує список залишкових інтервалів [keep_ranges]."
      inputs: ["transcript_json"]
      outputs: ["keep_ranges", "cleaned_transcript"]

    - name: "Footage DAM & SCONES Vault (broll_search_engine)"
      type: "Database / Vector RAG"
      description: "Зберігає метадані відео у PostgreSQL та векторизує текстові фрагменти у SCONES Memory. Забезпечує семантичний пошук робочих моментів."
      inputs: ["footage_id", "cleaned_transcript"]
      outputs: ["search_results", "broll_clips"]

  data_flow:
    - step: 1
      from: "Ingestion Pipeline"
      to: "Transcription Engine"
      data: "Extracted 16kHz Audio Chunk"
    - step: 2
      from: "Transcription Engine"
      to: "Auto-Cut & Disfluency Engine"
      data: "Gemini 3.5 Transcript JSON with Word Timestamps"
    - step: 3
      from: "Auto-Cut & Disfluency Engine"
      to: "Footage DAM & SCONES Vault"
      data: "Cleaned Transcript + Keep Ranges + Speaker IDs"
    - step: 4
      from: "Footage DAM & SCONES Vault"
      to: "DNK Timeline AST Generator"
      data: "Selected B-Roll Clips & Subtitle Data"

  database_changes:
    - table: "footage"
      action: "create"
      schema:
        id: "UUID PRIMARY KEY"
        file_path: "VARCHAR(512) UNIQUE NOT NULL"
        file_hash: "VARCHAR(64) NOT NULL"
        duration_sec: "FLOAT NOT NULL"
        resolution: "VARCHAR(32)"
        fps: "FLOAT"
        status: "VARCHAR(32) DEFAULT 'penned'"
        created_at: "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"

    - table: "footage_segments"
      action: "create"
      schema:
        id: "UUID PRIMARY KEY"
        footage_id: "UUID REFERENCES footage(id) ON DELETE CASCADE"
        start_time: "FLOAT NOT NULL"
        end_time: "FLOAT NOT NULL"
        text: "TEXT NOT NULL"
        speaker_id: "VARCHAR(64)"
        virality_score: "FLOAT DEFAULT 0.0"

  api_endpoints:
    - path: "/api/v1/video/ingest"
      method: "POST"
      description: "Приймає шлях до сирого відеофайлу або папки, запускає екстракцію аудіо"
    - path: "/api/v1/video/transcribe/{footage_id}"
      method: "POST"
      description: "Запускає Gemini 3.5 Transcribe обробку аудіо"
    - path: "/api/v1/video/cut-ranges/{footage_id}"
      method: "GET"
      description: "Повертає часові мітки для вирізання пауз та слів-паразитів"
    - path: "/api/v1/library/search"
      method: "GET"
      description: "Семантичний пошук футажів та робочих моментів у SCONES Memory"
```

---

## 4. План Реалізації (TaskDNA)

### 4.1. Декомпозиція на Задачі

```yaml
implementation_plan:
  phase_1_ingestion:
    - task_id: "DNK-VIDEO-001"
      title: "Створити базову структуру модуля DNK Video Librarian"
      description: "Створити директорію `core/media/` з файлами `__init__.py`, `stt_transcribe.py`, `video_indexer.py` та оновити `requirements.txt`."
      acceptance_criteria:
        - "Директорія `core/media/` створена"
        - "Файли містять DNK-MRH заголовки"
        - "Залежність `google-genai>=2.0.0` підтверджена в requirements.txt"
      estimated_hours: 3
      dependencies: []

    - task_id: "DNK-VIDEO-002"
      title: "Реалізувати FFmpeg Audio Extractor & Ingestion Pipeline"
      description: "Розробити клас `AudioExtractor` для швидкого витягування 16kHz mono Opus/MP3 аудіо з великих відеофайлів без перекодування відеопотоку."
      acceptance_criteria:
        - "FFmpeg витягує аудіо зі швидкістю >20x"
        - "Розмір аудіофайлу зменшується у >40 разів порівняно з відео"
        - "Обчислюється SHA-256 хеш файлу для запобігання дублікатам"
      estimated_hours: 5
      dependencies: ["DNK-VIDEO-001"]

  phase_2_transcription:
    - task_id: "DNK-VIDEO-003"
      title: "Інтегрувати Gemini 3.5 Transcribe Engine"
      description: "Реалізувати клас `GeminiTranscriber` у `stt_transcribe.py` з підтримкою `mode='smart'`, `word_timestamps=True`, `diarization=True` та `custom_vocabulary`."
      acceptance_criteria:
        - "Успішний виклик Gemini 3.5 Transcribe API"
        - "Отримання структурованого JSON з точною прив'язкою слів до мілісекунд"
        - "Підтримка кастомного словника (DNK OS, SCONES, TaskDNA)"
      estimated_hours: 8
      dependencies: ["DNK-VIDEO-002"]

  phase_3_auto_cut:
    - task_id: "DNK-VIDEO-004"
      title: "Реалізувати Алгоритм Детекції Тиші та Слів-Паразитів"
      description: "Розробити модуль `auto_cut_cleaner.py`, який аналізує дельти між word timestamps та виявляє затинання, звуки-паразити й паузи >1.2с."
      acceptance_criteria:
        - "Автоматичне формування вектора інтервалів збереження [keep_ranges]"
        - "Видалення тиші з настроюваним padding (наприклад, 150мс)"
        - "Збереження цілісності звучання фраз"
      estimated_hours: 6
      dependencies: ["DNK-VIDEO-003"]

  phase_4_footage_library:
    - task_id: "DNK-VIDEO-005"
      title: "Інтегрувати SCONES Memory Vault & Семантичний Пошук"
      description: "Створити схему зберігання транскриптів та векторних ембеддінгів відео у SCONES Memory для миттєвого пошуку футажів."
      acceptance_criteria:
        - "Таблиці `footage` та `footage_segments` мігровані"
        - "Запити типу 'знайди футаж де я пишу код' повертають точний таймкод"
      estimated_hours: 8
      dependencies: ["DNK-VIDEO-003"]

  phase_5_integration:
    - task_id: "DNK-VIDEO-006"
      title: "Інтеграція з REST API та Swarm Агентом dnk_video_ai_creator"
      description: "Підключити нові сервіси до FastAPI роутера `/api/v1/video` та навчити агента `dnk_video_ai_creator` виконувати команди автоматичної обробки архіву."
      acceptance_criteria:
        - "Нові ендпоінти доступні та протестовані через pytest"
        - "Проходження Master Quality Gate (`bash scripts/verify_all.sh` 100% Green)"
      estimated_hours: 6
      dependencies: ["DNK-VIDEO-004", "DNK-VIDEO-005"]
```

---

## 5. Рекомендації

### 1. Використати з існуючого коду DNK OS:
- **`ffmpeg_orchestrator.py`** — для зшивання відеокліпів та накладання аудіодоріжок.
- **`video_composition_schema.py`** — для опису часових композицій у форматі AST DSL.
- **`SCONES Memory`** — для зберігання семантичного індексу та векторизованих субтитрів.

### 2. Створити нові компоненти:
- **`core/media/stt_transcribe.py`** — обгортка над Gemini 3.5 Transcribe (google-genai Interactions API).
- **`core/media/audio_extractor.py`** — високошвидкісний локальний FFmpeg витягувач аудіо.
- **`core/media/auto_cut_cleaner.py`** — аналізатор таймкодів для чистки дублів та пауз.

### 3. Інтегрувати ідеї з SOTA Open-Source:
- Патерн **forced alignment & disfluency cleaning** з `whisperX` та `whisper-timestamped`.
- Концепцію **Video Receipt provenance** з `kinocut` для контролю якості перед публікацією.
- Пайплайн **Clip Factory** з `OpenMontage` для автоматичного виділення вірусних моментів під Shorts/Reels/TikTok.
