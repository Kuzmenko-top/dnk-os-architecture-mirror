// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/canvas/store.ts"
// purpose: "Zustand Reactive State Store for DNK OS Canvas Studio with Undo/Redo, Storage Sync, and Real AI Action Adapters."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "3.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CanvasState, NodeProperties, LayerState } from '../../canvas/storage/types/canvas';
import { UndoRedoStack } from '../../canvas/history/undo-redo-stack';
import { CanvasStorageService, generateUUID } from '../../canvas/storage/storage.service';
import { AddNodeCommand } from '../../canvas/history/commands/add-node.command';
import { UpdateNodeCommand } from '../../canvas/history/commands/update-node.command';
import { DeleteNodeCommand } from '../../canvas/history/commands/delete-node.command';
import { MoveNodeCommand, type TransformState } from '../../canvas/history/commands/move-node.command';
import { ReorderLayerCommand } from '../../canvas/history/commands/reorder-layer.command';
import { AIActions } from '../../canvas/ai/ai-actions';
import { AIClient } from '../../canvas/ai/ai-client';
import type {
  AIActionContext,
  AICutoutOptions,
  AICutoutResult,
  AIRelightOptions,
  AIRelightResult,
  AIGenerateLayerOptions,
  AIGenerateLayerResult,
} from '../../canvas/ai/types';

export type CanvasTool =
  | 'select'
  | 'hand'
  | 'rectangle'
  | 'circle'
  | 'text'
  | 'image'
  | 'pen'
  | 'ai-cutout'
  | 'ai-relight'
  | 'ai-generate';

export interface AIActionState {
  isProcessing: boolean;
  actionType: 'cutout' | 'relight' | 'generate' | null;
  progressMessage: string | null;
  progress: number | null;
  error: string | null;
}

export interface CanvasStudioStore {
  // Canvas State & History
  canvasState: CanvasState;
  undoRedoStack: UndoRedoStack;
  storageService: CanvasStorageService;
  aiClient: AIClient;

  // UI Selection & Tooling
  currentTool: CanvasTool;
  selectedNodeIds: string[];
  zoom: number;
  pan: { x: number; y: number };
  isDirty: boolean;

  // AI Progress & Status
  aiState: AIActionState;

  // Actions: Core & View
  setTool: (tool: CanvasTool) => void;
  setSelectedNodeIds: (ids: string[]) => void;
  setZoom: (zoom: number) => void;
  setPan: (pan: { x: number; y: number }) => void;
  setAIClient: (client: AIClient) => void;
  resetAIState: () => void;

  // Actions: Canvas Graph & History Mutations
  addNode: (node: NodeProperties, targetLayerId?: string) => Promise<void>;
  updateNode: (nodeId: string, patch: Partial<NodeProperties>, description?: string) => Promise<void>;
  deleteNode: (nodeId: string) => Promise<void>;
  addLayer: (name?: string) => Promise<string>;
  deleteLayer: (layerId: string) => Promise<void>;
  setActiveLayer: (layerId: string) => void;
  moveNode: (nodeId: string, dx: number, dy: number) => Promise<void>;
  reorderLayer: (targetId: string, oldIndex: number, newIndex: number, isLayer?: boolean) => Promise<void>;

  // Actions: Undo / Redo
  undo: () => Promise<void>;
  redo: () => Promise<void>;
  canUndo: () => boolean;
  canRedo: () => boolean;

  // Actions: Storage Sync
  saveDraft: () => Promise<void>;
  loadDraft: (canvasId: string) => Promise<boolean>;

  // Actions: Real AI Action Adapters
  runAICutout: (nodeId?: string, options?: AICutoutOptions) => Promise<AICutoutResult>;
  runAIRelight: (backgroundNodeId?: string, options?: AIRelightOptions) => Promise<AIRelightResult>;
  runAIGenerate: (prompt: string, options?: Partial<AIGenerateLayerOptions>) => Promise<AIGenerateLayerResult>;
}

const createInitialCanvasState = (): CanvasState => ({
  id: 'canvas-default-studio',
  name: 'DNK Studio Canvas',
  version: 1,
  viewport: { zoom: 1, x: 0, y: 0 },
  dimensions: { width: 1920, height: 1080 },
  layers: [
    {
      id: 'layer-bg-root',
      name: 'Background Layer',
      visible: true,
      locked: false,
      opacity: 1,
      zIndex: 0,
      nodes: [],
    },
    {
      id: 'layer-main-root',
      name: 'Main Content',
      visible: true,
      locked: false,
      opacity: 1,
      zIndex: 1,
      nodes: [],
    },
  ],
  activeLayerId: 'layer-main-root',
  selectedNodeIds: [],
  metadata: {},
  createdAt: Date.now(),
  updatedAt: Date.now(),
});

export const useCanvasStudioStore = create<CanvasStudioStore>()(
  persist(
    (set, get) => {
      const initialCanvasState = createInitialCanvasState();
      const storageService = new CanvasStorageService();
      const undoRedoStack = new UndoRedoStack(initialCanvasState);
      const aiClient = new AIClient({
        baseUrl: process.env.NEXT_PUBLIC_CANVAS_API_URL || 'http://localhost:8000',
        workspaceId: 'ws-alpha-001',
      });

      const syncStateFromStack = (updatedState: CanvasState) => {
        set({
          canvasState: { ...updatedState },
          isDirty: true,
        });
      };

      const getAIActionContext = (): AIActionContext => {
        const { canvasState, undoRedoStack: stack, aiClient: client, selectedNodeIds } = get();
        return {
          state: canvasState,
          commandStack: stack,
          selectedNodeId: selectedNodeIds[0],
          selectedNodeIds,
          aiClient: client,
          workspaceId: 'ws-alpha-001',
          onStatusChange: (status) => {
            set({
              aiState: {
                isProcessing: status.loading,
                actionType: (status.action as 'cutout' | 'relight' | 'generate') || null,
                progressMessage: status.message || (status.loading ? `Running ${status.action}...` : null),
                progress: status.progress ?? null,
                error: status.error ?? null,
              },
            });
          },
          onStateChange: (updatedState) => {
            syncStateFromStack(updatedState);
          },
        };
      };

      return {
        canvasState: initialCanvasState,
        undoRedoStack,
        storageService,
        aiClient,
        currentTool: 'select',
        selectedNodeIds: [],
        zoom: 1.0,
        pan: { x: 0, y: 0 },
        isDirty: false,
        aiState: {
          isProcessing: false,
          actionType: null,
          progressMessage: null,
          progress: null,
          error: null,
        },

        setTool: (tool: CanvasTool) => set({ currentTool: tool }),
        setSelectedNodeIds: (ids: string[]) => set({ selectedNodeIds: ids }),
        setZoom: (zoom: number) => set({ zoom: Math.max(0.1, Math.min(zoom, 5.0)) }),
        setPan: (pan: { x: number; y: number }) => set({ pan }),
        setAIClient: (client: AIClient) => set({ aiClient: client }),
        resetAIState: () =>
          set({
            aiState: {
              isProcessing: false,
              actionType: null,
              progressMessage: null,
              progress: null,
              error: null,
            },
          }),

        addNode: async (node: NodeProperties, targetLayerId?: string) => {
          const { undoRedoStack: stack, canvasState } = get();
          const layerId = targetLayerId || canvasState.activeLayerId || canvasState.layers[0]?.id || 'layer-main-root';
          const cmd = new AddNodeCommand(node, layerId);
          stack.execute(cmd);
          syncStateFromStack(stack.getState());
          set({ selectedNodeIds: [node.id] });
        },

        updateNode: async (nodeId: string, patch: Partial<NodeProperties>, description?: string) => {
          const { undoRedoStack: stack } = get();
          const cmd = new UpdateNodeCommand(nodeId, patch, description);
          stack.execute(cmd);
          syncStateFromStack(stack.getState());
        },

        deleteNode: async (nodeId: string) => {
          const { undoRedoStack: stack, selectedNodeIds } = get();
          const cmd = new DeleteNodeCommand(nodeId);
          stack.execute(cmd);
          syncStateFromStack(stack.getState());
          set({
            selectedNodeIds: selectedNodeIds.filter((id) => id !== nodeId),
          });
        },

        addLayer: async (name?: string) => {
          const { canvasState } = get();
          const newLayerId = generateUUID();
          const layerName = name || `Layer ${canvasState.layers.length + 1}`;
          const newLayer: LayerState = {
            id: newLayerId,
            name: layerName,
            visible: true,
            locked: false,
            opacity: 1,
            zIndex: canvasState.layers.length,
            nodes: [],
          };
          const nextState: CanvasState = {
            ...canvasState,
            layers: [...canvasState.layers, newLayer],
            activeLayerId: newLayerId,
            updatedAt: Date.now(),
          };
          syncStateFromStack(nextState);
          return newLayerId;
        },

        deleteLayer: async (layerId: string) => {
          const { canvasState } = get();
          if (canvasState.layers.length <= 1) return;
          const nextLayers = canvasState.layers.filter((l) => l.id !== layerId);
          const nextState: CanvasState = {
            ...canvasState,
            layers: nextLayers,
            activeLayerId: nextLayers[0]?.id || '',
            updatedAt: Date.now(),
          };
          syncStateFromStack(nextState);
        },

        setActiveLayer: (layerId: string) => {
          set((state) => ({
            canvasState: {
              ...state.canvasState,
              activeLayerId: layerId,
            },
          }));
        },

        moveNode: async (nodeId: string, dx: number, dy: number) => {
          const { undoRedoStack: stack, canvasState } = get();
          const node = canvasState.layers.flatMap((l) => l.nodes).find((n) => n.id === nodeId);
          if (node) {
            const prevTransform: TransformState = {
              x: node.x,
              y: node.y,
              width: node.width,
              height: node.height,
              rotation: node.rotation,
            };
            const nextTransform: TransformState = {
              ...prevTransform,
              x: node.x + dx,
              y: node.y + dy,
            };
            const cmd = new MoveNodeCommand(nodeId, prevTransform, nextTransform);
            stack.execute(cmd);
            syncStateFromStack(stack.getState());
          }
        },

        reorderLayer: async (targetId: string, oldIndex: number, newIndex: number, isLayer = true) => {
          const { undoRedoStack: stack } = get();
          const cmd = new ReorderLayerCommand(targetId, oldIndex, newIndex, isLayer);
          stack.execute(cmd);
          syncStateFromStack(stack.getState());
        },

        undo: async () => {
          const { undoRedoStack: stack } = get();
          if (stack.canUndo()) {
            await stack.undo();
            syncStateFromStack(stack.getState());
          }
        },

        redo: async () => {
          const { undoRedoStack: stack } = get();
          if (stack.canRedo()) {
            await stack.redo();
            syncStateFromStack(stack.getState());
          }
        },

        canUndo: () => get().undoRedoStack.canUndo(),
        canRedo: () => get().undoRedoStack.canRedo(),

        saveDraft: async () => {
          const { canvasState, storageService: storage } = get();
          await storage.saveDraft(canvasState);
          set({ isDirty: false });
        },

        loadDraft: async (canvasId: string) => {
          const { storageService: storage } = get();
          const draft = await storage.loadDraft(canvasId);
          if (draft && draft.state) {
            const newStack = new UndoRedoStack(draft.state);
            set({
              canvasState: draft.state,
              undoRedoStack: newStack,
              selectedNodeIds: [],
              isDirty: false,
            });
            return true;
          }
          return false;
        },

        runAICutout: async (nodeId?: string, options?: AICutoutOptions): Promise<AICutoutResult> => {
          const selectedIds = get().selectedNodeIds;
          const targetNodeId = nodeId || (selectedIds.length > 0 ? selectedIds[0] : undefined);

          if (!targetNodeId) {
            const errorMsg = 'No target image node selected for AI Cutout';
            set({
              aiState: {
                isProcessing: false,
                actionType: null,
                progressMessage: null,
                progress: null,
                error: errorMsg,
              },
            });
            return {
              success: false,
              imageSrc: '',
              nodeId: '',
              originalNodeId: '',
              executionTimeMs: 0,
            };
          }

          const context = getAIActionContext();
          try {
            const result = await AIActions.cutoutBackground(context, {
              nodeId: targetNodeId,
              ...options,
            });

            syncStateFromStack(get().undoRedoStack.getState());

            if (result.nodeId) {
              get().setSelectedNodeIds([result.nodeId]);
            }
            return result;
          } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'AI Cutout processing failed';
            set({
              aiState: {
                isProcessing: false,
                actionType: null,
                progressMessage: null,
                progress: null,
                error: errorMsg,
              },
            });
            return {
              success: false,
              imageSrc: '',
              nodeId: targetNodeId,
              originalNodeId: targetNodeId,
              executionTimeMs: 0,
            };
          }
        },

        runAIRelight: async (backgroundNodeId?: string, options?: AIRelightOptions): Promise<AIRelightResult> => {
          const selectedIds = get().selectedNodeIds;
          const foregroundNodeId = options?.foregroundNodeId || (selectedIds.length > 0 ? selectedIds[0] : undefined);

          if (!foregroundNodeId) {
            const errorMsg = 'No foreground node selected for AI Relighting';
            set({
              aiState: {
                isProcessing: false,
                actionType: null,
                progressMessage: null,
                progress: null,
                error: errorMsg,
              },
            });
            return {
              success: false,
              imageSrc: '',
              nodeId: '',
              executionTimeMs: 0,
            };
          }

          const targetBgId = backgroundNodeId || options?.backgroundNodeId;
          if (!targetBgId) {
            const errorMsg = 'No background environment node specified for AI Relighting';
            set({
              aiState: {
                isProcessing: false,
                actionType: null,
                progressMessage: null,
                progress: null,
                error: errorMsg,
              },
            });
            return {
              success: false,
              imageSrc: '',
              nodeId: foregroundNodeId,
              executionTimeMs: 0,
            };
          }

          const context = getAIActionContext();
          try {
            const result = await AIActions.relight(context, targetBgId, {
              foregroundNodeId,
              lightingPrompt: options?.lightingPrompt,
              lightDirection: options?.lightDirection ?? 'natural',
              intensity: options?.intensity ?? 1.0,
              replaceOriginal: options?.replaceOriginal ?? true,
              ...options,
            });

            syncStateFromStack(get().undoRedoStack.getState());

            if (result.nodeId) {
              get().setSelectedNodeIds([result.nodeId]);
            }
            return result;
          } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'AI Relight failed';
            set({
              aiState: {
                isProcessing: false,
                actionType: null,
                progressMessage: null,
                progress: null,
                error: errorMsg,
              },
            });
            return {
              success: false,
              imageSrc: '',
              nodeId: foregroundNodeId,
              executionTimeMs: 0,
            };
          }
        },

        runAIGenerate: async (prompt: string, options?: Partial<AIGenerateLayerOptions>): Promise<AIGenerateLayerResult> => {
          if (!prompt || !prompt.trim()) {
            const errorMsg = 'Prompt cannot be empty for AI Layer Generation';
            set({
              aiState: {
                isProcessing: false,
                actionType: null,
                progressMessage: null,
                progress: null,
                error: errorMsg,
              },
            });
            return {
              success: false,
              imageSrc: '',
              node: {} as NodeProperties,
              executionTimeMs: 0,
            };
          }

          const context = getAIActionContext();
          try {
            const result = await AIActions.generateLayer(context, prompt.trim(), {
              negativePrompt: options?.negativePrompt,
              style: options?.style ?? 'photorealistic',
              width: options?.width ?? 512,
              height: options?.height ?? 512,
              transparentBackground: options?.transparentBackground ?? true,
              targetLayerId: options?.targetLayerId || get().canvasState.activeLayerId || 'layer-main-root',
              ...options,
            });

            syncStateFromStack(get().undoRedoStack.getState());

            if (result.node && result.node.id) {
              get().setSelectedNodeIds([result.node.id]);
            }
            return result;
          } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : 'AI Layer Generation failed';
            set({
              aiState: {
                isProcessing: false,
                actionType: null,
                progressMessage: null,
                progress: null,
                error: errorMsg,
              },
            });
            return {
              success: false,
              imageSrc: '',
              node: {} as NodeProperties,
              executionTimeMs: 0,
            };
          }
        },
      };
    },
    {
      name: 'dnk_canvas_store',
      partialize: (state) => ({
        canvasState: state.canvasState,
        currentTool: state.currentTool,
        zoom: state.zoom,
      }),
    }
  )
);
