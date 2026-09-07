// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_workspace_CapCutTopBar"
// purpose: "Authentic CapCut-styled Top Navigation Bar with Document Title Dropdown, Creation Quick Tools (Add Text, Create Note, Connection Tool, Upload), Zoom Selector, Live Users Presence, Share Pill, and Feedback triggers"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { 
  ChevronDown, 
  Type, 
  FileText, 
  Link2, 
  Upload, 
  Grid3X3, 
  Share2, 
  MessageSquare,
  Home,
  Undo2,
  Redo2,
  Play,
  Sparkles,
  MousePointer,
  Hand
} from 'lucide-react';

interface CapCutTopBarProps {
  documentTitle?: string;
  onSelectDocumentTitle?: (title: string) => void;
  zoomLevel?: number;
  onZoomChange?: (zoom: number) => void;
  onAddText?: () => void;
  onCreateNote?: () => void;
  onAddConnection?: () => void;
  onUpload?: () => void;
  onToggleGrid?: () => void;
  onShare?: () => void;
  onFeedback?: () => void;
  onOpenSettings?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  canUndo?: boolean;
  canRedo?: boolean;
  onExportCanvas?: () => void;
  onImportCanvas?: () => void;
}

export default function CapCutTopBar({
  documentTitle = 'Product Roadmap',
  onSelectDocumentTitle,
  zoomLevel = 85,
  onZoomChange,
  onAddText,
  onCreateNote,
  onAddConnection,
  onUpload,
  onToggleGrid,
  onShare,
  onFeedback,
  onUndo,
  onRedo,
  canUndo = true,
  canRedo = true,
  onExportCanvas,
  onImportCanvas
}: CapCutTopBarProps) {
  return (
    <header className="h-14 bg-[#0d1017] border-b border-[#1a1f2c] px-4 flex items-center justify-between z-20 shrink-0 font-sans text-slate-200 select-none">
      {/* Left: Document Title Selector & Quick History Controls */}
      <div className="flex items-center gap-4">
        {/* Document Title Dropdown */}
        <button
          className="flex items-center gap-1.5 text-sm font-bold text-white hover:text-indigo-400 transition-colors cursor-pointer group"
          title="Switch Active Document Roadmap"
        >
          <span>{documentTitle}</span>
          <ChevronDown className="w-4 h-4 text-slate-400 group-hover:text-indigo-400 transition-transform group-hover:translate-y-0.5" />
        </button>

        <div className="h-4 w-px bg-[#1a1f2c]" />

        {/* History / Mode Controls (Home, Undo, Redo, Pointer, Pan) */}
        <div className="flex items-center gap-1 bg-[#161b26] p-1 rounded-xl border border-[#232938]">
          <button className="p-1.5 rounded-lg hover:bg-[#232938] text-slate-400 hover:text-white transition-colors cursor-pointer" title="Home View">
            <Home className="w-3.5 h-3.5" />
          </button>
          <button 
            onClick={onUndo}
            disabled={!canUndo}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              canUndo ? 'hover:bg-[#232938] text-slate-400 hover:text-white' : 'text-slate-600 cursor-not-allowed opacity-50'
            }`} 
            title="Undo (⌘Z)"
          >
            <Undo2 className="w-3.5 h-3.5" />
          </button>
          <button 
            onClick={onRedo}
            disabled={!canRedo}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              canRedo ? 'hover:bg-[#232938] text-slate-400 hover:text-white' : 'text-slate-600 cursor-not-allowed opacity-50'
            }`} 
            title="Redo (⌘⇧Z)"
          >
            <Redo2 className="w-3.5 h-3.5" />
          </button>
          <div className="h-3 w-px bg-[#232938] mx-0.5" />
          <button className="p-1.5 rounded-lg bg-[#232938] text-indigo-400 font-bold transition-colors cursor-pointer" title="Select Tool">
            <MousePointer className="w-3.5 h-3.5" />
          </button>
          <button className="p-1.5 rounded-lg hover:bg-[#232938] text-slate-400 hover:text-white transition-colors cursor-pointer" title="Hand / Pan Tool">
            <Hand className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Center: Creation Quick Tools Pill Island */}
      <div className="flex items-center gap-1.5 bg-[#161b26] border border-[#232938] rounded-2xl p-1 shadow-lg shadow-black/40">
        <button
          onClick={onAddText}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-[#232938] text-slate-300 hover:text-white text-xs font-medium transition-all active:scale-95 cursor-pointer"
        >
          <Type className="w-3.5 h-3.5 text-indigo-400" />
          <span>Add Text</span>
        </button>

        <button
          onClick={onCreateNote}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-950/80 border border-indigo-500/30 text-indigo-300 text-xs font-medium hover:bg-indigo-900/60 transition-all active:scale-95 cursor-pointer"
        >
          <FileText className="w-3.5 h-3.5 text-indigo-400" />
          <span>Create Note</span>
        </button>

        <button
          onClick={onAddConnection}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-[#232938] text-slate-300 hover:text-white text-xs font-medium transition-all active:scale-95 cursor-pointer"
        >
          <Link2 className="w-3.5 h-3.5 text-cyan-400" />
          <span>Connection Tool</span>
        </button>

        <button
          onClick={onUpload}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl hover:bg-[#232938] text-slate-300 hover:text-white text-xs font-medium transition-all active:scale-95 cursor-pointer"
        >
          <Upload className="w-3.5 h-3.5 text-emerald-400" />
          <span>Upload</span>
        </button>
      </div>

      {/* Right: Zoom, Grid, Live Presence Avatars, Share & Feedback */}
      <div className="flex items-center gap-3">
        {/* Zoom Selector */}
        <button
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-[#161b26] border border-[#232938] text-xs font-mono text-slate-300 hover:border-slate-600 transition-colors cursor-pointer"
          title="Canvas Zoom Level"
        >
          <span>Zoom: {zoomLevel}%</span>
          <ChevronDown className="w-3 h-3 text-slate-400" />
        </button>

        {/* Grid Toggle */}
        <button
          onClick={onToggleGrid}
          className="p-2 rounded-xl bg-[#161b26] border border-[#232938] text-slate-300 hover:text-white hover:border-slate-600 transition-colors cursor-pointer"
          title="Toggle Grid Display"
        >
          <Grid3X3 className="w-3.5 h-3.5 text-slate-400" />
        </button>

        <div className="h-4 w-px bg-[#1a1f2c]" />

        {/* Live Users Presence Pill */}
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] text-slate-400 font-medium hidden lg:inline">Live Users:</span>
          <div className="flex items-center -space-x-1.5">
            <div className="w-6 h-6 rounded-full bg-emerald-500 text-white font-bold text-[10px] flex items-center justify-center ring-2 ring-[#0d1017]" title="Alex K.">
              AK
            </div>
            <div className="w-6 h-6 rounded-full bg-pink-500 text-white font-bold text-[10px] flex items-center justify-center ring-2 ring-[#0d1017]" title="Maya R.">
              MR
            </div>
            <div className="w-6 h-6 rounded-full bg-cyan-500 text-white font-bold text-[10px] flex items-center justify-center ring-2 ring-[#0d1017]" title="David S.">
              DS
            </div>
          </div>
        </div>

        {/* Share Button (Pill Action) */}
        <button
          onClick={onShare}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-400 hover:to-blue-500 text-white text-xs font-bold shadow-md shadow-indigo-500/20 active:scale-95 transition-all cursor-pointer"
        >
          <Share2 className="w-3.5 h-3.5" />
          <span>Share</span>
        </button>

        {/* Feedback Button */}
        <button
          onClick={onFeedback}
          className="px-3 py-1.5 rounded-full bg-[#161b26] border border-[#232938] hover:bg-[#232938] text-slate-300 hover:text-white text-xs font-medium transition-colors cursor-pointer"
        >
          <span>Feedback</span>
        </button>
      </div>
    </header>
  );
}
