/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/gemini/adapter.ts"
# purpose: "Google Gemini Provider Adapter implementing LiveMultimodalProviderPort."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { LiveMultimodalProviderPort, ProviderAuditResult } from '../shared/provider-port.js';
import { GeminiClient } from './client.js';
import { GeminiMapper } from './mapper.js';
import { TokenBudgetManager } from '../shared/token-budget.js';
import { LLMTelemetryManager } from '../shared/telemetry.js';
import { MultimodalAuditInput, MultimodalAuditContext } from '@dnk/video-audit-core';
import { PromptPipeline } from '@dnk/video-audit-core';

export interface GeminiAdapterOptions {
  apiKey?: string;
  baseUrl?: string;
  fetchFn?: typeof fetch;
  temperature?: number;
  maxOutputTokens?: number;
}

export class GeminiAdapter implements LiveMultimodalProviderPort {
  public readonly providerId = 'gemini';
  public readonly modelSetVersion: string;
  
  private readonly client: GeminiClient;
  private readonly promptPipeline = new PromptPipeline();
  private readonly temperature: number;
  private readonly maxOutputTokens?: number;

  constructor(modelSetVersion = 'gemini-1.5-flash', options: GeminiAdapterOptions = {}) {
    this.modelSetVersion = modelSetVersion;
    this.client = new GeminiClient({
      apiKey: options.apiKey,
      baseUrl: options.baseUrl,
      fetchFn: options.fetchFn,
    });
    this.temperature = options.temperature ?? 0.1;
    this.maxOutputTokens = options.maxOutputTokens;
  }

  public async analyze(
    input: MultimodalAuditInput,
    context: MultimodalAuditContext
  ): Promise<ProviderAuditResult> {
    const startTime = Date.now();

    // 1. Generate system-governed versioned prompt
    const { prompt, inputArtifactHashes } = this.promptPipeline.generatePrompt(input, context);

    // 2. Context & Token Budget Verification
    TokenBudgetManager.enforceBudget(this.providerId, this.modelSetVersion, prompt, this.maxOutputTokens);

    // 3. Prepare Gemini API JSON payload
    const payload = {
      contents: [
        {
          role: 'user',
          parts: [{ text: prompt }],
        },
      ],
      generationConfig: {
        responseMimeType: 'application/json',
        temperature: this.temperature,
        maxOutputTokens: this.maxOutputTokens,
      },
    };

    try {
      // 4. Perform the API call via client
      const { response, status } = await this.client.generateContent(this.modelSetVersion, payload);
      const latencyMs = Date.now() - startTime;

      // 5. Map Gemini response into ProviderAuditResult
      const result = GeminiMapper.mapResponse(
        response,
        status,
        this.modelSetVersion,
        '1.0.0', // Prompt version
        inputArtifactHashes,
        latencyMs
      );

      // Record successful token consumption to Budget Manager
      if (result.usage?.inputTokens && result.usage?.outputTokens) {
        TokenBudgetManager.recordUsage(result.usage.inputTokens, result.usage.outputTokens);
      }

      // Log successful telemetry
      LLMTelemetryManager.logExecution({
        providerId: this.providerId,
        modelVersion: this.modelSetVersion,
        referenceAssetId: input.referenceAssetId,
        status: 'success',
        latencyMs,
        inputTokens: result.usage?.inputTokens,
        outputTokens: result.usage?.outputTokens,
      });

      return result;
    } catch (error: any) {
      const latencyMs = Date.now() - startTime;

      // Handle raw errors or already mapped error instances
      const mappedError = error.providerId ? error : GeminiMapper.mapError(error.status || 500, error);

      // Log failure telemetry
      LLMTelemetryManager.logExecution({
        providerId: this.providerId,
        modelVersion: this.modelSetVersion,
        referenceAssetId: input.referenceAssetId,
        status: 'failure',
        latencyMs,
        errorClass: mappedError.constructor.name,
        errorMessage: mappedError.message,
      });

      throw mappedError;
    }
  }
}
