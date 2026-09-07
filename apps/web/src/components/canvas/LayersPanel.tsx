// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/canvas/LayersPanel.tsx"
// purpose: "Layer hierarchy panel: reordering, lock/hide toggles, node selection sync & layer management."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import React, { useState } from 'react';
import { useCanvasStudioStore } from './store';
import type { LayerState } from '../../canvas/storage/types/canvas';

interface LayersPanelProps {
  className?: string;
}

export const LayersPanel: React.FC<LayersPanelProps> = ({ className = '' }) => {
  const [editingNodeId, setEditingNodeId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');

  const {
    canvasState,
    selectedNodeIds,
    setSelectedNodeIds,
    reorderLayer,
    updateNode,
    deleteNode,
  } = useCanvasStudioStore();

  const layers = canvasState.layers || [];

  const handleSelect = (id: string, multiSelect: boolean) => {
    if (multiSelect) {
      if (selectedNodeIds.includes(id)) {
        setSelectedNodeIds(selectedNodeIds.filter((item) => item !== id));
      } else {
        setSelectedNodeIds([...selectedNodeIds, id]);
      }
    } else {
      setSelectedNodeIds([id]);
    }
  };

  const handleToggleVisibility = (layer: LayerState, e: React.MouseEvent) => {
    e.stopPropagation();
    const isVisible = layer.visible !== false; // default true
    updateNode(layer.id, { visible: !isVisible });
  };

  const handleToggleLock = (layer: LayerState, e: React.MouseEvent) => {
    e.stopPropagation();
    const isLocked = Boolean(layer.locked);
    updateNode(layer.id, { locked: !isLocked });
  };

  const handleMoveUp = (index: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (index >= layers.length - 1) return;
    const targetLayer = layers[index];
    reorderLayer(targetLayer.id, index + 1);
  };

  const handleMoveDown = (index: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (index <= 0) return;
    const targetLayer = layers[index];
    reorderLayer(targetLayer.id, index - 1);
  };

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    deleteNode(id);
  };

  const handleStartRename = (layer: LayerState, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingNodeId(layer.id);
    setEditingName(layer.name || `Layer ${layer.id.slice(0, 4)}`);
  };

  const handleSaveRename = (id: string) => {
    if (editingName.trim()) {
      // Name update
      useCanvasStudioStore.getState().updateNode(id, { name: editingName.trim() });
    }
    setEditingNodeId(null);
  };

  const getNodeIcon = (type: LayerState['type']) => {
    switch (type) {
      case 'rect':
        return '▭';
      case 'circle':
        return '◯';
      case 'text':
        return 'T';
      case 'image':
        return '🖼️';
      default:
        return '📦';
    }
  };

  return (
    <div
      data-testid="dnk-layers-panel"
      className={`w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-full text-slate-100 select-none ${className}`}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <span>🥞</span>
          <span>Layers ({layers.length})</span>
        </h2>
      </div>

      {/* Layer List (Top of stack = highest z-index) */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {layers.length === 0 ? (
          <div className="p-4 text-center text-xs text-slate-500 italic">
            No layers on canvas. Add a shape or text to get started.
          </div>
        ) : (
          [...layers].reverse().map((layer, reverseIndex) => {
            // Calculate actual z-index in original array
            const actualIndex = layers.length - 1 - reverseIndex;
            const isSelected = selectedNodeIds.includes(layer.id);
            const isVisible = layer.visible !== false;
            const isLocked = Boolean(layer.locked);

            return (
              <div
                key={layer.id}
                data-testid={`layer-item-${layer.id}`}
                onClick={(e) => handleSelect(layer.id, e.shiftKey || e.metaKey)}
                className={`group flex items-center justify-between px-2.5 py-2 rounded-xl text-xs font-medium cursor-pointer transition ${
                  isSelected
                    ? 'bg-indigo-600/30 border border-indigo-500/50 text-white'
                    : 'hover:bg-slate-800/80 text-slate-300 border border-transparent'
                }`}
              >
                {/* Left: Type Icon + Name */}
                <div className="flex items-center gap-2 truncate min-w-0 flex-1">
                  <span className="text-slate-400 text-sm font-mono">{getNodeIcon(layer.type)}</span>
                  {editingNodeId === layer.id ? (
                    <input
                      autoFocus
                      type="text"
                      value={editingName}
                      onChange={(e) => setEditingName(e.target.value)}
                      onBlur={() => handleSaveRename(layer.id)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSaveRename(layer.id)}
                      className="bg-slate-950 text-white px-1.5 py-0.5 rounded border border-indigo-500 text-xs w-full focus:outline-none"
                    />
                  ) : (
                    <span
                      onDoubleClick={(e) => handleStartRename(layer, e)}
                      className="truncate font-medium hover:text-white"
                    >
                      {layer.name || `Layer ${actualIndex + 1}`}
                    </span>
                  )}
                </div>

                {/* Right Actions: Reorder, Lock, Hide, Delete */}
                <div className="flex items-center space-x-1 opacity-80 group-hover:opacity-100">
                  {/* Reorder Up */}
                  <button
                    type="button"
                    title="Move Layer Up"
                    disabled={actualIndex >= layers.length - 1}
                    onClick={(e) => handleMoveUp(actualIndex, e)}
                    className="p-1 hover:text-white disabled:opacity-20 text-slate-400"
                  >
                    ▲
                  </button>

                  {/* Reorder Down */}
                  <button
                    type="button"
                    title="Move Layer Down"
                    disabled={actualIndex <= 0}
                    onClick={(e) => handleMoveDown(actualIndex, e)}
                    className="p-1 hover:text-white disabled:opacity-20 text-slate-400"
                  >
                    ▼
                  </button>

                  {/* Lock Toggle */}
                  <button
                    type="button"
                    data-testid={`btn-lock-${layer.id}`}
                    title={isLocked ? 'Unlock Layer' : 'Lock Layer'}
                    onClick={(e) => handleToggleLock(layer, e)}
                    className={`p-1 hover:text-white ${isLocked ? 'text-amber-400' : 'text-slate-500'}`}
                  >
                    {isLocked ? '🔒' : '🔓'}
                  </button>

                  {/* Visibility Toggle */}
                  <button
                    type="button"
                    data-testid={`btn-vis-${layer.id}`}
                    title={isVisible ? 'Hide Layer' : 'Show Layer'}
                    onClick={(e) => handleToggleVisibility(layer, e)}
                    className={`p-1 hover:text-white ${isVisible ? 'text-slate-300' : 'text-slate-600'}`}
                  >
                    {isVisible ? '👁️' : '🙈'}
                  </button>

                  {/* Delete Button */}
                  <button
                    type="button"
                    data-testid={`btn-delete-${layer.id}`}
                    title="Delete Layer"
                    onClick={(e) => handleDelete(layer.id, e)}
                    className="p-1 hover:text-red-400 text-slate-500"
                  >
                    ✕
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
