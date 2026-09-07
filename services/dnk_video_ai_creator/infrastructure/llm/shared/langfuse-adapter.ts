/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/shared/langfuse-adapter.ts"
# purpose: "Langfuse Telemetry Adapter with Async Non-Blocking Export & Resilient Local Fallback."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { LlmMetrics, LlmTelemetry, LocalJsonTelemetry } from './telemetry.js';

export interface LangfuseConfig {
  publicKey?: string;
  secretKey?: string;
  baseUrl?: string;
  fallbackLogger?: LlmTelemetry;
}

export class LangfuseTelemetry implements LlmTelemetry {
  private readonly config: LangfuseConfig;
  private readonly fallback: LlmTelemetry;
  private langfuseClient: any = null;
  private isClientInitialized: boolean = false;

  constructor(config?: LangfuseConfig) {
    this.config = {
      publicKey: config?.publicKey ?? process.env.LANGFUSE_PUBLIC_KEY,
      secretKey: config?.secretKey ?? process.env.LANGFUSE_SECRET_KEY,
      baseUrl: config?.baseUrl ?? process.env.LANGFUSE_BASE_URL ?? 'https://cloud.langfuse.com',
      fallbackLogger: config?.fallbackLogger,
    };
    this.fallback = this.config.fallbackLogger ?? new LocalJsonTelemetry();
  }

  public isConfigured(): boolean {
    return Boolean(this.config.publicKey && this.config.secretKey);
  }

  private async getLangfuseClient(): Promise<any> {
    if (this.isClientInitialized) {
      return this.langfuseClient;
    }
    this.isClientInitialized = true;

    if (!this.isConfigured()) {
      return null;
    }

    try {
      // Dynamic import to prevent runtime failures if langfuse package is not installed
      // @ts-ignore
      const langfuseModule = await import('langfuse');
      const LangfuseConstructor = langfuseModule.Langfuse || (langfuseModule as any).default?.Langfuse;
      if (LangfuseConstructor) {
        this.langfuseClient = new LangfuseConstructor({
          publicKey: this.config.publicKey,
          secretKey: this.config.secretKey,
          baseUrl: this.config.baseUrl,
        });
      }
    } catch (err) {
      // Langfuse SDK not found or failed to load
      this.langfuseClient = null;
    }

    return this.langfuseClient;
  }

  public async recordMetrics(metrics: LlmMetrics): Promise<void> {
    // 1. Always record in fallback local logger to ensure no metrics are lost
    try {
      await this.fallback.recordMetrics(metrics);
    } catch (fallbackErr) {
      console.warn('[LangfuseTelemetry] Fallback telemetry failed:', fallbackErr);
    }

    // 2. If Langfuse is not configured, exit early without errors
    if (!this.isConfigured()) {
      return;
    }

    // 3. Attempt async export to Langfuse (non-blocking)
    try {
      const client = await this.getLangfuseClient();
      if (client && typeof client.trace === 'function') {
        const trace = client.trace({
          id: metrics.requestId,
          name: `llm-call-${metrics.modelId}`,
          metadata: {
            modelId: metrics.modelId,
            success: metrics.success,
            errorCode: metrics.errorCode,
            circuitTripped: metrics.circuitTripped ?? false,
            timestamp: metrics.timestamp,
            ...(metrics.metadata ?? {}),
          },
        });

        if (typeof trace.generation === 'function') {
          trace.generation({
            name: `generation-${metrics.modelId}`,
            model: metrics.modelId,
            usage: {
              input: metrics.tokensIn,
              output: metrics.tokensOut,
              total: metrics.tokensIn + metrics.tokensOut,
            },
            latency: metrics.latencyMs / 1000, // Langfuse expects seconds
            metadata: {
              spendTracked: metrics.spendTracked,
            },
          });
        }

        if (typeof client.flushAsync === 'function') {
          await client.flushAsync();
        }
      } else {
        // Alternative lightweight HTTP ingestion fallback if SDK not present
        await this.postDirectHttpIngestion(metrics);
      }
    } catch (langfuseErr) {
      // Non-blocking: catch and warn, local fallback is already recorded
      console.warn('[LangfuseTelemetry] Failed to export metrics to Langfuse (fallback preserved):', langfuseErr);
    }
  }

  private async postDirectHttpIngestion(metrics: LlmMetrics): Promise<void> {
    if (!this.config.baseUrl || !this.config.publicKey || !this.config.secretKey) {
      return;
    }

    try {
      const auth = Buffer.from(`${this.config.publicKey}:${this.config.secretKey}`).toString('base64');
      const url = `${this.config.baseUrl.replace(/\/$/, '')}/api/public/ingestion`;
      const body = {
        batch: [
          {
            id: `event-${metrics.requestId}`,
            type: 'trace-create',
            timestamp: metrics.timestamp,
            body: {
              id: metrics.requestId,
              name: `llm-call-${metrics.modelId}`,
              metadata: {
                modelId: metrics.modelId,
                success: metrics.success,
                errorCode: metrics.errorCode,
                latencyMs: metrics.latencyMs,
                spendTracked: metrics.spendTracked,
                tokensIn: metrics.tokensIn,
                tokensOut: metrics.tokensOut,
              },
            },
          },
        ],
      };

      if (typeof fetch !== 'undefined') {
        await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Basic ${auth}`,
          },
          body: JSON.stringify(body),
        });
      }
    } catch (httpErr) {
      // Ignored non-blocking
    }
  }

  public getFallback(): LlmTelemetry {
    return this.fallback;
  }
}
