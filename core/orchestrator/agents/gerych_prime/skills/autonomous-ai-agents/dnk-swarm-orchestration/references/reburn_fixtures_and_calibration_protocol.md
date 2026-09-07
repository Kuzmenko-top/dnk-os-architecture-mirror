# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/herich_librarian/references/reburn_fixtures_and_calibration_protocol.md"
# purpose: "Canonical Reference for ReBurn Fixtures, Calibration, and Ukrainian Terminology Benchmarks."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# --- END DNK-MRH-HEADER ---

# 🧪 ReBurn Fixtures, Semantic Calibration & Ukrainian Terminology Protocol (VIDEO-AUDIT-PIPELINE-001E-E)

## 📌 1. Objective & Scope
Define the standard for constructing, calibrating, and semantically verifying 10+ multimodal reference video fixtures tailored for the ReBurn e-commerce brand (smokehouse/coppering equipment). This ensures that any LLM/LMM-driven downstream reasoning engine remains anchored to real physical evidence and conforms to niche language requirements.

---

## 🎛️ 2. The 11 Canonical ReBurn Scenarios
Each scenario represents a distinct marketing or technical layout with strict, deterministic multimodal mocks (scenes, transcript, OCR, audio features) and expected output states:

| ID | Title / Genre | Target Status | Key Testing Characteristic |
|---|---|---|---|
| `reburn-product-demo-001` | Product Demo | `READY` | Stainless steel AISI 304, argon welds, visual camera movements. |
| `reburn-workshop-talking-head-001` | Workshop Expert | `READY` | Solves condensate/bitterness problem using condenser. |
| `reburn-before-after-001` | Before / After | `READY` | Visual contrast between barrel smoking and ReBurn chamber. |
| `reburn-educational-listicle-001` | Educational Listicle | `READY` | 3 critical chip/temperature mistakes, high visual text overlay. |
| `reburn-founder-story-001` | Founder Story | `READY` | Brand-trust building, garage workshop history. |
| `reburn-technical-explainer-001` | Technical Explainer | `READY` | Convection, heater elements, PID controllers, fan blowers. |
| `reburn-offer-cta-001` | Offer / CTA | `READY` | Business ROI calculations, price, call to action. |
| `reburn-no-audio-001` | No-Audio Video | `DEGRADED` | Tests graceful degradation when `allowEmptyTranscript` is active. |
| `reburn-no-ocr-001` | No-OCR Video | `READY` | Video has zero overlay text/captions. `allowEmptyOcr: true`. |
| `reburn-fast-paced-short-001` | Fast Short | `READY` | High audio/visual transition frequency, sound effect overlays. |
| `reburn-manual-review-001` | Borderline Case | `NEEDS_REVIEW` | Low ASR confidence, conflicting claims. Requires human gate. |

---

## 🛡️ 3. Semantic Validation Invariants (Zero-Hallucination Gate)
Rather than asserting exact-text string matches from LLM outputs, the validation suite enforces strict **semantic & physical rules**:

1. **The Hook Invariant**:
   * Every promotional/educational video must have a "Hook Claim".
   * The hook timestamp **must start near zero** (`<= 3000ms`).
2. **The Virality Restriction Invariant**:
   * Engagement, virality, CTR, or audience retention statistics can **never** be labeled as `observed` facts.
   * Unless integrated with live analytics platforms (TikTok/YouTube APIs), such claims must always be classified as `hypothesized`.
3. **The Evidence Traceability Invariant**:
   * Any `observed` claim must explicitly reference valid underlying proof: `transcriptWordIndexes`, `sceneIndexes`, `ocrFrameIds`, or `audioSegmentIndexes`.
4. **The Temporal Boundaries Invariant**:
   * No claim or scene timestamps can be negative or exceed the actual video duration.
5. **ID Integrity Invariant**:
   * References to `sceneId`, `segmentId`, or `frameId` must resolve to real, non-hallucinated documents within the input data packets.

---

## 🇺🇦 4. Ukrainian Terminology & Technical Term Benchmark
To pass quality checks, the pipeline must recognize and correctly map technical terms to avoid loose generic translations. The benchmark checks for a **>= 80% recall** of these key groupings:

### A. Smokehouse Engineering
* **Ukrainian**: *коптильна камера*, *димогенератор*, *конденсатовідвідник*, *нагнітач повітря*, *дефлектор*
* **English Equivs**: smoke chamber, smoke generator, condenser, air blower, deflector.

### B. Materials & Manufacturing
* **Ukrainian**: *нержавіюча сталь AISI 304*, *харчова сталь*, *аргонне зварювання*, *конвекція*, *PID-терморегулятор*
* **English Equivs**: stainless steel AISI 304, food-grade steel, argon welding, convection, PID controller.

### C. Smoking Craft
* **Ukrainian**: *тріска / щепа*, *холодне копчення*, *гаряче копчення*, *температура ядра продукту*
* **English Equivs**: wood chips, cold smoking, hot smoking, product core temperature.

---

## 🚀 5. Implementation Guidance
* Run the benchmark via:
  ```bash
  pnpm test tests/pipeline/analyzers/reburn-scenarios-benchmark.test.ts
  ```
* Ensure `verify_all.sh` remains green before committing any changes.
* When adding a new ReBurn scenario, update the list of registered manifests in `src/fixtures/reburn/manifests.ts` and define the corresponding mock artifacts in `packages/video-audit-core`.
