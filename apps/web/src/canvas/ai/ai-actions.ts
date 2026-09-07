/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/ai/ai-actions.ts"
 * purpose: "High-level AI Actions orchestrator executing background cutout, relighting, and layer generation with Canvas Undo/Redo integration."
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

import { generateUUID } from '../storage/storage.service';
import { AddNodeCommand } from '../history/commands/add-node.command';
import { UpdateNodeCommand } from '../history/commands/update-node.command';
import { AIClient } from './ai-client';
import type {
  AIActionContext,
  AICutoutOptions,
  AICutoutResult,
  AIRelightOptions,
  AIRelightResult,
  AIGenerateLayerOptions,
  AIGenerateLayerResult,
} from './types';
import type { NodeProperties } from '../storage/types/canvas';

function findNodeById(state: AIActionContext['state'], nodeId: string): { node: NodeProperties; layerId: string } | null {
  for (const layer of state.layers) {
    const node = layer.nodes.find((n) => n.id === nodeId);
    if (node) {
      return { node, layerId: layer.id };
    }
  }
  return null;
}

function getNodeImageSource(node: NodeProperties): string | undefined {
  if (node.props && typeof node.props === 'object') {
    const propsObj = node.props as Record<string, unknown>;
    if (typeof propsObj.src === 'string') return propsObj.src;
    if (typeof propsObj.url === 'string') return propsObj.url;
    if (typeof propsObj.image === 'string') return propsObj.image;
    if (typeof propsObj.base64 === 'string') return propsObj.base64;
  }
  if (node.customData && typeof node.customData === 'object') {
    const customObj = node.customData as Record<string, unknown>;
    if (typeof customObj.src === 'string') return customObj.src;
    if (typeof customObj.url === 'string') return customObj.url;
    if (typeof customObj.image === 'string') return customObj.image;
    if (typeof customObj.base64 === 'string') return customObj.base64;
  }
  if (node.fill && (node.fill.startsWith('data:image') || node.fill.startsWith('http'))) {
    return node.fill;
  }
  return undefined;
}

export class AIActions {
  private static getClient(context: AIActionContext): AIClient {
    if (context.aiClient) {
      return context.aiClient;
    }
    return new AIClient({
      baseUrl: context.apiBaseUrl,
      workspaceId: context.workspaceId,
      authToken: context.authToken,
    });
  }

  /**
   * BiRefNet Background Cutout / Removal
   */
  public static async cutoutBackground(
    context: AIActionContext,
    options: AICutoutOptions = {}
  ): Promise<AICutoutResult> {
    const targetNodeId = options.nodeId || context.selectedNodeId;
    if (!targetNodeId) {
      throw new Error('No target node specified for background cutout');
    }

    const nodeInfo = findNodeById(context.state, targetNodeId);
    if (!nodeInfo) {
      throw new Error(`Node with id ${targetNodeId} not found on canvas`);
    }

    const imageSrc = options.imageSrc || getNodeImageSource(nodeInfo.node);
    if (!imageSrc) {
      throw new Error(`Node ${targetNodeId} does not contain valid image source data`);
    }

    context.onStatusChange?.({ loading: true, action: 'cutout' });

    try {
      const client = this.getClient(context);
      const isBase64 = imageSrc.startsWith('data:') || !imageSrc.startsWith('http');
      
      const response = await client.cutout({
        imageBase64: isBase64 ? imageSrc : undefined,
        imageUrl: !isBase64 ? imageSrc : undefined,
        nodeId: targetNodeId,
        canvasId: context.state.id,
        returnMask: options.returnMask ?? false,
        threshold: options.threshold ?? 0.5,
      });

      const processedImageSrc = response.image_base64.startsWith('data:')
        ? response.image_base64
        : `data:${response.mime_type || 'image/png'};base64,${response.image_base64}`;

      const maskSrc = response.mask_base64
        ? (response.mask_base64.startsWith('data:')
          ? response.mask_base64
          : `data:${response.mime_type || 'image/png'};base64,${response.mask_base64}`)
        : undefined;

      const shouldReplace = options.replaceOriginal !== false;

      if (shouldReplace) {
        const updatedProps = {
          ...(nodeInfo.node.props || {}),
          src: processedImageSrc,
          aiCutout: true,
          cutoutProcessed: true,
          cutoutTimestamp: Date.now(),
        };

        const updateCmd = new UpdateNodeCommand(
          targetNodeId,
          {
            props: updatedProps,
            fill: nodeInfo.node.fill?.startsWith('data:') ? processedImageSrc : nodeInfo.node.fill,
          },
          `AI Cutout: ${nodeInfo.node.name || targetNodeId}`
        );

        if (context.commandStack) {
          context.commandStack.execute(updateCmd);
        } else {
          updateCmd.execute({ state: context.state, onStateChange: context.onStateChange });
        }

        context.onStatusChange?.({ loading: false });

        return {
          success: true,
          imageSrc: processedImageSrc,
          maskSrc,
          nodeId: targetNodeId,
          originalNodeId: targetNodeId,
          executionTimeMs: response.execution_time_ms,
        };
      } else {
        const newNodeId = generateUUID();
        const newNode: NodeProperties = {
          ...nodeInfo.node,
          id: newNodeId,
          name: `${nodeInfo.node.name || 'Image'} (Cutout)`,
          x: nodeInfo.node.x + 30,
          y: nodeInfo.node.y + 30,
          props: {
            ...(nodeInfo.node.props || {}),
            src: processedImageSrc,
            cutoutProcessed: true,
            originalNodeId: targetNodeId,
          },
          fill: nodeInfo.node.fill?.startsWith('data:') ? processedImageSrc : nodeInfo.node.fill,
        };

        const addCmd = new AddNodeCommand(
          newNode,
          options.targetLayerId || nodeInfo.layerId,
          `AI Cutout Copy: ${newNode.name}`
        );

        if (context.commandStack) {
          context.commandStack.execute(addCmd);
        } else {
          addCmd.execute({ state: context.state, onStateChange: context.onStateChange });
        }

        context.onStatusChange?.({ loading: false });

        return {
          success: true,
          imageSrc: processedImageSrc,
          maskSrc,
          nodeId: newNodeId,
          originalNodeId: targetNodeId,
          executionTimeMs: response.execution_time_ms,
        };
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      context.onStatusChange?.({ loading: false, error: errorMsg });
      throw err;
    }
  }

  /**
   * IC-Light Environment Relighting
   */
  public static async relight(
    context: AIActionContext,
    backgroundNodeId: string,
    options: AIRelightOptions = {}
  ): Promise<AIRelightResult> {
    const fgNodeId = options.foregroundNodeId || context.selectedNodeId;
    if (!fgNodeId) {
      throw new Error('No foreground node specified for relighting');
    }

    const fgNodeInfo = findNodeById(context.state, fgNodeId);
    if (!fgNodeInfo) {
      throw new Error(`Foreground node ${fgNodeId} not found`);
    }

    const bgNodeInfo = findNodeById(context.state, backgroundNodeId);
    if (!bgNodeInfo) {
      throw new Error(`Background node ${backgroundNodeId} not found`);
    }

    const fgSrc = options.foregroundSrc || getNodeImageSource(fgNodeInfo.node);
    const bgSrc = options.backgroundSrc || getNodeImageSource(bgNodeInfo.node);

    if (!fgSrc) {
      throw new Error(`Foreground node ${fgNodeId} does not contain valid image source data`);
    }

    context.onStatusChange?.({ loading: true, action: 'relight' });

    try {
      const client = this.getClient(context);
      const isFgBase64 = fgSrc.startsWith('data:') || !fgSrc.startsWith('http');
      const isBgBase64 = bgSrc ? (bgSrc.startsWith('data:') || !bgSrc.startsWith('http')) : undefined;

      const response = await client.relight({
        foregroundBase64: isFgBase64 ? fgSrc : undefined,
        foregroundUrl: !isFgBase64 ? fgSrc : undefined,
        backgroundBase64: bgSrc && isBgBase64 ? bgSrc : undefined,
        backgroundUrl: bgSrc && !isBgBase64 ? bgSrc : undefined,
        foregroundNodeId: fgNodeId,
        backgroundNodeId: backgroundNodeId,
        lightingPrompt: options.lightingPrompt,
        lightDirection: options.lightDirection || 'natural',
        intensity: options.intensity ?? 1.0,
        canvasId: context.state.id,
      });

      const processedImageSrc = response.image_base64.startsWith('data:')
        ? response.image_base64
        : `data:${response.mime_type || 'image/png'};base64,${response.image_base64}`;

      const shouldReplace = options.replaceOriginal !== false;

      if (shouldReplace) {
        const updateCmd = new UpdateNodeCommand(
          fgNodeId,
          {
            props: {
              ...(fgNodeInfo.node.props || {}),
              src: processedImageSrc,
              relighted: true,
              lightDirection: options.lightDirection || 'natural',
              intensity: options.intensity ?? 1.0,
            },
            fill: fgNodeInfo.node.fill?.startsWith('data:') ? processedImageSrc : fgNodeInfo.node.fill,
          },
          `AI Relight: ${fgNodeInfo.node.name || fgNodeId}`
        );

        if (context.commandStack) {
          context.commandStack.execute(updateCmd);
        } else {
          updateCmd.execute({ state: context.state, onStateChange: context.onStateChange });
        }

        context.onStatusChange?.({ loading: false });

        return {
          success: true,
          imageSrc: processedImageSrc,
          nodeId: fgNodeId,
          lightDirection: options.lightDirection || 'natural',
          intensity: options.intensity ?? 1.0,
          executionTimeMs: response.execution_time_ms,
        };
      } else {
        const newNodeId = generateUUID();
        const newNode: NodeProperties = {
          ...fgNodeInfo.node,
          id: newNodeId,
          name: `${fgNodeInfo.node.name || 'Image'} (Relit)`,
          x: fgNodeInfo.node.x + 40,
          y: fgNodeInfo.node.y + 40,
          props: {
            ...(fgNodeInfo.node.props || {}),
            src: processedImageSrc,
            relighted: true,
            lightDirection: options.lightDirection || 'natural',
            intensity: options.intensity ?? 1.0,
          },
          fill: fgNodeInfo.node.fill?.startsWith('data:') ? processedImageSrc : fgNodeInfo.node.fill,
        };

        const addCmd = new AddNodeCommand(
          newNode,
          options.targetLayerId || fgNodeInfo.layerId,
          `AI Relit Copy: ${newNode.name}`
        );

        if (context.commandStack) {
          context.commandStack.execute(addCmd);
        } else {
          addCmd.execute({ state: context.state, onStateChange: context.onStateChange });
        }

        context.onStatusChange?.({ loading: false });

        return {
          success: true,
          imageSrc: processedImageSrc,
          nodeId: newNodeId,
          lightDirection: options.lightDirection || 'natural',
          intensity: options.intensity ?? 1.0,
          executionTimeMs: response.execution_time_ms,
        };
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      context.onStatusChange?.({ loading: false, error: errorMsg });
      throw err;
    }
  }

  /**
   * FLUX.1 + LayerDiffuse Isolated Transparent Layer Generation
   */
  public static async generateLayer(
    context: AIActionContext,
    prompt: string,
    options: Partial<AIGenerateLayerOptions> = {}
  ): Promise<AIGenerateLayerResult> {
    if (!prompt || !prompt.trim()) {
      throw new Error('Prompt cannot be empty for layer generation');
    }

    context.onStatusChange?.({ loading: true, action: 'generate-layer' });

    try {
      const client = this.getClient(context);
      const width = options.width ?? 1024;
      const height = options.height ?? 1024;

      const response = await client.generateLayer({
        prompt,
        negativePrompt: options.negativePrompt,
        style: options.style ?? 'photorealistic',
        width,
        height,
        transparentBackground: options.transparentBackground ?? true,
        layerType: options.layerType ?? 'image',
        canvasId: context.state.id,
      });

      const processedImageSrc = response.image_base64.startsWith('data:')
        ? response.image_base64
        : `data:${response.mime_type || 'image/png'};base64,${response.image_base64}`;

      const newNodeId = generateUUID();
      const targetLayer = options.targetLayerId || context.state.layers[0]?.id || 'default-layer';

      const newNode: NodeProperties = {
        id: newNodeId,
        type: (options.layerType as any) || 'image',
        name: `AI: ${prompt.slice(0, 24)}...`,
        x: options.x ?? (context.state.viewport?.x ? -context.state.viewport.x + 100 : 100),
        y: options.y ?? (context.state.viewport?.y ? -context.state.viewport.y + 100 : 100),
        width,
        height,
        rotation: 0,
        opacity: 1,
        visible: true,
        locked: false,
        zIndex: 0,
        props: {
          src: processedImageSrc,
          prompt,
          negativePrompt: options.negativePrompt,
          style: options.style || 'photorealistic',
          aiGenerated: true,
          transparent: options.transparentBackground ?? true,
          model: response.model,
          metadata: response.metadata,
        },
        fill: processedImageSrc,
      };

      const addCmd = new AddNodeCommand(newNode, targetLayer, `AI Generate: ${prompt.slice(0, 30)}`);

      if (context.commandStack) {
        context.commandStack.execute(addCmd);
      } else {
        addCmd.execute({ state: context.state, onStateChange: context.onStateChange });
      }

      context.onStatusChange?.({ loading: false });

      return {
        success: true,
        imageSrc: processedImageSrc,
        node: newNode,
        executionTimeMs: response.execution_time_ms,
      };
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      context.onStatusChange?.({ loading: false, error: errorMsg });
      throw err;
    }
  }
}
