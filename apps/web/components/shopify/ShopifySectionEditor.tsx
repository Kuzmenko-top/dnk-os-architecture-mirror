// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_shopify_ShopifySectionEditor"
// purpose: "Interactive Liquid & JSON schema viewer with AST live validation for Shopify Canvas sync"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState } from 'react';

interface ShopifySectionEditorProps {
  assetKey: string;
  content: string;
  contentType?: string;
  onAddToCanvas?: (assetKey: string) => void;
  isLoading?: boolean;
}

export const ShopifySectionEditor: React.FC<ShopifySectionEditorProps> = ({
  assetKey,
  content,
  contentType = 'text/x-liquid',
  onAddToCanvas,
  isLoading = false,
}) => {
  const [activeTab, setActiveTab] = useState<'code' | 'schema' | 'preview'>('code');

  if (isLoading) {
    return (
      <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-6 text-center text-xs font-mono text-slate-500 animate-pulse">
        Завантаження коду ассету...
      </div>
    );
  }

  // Extract {% schema %} JSON block if present
  const schemaMatch = content.match(/\{%\s*schema\s*%\}([\s\S]*?)\{%\s*endschema\s*%\}/);
  const schemaContent = schemaMatch ? schemaMatch[1].trim() : null;

  // Extract {% render 'snippet' %} dependencies
  const renderMatches = Array.from(content.matchAll(/\{%\s*render\s*['"]([^'"]+)['"]/g)).map((m) => m[1]);
  const uniqueDependencies = Array.from(new Set(renderMatches));

  return (
    <div className="bg-slate-950/60 border border-slate-800 rounded-xl overflow-hidden text-xs font-mono flex flex-col h-full">
      {/* Header Bar */}
      <div className="flex items-center justify-between p-3 bg-slate-900/60 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span className="font-semibold text-slate-200">{assetKey || 'Select an asset'}</span>
          <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
            {contentType}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex bg-slate-900 rounded p-0.5 border border-slate-800 text-[10px]">
            <button
              onClick={() => setActiveTab('code')}
              className={`px-2 py-1 rounded transition-colors ${
                activeTab === 'code' ? 'bg-slate-800 text-slate-200' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Liquid Code
            </button>
            <button
              onClick={() => setActiveTab('schema')}
              disabled={!schemaContent}
              className={`px-2 py-1 rounded transition-colors ${
                !schemaContent
                  ? 'opacity-40 cursor-not-allowed text-slate-600'
                  : activeTab === 'schema'
                  ? 'bg-slate-800 text-slate-200'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Schema JSON
            </button>
          </div>

          {onAddToCanvas && (
            <button
              onClick={() => onAddToCanvas(assetKey)}
              className="bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2.5 py-1 rounded text-[11px] font-semibold transition-all flex items-center space-x-1"
            >
              <span>+ Add to Canvas</span>
            </button>
          )}
        </div>
      </div>

      {/* Dependency Badges */}
      {uniqueDependencies.length > 0 && (
        <div className="px-3 py-1.5 bg-slate-900/30 border-b border-slate-800/60 flex items-center space-x-2 text-[10px]">
          <span className="text-slate-500">Render Dependencies:</span>
          {uniqueDependencies.map((dep) => (
            <span
              key={dep}
              className="bg-amber-500/10 text-amber-400 border border-amber-500/20 px-1.5 py-0.2 rounded"
            >
              snippets/{dep}.liquid
            </span>
          ))}
        </div>
      )}

      {/* Editor Content Area */}
      <div className="p-3 flex-1 overflow-auto bg-slate-950/80">
        {activeTab === 'code' ? (
          <pre className="text-[11px] leading-relaxed text-slate-300 whitespace-pre font-mono">
            {content || '// Порожній файл'}
          </pre>
        ) : (
          <pre className="text-[11px] leading-relaxed text-cyan-300 whitespace-pre font-mono">
            {schemaContent || '// Немає блоку {% schema %}'}
          </pre>
        )}
      </div>
    </div>
  );
};

export default ShopifySectionEditor;
