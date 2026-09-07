// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/canvas/ai/ai-client.ts"
// purpose: "HTTP API client for Canvas Engine AI backend endpoints with JWT/Header authentication, error handling, and robust mock fallback."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

import type { AIClientConfig } from './types';

// Standard 1x1 transparent and colored base64 mock assets
const MOCK_TRANSPARENT_PNG =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkWPjfDwAEfQHzx5t0RAAAAABJRU5ErkJggg==';
const MOCK_MASK_PNG =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=';

export interface ExtendedAIClientConfig extends AIClientConfig {
  enableMockFallback?: boolean;
}

export class AIClient {
  private readonly baseUrl: string;
  private readonly workspaceId: string;
  private readonly authToken?: string;
  private readonly timeoutMs: number;
  private readonly enableMockFallback: boolean;

  constructor(config: ExtendedAIClientConfig = {}) {
    this.baseUrl = (config.baseUrl || '').replace(/\/+$/, '');
    this.workspaceId = config.workspaceId || 'ws-alpha-001';
    this.authToken = config.authToken;
    this.timeoutMs = config.timeoutMs || 30000;
    this.enableMockFallback = config.enableMockFallback ?? true;
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Workspace-Id': this.workspaceId,
    };
    if (this.authToken) {
      headers['Authorization'] = this.authToken.startsWith('Bearer ')
        ? this.authToken
        : `Bearer ${this.authToken}`;
    }
    return headers;
  }

  private async postJson<T>(
    endpoint: string,
    body: unknown,
    fallbackGenerator?: () => T
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const controller = new AbortController();
    const timeoutTimer = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
        try {
          const errData = await response.json();
          if (errData && errData.detail) {
            errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch {
          // Fallback to status text
        }
        throw new Error(errorMsg);
      }

      return (await response.json()) as T;
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        throw new Error(`AI Request timed out after ${this.timeoutMs}ms: ${url}`);
      }

      // If backend is unreachable and mock fallback is enabled, return synthesized response
      if (this.enableMockFallback && fallbackGenerator) {
        return fallbackGenerator();
      }

      throw err;
    } finally {
      clearTimeout(timeoutTimer);
    }
  }

  /**
   * BiRefNet background removal
   */
  public async cutout(params: {
    imageBase64?: string;
    imageUrl?: string;
    nodeId?: string;
    canvasId?: string;
    returnMask?: boolean;
    threshold?: number;
    options?: Record<string, unknown>;
  }): Promise<{
    success: boolean;
    image_base64: string;
    mask_base64?: string;
    node_id?: string;
    mime_type: string;
    execution_time_ms: number;
    model: string;
    metadata: Record<string, unknown>;
  }> {
    return this.postJson(
      '/api/v1/canvas/ai/cutout',
      {
        image_base64: params.imageBase64,
        image_url: params.imageUrl,
        node_id: params.nodeId,
        canvas_id: params.canvasId,
        return_mask: params.returnMask ?? false,
        threshold: params.threshold ?? 0.5,
        options: params.options,
      },
      () => ({
        success: true,
        image_base64: params.imageBase64 || MOCK_TRANSPARENT_PNG,
        mask_base64: params.returnMask ? MOCK_MASK_PNG : undefined,
        node_id: params.nodeId,
        mime_type: 'image/png',
        execution_time_ms: 120,
        model: 'birefnet-v1-fallback',
        metadata: {
          feather: 2,
          threshold: params.threshold ?? 0.5,
          fallback: true,
        },
      })
    );
  }

  /**
   * IC-Light relighting
   */
  public async relight(params: {
    foregroundImageBase64?: string;
    foregroundImageUrl?: string;
    backgroundImageBase64?: string;
    backgroundImageUrl?: string;
    foregroundNodeId?: string;
    backgroundNodeId?: string;
    lightingPrompt?: string;
    lightDirection?: string;
    intensity?: number;
    canvasId?: string;
    options?: Record<string, unknown>;
  }): Promise<{
    success: boolean;
    image_base64: string;
    foreground_node_id?: string;
    background_node_id?: string;
    mime_type: string;
    execution_time_ms: number;
    model: string;
    metadata: Record<string, unknown>;
  }> {
    return this.postJson(
      '/api/v1/canvas/ai/relight',
      {
        foreground_image_base64: params.foregroundImageBase64,
        foreground_image_url: params.foregroundImageUrl,
        background_image_base64: params.backgroundImageBase64,
        background_image_url: params.backgroundImageUrl,
        foreground_node_id: params.foregroundNodeId,
        background_node_id: params.backgroundNodeId,
        lighting_prompt: params.lightingPrompt,
        light_direction: params.lightDirection ?? 'natural',
        intensity: params.intensity ?? 1.0,
        canvas_id: params.canvasId,
        options: params.options,
      },
      () => ({
        success: true,
        image_base64: params.foregroundImageBase64 || MOCK_TRANSPARENT_PNG,
        foreground_node_id: params.foregroundNodeId,
        background_node_id: params.backgroundNodeId,
        mime_type: 'image/png',
        execution_time_ms: 180,
        model: 'ic-light-v1-fallback',
        metadata: {
          lightDirection: params.lightDirection ?? 'natural',
          lightingPrompt: params.lightingPrompt,
          fallback: true,
        },
      })
    );
  }

  /**
   * FLUX.1 + LayerDiffuse layer generation
   */
  public async generateLayer(params: {
    prompt: string;
    negativePrompt?: string;
    style?: string;
    width?: number;
    height?: number;
    transparentBackground?: boolean;
    layerType?: string;
    canvasId?: string;
    options?: Record<string, unknown>;
  }): Promise<{
    success: boolean;
    image_base64: string;
    mime_type: string;
    execution_time_ms: number;
    model: string;
    metadata: Record<string, unknown>;
  }> {
    return this.postJson(
      '/api/v1/canvas/ai/generate-layer',
      {
        prompt: params.prompt,
        negative_prompt: params.negativePrompt,
        style: params.style ?? 'photorealistic',
        width: params.width ?? 1024,
        height: params.height ?? 1024,
        transparent_background: params.transparentBackground ?? true,
        layer_type: params.layerType ?? 'image',
        canvas_id: params.canvasId,
        options: params.options,
      },
      () => ({
        success: true,
        image_base64: MOCK_TRANSPARENT_PNG,
        mime_type: 'image/png',
        execution_time_ms: 250,
        model: 'flux-layerdiffuse-v1-fallback',
        metadata: {
          prompt: params.prompt,
          negativePrompt: params.negativePrompt,
          style: params.style ?? 'photorealistic',
          width: params.width ?? 1024,
          height: params.height ?? 1024,
          transparentBackground: params.transparentBackground ?? true,
          fallback: true,
        },
      })
    );
  }
}

export { AIClient as CanvasAIClient };
