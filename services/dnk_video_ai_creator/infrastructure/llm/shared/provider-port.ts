/*
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/infrastructure/llm/shared/provider-port.ts"
# purpose: "Canonical Live Multimodal Provider Port & Result Interface."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { MultimodalAuditInput, MultimodalAuditContext } from '@dnk/video-audit-core';

export interface ProviderAuditResult {
  rawOutput: unknown;
  providerId: string;
  modelVersion: string;
  promptVersion: string;
  inputArtifactHashes: Record<string, string>;
  usage?: {
    inputTokens?: number;
    outputTokens?: number;
    latencyMs: number;
  };
}

export interface LiveMultimodalProviderPort {
  readonly providerId: 'gemini' | 'claude';
  readonly modelSetVersion: string;

  analyze(
    input: MultimodalAuditInput,
    context: MultimodalAuditContext
  ): Promise<ProviderAuditResult>;
}
