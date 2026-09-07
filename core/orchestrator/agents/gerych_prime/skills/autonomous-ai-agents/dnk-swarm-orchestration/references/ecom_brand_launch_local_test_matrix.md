# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/ecom_brand_launch_local_test_matrix.md"
# purpose: "E2E Local Testing Matrix & Verification Protocol for DNK OS E-Com Brand Launch."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧪 DNK OS E-Com Brand Launch Local Test Matrix & Acceptance Protocol

This reference details the canonical 6-step end-to-end verification flow for testing the full DNK OS stack locally.

## 🏁 Pre-Flight Infrastructure Checks
Before running the interactive or headless test suite, verify the services:
```bash
# 1. Check container health
docker compose -f docker-compose.mvp.yml ps

# 2. Check ports and endpoints
curl -sI http://localhost:3000          # Next.js 14 Web UI (200 OK)
curl -sI http://localhost:3000/canvas   # Canvas App (200 OK)
curl -s http://localhost:8000/health    # API Gateway ({"status":"ok"})
nc -zv localhost 5432                   # PostgreSQL 16
nc -zv localhost 6379                   # Redis 7
```

---

## 📋 The 6 Verification Steps

### Step 1: Launchpad → Onboarding Wizard
- **Path**: `apps/web/components/onboarding/OnboardingWizard.tsx` & `LaunchpadView.tsx`
- **Input Parameters**:
  - `Goal`: `"Launch eco-friendly DTC skincare brand"`
  - `Audience`: `"Women 25-40, Ukraine, eco-conscious"`
  - `Style`: `"Minimalist, clean, premium"`
  - `UTP`: `"100% natural ingredients, zero waste packaging"`
- **Acceptance Criteria**:
  - Canvas initializes with 4 connected starter nodes:
    1. `StrategyMarkdownNode` (Brand identity, positioning, target demographic)
    2. `DesignGalleryNode` (Moodboard and visual style tokens)
    3. `ConceptMindmapNode` (Category taxonomy and product hierarchy)
    4. `SprintKanbanNode` (E-com launch tasks: Shopify setup, shoot, ads)
  - Brand DNA payload persisted to SCONES cognitive memory (`ws-alpha-001`).

### Step 2: AI Co-Pilot (Cmd+K) with Budget Guard
- **Path**: `apps/web/src/canvas/copilot/CopilotToolbar.tsx` & `apps/web/lib/budgetGuard.ts`
- **Execution Flow**:
  1. Focus `StrategyMarkdownNode` on Canvas.
  2. Trigger shortcut `Cmd+K` to open floating Co-Pilot palette.
  3. Enter prompt: `"Згенеруй 3 варіанти hero-секції для головної сторінки"`.
  4. Budget Guard validates cost estimation (~$0.02, risk: low).
  5. Click `⚡ Generate` / Submit.
- **Acceptance Criteria**:
  - Real-time token streaming chunks render into the node body without UI freezing.
  - `DesignGalleryNode` receives 3 generated hero layout options.
  - Swarm propagation cascade triggers down connected edges to `ShopifyBuilderNode` and `SprintKanbanNode`.

### Step 3: Photo Studio (BiRefNet + IC-Light)
- **Path**: `apps/web/components/canvas/nodes/PhotoStudioNode.tsx` & `/api/v1/canvas/ai/*`
- **Execution Flow**:
  1. Add/open `PhotoStudioNode`.
  2. Upload raw skincare bottle product photograph.
  3. Execute `✂️ Вирізати фон (BiRefNet)`.
  4. Select directional lighting preset (`Left`, 70% intensity).
  5. Execute `💡 Застосувати освітлення (IC-Light)`.
- **Acceptance Criteria**:
  - Transparent PNG cutout generated cleanly without border halo artifacts.
  - Directional lighting realistic cast with shadows consistent with 70% intensity.
  - Processed asset automatically saved to canvas node asset manager and media gallery.

### Step 4: Video Intelligence (Audit)
- **Path**: `apps/web/components/canvas/nodes/VideoAuditReportNode.tsx` & `packages/video-audit-core`
- **Execution Flow**:
  1. Open `VideoAuditReportNode`.
  2. Input sample competitor/creative TikTok/Reels URL.
  3. Execute `🔍 Analyze Video`.
- **Acceptance Criteria**:
  - Ukrainian ASR transcript generated with timestamps.
  - Hook Score calculated (0–100 scale, evaluating first 3 seconds).
  - Retention curve displayed with drop-off inflection points.
  - Claim verification matrix generated:
    - 🟢 `Observed`: physically visible/audible in video with timestamp citation.
    - 🟡 `Inferred`: reasoned marketing implication.
    - 🔴 `Hypothesized`: speculative virality/retention projection.

### Step 5: 9:16 Shorts Generation & Shopify Sync
- **Path**: `apps/web/components/canvas/nodes/VideoCreatorNode.tsx` & `services/dnk_video_ai_creator`
- **Execution Flow**:
  1. Open `VideoCreatorNode`.
  2. Select template: `ugc_reel_9_16`.
  3. Select audio soundtrack: `phonk`.
  4. Execute `🎬 Generate 9:16 Short`.
  5. Click `🛍️ Sync to Shopify`.
- **Acceptance Criteria**:
  - 1080x1920 @ 30fps vertical video rendered with synced captions.
  - Interactive scrubbing and playback confirmed in `RemotionPlayer`.
  - Media asset synced to Shopify Media API and linked to store product gallery.

### Step 6: Persistence & Multi-User Collaboration
- **Path**: `apps/web/store/canvasStore.ts`, PostgreSQL `hub_memory`, `/api/v1/ws/canvas`
- **Execution Flow**:
  1. Refresh browser window (`http://localhost:3000/canvas`).
  2. Verify Canvas restoration.
  3. Connect second browser session/tab via WebSocket.
- **Acceptance Criteria**:
  - State cleanly rehydrated from PostgreSQL database with IndexedDB local fallback.
  - Remote cursor movements and user presence indicators update in real time.
  - Optimistic Concurrency Control (OCC) delta sync batches mutations (750ms debounce) with 0 state tearing.
  - Dependency drift guard: Webpack resolve alias in `apps/web/next.config.mjs` maps `'reactflow'` to `'@xyflow/react'`.

---

## 📊 Summary Acceptance Checklist Template

```yaml
test_checklist:
  launchpad_onboarding: "✅ 4 кроки → canvas з 4 нодами"
  ai_copilot: "✅ Cmd+K → streaming → swarm propagation"
  photo_studio: "✅ BiRefNet cutout + IC-Light relight"
  video_audit: "✅ ASR + Hook Score + Claim verification"
  shorts_generation: "✅ 9:16 Remotion + Shopify Media API"
  persistence: "✅ Refresh → canvas відновився"
  collaboration: "✅ Multi-user WebSocket (cursor, presence)"
  
  overall: "✅ ALL TESTS PASSED"
```
