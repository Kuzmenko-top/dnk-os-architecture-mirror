// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/canvas/CanvasToolbar.tsx"
// purpose: "Studio top navigation & tool bar: selection, shapes, text, zoom, undo/redo, and AI Magic Actions."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import React, { useState, useRef } from 'react';
import { useCanvasStudioStore, type CanvasTool } from './store';
import { generateUUID } from '../../canvas/storage/storage.service';
import { AIPromptModal } from './AIPromptModal';
import type { AIGenerateLayerOptions } from '../../canvas/ai/types';

interface CanvasToolbarProps {
  className?: string;
}

export const CanvasToolbar: React.FC<CanvasToolbarProps> = ({ className = '' }) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [showRelightModal, setShowRelightModal] = useState(false);
  const [relightPrompt, setRelightPrompt] = useState('');

  const {
    activeTool,
    setActiveTool,
    canUndo,
    canRedo,
    undo,
    redo,
    saveDraft,
    isSaving,
    isDirty,
    zoomLevel,
    setZoomLevel,
    selectedNodeIds,
    canvasState,
    addNode,
    aiState,
    runAICutout,
    runAIRelight,
    runAIGenerate,
  } = useCanvasStudioStore();

  const selectedNodeId = selectedNodeIds.length === 1 ? selectedNodeIds[0] : null;
  const zoomPercentage = Math.round(zoomLevel * 100);

  const handleZoomIn = () => setZoomLevel(zoomLevel + 0.1);
  const handleZoomOut = () => setZoomLevel(zoomLevel - 0.1);
  const handleZoomReset = () => setZoomLevel(1.0);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      const dataUrl = event.target?.result as string;
      if (dataUrl) {
        await addNode({
          id: generateUUID(),
          type: 'image',
          name: file.name.replace(/\.[^/.]+$/, ''),
          x: 200,
          y: 200,
          width: 300,
          height: 200,
          props: {
            src: dataUrl,
            assetName: file.name,
          },
        });
        setActiveTool('select');
      }
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const handleTriggerCutout = async () => {
    if (!selectedNodeId) return;
    await runAICutout(selectedNodeId);
  };

  const handleTriggerRelight = async () => {
    if (!selectedNodeId || !relightPrompt.trim()) return;
    setShowRelightModal(false);
    await runAIRelight(selectedNodeId, { lightingPrompt: relightPrompt.trim() });
    setRelightPrompt('');
  };

  const handleTriggerGenerate = async (prompt: string, options: Partial<AIGenerateLayerOptions>) => {
    setShowGenerateModal(false);
    await runAIGenerate(prompt, options);
  };

  return (
    <div
      data-testid="dnk-canvas-toolbar"
      className={`flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800 text-slate-100 select-none ${className}`}
    >
      {/* 🛠️ Section 1: Creation & Selection Tools */}
      <div className="flex items-center space-x-1">
        <button
          type="button"
          data-testid="tool-select"
          title="Select Tool (V)"
          onClick={() => setActiveTool('select')}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1.5 ${
            activeTool === 'select'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'hover:bg-slate-800 text-slate-300'
          }`}
        >
          <span>↖</span>
          <span>Select</span>
        </button>

        <button
          type="button"
          data-testid="tool-hand"
          title="Hand Pan Tool (H)"
          onClick={() => setActiveTool('hand')}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1.5 ${
            activeTool === 'hand'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'hover:bg-slate-800 text-slate-300'
          }`}
        >
          <span>✋</span>
          <span>Pan</span>
        </button>

        <div className="h-5 w-px bg-slate-800 mx-1" />

        <button
          type="button"
          data-testid="tool-rect"
          title="Rectangle (R)"
          onClick={() => setActiveTool('rect')}
          className={`px-2.5 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1.5 ${
            activeTool === 'rect'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'hover:bg-slate-800 text-slate-300'
          }`}
        >
          <span>▭</span>
          <span>Rect</span>
        </button>

        <button
          type="button"
          data-testid="tool-circle"
          title="Circle (C)"
          onClick={() => setActiveTool('circle')}
          className={`px-2.5 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1.5 ${
            activeTool === 'circle'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'hover:bg-slate-800 text-slate-300'
          }`}
        >
          <span>◯</span>
          <span>Circle</span>
        </button>

        <button
          type="button"
          data-testid="tool-text"
          title="Text (T)"
          onClick={() => setActiveTool('text')}
          className={`px-2.5 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1.5 ${
            activeTool === 'text'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'hover:bg-slate-800 text-slate-300'
          }`}
        >
          <span>T</span>
          <span>Text</span>
        </button>

        <button
          type="button"
          data-testid="tool-image-upload"
          title="Upload Image Asset"
          onClick={() => fileInputRef.current?.click()}
          className="px-2.5 py-1.5 rounded-lg text-sm font-medium transition hover:bg-slate-800 text-slate-300 flex items-center gap-1.5"
        >
          <span>🖼️</span>
          <span>Image</span>
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleImageUpload}
        />
      </div>

      {/* 🪄 Section 2: AI Magic Actions */}
      <div className="flex items-center space-x-1.5 bg-slate-950/80 p-1 rounded-xl border border-indigo-900/40">
        <button
          type="button"
          data-testid="ai-cutout-btn"
          title="1-Click Background Removal (BiRefNet / SAM 2)"
          disabled={!selectedNodeId || aiState.isProcessing}
          onClick={handleTriggerCutout}
          className="px-3 py-1 rounded-lg text-xs font-semibold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center gap-1 shadow-sm transition"
        >
          <span>✂️</span>
          <span>1-Click Cutout</span>
        </button>

        <button
          type="button"
          data-testid="ai-relight-btn"
          title="Harmonized Relighting (IC-Light)"
          disabled={!selectedNodeId || aiState.isProcessing}
          onClick={() => setShowRelightModal(true)}
          className="px-3 py-1 rounded-lg text-xs font-semibold bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center gap-1 shadow-sm transition"
        >
          <span>💡</span>
          <span>AI Relight</span>
        </button>

        <button
          type="button"
          data-testid="ai-generate-btn"
          title="Generate Layer (FLUX.1 + LayerDiffuse)"
          disabled={aiState.isProcessing}
          onClick={() => setShowGenerateModal(true)}
          className="px-3 py-1 rounded-lg text-xs font-semibold bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center gap-1 shadow-sm transition"
        >
          <span>✨</span>
          <span>Generate Layer</span>
        </button>
      </div>

      {/* ⚡ Section 3: History, Zoom & Save Controls */}
      <div className="flex items-center space-x-2">
        {/* Undo / Redo */}
        <div className="flex items-center space-x-1">
          <button
            type="button"
            data-testid="history-undo-btn"
            title="Undo (Ctrl+Z)"
            disabled={!canUndo}
            onClick={() => undo()}
            className="p-1.5 rounded-lg text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition"
          >
            ↩
          </button>
          <button
            type="button"
            data-testid="history-redo-btn"
            title="Redo (Ctrl+Y)"
            disabled={!canRedo}
            onClick={() => redo()}
            className="p-1.5 rounded-lg text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition"
          >
            ↪
          </button>
        </div>

        <div className="h-5 w-px bg-slate-800" />

        {/* Zoom Controls */}
        <div className="flex items-center space-x-1 text-xs">
          <button
            type="button"
            data-testid="zoom-out-btn"
            title="Zoom Out (-)"
            onClick={handleZoomOut}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-300"
          >
            -
          </button>
          <button
            type="button"
            data-testid="zoom-reset-btn"
            title="Reset Zoom to 100%"
            onClick={handleZoomReset}
            className="px-1.5 py-1 font-mono text-slate-300 hover:text-white"
          >
            {zoomPercentage}%
          </button>
          <button
            type="button"
            data-testid="zoom-in-btn"
            title="Zoom In (+)"
            onClick={handleZoomIn}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-300"
          >
            +
          </button>
        </div>

        <div className="h-5 w-px bg-slate-800" />

        {/* Save Draft Button */}
        <button
          type="button"
          data-testid="save-draft-btn"
          title="Save Canvas State to IndexedDB / OPFS"
          disabled={isSaving || !isDirty}
          onClick={() => saveDraft()}
          className={`px-3 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
            isDirty
              ? 'bg-blue-600 hover:bg-blue-500 text-white shadow'
              : 'bg-slate-800 text-slate-400'
          }`}
        >
          <span>{isSaving ? '⏳' : '💾'}</span>
          <span>{isSaving ? 'Saving...' : isDirty ? 'Save *' : 'Saved'}</span>
        </button>
      </div>

      {/* Modal: AI Generate Layer */}
      <AIPromptModal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        onSubmit={handleTriggerGenerate}
        isProcessing={aiState.isProcessing && aiState.actionType === 'generate'}
      />

      {/* Modal: AI Relight */}
      {showRelightModal && (
        <div
          data-testid="modal-ai-relight"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        >
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-5 w-full max-w-md shadow-2xl">
            <h3 className="text-base font-bold text-slate-100 mb-2 flex items-center gap-2">
              <span>💡</span> AI Relight (IC-Light)
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Specify lighting setup or environment color temperature to harmonize the selected layer.
            </p>
            <textarea
              autoFocus
              data-testid="input-ai-relight-prompt"
              value={relightPrompt}
              onChange={(e) => setRelightPrompt(e.target.value)}
              placeholder="e.g. Sunset golden hour backlight with warm rim lighting..."
              className="w-full h-24 p-3 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500 mb-4 resize-none"
            />
            <div className="flex justify-end space-x-2">
              <button
                type="button"
                onClick={() => setShowRelightModal(false)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                data-testid="submit-ai-relight"
                disabled={!relightPrompt.trim()}
                onClick={handleTriggerRelight}
                className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-amber-600 hover:bg-amber-500 text-white disabled:opacity-40"
              >
                Apply Relight
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
