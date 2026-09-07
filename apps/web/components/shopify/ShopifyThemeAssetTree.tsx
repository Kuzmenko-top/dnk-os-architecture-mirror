// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_shopify_ShopifyThemeAssetTree"
// purpose: "Categorized interactive Shopify Theme file tree for Visual Canvas & Section Inspector"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState } from 'react';
import { ThemeAssetTree, ThemeAsset } from '../../lib/api/shopify_canvas_client';

interface ShopifyThemeAssetTreeProps {
  tree: ThemeAssetTree | null;
  selectedAssetKey?: string;
  onSelectAsset?: (asset: ThemeAsset) => void;
  isLoading?: boolean;
}

export const ShopifyThemeAssetTree: React.FC<ShopifyThemeAssetTreeProps> = ({
  tree,
  selectedAssetKey,
  onSelectAsset,
  isLoading = false,
}) => {
  const [expandedCats, setExpandedCats] = useState<Record<string, boolean>>({
    layout: true,
    templates: true,
    sections: true,
    snippets: true,
    assets: false,
    config: false,
    locales: false,
  });

  if (isLoading) {
    return (
      <div className="p-4 text-xs font-mono text-slate-500 animate-pulse">
        Завантаження структури ассетів теми...
      </div>
    );
  }

  if (!tree) {
    return (
      <div className="p-4 text-xs font-mono text-slate-500">
        Немає даних дерева теми
      </div>
    );
  }

  const categories: Array<{ key: keyof ThemeAssetTree; label: string; icon: string; badgeColor: string }> = [
    { key: 'layout', label: 'Layouts', icon: '📐', badgeColor: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' },
    { key: 'templates', label: 'Templates', icon: '📄', badgeColor: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
    { key: 'sections', label: 'Sections', icon: '🧩', badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
    { key: 'snippets', label: 'Snippets', icon: '✂️', badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
    { key: 'assets', label: 'Assets (CSS/JS)', icon: '🎨', badgeColor: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
    { key: 'config', label: 'Config', icon: '⚙️', badgeColor: 'bg-slate-500/10 text-slate-400 border-slate-500/20' },
    { key: 'locales', label: 'Locales', icon: '🌐', badgeColor: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
  ];

  const toggleCategory = (catKey: string) => {
    setExpandedCats((prev) => ({ ...prev, [catKey]: !prev[catKey] }));
  };

  return (
    <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 space-y-2 text-xs font-mono">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-[11px] text-slate-400">
        <span className="font-semibold text-slate-300">Файли Теми ({tree.total_files})</span>
        <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
          Shopify v2024-01
        </span>
      </div>

      <div className="space-y-1 overflow-y-auto max-h-96 pr-1">
        {categories.map(({ key, label, icon, badgeColor }) => {
          const items = (tree[key] as ThemeAsset[]) || [];
          if (items.length === 0) return null;
          const isExpanded = expandedCats[key as string] ?? false;

          return (
            <div key={key as string} className="space-y-0.5">
              <button
                onClick={() => toggleCategory(key as string)}
                className="w-full flex items-center justify-between p-1.5 rounded hover:bg-slate-900/80 text-left transition-colors text-slate-300"
              >
                <div className="flex items-center space-x-1.5">
                  <span>{icon}</span>
                  <span className="font-medium text-[11px]">{label}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <span className={`text-[9px] px-1.5 py-0.2 rounded border ${badgeColor}`}>
                    {items.length}
                  </span>
                  <span className="text-[10px] text-slate-500">{isExpanded ? '▼' : '▶'}</span>
                </div>
              </button>

              {isExpanded && (
                <div className="pl-5 space-y-0.5 border-l border-slate-800/80 ml-2">
                  {items.map((asset) => {
                    const isSelected = selectedAssetKey === asset.key;
                    const fileName = asset.key.split('/').pop() || asset.key;

                    return (
                      <button
                        key={asset.key}
                        onClick={() => onSelectAsset?.(asset)}
                        className={`w-full flex items-center justify-between px-2 py-1 rounded text-[11px] text-left transition-all ${
                          isSelected
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                        }`}
                      >
                        <span className="truncate">{fileName}</span>
                        {asset.size && (
                          <span className="text-[9px] text-slate-500 font-mono">
                            {(asset.size / 1024).toFixed(1)}k
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ShopifyThemeAssetTree;
