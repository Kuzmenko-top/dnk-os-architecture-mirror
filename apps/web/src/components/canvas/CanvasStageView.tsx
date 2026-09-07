// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/canvas/CanvasStageView.tsx"
// purpose: "React View Bridge for Konva.Stage, multi-tier canvas orchestration, tool interactions, and hotkeys."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import React, { useEffect, useRef, useCallback } from 'react';
import { CanvasStageService } from '../../canvas/core/stage.service';
import { useCanvasStudioStore, type CanvasTool } from './store';
import { generateUUID } from '../../canvas/storage/storage.service';

interface CanvasStageViewProps {
  className?: string;
  onStageReady?: (stageService: CanvasStageService) => void;
}

export const CanvasStageView: React.FC<CanvasStageViewProps> = ({
  className = 'w-full h-full min-h-[500px]',
  onStageReady,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const isCreatingRef = useRef<boolean>(false);
  const startPosRef = useRef<{ x: number; y: number } | null>(null);

  const {
    activeTool,
    setActiveTool,
    canvasState,
    selectedNodeIds,
    setSelectedNodeIds,
    setStageService,
    addNode,
    deleteNode,
    undo,
    redo,
    setZoomLevel,
  } = useCanvasStudioStore();

  // Initialize and mount CanvasStageService
  useEffect(() => {
    if (!containerRef.current) return;

    const width = containerRef.current.clientWidth || 1280;
    const height = containerRef.current.clientHeight || 720;

    const stageService = new CanvasStageService({
      container: containerRef.current,
      width,
      height,
      viewport: canvasState.viewport,
      grid: {
        enabled: true,
        type: 'dots',
        size: 20,
      },
    });

    setStageService(stageService);
    if (onStageReady) {
      onStageReady(stageService);
    }

    // Subscribe to viewport changes to update zoom in store
    const unsubscribeViewport = stageService.onViewportChange((vp) => {
      setZoomLevel(vp.zoom);
    });

    // Resize Observer for auto-fitting canvas to container
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect) {
          stageService.setSize(entry.contentRect.width, entry.contentRect.height);
        }
      }
    });

    resizeObserver.observe(containerRef.current);

    return () => {
      unsubscribeViewport();
      resizeObserver.disconnect();
      setStageService(null);
      stageService.destroy();
    };
  }, []);

  // Global Keyboard Shortcuts (Undo, Redo, Delete, Selection, Space-to-Hand)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore key events if user is typing inside an input or textarea
      if (
        document.activeElement &&
        (document.activeElement.tagName === 'INPUT' ||
          document.activeElement.tagName === 'TEXTAREA' ||
          document.activeElement.getAttribute('contenteditable') === 'true')
      ) {
        return;
      }

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const isCmdOrCtrl = isMac ? e.metaKey : e.ctrlKey;

      if (isCmdOrCtrl && e.key.toLowerCase() === 'z') {
        e.preventDefault();
        if (e.shiftKey) {
          redo();
        } else {
          undo();
        }
      } else if (isCmdOrCtrl && e.key.toLowerCase() === 'y') {
        e.preventDefault();
        redo();
      } else if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedNodeIds.length > 0) {
          e.preventDefault();
          for (const id of selectedNodeIds) {
            deleteNode(id);
          }
        }
      } else if (e.key === 'Escape') {
        setSelectedNodeIds([]);
        setActiveTool('select');
      } else if (e.key === 'v' || e.key === 'V') {
        setActiveTool('select');
      } else if (e.key === 'h' || e.key === 'H') {
        setActiveTool('hand');
      } else if (e.key === 'r' || e.key === 'R') {
        setActiveTool('rect');
      } else if (e.key === 'c' || e.key === 'C') {
        setActiveTool('circle');
      } else if (e.key === 't' || e.key === 'T') {
        setActiveTool('text');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [selectedNodeIds, undo, redo, deleteNode, setSelectedNodeIds, setActiveTool]);

  // Pointer & Shape Creation handlers
  const handlePointerDown = useCallback(
    async (e: React.PointerEvent<HTMLDivElement>) => {
      if (activeTool === 'select' || activeTool === 'hand') return;

      const { stageService } = useCanvasStudioStore.getState();
      if (!stageService) return;

      const stage = stageService.stage;
      const stagePointer = stage.getPointerPosition();
      if (!stagePointer) return;

      const viewport = stageService.getViewport();
      const canvasX = (stagePointer.x - viewport.x) / viewport.zoom;
      const canvasY = (stagePointer.y - viewport.y) / viewport.zoom;

      isCreatingRef.current = true;
      startPosRef.current = { x: canvasX, y: canvasY };

      if (activeTool === 'text') {
        isCreatingRef.current = false;
        await addNode({
          id: generateUUID(),
          type: 'text',
          name: 'Text Layer',
          x: Math.round(canvasX),
          y: Math.round(canvasY),
          width: 200,
          height: 40,
          fill: '#F8FAFC',
          props: {
            text: 'Click or type to edit...',
            fontSize: 24,
            fontFamily: 'Inter, sans-serif',
            fontWeight: 'normal',
          },
        });
        setActiveTool('select');
      }
    },
    [activeTool, addNode, setActiveTool]
  );

  const handlePointerUp = useCallback(
    async (e: React.PointerEvent<HTMLDivElement>) => {
      if (!isCreatingRef.current || !startPosRef.current) return;

      const { stageService } = useCanvasStudioStore.getState();
      if (!stageService) return;

      const stage = stageService.stage;
      const stagePointer = stage.getPointerPosition();
      if (!stagePointer) return;

      const viewport = stageService.getViewport();
      const endCanvasX = (stagePointer.x - viewport.x) / viewport.zoom;
      const endCanvasY = (stagePointer.y - viewport.y) / viewport.zoom;

      const x = Math.min(startPosRef.current.x, endCanvasX);
      const y = Math.min(startPosRef.current.y, endCanvasY);
      const width = Math.max(20, Math.abs(endCanvasX - startPosRef.current.x));
      const height = Math.max(20, Math.abs(endCanvasY - startPosRef.current.y));

      isCreatingRef.current = false;
      startPosRef.current = null;

      if (activeTool === 'rect') {
        await addNode({
          id: generateUUID(),
          type: 'rect',
          name: 'Rectangle',
          x: Math.round(x),
          y: Math.round(y),
          width: Math.round(width),
          height: Math.round(height),
          fill: '#3B82F6',
          stroke: '#1D4ED8',
          strokeWidth: 2,
        });
        setActiveTool('select');
      } else if (activeTool === 'circle') {
        await addNode({
          id: generateUUID(),
          type: 'circle',
          name: 'Circle',
          x: Math.round(x),
          y: Math.round(y),
          width: Math.round(Math.max(width, height)),
          height: Math.round(Math.max(width, height)),
          fill: '#10B981',
          stroke: '#047857',
          strokeWidth: 2,
        });
        setActiveTool('select');
      }
    },
    [activeTool, addNode, setActiveTool]
  );

  return (
    <div
      data-testid="dnk-canvas-stage-view"
      className={`relative overflow-hidden bg-slate-950 select-none ${className} ${
        activeTool === 'hand' ? 'cursor-grab active:cursor-grabbing' : 'cursor-default'
      }`}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
    >
      <div
        ref={containerRef}
        data-testid="konva-stage-container"
        className="absolute inset-0 w-full h-full"
      />
    </div>
  );
};
