---
title: "014 Voice AI Audio Synthesis & Remotion MP4 Exporter"
tags:
  - architecture
  - remotion
  - voice-ai
  - video-exporter
  - dnk-hub
date: "2026-09-06"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/014 Voice AI Audio Synthesis & Remotion MP4 Exporter.md"
purpose: "Architectural decisions, rationale, and runtime contracts for Voice AI synthesis and Remotion 9:16 MP4 exporter."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🎙️ Voice AI Audio Synthesis & Remotion 9:16 MP4 Exporter

## 📌 Context & Motivation
У рамках маркетингового контуру DNK OS (`TASK-DNK-REMOTION-20260906-010`) реалізовано повноцінний цикл генерації аудіо-начитки з тексту (`voiceover_script`) та рендерингу вертикального 9:16 MP4 відео для TikTok, YouTube Shorts та Instagram Reels.

## 🧱 Key Architectural Components

### 1. Backend Voice Synthesizer (`services/dnk_video_ai_creator/voice_synthesizer.py`)
- **Engine**: Підтримує модульні провайдери TTS (OpenAI TTS, ElevenLabs) із детермінованим mock-генератором WAV-хвилі для локального оточення та CI/CD.
- **Cache & Storage**: Синтезовані аудіо-файли зберігаються за структурою `artifacts/marketing_videos/{node_id}/voiceover.mp3`.
- **API Endpoints**:
  - `POST /api/v3/node_tasks/{node_id}/synthesize_voiceover`
  - `GET /api/v3/node_tasks/{node_id}/voiceover_audio` (Stream audio/mpeg)

### 2. Remotion MP4 Exporter (`services/dnk_video_ai_creator/remotion_exporter.py`)
- **Engine**: Асинхронний воркер рендерингу Remotion через CLI/Node.js або headless runner.
- **Dynamic Status Polling**:
  - `POST /api/v3/node_tasks/{node_id}/export_video_mp4` (повертає `status: 'completed'` / `'processing'`)
  - `GET /api/v3/node_tasks/{node_id}/video_export_status`

### 3. Frontend Zustand Integration (`apps/web/store/nodeTasksStore.ts`)
- Зберігає стан аудіо та рендерингу:
  - `audioUrls: Record<string, string>`
  - `isSynthesizingVoice: Record<string, boolean>`
  - `isExportingVideo: Record<string, boolean>`
  - `videoExportStatuses: Record<string, VideoExportStatus>`
- Екшени: `synthesizeVoiceover()`, `exportVideoMp4()`, `fetchVideoExportStatus()`.

### 4. Interactive Video Viewer (`apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx`)
- Кнопка **`[🎙️ Озвучити через Voice AI]`** з інтерактивним індикатором прогресу.
- Прихований синхронізований `<audio>` плеєр:
  - Позиція аудіо синхронізується з кадрами відео: `audio.currentTime = currentFrame / fps`.
- Бейдж **`🔊 Аудіо озвучено`** поруч із таймкодом.
- Кнопка **`[⬇️ Експорт MP4 (9:16)]`** з автоматичним переходом у **`[✅ Скачати MP4]`** після завершення рендерингу.

## 🔗 Related Notes & ADRs
- [[010 Remotion Storyboard Architecture]]
- [[013 Deep Dynamic Obsidian Sync]]
