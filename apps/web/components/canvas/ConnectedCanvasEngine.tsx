// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/canvas/ConnectedCanvasEngine.tsx"
// purpose: "Store-Connected React Flow Spatial Canvas Engine with JSON Canvas (.canvas) Export/Import, Undo/Redo, and 6-Card Fast Palette"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useRef, useEffect } from 'react';
import CanvasEngine from './CanvasEngine';
import { useCanvasStore } from '../../store/canvasStore';
import { 
  Undo2, 
  Redo2, 
  Download, 
  Upload, 
  Plus, 
  Sparkles,
  Layers,
  FileCode,
  Layout,
  Trello,
  Search,
  BookOpen
} from 'lucide-react';

export default function ConnectedCanvasEngine() {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    setEdges,
    selectNode,
    addNode,
    undo,
    redo,
    exportJSONCanvas,
    importJSONCanvas,
  } = useCanvasStore();

  // Keyboard Shortcuts: Cmd+Z, Cmd+Shift+Z
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
        if (e.shiftKey) {
          redo();
        } else {
          undo();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [undo, redo]);

  const handleExport = () => {
    const doc = exportJSONCanvas();
    const jsonStr = JSON.stringify(doc, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `spatial-workspace-${Date.now()}.canvas`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = event.target?.result as string;
        const parsed = JSON.parse(content);
        importJSONCanvas(parsed);
      } catch (err) {
        console.error('Failed to parse JSON Canvas file:', err);
      }
    };
    reader.readAsText(file);
    // Reset input so re-selecting same file works
    e.target.value = '';
  };

  const spawnCard = (type: string, title: string) => {
    // Generate scattered position in visible viewport center
    const x = 200 + Math.random() * 200;
    const y = 150 + Math.random() * 150;
    addNode(type, { x, y }, { title });
  };

  return (
    <div className="relative w-full h-full min-h-[600px] overflow-hidden bg-[#0a0d14]">
      {/* Top Floating Action Ribbon */}
      <div className="absolute top-4 left-6 z-30 flex items-center gap-2 p-1.5 rounded-2xl bg-[#121620]/90 backdrop-blur-xl border border-[#232938] shadow-2xl">
        {/* Quick Add Menu */}
        <div className="flex items-center gap-1 border-r border-[#232938] pr-2">
          <button
            onClick={() => spawnCard('StrategyMarkdownNode', 'Strategy Plan')}
            className="px-2.5 py-1.5 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/25 border border-indigo-500/30 text-indigo-300 text-xs font-medium flex items-center gap-1.5 transition-all"
            title="Add Strategy Card"
          >
            <BookOpen className="w-3.5 h-3.5" />
            Strategy
          </button>
          <button
            onClick={() => spawnCard('MarketResearchNode', 'Market Analysis')}
            className="px-2.5 py-1.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 text-xs font-medium flex items-center gap-1.5 transition-all"
            title="Add Research Card"
          >
            <Search className="w-3.5 h-3.5" />
            Research
          </button>
          <button
            onClick={() => spawnCard('ConceptMindmapNode', 'Brainstorm Map')}
            className="px-2.5 py-1.5 rounded-xl bg-purple-500/10 hover:bg-purple-500/25 border border-purple-500/30 text-purple-300 text-xs font-medium flex items-center gap-1.5 transition-all"
            title="Add Mindmap Card"
          >
            <Layers className="w-3.5 h-3.5" />
            Mindmap
          </button>
          <button
            onClick={() => spawnCard('DesignGalleryNode', 'Brand Assets')}
            className="px-2.5 py-1.5 rounded-xl bg-pink-500/10 hover:bg-pink-500/25 border border-pink-500/30 text-pink-300 text-xs font-medium flex items-center gap-1.5 transition-all"
            title="Add Design Card"
          >
            <Layout className="w-3.5 h-3.5" />
            Design
          </button>
          <button
            onClick={() => spawnCard('SprintKanbanNode', 'Sprint Execution')}
            className="px-2.5 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 text-xs font-medium flex items-center gap-1.5 transition-all"
            title="Add Kanban Card"
          >
            <Trello className="w-3.5 h-3.5" />
            Kanban
          </button>
          <button
            onClick={() => spawnCard('ApiDocsCodeNode', 'Code / API Specs')}
            className="px-2.5 py-1.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/25 border border-cyan-500/30 text-cyan-300 text-xs font-medium flex items-center gap-1.5 transition-all"
            title="Add Code Card"
          >
            <FileCode className="w-3.5 h-3.5" />
            Code
          </button>
        </div>

        {/* History Controls */}
        <div className="flex items-center gap-1 border-r border-[#232938] pr-2">
          <button
            onClick={undo}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title="Undo (Cmd+Z)"
          >
            <Undo2 className="w-4 h-4" />
          </button>
          <button
            onClick={redo}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title="Redo (Cmd+Shift+Z)"
          >
            <Redo2 className="w-4 h-4" />
          </button>
        </div>

        {/* JSON Canvas I/O */}
        <div className="flex items-center gap-1">
          <button
            onClick={handleExport}
            className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-slate-800 transition-colors"
            title="Export standard .canvas (JSON Canvas)"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition-colors"
            title="Import .canvas file"
          >
            <Upload className="w-4 h-4" />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".canvas,.json"
            onChange={handleImport}
            className="hidden"
          />
        </div>
      </div>

      {/* Underlaying Canvas Engine */}
      <CanvasEngine />
    </div>
  );
}
