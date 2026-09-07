/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/prompt/index.ts"
# purpose: "Unified Prompt Pipeline Orchestrator and Exports."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { MultimodalAuditInput, MultimodalAuditContext } from '../../ports/multimodal-audit-provider.js';
import { PromptTemplateRegistry, PromptRenderer } from './templates.js';
import { MultimodalContextBuilder, BuiltContext } from './context-builder.js';
import { AuditOutputPolicy, PolicyCheckResult } from './output-policy.js';

export * from './templates.js';
export * from './context-builder.js';
export * from './parser.js';
export * from './claim-validator.js';
export * from './output-policy.js';

export class PromptPipeline {
  private registry = new PromptTemplateRegistry();
  private renderer = new PromptRenderer();
  private contextBuilder = new MultimodalContextBuilder();
  private policy = new AuditOutputPolicy();
  private defaultVersion = '1.0.0';

  /**
   * Generates the structured prompt with multimodal inputs serialized as canonical context.
   */
  generatePrompt(
    input: MultimodalAuditInput,
    context: MultimodalAuditContext,
    version?: string
  ): { prompt: string; inputArtifactHashes: Record<string, string>; warnings: string[] } {
    const targetVersion = version ?? this.defaultVersion;
    const template = this.registry.getTemplate(targetVersion);

    const builtContext: BuiltContext = this.contextBuilder.build(input, context);

    const prompt = this.renderer.render(template, {
      contextString: builtContext.contextString,
      schemaVersion: 'multimodal-audit.v1'
    });

    return {
      prompt,
      inputArtifactHashes: builtContext.inputArtifactHashes,
      warnings: builtContext.warnings
    };
  }

  /**
   * Applies the audit output policy to parse, repair, and validate an LLM's response.
   */
  evaluateResponse(
    rawResponse: string,
    input: MultimodalAuditInput,
    inputWarnings: string[] = []
  ): PolicyCheckResult {
    return this.policy.apply(rawResponse, input, inputWarnings);
  }
}
