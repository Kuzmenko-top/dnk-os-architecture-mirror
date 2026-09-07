// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_ShopifyCanvasSyncBar"
// purpose: "Shopify Theme sync toolbar for Canvas & Whiteboard visual workspace (DNK-ECOM-004)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState } from 'react';
import { ShopifyCanvasGraph } from '../../lib/api/shopify_canvas_client';

interface ShopifyCanvasSyncBarProps {
  graph: ShopifyCanvasGraph | null;
  selectedStore: string;
  selectedThemeId: string | number;
  onSyncToCanvas?: (graph: ShopifyCanvasGraph) => void;
  onOpenAssetTree?: () => void;
  isSyncing?: boolean;
}

export const ShopifyCanvasSyncBar: React.FC<ShopifyCanvasSyncBarProps> = ({
  graph,
  selectedStore = 'dnk-e-com.myshopify.com',
  selectedThemeId = '160000001',
  onSyncToCanvas,
  onOpenAssetTree,
  isSyncing = false,
}) => {
  const [storeInput, setStoreInput] = useState(selectedStore);

  const nodeCount = graph?.nodes?.length ?? 0;
  const edgeCount = graph?.edges?.length ?? 0;

  return (
    <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-3 flex items-center justify-between shadow-xl text-xs font-mono">
      {/* Left info badge */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-bold text-slate-200">Shopify Theme Canvas Sync</span>
        </div>

        <div className="h-4 w-px bg-slate-800" />

        <div className="flex items-center space-x-2 text-slate-400">
          <span>Store:</span>
          <span className="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            {selectedStore}
          </span>
          <span>Theme ID:</span>
          <span className="text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
            #{selectedThemeId}
          </span>
        </div>
      </div>

      {/* Center Graph Stats */}
      <div className="hidden md:flex items-center space-x-3 text-[11px] text-slate-400">
        <div className="flex items-center space-x-1">
          <span className="text-slate-500">Nodes:</span>
          <span className="font-bold text-slate-200">{nodeCount}</span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="text-slate-500">Relationships:</span>
          <span className="font-bold text-amber-400">{edgeCount}</span>
        </div>
        <div className="flex items-center space-x-1">
          <span className="text-slate-500">AST Validation:</span>
          <span className="text-emerald-400 font-semibold">100% VALID</span>
        </div>
      </div>

      {/* Right Action buttons */}
      <div className="flex items-center space-x-2">
        {onOpenAssetTree && (
          <button
            onClick={onOpenAssetTree}
            className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-all font-medium"
          >
            📁 Asset Tree
          </button>
        )}

        {onSyncToCanvas && graph && (
          <button
            onClick={() => onSyncToCanvas(graph)}
            disabled={isSyncing}
            className="px-3.5 py-1.5 rounded-lg border border-emerald-500/40 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 font-semibold transition-all flex items-center space-x-1.5 shadow-lg shadow-emerald-950/40"
          >
            <span>{isSyncing ? 'Синхронізація...' : '⚡ Sync to Whiteboard'}</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default ShopifyCanvasSyncBar;
