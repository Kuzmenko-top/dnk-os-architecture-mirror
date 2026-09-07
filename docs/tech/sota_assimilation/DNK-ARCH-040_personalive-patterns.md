# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-ARCH-040_personalive-patterns.md"
# purpose: "Architecture & Structural Patterns: Hexagonal Adapter, WebSocket Frame Streaming, and SpendGuard"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🏛️ Architecture Patterns DNK-ARCH-040: PersonaLive Streaming Pipeline

## 1. Hexagonal Architecture Topology
```
[Client / Visual Shell]
        |
        v
[FastAPI Router: /personalive]
        |
        v
[Hexagonal Port: PersonaLivePort]
        |
        v
[DNKPersonaLiveAdapter] ---> [SpendGuard Budget Limiter]
        |                 ---> [Path Traversal Validator]
        v
[Async Video Frame Stream Generator (WebSocket)]
```

## 2. Key Architectural Invariants
1. **Async Generator Decoupling**: Video frames are yielded as discrete `FramePacket` chunks over async iterators, preventing memory accumulation.
2. **Keyframe Marking**: Frames are stamped with `is_keyframe` flag every N frames (e.g. 15) for smooth client reconnection and seeking.
3. **Budget Guard**: Before initiating any animation job, estimated duration is multiplied by cost per second and checked against SpendGuard limits.
