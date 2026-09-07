# 🔌 Direct REST LLM Provider Adapters & Gateway Policies

This reference guide details the production architecture pattern for integrating multiple LLM providers (e.g., Google Gemini and Anthropic Claude) directly via lightweight REST interfaces, without relying on vendor SDKs in the core logic.

---

## 🏛️ 1. SDK-Free Isolation Pattern

Rather than importing massive SDKs (like `@google/genai` or `@anthropic-ai/sdk`) directly into your core domain, isolate them behind a clean, provider-agnostic port definition in your application service layer.

```text
infrastructure/llm/
  ├── shared/
  │     ├── provider-port.ts    # Agnostic interfaces (LiveMultimodalProviderPort)
  │     ├── provider-errors.ts  # Consolidated neutral exception hierarchy
  │     ├── retry-policy.ts     # Idempotent retry governor with promise coalescing
  │     ├── token-budget.ts     # Local context budget / proactive overflow checks
  │     └── telemetry.ts        # Sanitized token / latency metrics recorder
  ├── gemini/
  │     ├── client.ts           # Direct fetch rest-client for Gemini
  │     ├── adapter.ts          # Orchestrator binding port + retry + budget + mapper
  │     └── mapper.ts           # Translates inputs/outputs and API errors
  └── claude/
        ├── client.ts           # Direct fetch rest-client for Claude
        ├── adapter.ts          # Orchestrator binding port + retry + budget + mapper
        └── mapper.ts           # Translates inputs/outputs and API errors
```

---

## 🛡️ 2. Agnostic Exception Classification

Every provider has its own set of HTTP codes, error messages, and payload formats. Design an abstract exception hierarchy to unify error handling across all clients:

```typescript
export abstract class ProviderError extends Error {
  public abstract readonly isRetryable: boolean;
  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
  }
}

// ⏳ Retryable Errors (Temporary failures, safe to try again)
export class RateLimitExceededError extends ProviderError { readonly isRetryable = true; }
export class TimeoutError extends ProviderError { readonly isRetryable = true; }
export class ProviderServerError extends ProviderError { readonly isRetryable = true; }
export class NetworkConnectionError extends ProviderError { readonly isRetryable = true; }

// 🛑 Permanent Errors (Configuration, syntax, or content policy violations)
export class AuthenticationError extends ProviderError { readonly isRetryable = false; }
export class ContextOverflowError extends ProviderError { readonly isRetryable = false; }
export class ContentPolicyViolationError extends ProviderError { readonly isRetryable = false; }
export class SchemaViolationError extends ProviderError { readonly isRetryable = false; }
```

---

## 🗝️ 3. Idempotent Retry Governor & Promise Coalescing

To prevent duplicate LLM calls on high-concurrency requests or flaky network retries, use a deterministic SHA-256 Idempotency Key combined with a Promise Coalescing Lock (Coalescent Locking).

### A. Key Synthesis
Generate a key from the exact input/prompt signature:
$$\text{SHA-256}(\text{referenceAssetId} + \text{inputArtifactHashes} + \text{promptVersion} + \text{modelVersion} + \text{providerId})$$

### B. Promise Coalescing
If a duplicate request is already in-flight, await the *existing* promise instead of initiating a new LLM request:

```typescript
export class IdempotentRetryExecutor {
  private cache = new Map<string, ProviderAuditResult>();
  private activePromises = new Map<string, Promise<ProviderAuditResult>>();

  public async execute(
    key: string,
    executeFn: () => Promise<ProviderAuditResult>
  ): Promise<ProviderAuditResult> {
    // 1. Return already completed cached result
    if (this.cache.has(key)) {
      return this.cache.get(key)!;
    }

    // 2. Coalesce in-flight duplicates
    if (this.activePromises.has(key)) {
      return this.activePromises.get(key)!;
    }

    // 3. Initiate request with exponential backoff & jitter
    const executionPromise = (async () => {
      try {
        const result = await this.executeWithRetry(executeFn);
        this.cache.set(key, result);
        return result;
      } finally {
        this.activePromises.delete(key);
      }
    })();

    this.activePromises.set(key, executionPromise);
    return executionPromise;
  }
}
```

---

## ⚖️ 4. Proactive Context Budgeting & Token Management

Never rely solely on the remote API to detect context window overflows. Doing so is expensive and slow. Keep track of estimated token usage locally:

```typescript
export class TokenBudgetManager {
  // Rough estimate: 1 token ≈ 4 characters
  public static estimateTokens(text: string): number {
    return Math.ceil(text.length / 4);
  }

  public static enforceBudget(prompt: string, ceiling: number): void {
    const estimated = this.estimateTokens(prompt);
    // Allow a 10% safety buffer before rejecting
    if (estimated > ceiling * 0.9) {
      throw new ContextOverflowError(
        `Proactive Context Overflow: estimated prompt tokens (${estimated}) exceeds 90% of model limit (${ceiling})`
      );
    }
  }
}
```

---

## 🔒 5. Redaction of Sensitive Prompt Content

Your centralized telemetry and log sinks must never ingest API keys or raw user prompt contents. Create a sanitization layer that intercepts all log requests:

```typescript
export class SecureTelemetryLogger {
  public static log(
    providerId: string,
    modelId: string,
    assetId: string,
    status: 'success' | 'failure',
    metrics: { inputTokens: number; outputTokens: number; latencyMs: number },
    error?: Error
  ): void {
    // Standardized secure log structure - strictly metadata only!
    const logObj = {
      timestamp: new Date().toISOString(),
      providerId,
      modelId,
      assetId,
      status,
      ...metrics,
      errorName: error?.name,
      errorMessage: error ? this.sanitizeMessage(error.message) : undefined,
    };
    console.log(`[LLM_TELEMETRY] ${modelId} | Asset: ${assetId} | Status: ${status} | Latency: ${metrics.latencyMs}ms | InputTokens: ${metrics.inputTokens} | OutputTokens: ${metrics.outputTokens}${error ? ` | Error: ${error.name} (${error.message})` : ''}`);
  }

  private static sanitizeMessage(message: string): string {
    // Redact potential bearer tokens, hex hashes, or nested prompt content from error strings
    return message
      .replace(/AIzaSy[A-Za-z0-9-_]{35}/g, '[REDACTED_GEMINI_KEY]')
      .replace(/sk-ant-[A-Za-z0-9-_]{50,}/g, '[REDACTED_CLAUDE_KEY]');
  }
}
```

---

## 💰 6. Spend Protection & Live Provider Qualification Gating

Live tests hitting real LLM APIs must never run in standard CI or unmonitored environments, risking unbounded billings or credential leakage.

### A. Environment-Injected Secret Invariant
* Never commit API keys or pull them from repo-level `.env` files in production logic.
* In production and staging, keys must be dynamically injected via secure environment variables or secret managers (e.g. AWS Secrets Manager, Vault, GCP Secret Manager).

### B. Dedicated Live Test Gating
Live integration tests should only execute when an explicit opt-in environment flag is supplied:
```bash
RUN_LIVE_LLM_TESTS=1 pnpm test:live
```
Standard `pnpm test` must automatically skip (or mock) live provider calls.

### C. LiveSpendGuard Invariant
Wrap any live qualification or probe run in a spend-guard that halts the run immediately upon exceeding safety thresholds:
```typescript
export interface SpendLimits {
  maxRequestsPerRun: number;   // e.g. 5
  maxInputTokens: number;      // e.g. 30,000
  maxOutputTokens: number;     // e.g. 4,000
  maxCostEstimateUsd: number;  // e.g. $0.05
  allowedModels: string[];     // explicit whitelist
}
```
If an unauthorized model ID is requested or a threshold is breached, throw `SpendLimitExceededError` fail-closed.

---

## ⚡ 7. Vertex AI OpenAPI Endpoint & Thinking Models Invariant

When integrating Google Vertex AI via direct REST or OpenAI-compatible client adapters (`_VertexOpenAI`):

### A. Thinking / Reasoning Token Budget Depletion
Modern Gemini architectures (Gemini 2.5, 3.0, 3.8-flash) emit internal thinking/reasoning tokens prior to generating output text.
* **Pitfall**: Setting a low `max_tokens` (e.g., `<= 16` or `<= 32` for binary classification, smart approvals, or sentiment tags) causes the reasoning step to consume the entire token budget before emitting visible text. The model terminates with `finish_reason: length` and `message.content: null`, triggering downstream `AttributeError: 'NoneType' object has no attribute 'content'` or hanging timeouts.
* **Remedy**: Always enforce a lower-bound ceiling of `max_tokens >= 64` (recommended: `128`) for auxiliary/decision tasks, or explicitly disable thinking tokens (`thinking_budget: 0`) if supported by the provider payload.

### B. Vertex AI OpenAI-Compatible Endpoint Model Namespacing
The unified OpenAPI endpoint (`https://{region}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{region}/endpoints/openapi`):
* **Format Requirement**: Strictly enforces `<publisher>/<model>` naming (e.g., `google/gemini-3.8-flash` or `google/gemini-2.5-flash`). Supplying bare names like `gemini-3.8-flash` causes an immediate HTTP 400 (`Malformed publisher model`).
* **Endpoint Selection**: The OpenAPI-compatible endpoint provides lower latency (~0.8s) and predictable streaming behavior compared to legacy publisher endpoints (`.../publishers/google/models/...:generateContent`) for tool-calling and auxiliary governance tasks.

