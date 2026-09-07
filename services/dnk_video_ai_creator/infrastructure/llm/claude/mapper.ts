/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/claude/mapper.ts"
# purpose: "Anthropic Claude Response & Error Adapter Mapping Layer."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import {
  RateLimitError,
  InvalidCredentialsError,
  InvalidModelError,
  TemporaryServerError,
  ContentPolicyError,
  ProviderError,
  NetworkFailureError,
} from '../shared/provider-errors.js';
import { ClaudeResponsePayload } from './client.js';
import { ProviderAuditResult } from '../shared/provider-port.js';

export class ClaudeMapper {
  /**
   * Maps Claude message response into a normalized ProviderAuditResult.
   */
  public static mapResponse(
    response: ClaudeResponsePayload,
    status: number,
    modelName: string,
    promptVersion: string,
    inputArtifactHashes: Record<string, string>,
    latencyMs: number
  ): ProviderAuditResult {
    if (status !== 200 || response.error) {
      throw this.mapError(status, response);
    }

    const textPart = response.content?.[0];
    if (!textPart || textPart.type !== 'text' || textPart.text === undefined) {
      throw new ProviderError('No text content returned from Claude.', 'claude');
    }

    const inputTokens = response.usage?.input_tokens;
    const outputTokens = response.usage?.output_tokens;

    return {
      rawOutput: textPart.text,
      providerId: 'claude',
      modelVersion: modelName,
      promptVersion,
      inputArtifactHashes,
      usage: {
        inputTokens,
        outputTokens,
        latencyMs,
      },
    };
  }

  /**
   * Translates Claude HTTP status codes and error bodies to standard ProviderError subclasses.
   */
  public static mapError(status: number, errorBody: any): Error {
    const errorDetail = errorBody?.error;
    const type = errorDetail?.type || '';
    const message = errorDetail?.message || JSON.stringify(errorBody);

    if (type === 'authentication_error') {
      return new InvalidCredentialsError(`Claude Auth Error: ${message}`, 'claude', errorBody);
    }
    if (type === 'permission_error') {
      return new ContentPolicyError(`Claude Safety Block: ${message}`, 'claude', errorBody);
    }
    if (type === 'rate_limit_error' || status === 429) {
      return new RateLimitError(`Claude Rate Limit Exceeded: ${message}`, 'claude', 5000, errorBody);
    }
    if (type === 'invalid_request_error') {
      if (message.includes('model') || message.includes('Model')) {
        return new InvalidModelError(`Claude Model Configuration Error: ${message}`, 'claude', errorBody);
      }
      return new ProviderError(`Claude Bad Request: ${message}`, 'claude', errorBody);
    }
    if (type === 'api_error' || status >= 500) {
      return new TemporaryServerError(`Claude API/Server Error (${status}): ${message}`, 'claude', errorBody);
    }
    if (type === 'overloaded_error') {
      return new TemporaryServerError(`Claude Overloaded Error: ${message}`, 'claude', errorBody);
    }

    switch (status) {
      case 401:
      case 403:
        return new InvalidCredentialsError(`Claude Auth Error: ${message}`, 'claude', errorBody);
      case 404:
        return new InvalidModelError(`Claude Endpoint Not Found: ${message}`, 'claude', errorBody);
      default:
        return new NetworkFailureError(`Claude Request Failed (${status}): ${message}`, 'claude', errorBody);
    }
  }
}
