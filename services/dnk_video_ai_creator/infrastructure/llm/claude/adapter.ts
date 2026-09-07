/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/claude/adapter.ts"
# purpose: "Anthropic Claude Provider Adapter implementing LiveMultimodalProviderPort."
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
import { ClaudeClient } from './client.js';
import { ClaudeMapper } from './mapper.js';
import { TokenBudgetManager } from '../shared/token-budget.js';
import { LLMTelemetryManager } from '../shared/telemetry.js';
import { MultimodalAuditInput, MultimodalAuditContext } from '@dnk/video-audit-core';
import { PromptPipeline } from '@dnk/video-audit-core';

export interface ClaudeAdapterOptions {
  apiKey?: string;
  baseUrl?: string;
  fetchFn?: typeof fetch;
  temperature?: number;
  maxOutputTokens?: number;
}

export class ClaudeAdapter implements LiveMultimodalProviderPort {
  public readonly providerId = 'claude';
  public readonly modelSetVersion: string;

  private readonly client: ClaudeClient;
  private readonly promptPipeline = new PromptPipeline();
  private readonly temperature: number;
  private readonly maxOutputTokens: number;

  constructor(modelSetVersion = 'claude-3-5-sonnet-20241022', options: ClaudeAdapterOptions = {}) {
    this.modelSetVersion = modelSetVersion;
    this.client = new ClaudeClient({
      apiKey: options.apiKey,
      baseUrl: options.baseUrl,
      fetchFn: options.fetchFn,
    });
    this.temperature = options.temperature ?? 0.1;
    this.maxOutputTokens = options.maxOutputTokens ?? 4096;
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

    // 3. Prepare Claude Messages JSON payload
    const payload = {
      model: this.modelSetVersion,
      max_tokens: this.maxOutputTokens,
      temperature: this.temperature,
      messages: [
        {
          role: 'user' as const,
          content: prompt,
        },
      ],
    };

    try {
      // 4. Perform the API call via client
      const { response, status } = await this.client.createMessage(payload);
      const latencyMs = Date.now() - startTime;

      // 5. Map Claude response into ProviderAuditResult
      const result = ClaudeMapper.mapResponse(
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
      const mappedError = error.providerId ? error : ClaudeMapper.mapError(error.status || 500, error);

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
