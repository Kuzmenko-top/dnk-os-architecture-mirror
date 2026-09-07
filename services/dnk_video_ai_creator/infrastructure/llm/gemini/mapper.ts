/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/gemini/mapper.ts"
# purpose: "Google Gemini Response & Error Adapter Mapping Layer."
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
import { GeminiResponsePayload } from './client.js';
import { ProviderAuditResult } from '../shared/provider-port.js';

export class GeminiMapper {
  /**
   * Maps Gemini generateContent response into a normalized ProviderAuditResult.
   */
  public static mapResponse(
    response: GeminiResponsePayload,
    status: number,
    modelName: string,
    promptVersion: string,
    inputArtifactHashes: Record<string, string>,
    latencyMs: number
  ): ProviderAuditResult {
    if (status !== 200) {
      throw this.mapError(status, response);
    }

    const candidate = response.candidates?.[0];
    if (!candidate) {
      throw new ProviderError('No candidate response returned from Gemini.', 'gemini');
    }

    if (candidate.finishReason === 'SAFETY') {
      throw new ContentPolicyError('Response blocked by Gemini safety policy.', 'gemini');
    }

    const text = candidate.content?.parts?.[0]?.text;
    if (text === undefined) {
      throw new ProviderError('Empty text part in Gemini candidate content.', 'gemini');
    }

    const inputTokens = response.usageMetadata?.promptTokenCount;
    const outputTokens = response.usageMetadata?.candidatesTokenCount;

    return {
      rawOutput: text,
      providerId: 'gemini',
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
   * Translates Gemini HTTP status codes and error bodies to standard ProviderError subclasses.
   */
  public static mapError(status: number, errorBody: any): Error {
    const message = errorBody?.error?.message || errorBody?.message || JSON.stringify(errorBody);

    switch (status) {
      case 401:
      case 403:
        return new InvalidCredentialsError(`Gemini Auth Error: ${message}`, 'gemini', errorBody);
      case 429:
        return new RateLimitError(`Gemini Rate Limit Exceeded: ${message}`, 'gemini', 5000, errorBody);
      case 400:
        if (message.includes('model') || message.includes('Model')) {
          return new InvalidModelError(`Gemini Model Configuration Error: ${message}`, 'gemini', errorBody);
        }
        return new ProviderError(`Gemini Bad Request: ${message}`, 'gemini', errorBody);
      case 404:
        return new InvalidModelError(`Gemini Model/Endpoint Not Found: ${message}`, 'gemini', errorBody);
      case 500:
      case 502:
      case 503:
      case 504:
        return new TemporaryServerError(`Gemini Server Error (${status}): ${message}`, 'gemini', errorBody);
      default:
        return new NetworkFailureError(`Gemini Request Failed (${status}): ${message}`, 'gemini', errorBody);
    }
  }
}
