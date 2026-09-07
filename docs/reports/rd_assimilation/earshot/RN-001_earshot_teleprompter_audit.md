# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/earshot/RN-001_earshot_teleprompter_audit.md"
# purpose: "Comprehensive Architectural Audit of Earshot Teleprompter & Open-Source Landscape Research"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎙️ RN-001: Earshot Teleprompter Architectural Audit & Open-Source Ecosystem Analysis

## 📌 Executive Summary
**Earshot Teleprompter** (`https://app.earshot.to/teleprompter`) represents an evolution from traditional mechanical teleprompters (which merely scroll text at a fixed rate) into an **Intelligent Vocal & Performance Coaching Prompter** for high-engagement "talking head / yapping" short-form video creators.

Rather than treating text as static script lines, Earshot introduces **Prosodic Notation & Delivery Choreography** directly in the prompter HUD, training creators in tone variance, pacing, strategic pauses, and physical gestures.

---

## 🔍 1. Detailed Audit of Earshot Teleprompter

### 1.1 Core Value Proposition & UX Workflow
1. **Script Ingestion & Idea Structuring**:
   - **"Talk your idea"**: Voice ramble input converted into a structured, punchy script via LLM.
   - **"Generate from viral vids"**: Script generation based on high-performing viral video structures.
   - **"Type it yourself"**: Manual editor with word count and estimated speaking duration (e.g. 39 words ≈ 11s).

2. **Prosodic Notation System (Vocal Choreography)**:
   - 🔴 **BIG RED WORDS (Punch words)**: Loud, energetic, elongated emphasis on core message anchors.
   - 🔵 **UNDERLINED / Tone Hold**: Syllable extension ("hold it a bit longer, not louder just longer") to introduce melodic cadence.
   - ⚪ **NORMAL WHITE (Speed-through)**: Connective/filler words spoken rapidly without emphasis.
   - ⌞ ⌟ **Bracket Marks (Micro-Pauses)**: Explicit breath and dramatic pause indicators.
   - ↘️ **SLOPED TAIL (Pitch Inflexion)**: Lowering voice frequency at clause/sentence endings.
   - ✋ **Hand Gesture Alerts**: Visual icons prompting body language cues aligned with verbal punches.

3. **Prompter HUD & Real-Time Engine**:
   - Real-time **Word State Machine**: Tracks `say now` vs `said` words.
   - Dynamic **Pace Controller**: Configurable WPM targets (default ~190 WPM) with real-time timer.
   - WebRTC / `getUserMedia` camera overlay for direct eye-contact recording.

4. **Post-Recording Pipeline**:
   - Automated video trimming, jump-cut silence removal, and animated caption rendering.

---

## 🌐 2. Open-Source GitHub Ecosystem & Comparative Landscape

| Project | Stack | Architecture / Key Features | License | Relevance |
| :--- | :--- | :--- | :--- | :--- |
| [**jlecomte/voice-activated-teleprompter**](https://github.com/jlecomte/voice-activated-teleprompter) | React, Vite, Web Speech API | Real-time speech-synchronized auto-scrolling teleprompter. | MIT | ⭐️⭐️⭐️⭐️⭐️ Direct Web Foundation |
| [**contrastlogic/whisper-rail-teleprompter**](https://github.com/contrastlogic/whisper-rail-teleprompter) | Tauri, Rust, Whisper | Desktop teleprompter following live microphone speaking rhythm with Whisper ASR. | MIT / Open | ⭐️⭐️⭐️⭐️ High-precision local ASR |
| [**Cuperino/QPrompt-Teleprompter**](https://github.com/Cuperino/QPrompt-Teleprompter) | C++, Qt, Kirigami | Professional multi-platform prompter (Linux, macOS, Windows, Android) with hardware control. | GPL-3.0 | ⭐️⭐️⭐️ UI/UX ergonomics benchmark |
| [**danielgross/teleprompter**](https://github.com/danielgross/teleprompter) | Python, PyTorch, Transformers | On-device charismatic speaking prompter using semantic embeddings and local ASR. | MIT | ⭐️⭐️⭐️⭐️ Charisma/Coaching AI |
| [**gulbaharelmas/Whisperer**](https://github.com/gulbaharelmas/Whisperer_Real_Time_Speech_Synchronization_and_Intelligent_Prompter_System_for_English) | Python, Whisper, PyTorch | Real-time speech synchronization and intelligent word-tracking prompter. | Open Source | ⭐️⭐️⭐️⭐️ Forced-alignment model |
| [**sherwinvishesh/Echo-Prompter**](https://github.com/sherwinvishesh/Echo-Prompter) | JavaScript, TensorFlow.js | In-browser voice-assisted teleprompter tracking spoken words. | MIT | ⭐️⭐️⭐️ Browser ML tracking |

---

## 🏗️ 3. Architecture for DNK OS Integration (`dnk_teleprompter`)

To incorporate an Earshot-grade AI teleprompter into the DNK OS ecosystem (bridged with `dnk_video_ai_creator` and `apps/web/`):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DNK Teleprompter Engine                         │
├───────────────────────┬────────────────────────┬───────────────────────┤
│ 1. AI Script Structurer│ 2. Prosody Choreographer│ 3. Real-time Prompter │
│  - Whisper Ramble-to-  │  - JSON Schema Prompt:  │  - Web Speech / VAD   │
│    Script Converter   │    * emphasis_words     │  - Syllable Highlighting│
│  - Viral Hook Ingestion│    * pauses_ms [⌞ ⌟]   │  - WPM Pacer (180-210) │
│  - Duration Estimator │    * tone_drops [↘️]    │  - Camera Stream + HUD │
│                       │    * gesture_triggers   │  - Mirror & Eye-Align │
└───────────────────────┴────────────────────────┴───────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Post-Recording & Remotion Pipeline                   │
│   (Auto-cut silences, dynamic captions via dnk_video_ai_creator)       │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Recommended Component Stack
- **Frontend HUD**: Next.js / Tailwind CSS / Lucide Icons (`apps/web/src/components/teleprompter/`).
- **Real-time Tracking**: Web Speech API (`webkitSpeechRecognition`) for zero-latency browser tracking with fallback to local `whisper.cpp` / WebAssembly Whisper.
- **Prosody Engine**: Fast LLM structured output generator (vLLM / Vertex / OpenAI) returning word-level markup tokens:
  ```json
  {
    "segments": [
      { "text": "Viral", "style": "big_red", "gesture": null },
      { "text": "yapping videos", "style": "normal", "gesture": null },
      { "text": "require", "style": "tone_hold", "gesture": "hand_open" },
      { "type": "pause", "duration_ms": 350 },
      { "text": "good tone.", "style": "pitch_drop", "gesture": null }
    ]
  }
  ```

---

## 🎯 4. Key Takeaways & Recommendations
1. **Core Competitive Edge**: Earshot's main innovation is **prosody visualization** (teaching rhythm and energy visually) rather than just speech recognition.
2. **Assimilation Target**: Utilize the open-source MIT architecture of `jlecomte/voice-activated-teleprompter` as the browser tracking foundation, combined with a custom LLM Prosody Markup Transformer.
3. **Synergy with DNK OS**: Seamlessly connects to `dnk_video_ai_creator` (Remotion pipeline) to record, track, and immediately render viral short-form assets.
