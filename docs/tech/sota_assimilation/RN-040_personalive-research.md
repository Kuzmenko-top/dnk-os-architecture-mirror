# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/RN-040_personalive-research.md"
# purpose: "Research Note: SOTA discovery, streaming avatar architecture, and license audit of GVCLab/PersonaLive"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🔬 Research Note RN-040: GVCLab/PersonaLive SOTA Assimilation

## 1. Executive Summary & Repository Discovery
- **Repository**: `GVCLab/PersonaLive`
- **Focus Areas**: Real-Time Streaming Portrait Animation, Audio-to-Expression Synchronization, Dynamic Pose Guidance.
- **License**: Apache 2.0 (Track 1 — Permissive Component & Architecture Assimilation).
- **Domain Alignment**: Powers `dnk_video_ai_creator` worker and DNK OS Media Studio streaming avatars.

## 2. Technical Capabilities
1. **Low-Latency Streaming Synthesis**: Real-time generation capable of 25–30 FPS on modern hardware acceleration backends.
2. **Audio-Driven Expression Warping**: Extracts phoneme alignment, audio energy, and facial landmark offsets without requiring rigid 3D meshes.
3. **Memory Optimization**: Integrates with xFormers / FlashAttention to bound GPU VRAM usage under 6GB for streaming inference.

## 3. Integration Strategy
- **Hexagonal Port**: `PersonaLivePort` with `DNKPersonaLiveAdapter` in `core/adapters/dnk_personalive_adapter.py`.
- **API Exposure**: REST endpoints (`/personalive/animate`, `/personalive/status/{session_id}`) and WebSocket streaming (`/personalive/stream/{session_id}`).
- **Guardrails**: Integrated SpendGuard ceiling to protect against runaway GPU compute costs.
