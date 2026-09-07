// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_cabinet_DiffViewer"
// purpose: "Unified and Split diff viewer component with line numbers, hunk headers, and virtualization support"
// author: "DNK-e.com Maksym"

import React, { useState } from "react";
import { ParsedFileDiff, DiffHunk, DiffLine } from "../../lib/api_client";

interface DiffViewerProps {
  fileDiff?: ParsedFileDiff;
  viewMode?: "unified" | "split";
  onViewModeChange?: (mode: "unified" | "split") => void;
  isLoading?: boolean;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
  fileDiff,
  viewMode = "unified",
  onViewModeChange,
  isLoading = false
}) => {
  const [copied, setCopied] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 bg-slate-950/60 rounded-lg border border-slate-800">
        <div className="text-slate-400 font-mono text-xs animate-pulse">
          Loading file diff...
        </div>
      </div>
    );
  }

  if (!fileDiff) {
    return (
      <div className="flex items-center justify-center h-64 bg-slate-950/60 rounded-lg border border-slate-800">
        <div className="text-slate-500 font-mono text-xs">
          Select a file from the tree to inspect changes
        </div>
      </div>
    );
  }

  const handleCopyPatch = () => {
    if (!fileDiff) return;
    const rawPatch = fileDiff.hunks
      .map(
        (h) =>
          h.header +
          "\n" +
          h.lines
            .map((l) => (l.type === "add" ? "+" : l.type === "delete" ? "-" : " ") + l.content)
            .join("\n")
      )
      .join("\n");

    navigator.clipboard.writeText(rawPatch);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "added":
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">ADDED</span>;
      case "modified":
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/20 text-amber-400 border border-amber-500/30">MODIFIED</span>;
      case "deleted":
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-500/20 text-rose-400 border border-rose-500/30">DELETED</span>;
      case "renamed":
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-500/20 text-purple-400 border border-purple-500/30">RENAMED</span>;
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950/80 border border-slate-800 rounded-lg overflow-hidden font-mono text-xs">
      {/* File Diff Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-2 truncate pr-2">
          {getStatusBadge(fileDiff.status)}
          <span className="font-semibold text-slate-200 truncate" title={fileDiff.filename}>
            {fileDiff.filename}
          </span>
          <span className="text-[11px] text-emerald-400 font-mono">+{fileDiff.additions}</span>
          <span className="text-[11px] text-rose-400 font-mono">-{fileDiff.deletions}</span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* View Mode Toggle */}
          {onViewModeChange && (
            <div className="flex bg-slate-950 p-0.5 rounded border border-slate-800">
              <button
                onClick={() => onViewModeChange("unified")}
                className={`px-2 py-0.5 text-[10px] font-semibold rounded ${
                  viewMode === "unified"
                    ? "bg-slate-800 text-cyan-300"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Unified
              </button>
              <button
                onClick={() => onViewModeChange("split")}
                className={`px-2 py-0.5 text-[10px] font-semibold rounded ${
                  viewMode === "split"
                    ? "bg-slate-800 text-cyan-300"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Split
              </button>
            </div>
          )}

          <button
            onClick={handleCopyPatch}
            className="px-2 py-1 text-[10px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition-colors"
          >
            {copied ? "Copied!" : "Copy Patch"}
          </button>
        </div>
      </div>

      {/* Diff Content Body */}
      <div className="flex-1 overflow-x-auto overflow-y-auto bg-slate-950 p-2">
        {fileDiff.is_binary ? (
          <div className="p-8 text-center text-slate-500">
            Binary file changes cannot be displayed inline.
          </div>
        ) : fileDiff.hunks.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            No patch content available for this file.
          </div>
        ) : (
          fileDiff.hunks.map((hunk, hIdx) => (
            <div key={hIdx} className="mb-4 rounded border border-slate-800/80 overflow-hidden">
              {/* Hunk Header */}
              <div className="px-3 py-1 bg-slate-900/80 text-cyan-400/90 text-[11px] font-mono border-b border-slate-800/80 select-none">
                {hunk.header}
              </div>

              {/* Hunk Lines */}
              {viewMode === "unified" ? (
                <div className="divide-y divide-slate-900/40">
                  {hunk.lines.map((line, lIdx) => (
                    <div
                      key={lIdx}
                      className={`flex items-stretch font-mono text-[11px] leading-relaxed ${
                        line.type === "add"
                          ? "bg-emerald-950/30 text-emerald-300"
                          : line.type === "delete"
                          ? "bg-rose-950/30 text-rose-300"
                          : "text-slate-300 hover:bg-slate-900/40"
                      }`}
                    >
                      <div className="w-10 py-0.5 px-1 text-right text-slate-600 select-none bg-slate-900/40 border-r border-slate-800/40 shrink-0">
                        {line.old_line_number || ""}
                      </div>
                      <div className="w-10 py-0.5 px-1 text-right text-slate-600 select-none bg-slate-900/40 border-r border-slate-800/40 shrink-0">
                        {line.new_line_number || ""}
                      </div>
                      <div className="w-6 py-0.5 text-center select-none shrink-0 font-bold">
                        {line.type === "add" ? "+" : line.type === "delete" ? "-" : " "}
                      </div>
                      <div className="py-0.5 px-2 whitespace-pre overflow-x-auto flex-1 font-mono">
                        {line.content}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                /* Split Side-by-Side Mode */
                <div className="divide-y divide-slate-900/40">
                  {hunk.lines.map((line, lIdx) => {
                    const isAdd = line.type === "add";
                    const isDel = line.type === "delete";

                    return (
                      <div key={lIdx} className="grid grid-cols-2 font-mono text-[11px] leading-relaxed">
                        {/* Left Side (Old) */}
                        <div
                          className={`flex items-stretch border-r border-slate-800/60 ${
                            isDel ? "bg-rose-950/30 text-rose-300" : isAdd ? "bg-slate-950/50 text-slate-700" : "text-slate-300"
                          }`}
                        >
                          <div className="w-10 py-0.5 px-1 text-right text-slate-600 select-none bg-slate-900/40 border-r border-slate-800/40 shrink-0">
                            {!isAdd ? line.old_line_number || "" : ""}
                          </div>
                          <div className="py-0.5 px-2 whitespace-pre overflow-x-auto flex-1 font-mono">
                            {!isAdd ? line.content : ""}
                          </div>
                        </div>

                        {/* Right Side (New) */}
                        <div
                          className={`flex items-stretch ${
                            isAdd ? "bg-emerald-950/30 text-emerald-300" : isDel ? "bg-slate-950/50 text-slate-700" : "text-slate-300"
                          }`}
                        >
                          <div className="w-10 py-0.5 px-1 text-right text-slate-600 select-none bg-slate-900/40 border-r border-slate-800/40 shrink-0">
                            {!isDel ? line.new_line_number || "" : ""}
                          </div>
                          <div className="py-0.5 px-2 whitespace-pre overflow-x-auto flex-1 font-mono">
                            {!isDel ? line.content : ""}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
