// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_workspace_StudioDock"
// purpose: "Bottom Studio Dock for Note-Based Canvas (Task 3) supporting fast living document & task note insertion in authentic Shopify Design System"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "4.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { 
  FileText, 
  Dna, 
  ShoppingBag, 
  Film, 
  Sparkles, 
  Plus, 
  Bot, 
  Database,
  Layers,
  Camera,
  TrendingUp,
  GitBranch,
  CheckSquare,
  Palette,
  Code2,
  Globe,
  ChevronUp,
  Pencil
} from 'lucide-react';

export type SpawnNodeType = 
  | 'note' 
  | 'taskdna' 
  | 'shopify_spec' 
  | 'video_script' 
  | 'photo_studio' 
  | 'swarm'
  | 'strategy'
  | 'market_research'
  | 'mindmap'
  | 'kanban'
  | 'design_gallery'
  | 'api_code'
  | 'live_preview';

interface StudioDockProps {
  activeModule?: string;
  onSelectModule?: (module: string) => void;
  onOpenCommandBar?: () => void;
  onSpawnNode?: (type: SpawnNodeType) => void;
  isWhiteboardActive?: boolean;
  onToggleWhiteboard?: () => void;
}

export default function StudioDock({
  activeModule,
  onSelectModule,
  onOpenCommandBar,
  onSpawnNode,
  isWhiteboardActive,
  onToggleWhiteboard
}: StudioDockProps) {
  const [showAllNodes, setShowAllNodes] = React.useState(false);

  const primarySpawnActions = [
    { type: 'strategy' as SpawnNodeType, label: 'Strategy', icon: FileText, color: 'text-indigo-400' },
    { type: 'photo_studio' as SpawnNodeType, label: 'Photos', icon: Camera, color: 'text-[#36f4a4]' },
    { type: 'video_script' as SpawnNodeType, label: '9:16 Video', icon: Film, color: 'text-[#c1fbd4]' },
    { type: 'shopify_spec' as SpawnNodeType, label: 'Shopify', icon: ShoppingBag, color: 'text-emerald-400' },
    { type: 'kanban' as SpawnNodeType, label: 'Sprint', icon: CheckSquare, color: 'text-amber-400' },
    { type: 'swarm' as SpawnNodeType, label: 'Swarm Agent', icon: Bot, color: 'text-purple-400' },
  ];

  const extendedSpawnActions = [
    { type: 'market_research' as SpawnNodeType, label: 'Market Research', icon: TrendingUp, color: 'text-blue-400' },
    { type: 'mindmap' as SpawnNodeType, label: 'Concept Mindmap', icon: GitBranch, color: 'text-pink-400' },
    { type: 'design_gallery' as SpawnNodeType, label: 'Design Gallery', icon: Palette, color: 'text-rose-400' },
    { type: 'api_code' as SpawnNodeType, label: 'API & Code', icon: Code2, color: 'text-teal-400' },
    { type: 'taskdna' as SpawnNodeType, label: 'TaskDNA DAG', icon: Dna, color: 'text-lime-400' },
    { type: 'live_preview' as SpawnNodeType, label: 'Live Web Preview', icon: Globe, color: 'text-cyan-400' },
    { type: 'note' as SpawnNodeType, label: 'Note Document', icon: FileText, color: 'text-slate-300' },
  ];

  const modules = [
    { id: 'photos', label: 'Photo Studio', icon: Camera, color: 'text-[#36f4a4]' },
    { id: 'video', label: 'Video Studio', icon: Film, color: 'text-[#c1fbd4]' },
    { id: 'shopify', label: 'Shopify Store', icon: ShoppingBag, color: 'text-[#36f4a4]' },
    { id: 'tasks', label: 'TaskDNA Trees', icon: Dna, color: 'text-[#36f4a4]' },
    { id: 'vault', label: 'SCONES Memory', icon: Database, color: 'text-slate-300' },
  ];

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-[#02090a]/95 backdrop-blur-2xl border border-[#1e2c31] rounded-full p-1.5 shadow-[0_16px_50px_rgba(0,0,0,0.95)] flex items-center gap-1.5 z-30 pointer-events-auto select-none">
      {/* Primary Action: Compose Pill */}
      <button
        onClick={onOpenCommandBar}
        className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#36f4a4] hover:bg-[#2de097] text-black font-bold text-xs transition-all shadow-md shadow-[#36f4a4]/20 active:scale-95 cursor-pointer mr-1"
        title="Open Command Palette (⌘K)"
      >
        <Sparkles className="w-3.5 h-3.5 stroke-[2.5]" />
        <span>Compose (⌘K)</span>
      </button>

      <div className="h-5 w-px bg-[#1e2c31]" />

      {/* Note Spawners (Full Pill Rounded) */}
      <div className="flex items-center gap-1 px-1">
        {primarySpawnActions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.type}
              onClick={() => onSpawnNode?.(action.type)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-[#1e2c31] bg-[#061a1c]/80 text-xs font-medium transition-all active:scale-95 cursor-pointer text-slate-200 hover:border-[#36f4a4]/60 hover:bg-[#102620]"
              title={`Spawn new ${action.label} on Canvas`}
            >
              <Plus className="w-3 h-3 text-[#36f4a4]" />
              <Icon className={`w-3.5 h-3.5 ${action.color}`} />
              <span className="font-semibold">{action.label}</span>
            </button>
          );
        })}

        {/* More Nodes Toggle */}
        <div className="relative">
          <button
            onClick={() => setShowAllNodes(!showAllNodes)}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-full border border-[#1e2c31] bg-[#061a1c]/80 text-xs font-medium transition-all text-slate-300 hover:text-white hover:border-[#36f4a4]/60 cursor-pointer"
            title="More Node Types"
          >
            <span>More</span>
            <ChevronUp className={`w-3 h-3 transition-transform ${showAllNodes ? 'rotate-180' : ''}`} />
          </button>

          {showAllNodes && (
            <div className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 bg-[#061a1c]/95 backdrop-blur-2xl border border-[#1e2c31] rounded-2xl p-2 shadow-2xl flex flex-col gap-1 min-w-[190px] z-50">
              <div className="text-[10px] uppercase font-bold text-slate-400 px-2 py-1 tracking-wider border-b border-[#1e2c31]">
                Extended Node Types
              </div>
              {extendedSpawnActions.map((action) => {
                const Icon = action.icon;
                return (
                  <button
                    key={action.type}
                    onClick={() => {
                      onSpawnNode?.(action.type);
                      setShowAllNodes(false);
                    }}
                    className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl text-xs font-medium text-slate-200 hover:bg-[#102620] hover:text-[#36f4a4] transition-colors cursor-pointer text-left"
                  >
                    <Icon className={`w-3.5 h-3.5 ${action.color}`} />
                    <span>{action.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <div className="h-5 w-px bg-[#1e2c31]" />

      {/* Quick View Switches */}
      <div className="flex items-center gap-1">
        {modules.map((m) => {
          const Icon = m.icon;
          const isActive = activeModule === m.id;
          return (
            <button
              key={m.id}
              onClick={() => onSelectModule?.(m.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                isActive
                  ? 'bg-[#36f4a4]/15 text-[#36f4a4] border border-[#36f4a4]/50 font-semibold shadow-sm'
                  : 'text-slate-400 hover:bg-[#061a1c] hover:text-white'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${m.color}`} />
              <span className="hidden md:inline">{m.label}</span>
            </button>
          );
        })}
      </div>

      <div className="h-5 w-px bg-[#1e2c31]" />

      {/* Whiteboard Sketch Overlay Toggle */}
      <button
        onClick={onToggleWhiteboard}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${
          isWhiteboardActive
            ? 'bg-amber-400/20 text-amber-300 border border-amber-400/60 shadow-[0_0_12px_rgba(251,191,36,0.25)]'
            : 'text-slate-400 hover:bg-[#061a1c] hover:text-white border border-transparent'
        }`}
        title="Toggle Sketch Layer (W)"
      >
        <Pencil className="w-3.5 h-3.5 text-amber-400" />
        <span className="hidden sm:inline">Sketch</span>
        <span className="text-[9px] bg-white/10 px-1 py-0.2 rounded font-mono text-slate-300">W</span>
      </button>
    </div>
  );
}
