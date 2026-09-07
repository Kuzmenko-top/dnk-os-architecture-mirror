/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/shared/telemetry.ts"
# purpose: "Secure LLM Execution Telemetry, Metrics Logging, Dashboard Metrics, and Multi-Target Exporters."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import * as fs from 'fs';
import * as path from 'path';

export interface LlmMetrics {
  requestId: string;
  modelId: string;
  latencyMs: number;
  tokensIn: number;
  tokensOut: number;
  spendTracked: number;
  circuitTripped?: boolean;
  success: boolean;
  errorCode?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface LlmTelemetry {
  recordMetrics(metrics: LlmMetrics): Promise<void>;
}

export interface DashboardMetrics {
  spendPerHour: number;
  spendPerDay: number;
  spendPerWeek: number;
  totalSpend: number;
  avgLatencyMs: number;
  latencyP50: number;
  latencyP95: number;
  latencyP99: number;
  successRate: number;
  circuitBreakerTrips: number;
  topAdaptationRequestsByCost: Array<{
    requestId: string;
    modelId: string;
    spendTracked: number;
    timestamp: string;
  }>;
}

export interface TelemetryEvent {
  providerId: string;
  modelVersion: string;
  referenceAssetId: string;
  status: 'success' | 'failure' | 'manual_review';
  latencyMs: number;
  inputTokens?: number;
  outputTokens?: number;
  errorClass?: string;
  errorMessage?: string;
}

export class LocalJsonTelemetry implements LlmTelemetry {
  private readonly records: LlmMetrics[] = [];
  private readonly logFilePath?: string;

  constructor(options?: { logFilePath?: string }) {
    this.logFilePath = options?.logFilePath;
  }

  public async recordMetrics(metrics: LlmMetrics): Promise<void> {
    const sanitized = this.sanitizeMetrics(metrics);
    this.records.push(sanitized);

    if (this.logFilePath) {
      try {
        const dir = path.dirname(this.logFilePath);
        if (!fs.existsSync(dir)) {
          fs.mkdirSync(dir, { recursive: true });
        }
        fs.appendFileSync(this.logFilePath, JSON.stringify(sanitized) + '\n', 'utf-8');
      } catch (err) {
        console.warn(`[LocalJsonTelemetry] Failed to write log to ${this.logFilePath}:`, err);
      }
    }
  }

  public getRecords(): LlmMetrics[] {
    return [...this.records];
  }

  public clear(): void {
    this.records.length = 0;
  }

  public calculateDashboardMetrics(now: Date = new Date()): DashboardMetrics {
    if (this.records.length === 0) {
      return {
        spendPerHour: 0,
        spendPerDay: 0,
        spendPerWeek: 0,
        totalSpend: 0,
        avgLatencyMs: 0,
        latencyP50: 0,
        latencyP95: 0,
        latencyP99: 0,
        successRate: 1.0,
        circuitBreakerTrips: 0,
        topAdaptationRequestsByCost: [],
      };
    }

    const nowMs = now.getTime();
    const oneHourMs = 3600 * 1000;
    const oneDayMs = 24 * oneHourMs;
    const oneWeekMs = 7 * oneDayMs;

    let spendHour = 0;
    let spendDay = 0;
    let spendWeek = 0;
    let totalSpend = 0;
    let successCount = 0;
    let circuitTrips = 0;

    const latencies: number[] = [];

    for (const r of this.records) {
      const recordTime = new Date(r.timestamp).getTime();
      const ageMs = Math.max(0, nowMs - recordTime);

      totalSpend += r.spendTracked;
      if (ageMs <= oneHourMs) spendHour += r.spendTracked;
      if (ageMs <= oneDayMs) spendDay += r.spendTracked;
      if (ageMs <= oneWeekMs) spendWeek += r.spendTracked;

      if (r.success) successCount += 1;
      if (r.circuitTripped) circuitTrips += 1;

      latencies.push(r.latencyMs);
    }

    latencies.sort((a, b) => a - b);
    const avgLatencyMs = latencies.reduce((sum, v) => sum + v, 0) / latencies.length;

    const p50 = this.getPercentile(latencies, 0.50);
    const p95 = this.getPercentile(latencies, 0.95);
    const p99 = this.getPercentile(latencies, 0.99);

    const sortedByCost = [...this.records]
      .sort((a, b) => b.spendTracked - a.spendTracked)
      .slice(0, 10)
      .map((r) => ({
        requestId: r.requestId,
        modelId: r.modelId,
        spendTracked: r.spendTracked,
        timestamp: r.timestamp,
      }));

    return {
      spendPerHour: Number(spendHour.toFixed(6)),
      spendPerDay: Number(spendDay.toFixed(6)),
      spendPerWeek: Number(spendWeek.toFixed(6)),
      totalSpend: Number(totalSpend.toFixed(6)),
      avgLatencyMs: Number(avgLatencyMs.toFixed(2)),
      latencyP50: Number(p50.toFixed(2)),
      latencyP95: Number(p95.toFixed(2)),
      latencyP99: Number(p99.toFixed(2)),
      successRate: Number((successCount / this.records.length).toFixed(4)),
      circuitBreakerTrips: circuitTrips,
      topAdaptationRequestsByCost: sortedByCost,
    };
  }

  private getPercentile(sorted: number[], p: number): number {
    if (sorted.length === 0) return 0;
    const index = (sorted.length - 1) * p;
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    const weight = index - lower;
    return sorted[lower] * (1 - weight) + sorted[upper] * weight;
  }

  private sanitizeMetrics(m: LlmMetrics): LlmMetrics {
    const sanitizedError = m.errorCode ? this.sanitizeString(m.errorCode) : undefined;
    return {
      ...m,
      errorCode: sanitizedError,
    };
  }

  private sanitizeString(text: string): string {
    let cleaned = text;
    cleaned = cleaned.replace(/\b[0-9a-fA-F]{32,}\b/g, '[REDACTED_HEX_KEY]');
    cleaned = cleaned.replace(/(bearer\s+)[a-zA-Z0-9_\-\.]+/gi, '$1[REDACTED_TOKEN]');
    cleaned = cleaned.replace(/(password|key|secret)=[^&\s]+/gi, '$1=[REDACTED]');
    return cleaned;
  }
}

export class CompositeTelemetry implements LlmTelemetry {
  private readonly exporters: LlmTelemetry[];

  constructor(exporters: LlmTelemetry[]) {
    this.exporters = exporters;
  }

  public async recordMetrics(metrics: LlmMetrics): Promise<void> {
    // Non-blocking parallel execution: never throw error back to the caller
    const tasks = this.exporters.map(async (exporter) => {
      try {
        await exporter.recordMetrics(metrics);
      } catch (err) {
        console.warn('[CompositeTelemetry] One of telemetry exporters threw error:', err);
      }
    });

    await Promise.all(tasks);
  }
}

export class LLMTelemetryManager {
  private static events: TelemetryEvent[] = [];

  public static clearEvents(): void {
    this.events = [];
  }

  public static logExecution(event: TelemetryEvent): void {
    const sanitizedError = event.errorMessage
      ? this.sanitizeText(event.errorMessage)
      : undefined;

    const sanitizedEvent: TelemetryEvent = {
      ...event,
      errorMessage: sanitizedError,
    };

    this.events.push(sanitizedEvent);

    console.log(
      `[LLM_TELEMETRY] ${sanitizedEvent.providerId}/${sanitizedEvent.modelVersion} | ` +
        `Asset: ${sanitizedEvent.referenceAssetId} | Status: ${sanitizedEvent.status} | ` +
        `Latency: ${sanitizedEvent.latencyMs}ms | InputTokens: ${sanitizedEvent.inputTokens || 0} | ` +
        `OutputTokens: ${sanitizedEvent.outputTokens || 0}` +
        (sanitizedEvent.errorClass ? ` | Error: ${sanitizedEvent.errorClass} (${sanitizedEvent.errorMessage})` : '')
    );
  }

  public static getEvents(): TelemetryEvent[] {
    return [...this.events];
  }

  private static sanitizeText(text: string): string {
    let cleaned = text;
    cleaned = cleaned.replace(/\b[0-9a-fA-F]{32,}\b/g, '[REDACTED_HEX_KEY]');
    cleaned = cleaned.replace(/(bearer\s+)[a-zA-Z0-9_\-\.]+/gi, '$1[REDACTED_TOKEN]');
    cleaned = cleaned.replace(/(password|key|secret)=[^&\s]+/gi, '$1=[REDACTED]');
    return cleaned;
  }
}
