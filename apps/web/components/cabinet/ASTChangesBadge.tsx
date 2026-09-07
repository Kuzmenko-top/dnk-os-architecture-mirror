// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_cabinet_ASTChangesBadge"
// purpose: "AST Symbol changes badge component for displaying class, function, method and MRH header changes"
// author: "DNK-e.com Maksym"

import React, { useState } from "react";
import { ASTFileDiff, ASTSymbolChange } from "../../lib/api_client";

interface ASTChangesBadgeProps {
  astDiff?: ASTFileDiff;
  compact?: boolean;
}

export const ASTChangesBadge: React.FC<ASTChangesBadgeProps> = ({ astDiff, compact = false }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!astDiff || (!astDiff.symbols || astDiff.symbols.length === 0)) {
    return null;
  }

  const { added_count, modified_count, deleted_count, symbols } = astDiff;

  const getSymbolKindIcon = (kind: ASTSymbolChange["kind"]) => {
    switch (kind) {
      case "class":
        return "📦";
      case "function":
        return "⚡";
      case "method":
        return "🔹";
      case "header":
        return "🛡️";
      default:
        return "📄";
    }
  };

  const getChangeBadgeColor = (changeType: ASTSymbolChange["change_type"]) => {
    switch (changeType) {
      case "added":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "modified":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      case "deleted":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
    }
  };

  return (
    <div className="relative inline-block text-left">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono bg-cyan-950/40 border border-cyan-800/40 text-cyan-300 hover:bg-cyan-900/40 transition-colors"
        title="AST Symbol Changes"
      >
        <span className="text-cyan-400 font-bold">AST:</span>
        {added_count > 0 && <span className="text-emerald-400">+{added_count}</span>}
        {modified_count > 0 && <span className="text-amber-400">~{modified_count}</span>}
        {deleted_count > 0 && <span className="text-rose-400">-{deleted_count}</span>}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 rounded-lg bg-slate-900 border border-slate-700 shadow-xl z-50 p-3 text-xs">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
            <span className="font-semibold text-slate-200">AST Changes ({symbols.length})</span>
            <span className="text-[10px] text-slate-400 font-mono">{astDiff.language}</span>
          </div>

          <div className="max-h-56 overflow-y-auto space-y-1.5 pr-1">
            {symbols.map((sym, idx) => (
              <div
                key={idx}
                className={`flex items-center justify-between p-1.5 rounded border text-[11px] font-mono ${getChangeBadgeColor(
                  sym.change_type
                )}`}
              >
                <div className="flex items-center gap-1.5 truncate">
                  <span>{getSymbolKindIcon(sym.kind)}</span>
                  <span className="font-medium truncate" title={sym.name}>
                    {sym.name}
                  </span>
                </div>
                <span className="text-[9px] uppercase px-1 rounded bg-slate-800/80">
                  {sym.kind}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
