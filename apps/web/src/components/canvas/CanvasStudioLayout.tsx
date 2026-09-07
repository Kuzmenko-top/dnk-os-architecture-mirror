// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/canvas/CanvasStudioLayout.tsx"
// purpose: "Master Canvas Studio layout container combining toolbar, layers panel, viewport stage & inspector."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import React, { useEffect } from 'react';
import { useCanvasStudioStore } from './store';
import { CanvasToolbar } from './CanvasToolbar';
import { LayersPanel } from './LayersPanel';
import { CanvasStageView } from './CanvasStageView';
import { InspectorPanel } from './InspectorPanel';
import { AIProgressToast } from './AIProgressToast';

interface CanvasStudioLayoutProps {
  className?: string;
  initialDraftId?: string;
}

export const CanvasStudioLayout: React.FC<CanvasStudioLayoutProps> = ({
  className = '',
  initialDraftId = 'default-studio-draft',
}) => {
  const { loadDraft, canvasState, activeTool, selectedNodeIds, aiState, resetAIState } =
    useCanvasStudioStore();

  useEffect(() => {
    loadDraft(initialDraftId);
  }, [loadDraft, initialDraftId]);

  return (
    <div
      data-testid="dnk-canvas-studio-layout"
      className={`flex flex-col w-screen h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans ${className}`}
    >
      {/* Top Navigation & Toolbar */}
      <CanvasToolbar />

      {/* Main Workspace Grid (Left Panel, Stage, Right Panel) */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left: Layers Panel */}
        <LayersPanel />

        {/* Center: Konva Viewport Stage */}
        <div className="flex-1 h-full relative overflow-hidden bg-slate-950">
          <CanvasStageView />

          {/* Real-time AI Progress Overlay Toast */}
          <AIProgressToast
            isVisible={aiState.isProcessing}
            actionType={aiState.actionType}
            message={aiState.progressMessage}
            progress={aiState.progress}
            error={aiState.error}
            onDismiss={resetAIState}
          />
        </div>

        {/* Right: Property Inspector Panel */}
        <InspectorPanel />
      </div>

      {/* Bottom Status Bar */}
      <div
        data-testid="canvas-status-bar"
        className="px-4 py-1.5 bg-slate-950 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between font-mono select-none"
      >
        <div className="flex items-center space-x-4">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Ready</span>
          </span>
          <span>
            Canvas: {canvasState.dimensions?.width || 1920} × {canvasState.dimensions?.height || 1080} px
          </span>
          <span>Tool: <strong className="text-slate-300">{activeTool.toUpperCase()}</strong></span>
          <span>Selected: <strong className="text-indigo-400">{selectedNodeIds.length}</strong></span>
        </div>

        <div className="flex items-center space-x-3">
          <span>DNK OS Canvas Engine v2.0.0</span>
          <span>|</span>
          <span className="text-slate-400">60 FPS</span>
        </div>
      </div>
    </div>
  );
};
