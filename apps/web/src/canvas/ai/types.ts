/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/ai/types.ts"
 * purpose: "TypeScript type definitions and DTO contracts for Canvas AI Action Adapters (BiRefNet, IC-Light, FLUX.1)."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym & Gerych"
 * license: "DNK-INTERNAL"
 * --- END DNK-MRH-HEADER ---
 */

import type { CanvasState, NodeProperties } from '../storage/types/canvas';
import type { UndoRedoStack } from '../history/undo-redo-stack';

export interface AIClientConfig {
  baseUrl?: string;
  workspaceId?: string;
  authToken?: string;
  timeoutMs?: number;
}

export interface AIActionContext {
  state: CanvasState;
  commandStack?: UndoRedoStack;
  selectedNodeId?: string;
  selectedNodeIds?: string[];
  workspaceId?: string;
  authToken?: string;
  apiBaseUrl?: string;
  aiClient?: import('./ai-client').AIClient;
  onStateChange?: (state: CanvasState) => void;
  onStatusChange?: (status: {
    loading: boolean;
    action?: 'cutout' | 'relight' | 'generate' | string;
    message?: string;
    progress?: number | null;
    error?: string;
  }) => void;
}

export interface AICutoutOptions {
  nodeId?: string;
  imageSrc?: string;
  returnMask?: boolean;
  threshold?: number;
  targetLayerId?: string;
  replaceOriginal?: boolean;
}

export interface AICutoutResult {
  success: boolean;
  imageSrc: string;
  maskSrc?: string;
  nodeId: string;
  originalNodeId?: string;
  executionTimeMs?: number;
}

export interface AIRelightOptions {
  foregroundNodeId?: string;
  backgroundNodeId?: string;
  foregroundSrc?: string;
  backgroundSrc?: string;
  lightingPrompt?: string;
  lightDirection?: 'natural' | 'left' | 'right' | 'top' | 'bottom' | 'ambient';
  intensity?: number;
  targetLayerId?: string;
  replaceOriginal?: boolean;
}

export interface AIRelightResult {
  success: boolean;
  imageSrc: string;
  nodeId: string;
  lightDirection?: string;
  intensity?: number;
  executionTimeMs?: number;
}

export interface AIGenerateLayerOptions {
  prompt: string;
  negativePrompt?: string;
  style?: 'photorealistic' | 'isometric' | 'cyberpunk' | 'minimalist' | 'watercolor' | 'sketch' | (string & {});
  width?: number;
  height?: number;
  transparentBackground?: boolean;
  layerType?: 'image' | 'shape' | 'text' | 'background';
  targetLayerId?: string;
  x?: number;
  y?: number;
}

export interface AIGenerateLayerResult {
  success: boolean;
  imageSrc: string;
  node: NodeProperties;
  executionTimeMs?: number;
}
