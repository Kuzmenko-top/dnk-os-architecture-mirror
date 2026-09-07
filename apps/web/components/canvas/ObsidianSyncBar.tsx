// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_ObsidianSyncBar"
// purpose: "Obsidian Vault & JSON Canvas Two-Way Sync Bar with Conflict Resolution & Status Indicator"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import { useCanvasStore } from '../../store/canvasStore';
import { 
  ArrowUpRight, 
  ArrowDownLeft, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Settings2, 
  FolderSync, 
  X 
} from 'lucide-react';

interface ObsidianSyncBarProps {
  defaultVaultPath?: string;
  defaultCanvasName?: string;
  className?: string;
}

export const ObsidianSyncBar: React.FC<ObsidianSyncBarProps> = ({
  defaultVaultPath = './docs/notes',
  defaultCanvasName,
  className = ''
}) => {
  const { 
    obsidianSyncStatus, 
    obsidianSyncMessage, 
    syncToObsidian, 
    canvasId,
    nodes,
    edges 
  } = useCanvasStore();

  const [vaultPath, setVaultPath] = useState(defaultVaultPath);
  const [canvasName, setCanvasName] = useState(defaultCanvasName || `canvas_${canvasId}`);
  const [conflictStrategy, setConflictStrategy] = useState<'last-write-wins' | 'merge-tags'>('last-write-wins');
  const [showSettings, setShowSettings] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Sync canvas name when canvasId changes
  useEffect(() => {
    if (!defaultCanvasName) {
      setCanvasName(`canvas_${canvasId}`);
    }
  }, [canvasId, defaultCanvasName]);

  // Handle toast notifications on sync status updates
  useEffect(() => {
    if (obsidianSyncStatus === 'success' || obsidianSyncStatus === 'error') {
      setToastMessage(obsidianSyncMessage || (obsidianSyncStatus === 'success' ? 'Sync completed' : 'Sync failed'));
      const timer = setTimeout(() => {
        setToastMessage(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [obsidianSyncStatus, obsidianSyncMessage]);

  const handleExport = async () => {
    await syncToObsidian('export', {
      vaultPath,
      canvasName,
      conflictStrategy
    });
  };

  const handleImport = async () => {
    await syncToObsidian('import', {
      vaultPath,
      canvasName,
      conflictStrategy
    });
  };

  const handleTwoWaySync = async () => {
    await syncToObsidian('sync', {
      vaultPath,
      canvasName,
      conflictStrategy
    });
  };

  const isSyncing = obsidianSyncStatus === 'syncing';

  return (
    <div className={`relative z-20 flex flex-col items-center select-none ${className}`}>
      {/* Toast Alert Banner */}
      {toastMessage && (
        <div 
          className={`mb-2 px-3 py-1.5 rounded-lg text-xs flex items-center gap-2 shadow-lg backdrop-blur-md transition-all duration-300 border ${
            obsidianSyncStatus === 'error'
              ? 'bg-rose-950/80 border-rose-500/50 text-rose-200'
              : 'bg-emerald-950/80 border-emerald-500/50 text-emerald-200'
          }`}
        >
          {obsidianSyncStatus === 'error' ? (
            <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
          ) : (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
          )}
          <span className="truncate max-w-xs">{toastMessage}</span>
          <button 
            type="button"
            onClick={() => setToastMessage(null)}
            className="text-neutral-400 hover:text-white ml-1"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Main Obsidian Sync Toolbar */}
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#14151a]/90 backdrop-blur-md border border-[#2a2b36] shadow-2xl text-xs text-neutral-300">
        <div className="flex items-center gap-1.5 pr-2 border-r border-[#262835]">
          <FolderSync className="w-4 h-4 text-purple-400 shrink-0" />
          <span className="font-semibold text-white tracking-wide flex items-center gap-1">
            Obsidian
            <span className="text-[10px] px-1.5 py-0.2 bg-purple-500/20 text-purple-300 rounded border border-purple-500/30">
              v1.0
            </span>
          </span>
        </div>

        {/* Node & Edge stats */}
        <div className="hidden sm:flex items-center gap-1.5 px-1.5 text-[11px] text-neutral-400">
          <span>{nodes.length} nodes</span>
          <span>•</span>
          <span>{edges.length} edges</span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            disabled={isSyncing}
            onClick={handleExport}
            title="Export living canvas to Markdown notes and .canvas in Obsidian Vault"
            className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#20222e] hover:bg-[#2b2e3d] active:scale-95 disabled:opacity-50 text-neutral-200 hover:text-white transition-all font-medium border border-neutral-700/50"
          >
            <ArrowUpRight className="w-3.5 h-3.5 text-indigo-400" />
            <span>Export</span>
          </button>

          <button
            type="button"
            disabled={isSyncing}
            onClick={handleImport}
            title="Import Markdown notes and .canvas from Obsidian Vault"
            className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#20222e] hover:bg-[#2b2e3d] active:scale-95 disabled:opacity-50 text-neutral-200 hover:text-white transition-all font-medium border border-neutral-700/50"
          >
            <ArrowDownLeft className="w-3.5 h-3.5 text-emerald-400" />
            <span>Import</span>
          </button>

          <button
            type="button"
            disabled={isSyncing}
            onClick={handleTwoWaySync}
            title="Two-way bidirectional synchronization with conflict resolution"
            className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-purple-600/20 hover:bg-purple-600/30 text-purple-200 active:scale-95 disabled:opacity-50 transition-all font-medium border border-purple-500/40"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-purple-400 ${isSyncing ? 'animate-spin' : ''}`} />
            <span>{isSyncing ? 'Syncing...' : 'Sync'}</span>
          </button>
        </div>

        {/* Settings Toggle Button */}
        <div className="pl-1 border-l border-[#262835]">
          <button
            type="button"
            onClick={() => setShowSettings(!showSettings)}
            title="Obsidian Sync Vault Configuration"
            className={`p-1.5 rounded-md transition-all ${
              showSettings 
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40' 
                : 'text-neutral-400 hover:text-neutral-200 hover:bg-[#20222e]'
            }`}
          >
            <Settings2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Expandable Settings Flyout */}
      {showSettings && (
        <div className="absolute top-full mt-2 w-80 p-3 rounded-xl bg-[#14151a]/95 backdrop-blur-md border border-[#2a2b36] shadow-2xl text-xs space-y-3">
          <div className="flex items-center justify-between pb-1.5 border-b border-[#262835]">
            <span className="font-medium text-white flex items-center gap-1.5">
              <Settings2 className="w-3.5 h-3.5 text-purple-400" />
              Obsidian Vault Settings
            </span>
            <button 
              type="button"
              onClick={() => setShowSettings(false)}
              className="text-neutral-400 hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] text-neutral-400 font-medium">Vault Target Directory</label>
            <input
              type="text"
              value={vaultPath}
              onChange={(e) => setVaultPath(e.target.value)}
              placeholder="./docs/notes"
              className="w-full px-2 py-1 rounded bg-[#1b1c24] border border-[#2f3140] text-neutral-200 text-[11px] focus:outline-none focus:border-purple-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] text-neutral-400 font-medium">Canvas File Name</label>
            <input
              type="text"
              value={canvasName}
              onChange={(e) => setCanvasName(e.target.value)}
              placeholder="canvas_default"
              className="w-full px-2 py-1 rounded bg-[#1b1c24] border border-[#2f3140] text-neutral-200 text-[11px] focus:outline-none focus:border-purple-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] text-neutral-400 font-medium">Conflict Resolution</label>
            <select
              value={conflictStrategy}
              onChange={(e) => setConflictStrategy(e.target.value as any)}
              className="w-full px-2 py-1 rounded bg-[#1b1c24] border border-[#2f3140] text-neutral-200 text-[11px] focus:outline-none focus:border-purple-500"
            >
              <option value="last-write-wins">Last Write Wins (Timestamp based)</option>
              <option value="merge-tags">Merge Tags & Keep Canvas Geometry</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
};

export default ObsidianSyncBar;
