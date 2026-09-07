# --- DNK-MRH-HEADER ---
# mrh_id: "references/niche_adaptation_engine_and_spendguard_protocol.md"
# purpose: "Niche Adaptation Engine architectural patterns, SpendGuard patterns, dynamic timeline, sidecar caching, and contract mapping."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧬 Niche Adaptation Engine & SpendGuard-Guarded LLM Protocol

## 🎯 Core Architectural Concepts

The Niche Adaptation Engine (`@dnk/video-audit-core/src/adaptation`) handles the secure transformation of original video transcripts/audits into compliant scripts and assets for new brands/products. To ensure 100% robustness, compliance, and budget safety, follow these patterns:

---

### 1. Explicit Data Mapping Contract (Report Decoupling)
*   **Problem**: Downstream adaptation services (e.g. `MechanismExtractor`) should not depend directly on the dense, nested, and potentially volatile structure of the `VideoAuditReport` directly.
*   **Pattern**: Implement an explicit translation layer or mapper (`mapAuditReportToExtractionInput`) to transform the report into a lean, dedicated interface (`MechanismExtractionInput`). This prevents breaking downstream logic when report schemas evolve.
*   **Implementation Example**:
    ```typescript
    export function mapAuditReportToExtractionInput(report: VideoAuditReport): MechanismExtractionInput {
      return {
        observedFacts: (report.findings || []).map(f => f.text),
        keyInsights: [
          ...(report.structure?.takeaways || []),
          ...(report.strengths || []).map(s => s.text)
        ]
      };
    }
    ```

---

### 2. Proportional Chronological Timeline Constraining
*   **Problem**: Automated script writers (deterministic or LLM-driven) often hardcode scene durations. Under low target durations (e.g. `15000ms`), hardcoded durations cause the cumulative time to exceed the target or cause later scenes (e.g. `CTA`) to have a `startMs` greater than the requested `targetDurationMs` or `endMs`, causing schema or runtime validation exceptions (e.g. Zod `.refine(startMs <= endMs)`).
*   **Pattern**: Calculate scene durations proportionally and dynamically based on `targetDurationMs`. Constrain and distribute the remaining time proportionally among the mid-scenes after deducting fixed/minimum scene times (e.g. hook and CTA).
*   **Dynamic Ratio Split Formula**:
    ```typescript
    const hookDurationMs = 3500;
    const ctaDurationMs = 5000;
    const remainingMs = Math.max(5000, request.targetDurationMs - hookDurationMs - ctaDurationMs);

    // Proportional splits of remaining time (e.g. 40% problem, 60% solution)
    const problemDurationMs = Math.round(remainingMs * 0.4);
    const solutionDurationMs = Math.round(remainingMs * 0.6);

    const scenes = [
      { id: "hook", startMs: 0, endMs: hookDurationMs },
      { id: "problem", startMs: hookDurationMs, endMs: hookDurationMs + problemDurationMs },
      { id: "solution", startMs: hookDurationMs + problemDurationMs, endMs: hookDurationMs + problemDurationMs + solutionDurationMs },
      { id: "cta", startMs: hookDurationMs + problemDurationMs + solutionDurationMs, endMs: request.targetDurationMs }
    ];
    ```

---

### 3. SpendGuard-Guarded LLM Adapter with Graceful Fallbacks
*   **Problem**: Dynamic LLM generation can incur high token or API usage costs, risking budget depletion in automated multi-agent runs or infinite loop cycles.
*   **Pattern**: Wrap all LLM-driven operations under a dedicated cost tracking guard (`SpendGuard`). If the accumulated session costs exceed a tight safety limit (e.g. `$0.15`), or if the LLM provider experiences network/auth drops, intercept the error and execute a **graceful fallback** to a deterministic, zero-cost generator (`DeterministicScriptWriter`).
*   **Resiliency Design Pattern**:
    ```typescript
    export class LiveLlmScriptWriter implements ScriptWriter {
      constructor(
        private llmClient: LlmClient,
        private spendGuard: SpendGuard,
        private fallbackWriter: ScriptWriter
      ) {}

      async generate(request: AdaptationRequest, mechanisms: MechanismExtractionResult): Promise<ScriptDocument> {
        if (this.spendGuard.isBudgetExhausted()) {
          console.warn("SpendGuard budget exhausted. Falling back to deterministic script writer.");
          return this.fallbackWriter.generate(request, mechanisms);
        }

        try {
          const result = await this.llmClient.generate(request, mechanisms);
          this.spendGuard.recordUsage(result.inputTokens, result.outputTokens);
          return result;
        } catch (error) {
          console.error("LLM generation failed, falling back gracefully:", error);
          return this.fallbackWriter.generate(request, mechanisms);
        }
      }
    }
    ```

---

### 4. Lexical Pattern Generalization
*   **Problem**: Strict lexical matching (e.g. exact substring search for `"сертифікат"`) fails when matching inflected/declined grammatical variants in highly inflected languages like Ukrainian (e.g., `"сертифікати"`, `"сертифікацію"`, `"сертифіковане"`).
*   **Pattern**: Reduce key brand-guard or policy-guard matches to root-level stems or prefix substrings (e.g., matching `"сертифік"` or `"європейськ"`). This provides high classification recall and blocks unapproved claims robustly.

---

### 5. Robust Sidecar Caching Invariants for AI Tasks
*   **Problem**: Heavy/expensive AI operations (e.g., speech-to-text, translation, OCR) need local file system caching (Sidecar Caching) to bypass remote provider APIs, but simple name-based caching is fragile. Corrupt JSON caches or stale inputs (e.g., when the raw source video/audio content changes) can result in incorrect outputs or crashing pipelines.
*   **Pattern**: Implement sidecar caching using strict cryptographic hashing and contract schemas:
    1. **Multi-Factor Cache Key**: Cache keys must combine the source's asset reference and all critical input variables to ensure deterministic isolation (e.g., `references/${job.referenceAssetId}/transcript/${providerId}-${modelVersion}-${schemaVersion}-${languageHint}.json`).
    2. **Cryptographic Source Hash (Content Integrity)**: Store and match the source file's SHA-256 hash (`source_sha256`) in the cache metadata. If the video file is updated or replaced, the hash fails to match, prompting an automatic Cache Miss.
    3. **Schema Validation on Read**: Before returning the cached document, parse it through its target validation schema (e.g., Zod's `TranscriptDocumentSchema.safeParse`). If validation fails (e.g., corrupted file or outdated scheme format), bypass the cache cleanly with a fallback to the remote provider instead of failing the pipeline.
    4. **Artifact Manifest Mapping**: Accompany each cache JSON write with a manifest registration tracking the file generation date and checksum.

---

### 6. Speaking Pacing & Duration Policies
*   **Problem**: Hardcoding expected words-per-minute (WPM) speeds across transcription analyzers and script writers limits flexibility when evaluating adaptation results with differing spoken tempos.
*   **Pattern**:
    1. **Metadata-Driven Pacing**: Instead of using global static constants, dynamically calculate the expected/target speaking rate and store it directly in the adaptation's metadata (e.g., `prosody.globalPacing.targetWpm` within the generated `ProsodyDocument`).
    2. **Fallback Cascades**: Configure evaluators and policies to dynamically pull the WPM pacing from the metadata (`input.prosody?.globalPacing?.targetWpm`), falling back on standard defaults (such as `130` WPM) only when missing.
    3. **Pacing Constraints (Duration Tolerance)**: Calculate actual durations using the total word count divided by the computed WPM rate, asserting tolerances (e.g., ±25% duration limits) cleanly.

---

### 7. Dashed-to-Underscore Module Hygiene in Mixed Mono-repos
*   **Problem**: In mixed Node.js/Python mono-repos, TypeScript workspace directories frequently use dashed naming conventions (e.g., `packages/video-audit-core`), but Python module import systems explicitly forbid dashes (`-`) in package names, requiring underscores (`_`).
*   **Pattern**: Maintain the canonical NPM package and directory name with dashes (`video-audit-core`) to preserve TypeScript references and lockfiles (`pnpm-workspace.yaml`, `tsconfig.json`). Create a symbolic link (symlink) using underscores (`video_audit_core`) pointing directly to the dashed directory. This allows Python scripts to easily run in `.venv` and import the local directory without renaming the canonical NPM codebase or breaking TS workspace integrity.
