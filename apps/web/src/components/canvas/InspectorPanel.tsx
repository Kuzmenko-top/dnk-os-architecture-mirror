// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/canvas/InspectorPanel.tsx"
// purpose: "Property Inspector panel: geometry, appearance, typography & node properties editor."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import React from 'react';
import { useCanvasStudioStore } from './store';
import type { NodeProperties } from '../../canvas/storage/types/canvas';

interface InspectorPanelProps {
  className?: string;
}

export const InspectorPanel: React.FC<InspectorPanelProps> = ({ className = '' }) => {
  const { selectedNodeIds, canvasState, updateNode, runAICutout } = useCanvasStudioStore();

  const layers = canvasState.layers || [];
  const selectedLayers = layers.filter((layer) => selectedNodeIds.includes(layer.id));
  const selectedLayer = selectedLayers.length === 1 ? selectedLayers[0] : null;

  // The node inside layer
  const primaryNode: NodeProperties | null =
    selectedLayer && selectedLayer.nodes && selectedLayer.nodes.length > 0
      ? selectedLayer.nodes[0]
      : null;

  if (selectedLayers.length === 0) {
    return (
      <div
        data-testid="dnk-inspector-panel"
        className={`w-72 bg-slate-900 border-l border-slate-800 flex flex-col h-full text-slate-100 select-none p-4 ${className}`}
      >
        <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-6 flex items-center gap-2">
          <span>⚙️</span>
          <span>Properties</span>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center text-center p-4 border border-dashed border-slate-800 rounded-2xl">
          <span className="text-2xl mb-2">🎯</span>
          <p className="text-xs font-medium text-slate-400">No selection</p>
          <p className="text-[11px] text-slate-600 mt-1">
            Click an element on canvas or layer list to inspect properties.
          </p>
        </div>
      </div>
    );
  }

  if (selectedLayers.length > 1) {
    return (
      <div
        data-testid="dnk-inspector-panel"
        className={`w-72 bg-slate-900 border-l border-slate-800 flex flex-col h-full text-slate-100 select-none p-4 ${className}`}
      >
        <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-6 flex items-center gap-2">
          <span>⚙️</span>
          <span>Properties</span>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center text-center p-4 border border-indigo-900/40 bg-indigo-950/20 rounded-2xl">
          <span className="text-2xl mb-2">✨</span>
          <p className="text-xs font-bold text-indigo-300">
            {selectedLayers.length} Layers Selected
          </p>
          <p className="text-[11px] text-slate-400 mt-1">
            Multi-selection mode.
          </p>
        </div>
      </div>
    );
  }

  if (!selectedLayer || !primaryNode) return null;

  const nodeProps = primaryNode.props || {};

  const handlePropertyChange = (patch: Partial<NodeProperties>) => {
    updateNode(selectedLayer.id, patch);
  };

  const handlePropsChange = (propsPatch: Record<string, unknown>) => {
    updateNode(selectedLayer.id, {
      props: {
        ...nodeProps,
        ...propsPatch,
      },
    });
  };

  return (
    <div
      data-testid="dnk-inspector-panel"
      className={`w-72 bg-slate-900 border-l border-slate-800 flex flex-col h-full text-slate-100 select-none overflow-y-auto ${className}`}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs">⚙️</span>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Inspector
          </h2>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-indigo-400 border border-slate-700">
          {(primaryNode.type || 'layer').toUpperCase()}
        </span>
      </div>

      <div className="p-4 space-y-6">
        {/* Section 1: Geometry */}
        <div>
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center justify-between">
            <span>Geometry</span>
            <span className="text-[10px] font-mono text-slate-500">Transform</span>
          </h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <label className="block text-[10px] text-slate-500 mb-1">X Position</label>
              <input
                type="number"
                data-testid="input-prop-x"
                value={Math.round(primaryNode.x || 0)}
                onChange={(e) => handlePropertyChange({ x: parseFloat(e.target.value) || 0 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-[10px] text-slate-500 mb-1">Y Position</label>
              <input
                type="number"
                data-testid="input-prop-y"
                value={Math.round(primaryNode.y || 0)}
                onChange={(e) => handlePropertyChange({ y: parseFloat(e.target.value) || 0 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-[10px] text-slate-500 mb-1">Width (W)</label>
              <input
                type="number"
                data-testid="input-prop-width"
                value={Math.round(primaryNode.width || 0)}
                onChange={(e) => handlePropertyChange({ width: Math.max(1, parseFloat(e.target.value) || 1) })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-[10px] text-slate-500 mb-1">Height (H)</label>
              <input
                type="number"
                data-testid="input-prop-height"
                value={Math.round(primaryNode.height || 0)}
                onChange={(e) => handlePropertyChange({ height: Math.max(1, parseFloat(e.target.value) || 1) })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="col-span-2">
              <div className="flex justify-between items-center mb-1">
                <label className="text-[10px] text-slate-500">Rotation</label>
                <span className="text-[10px] font-mono text-slate-400">{Math.round(primaryNode.rotation || 0)}°</span>
              </div>
              <input
                type="range"
                min="0"
                max="360"
                data-testid="input-prop-rotation"
                value={primaryNode.rotation || 0}
                onChange={(e) => handlePropertyChange({ rotation: parseInt(e.target.value, 10) })}
                className="w-full accent-indigo-500 bg-slate-950 h-1.5 rounded-lg cursor-pointer"
              />
            </div>
          </div>
        </div>

        <div className="h-px bg-slate-800" />

        {/* Section 2: Appearance & Styling */}
        <div>
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">
            Appearance
          </h3>
          <div className="space-y-3 text-xs">
            {/* Fill Color */}
            <div>
              <label className="block text-[10px] text-slate-500 mb-1">Fill Color</label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  data-testid="input-prop-fill"
                  value={primaryNode.fill || '#3b82f6'}
                  onChange={(e) => handlePropertyChange({ fill: e.target.value })}
                  className="w-8 h-8 rounded-lg bg-transparent border-0 cursor-pointer"
                />
                <input
                  type="text"
                  value={primaryNode.fill || '#3b82f6'}
                  onChange={(e) => handlePropertyChange({ fill: e.target.value })}
                  className="flex-1 font-mono bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Stroke Color & Width */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[10px] text-slate-500 mb-1">Stroke Color</label>
                <input
                  type="color"
                  data-testid="input-prop-stroke"
                  value={primaryNode.stroke || '#000000'}
                  onChange={(e) => handlePropertyChange({ stroke: e.target.value })}
                  className="w-full h-8 rounded-lg bg-transparent border-0 cursor-pointer"
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-500 mb-1">Stroke Width</label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  data-testid="input-prop-strokewidth"
                  value={primaryNode.strokeWidth || 0}
                  onChange={(e) => handlePropertyChange({ strokeWidth: Math.max(0, parseInt(e.target.value, 10) || 0) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Opacity Slider */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-[10px] text-slate-500">Opacity</label>
                <span className="text-[10px] font-mono text-slate-400">
                  {Math.round((primaryNode.opacity ?? 1) * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                data-testid="input-prop-opacity"
                value={(primaryNode.opacity ?? 1) * 100}
                onChange={(e) => handlePropertyChange({ opacity: parseInt(e.target.value, 10) / 100 })}
                className="w-full accent-indigo-500 bg-slate-950 h-1.5 rounded-lg cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Section 3: Typography (If Text) */}
        {primaryNode.type === 'text' && (
          <>
            <div className="h-px bg-slate-800" />
            <div>
              <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">
                Typography
              </h3>
              <div className="space-y-3 text-xs">
                <div>
                  <label className="block text-[10px] text-slate-500 mb-1">Text Content</label>
                  <textarea
                    data-testid="input-prop-text-content"
                    value={(nodeProps.text as string) || ''}
                    onChange={(e) => handlePropsChange({ text: e.target.value })}
                    className="w-full h-20 bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[10px] text-slate-500 mb-1">Font Size</label>
                    <input
                      type="number"
                      min="8"
                      max="300"
                      data-testid="input-prop-fontsize"
                      value={(nodeProps.fontSize as number) || 24}
                      onChange={(e) => handlePropsChange({ fontSize: parseInt(e.target.value, 10) || 24 })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] text-slate-500 mb-1">Alignment</label>
                    <select
                      data-testid="select-prop-align"
                      value={(nodeProps.align as string) || 'left'}
                      onChange={(e) => handlePropsChange({ align: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="left">Left</option>
                      <option value="center">Center</option>
                      <option value="right">Right</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Section 4: Image Layer Specifics */}
        {primaryNode.type === 'image' && (
          <>
            <div className="h-px bg-slate-800" />
            <div>
              <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">
                Image Layer
              </h3>
              <div className="space-y-3 text-xs">
                {nodeProps.src && (
                  <div className="p-2 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-center overflow-hidden">
                    <img
                      src={nodeProps.src as string}
                      alt={primaryNode.name}
                      className="max-h-28 object-contain rounded-lg"
                    />
                  </div>
                )}

                <button
                  type="button"
                  data-testid="btn-inspector-cutout"
                  onClick={() => runAICutout(selectedLayer.id)}
                  className="w-full py-2 px-3 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center gap-1.5 shadow transition"
                >
                  <span>✂️</span>
                  <span>1-Click Cutout (BiRefNet)</span>
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export const PropertyInspector = InspectorPanel;
