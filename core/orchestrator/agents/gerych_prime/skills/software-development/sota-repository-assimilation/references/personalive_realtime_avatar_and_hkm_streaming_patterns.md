# --- DNK-MRH-HEADER ---
# mrh_id: "sota_personalive_avatar_and_hkm_streaming_patterns"
# purpose: "Reference architecture for real-time live-streaming portrait animation, few-step DDIM denoising, and Historical Keyframe Mechanism (HKM) clean-room assimilation."
# canonical_source: false
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎭 PersonaLive Real-Time Avatar & Historical Keyframe Mechanism (HKM) Streaming Patterns

## 1. Overview & Core Breakthrough
Conventional diffusion-based talking head systems (AniPortrait, EchoMimic, Hallo) batch 16–24 frames with 25–50 denoising steps, incurring 1.5–3.0s latency. Furthermore, autoregressive frame-by-frame generation causes catastrophic identity drift over extended streaming sessions.
PersonaLive (CVPR 2026) achieves **sub-30ms / >30 FPS** latency and drift-free infinite streaming through 4 synergistic innovations:

1. **Hybrid Motion Representation**:
   - 3D Implicit Keypoints (LivePortrait ConvNeXt, 21 KPs) capture macro head orientation, rigid geometry, and eye gaze.
   - Implicit Face Patches (`MotEncoder` from facial crops) capture subtle mouth articulation, lip dynamics, and micro-expressions.
2. **Appearance Distillation & 1–4 Step DDIM Schedule**:
   - Discrete inference schedule: `timesteps = [999, 666, 333, 0]` with step size 333.
   - Reference latent conditioning anchors facial appearance, eliminating the need for multi-step noise reduction.
3. **Micro-Chunk Autoregressive Sliding Queue**:
   - Deques for `latents_pile` (sliding window size 2–4), `pose_pile`, and `motion_pile`.
   - Pop oldest frame -> decode via VAE -> stream immediately; push forward remaining latents to anchor the next frame.
4. **Historical Keyframe Mechanism (HKM)**:
   - Dynamic `motion_bank` tracking motion feature vectors.
   - L2 distance metric: when current motion deviates by $d(B, A) > 17.0$, the frame is registered as a novel historical keyframe (up to 3 keyframes).
   - Dynamically updates Reference UNet KV cross-attention cache (`update_hkf`), resetting drift and locking facial identity.

---

## 2. Clean-Room Architectural Blueprint for DNK OS (Track 2)

```
[Audio Chunk (PCM)] ──► [Feature Extractor (Wav2Vec / Whisper)] ─┐
                                                                 ├─► [Hybrid Motion Buffer]
[Camera Stream / Pose] ─► [LivePortrait Keypoint Extractor] ──────┘             │
                                                                               ▼
┌─────────────────────────── Sliding Window Latent Buffer ───────────────────────────────┐
│ [Frame t-2 Latent] <─ [Frame t-1 Latent] <─ [Frame t (Noised Reference Latent)]         │
└──────────────────────────────────────┬─────────────────────────────────────────────────┘
                                       │
                                       ▼
┌───────────────────────────────── 3D Denoising UNet ────────────────────────────────────┐
│ Cross-Attention ◄── HKM Dynamic Keyframe Bank (Reference UNet KV Cache)                │
└──────────────────────────────────────┬─────────────────────────────────────────────────┘
                                       ▼
                     [Oldest Latent Chunk Popleft]
                                       ▼
                            [Fast VAE Decoder]
                                       ▼
                   [Output Frame Buffer (WebRTC / WS)]
```

---

## 3. Implementation Invariants & Pitfalls

### Pitfall 1: Dual-License Conflict
- **Signal**: Repo has `LICENSE` as Apache-2.0, but README has a strict "non-commercial research only" restriction.
- **Protocol**: Always route to **Track 2 Clean-Room Synthesis**. Do NOT copy model wrapper code into core modules. Encapsulate external model weights within an isolated worker/container and interface via standard WebRTC/WebSocket JSON-RPC.

### Pitfall 2: Memory Leak in Infinite Sliding Deques
- **Signal**: Tensor allocation in `latents_pile` or `motion_bank` without `.detach()` retains calculation graphs, quickly causing CUDA OOM after 500+ frames.
- **Protocol**: Always store detached tensors or raw numpy arrays in queues: `latents_pile.append(latent.detach())`.

### Pitfall 3: HKM Cache Explosion
- **Signal**: Setting HKM distance threshold too low ($d < 10.0$) triggers keyframe updates on every frame, killing real-time performance.
- **Protocol**: Bound maximum keyframes to $N \le 3$, enforce warmup threshold (e.g. `count > 8`), and set conservative distance threshold ($d \ge 17.0$).

### Pitfall 4: Hardware Quirks on Blackwell / RTX 50-Series
- **Signal**: Running inference with xformers enabled on newer Blackwell (RTX 50-series) GPUs causes runtime errors or silent CUDA crashes.
- **Protocol**: Fallback to `--acceleration none` or `--use_xformers False` when compiling PyTorch pipelines on newer microarchitectures until upstream wheel compatibility lands.

### Pitfall 5: Remote Repo Discovery & Inspection Fallbacks
- **Signal**: Native GitHub MCP tools fail due to missing scope or environment config when accessing third-party public repositories.
- **Protocol**: Fallback to zero-clone extraction via `web_extract` on `https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<file>` (e.g. `README.md`, `LICENSE`, `configs/inference.yaml`) instead of full `git clone`.

### Pitfall 6: Universal Relative Path Invariant in Reports & Notes
- **Signal**: Emitting host-dependent absolute paths (`/Users/...`) in audit summaries or Obsidian notes breaks portability across development environments.
- **Protocol**: Always use relative paths (`./docs/notes/...` or `docs/tech/sota_assimilation/...`) or virtual prefixes (`vault:<note.md>`).

### Pitfall 7: Async Generator Protocol in Real-Time Frame Streaming Adapters
- **Signal**: In Python adapters yielding real-time media/video packets (e.g. `generate_frame_stream`), misconfiguring `async def` with `yield` vs standard `def` with `yield` causes `TypeError: 'async_generator' object is not iterable` or generator exhaustion in downstream consumers.
- **Protocol**: When streaming over WebSockets or async endpoints, declare `async def generate_frame_stream(...) -> AsyncGenerator[FramePacket, None]:` with `yield` and consume via `async for packet in ...`. For synchronous test fixtures, mock frame buffers using standard lists or synchronized queues.

### Pitfall 8: FastAPI Schema Packaging & Dual-Prefix Mount Compatibility
- **Signal**: Adding a new streaming router without `apps/api/schemas/__init__.py` causes silent import failures or skips in dynamic router discovery, resulting in 404 Route Not Found during TestClient verification.
- **Protocol**: Always ensure target schema folders have explicit `__init__.py` package markers before writing schema modules. When registering routers in FastAPI, support both canonical root `/personalive` and gateway `/api/v1/personalive` routes to maintain compatibility between standalone microservice workers and the unified API shell.

---

## 4. SOTA Evolution: EditaLive & 3-Stage Training Pipeline

1. **EditaLive Evolution (2026.08.28)**:
   - Upstream evolution `GVCLab/EditaLive` extends PersonaLive to full-body expressive animation and dynamic feature editing (clothing, lighting, background) in real-time.
   - DNK OS Clean-Room roadmap incorporates EditaLive's decoupled body-pose conditioning into `services/dnk_video_ai_creator/`.

2. **Three-Stage Training Pipeline**:
   - **Stage 1 (Image Warm-up)**: Train spatial appearance UNet with static portraits.
   - **Stage 2 (Adversarial Refinement)**: Joint training with StyleGAN2-based spatial discriminator to enhance lip sharpness and dental fidelity.
   - **Stage 3 (Temporal Streaming Fine-Tuning)**: Fine-tune 3D temporal convolution layers on continuous streaming sequences using sliding micro-chunks.
