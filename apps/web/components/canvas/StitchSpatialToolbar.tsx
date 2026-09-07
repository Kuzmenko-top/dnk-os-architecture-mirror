// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_StitchSpatialToolbar"
// purpose: "Right floating spatial toolbar matching Google Stitch UI with DNK Highlights and Mind Map quick spawn"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.1.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { 
  MousePointer, 
  Square, 
  Pencil, 
  Hand, 
  Image as ImageIcon, 
  Smile, 
  Star,
  Lightbulb,
  Target,
  CheckSquare,
  Bot,
  Paperclip,
  Sparkles,
  Loader2,
  Boxes
} from 'lucide-react';
import { useCanvasStore } from '@/store/canvasStore';

interface StitchSpatialToolbarProps {
  activeTool?: string;
  onSelectTool?: (tool: string) => void;
  onAutoCluster?: () => void;
}

export default function StitchSpatialToolbar({
  activeTool = 'select',
  onSelectTool,
  onAutoCluster
}: StitchSpatialToolbarProps) {
  const [currentTool, setCurrentTool] = useState(activeTool);
  const addNode = useCanvasStore((state) => state.addNode);
  const autoClusterMindMap = useCanvasStore((state) => state.autoClusterMindMap);
  const isClustering = useCanvasStore((state) => state.isClustering);

  const handleAutoCluster = async () => {
    if (onAutoCluster) {
      onAutoCluster();
    } else if (typeof autoClusterMindMap === 'function') {
      await autoClusterMindMap({ language: 'uk' });
    }
  };

  const tools = [
    { id: 'select', icon: MousePointer, label: 'Select / Pointer (V)' },
    { id: 'frame', icon: Square, label: 'Frame / Bounding Box (F)' },
    { id: 'draw', icon: Pencil, label: 'Pencil / Draw (P)' },
    { id: 'hand', icon: Hand, label: 'Pan Tool (H)' },
    { id: 'media', icon: ImageIcon, label: 'Image Import (M)' },
    { id: 'sticker', icon: Smile, label: 'Sticker / Emoji (E)' },
    { id: 'star', icon: Star, label: 'Bookmark / Templates (S)' },
  ];

  const mindMapNodes = [
    {
      id: 'mindmap-idea',
      nodeType: 'MindMapIdeaNode',
      icon: Lightbulb,
      label: '💡 Ідея',
      sublabel: 'Idea Node',
      accentColor: 'hover:text-amber-400 hover:border-amber-500/40',
      activeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/50',
      defaultData: {
        title: 'Нова Ідея',
        description: 'Опишіть гіпотезу або інсайт...',
        tags: ['#ideation'],
        confidence_score: 4,
      },
    },
    {
      id: 'mindmap-goal',
      nodeType: 'MindMapGoalNode',
      icon: Target,
      label: '🎯 Ціль',
      sublabel: 'Goal Node',
      accentColor: 'hover:text-emerald-400 hover:border-emerald-500/40',
      activeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50',
      defaultData: {
        title: 'Стратегічна Ціль',
        target_date: '2026-12-31',
        progress: 0,
        metrics: ['Основна метрика'],
      },
    },
    {
      id: 'mindmap-task',
      nodeType: 'MindMapTaskNode',
      icon: CheckSquare,
      label: '✅ Задача',
      sublabel: 'Task Node',
      accentColor: 'hover:text-blue-400 hover:border-blue-500/40',
      activeColor: 'bg-blue-500/20 text-blue-300 border-blue-500/50',
      defaultData: {
        title: 'Виконавча Задача',
        task_status: 'todo',
        priority: 'medium',
        assignee: 'Unassigned',
      },
    },
    {
      id: 'mindmap-agent',
      nodeType: 'MindMapAgentNode',
      icon: Bot,
      label: '🤖 Агент',
      sublabel: 'Agent Node',
      accentColor: 'hover:text-orange-400 hover:border-orange-500/40',
      activeColor: 'bg-orange-500/20 text-orange-300 border-orange-500/50',
      defaultData: {
        title: 'Gerych Subagent',
        agent_type: 'gerych_builder',
        status: 'idle',
      },
    },
    {
      id: 'mindmap-evidence',
      nodeType: 'MindMapEvidenceNode',
      icon: Paperclip,
      label: '📎 Артефакт',
      sublabel: 'Artifact Node',
      accentColor: 'hover:text-purple-400 hover:border-purple-500/40',
      activeColor: 'bg-purple-500/20 text-purple-300 border-purple-500/50',
      defaultData: {
        title: 'Артефакт / Документ',
        evidence_type: 'doc',
        target_uri: 'docs/architecture',
        source_name: 'DNK Docs',
      },
    },
  ];

  const handleToolClick = (toolId: string) => {
    setCurrentTool(toolId);
    onSelectTool?.(toolId);
  };

  const handleSpawnMindMap = (item: (typeof mindMapNodes)[0]) => {
    setCurrentTool(item.id);
    onSelectTool?.(item.id);

    if (typeof addNode === 'function') {
      const offset = Math.floor(Math.random() * 80) - 40;
      addNode(
        item.nodeType,
        { x: 350 + offset, y: 250 + offset },
        item.defaultData
      );
    }
  };

  return (
    <aside className="absolute right-4 top-1/2 -translate-y-1/2 bg-[#1c1d22]/95 backdrop-blur-2xl border border-white/10 rounded-2xl p-1.5 shadow-2xl flex flex-col gap-1.5 z-30 pointer-events-auto">
      {/* Primary Stitch Tools */}
      <div className="flex flex-col gap-1">
        {tools.map((tool) => {
          const Icon = tool.icon;
          const isActive = currentTool === tool.id;
          return (
            <button
              key={tool.id}
              onClick={() => handleToolClick(tool.id)}
              title={tool.label}
              className={`p-2 rounded-xl transition-all relative group cursor-pointer ${
                isActive
                  ? 'bg-white text-black shadow-lg rounded-xl font-bold'
                  : 'text-neutral-400 hover:text-white hover:bg-white/10'
              }`}
            >
              <Icon className="w-4 h-4" />
              {/* Tooltip */}
              <span className="absolute right-full mr-2.5 top-1/2 -translate-y-1/2 px-2.5 py-1 rounded-lg bg-neutral-900 text-neutral-200 text-[10px] font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none border border-neutral-800 shadow-xl">
                {tool.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* Mind Map Subgroup */}
      <div className="flex flex-col gap-1 pt-1.5 border-t border-white/10">
        <div className="text-[9px] uppercase tracking-wider text-neutral-500 font-semibold px-1 text-center select-none">
          Mind
        </div>
        {mindMapNodes.map((item) => {
          const Icon = item.icon;
          const isActive = currentTool === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleSpawnMindMap(item)}
              title={item.label}
              aria-label={item.label}
              data-testid={`spawn-${item.id}`}
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData('application/reactflow', item.nodeType);
                e.dataTransfer.setData(
                  'application/reactflow-data',
                  JSON.stringify(item.defaultData)
                );
                e.dataTransfer.effectAllowed = 'move';
              }}
              className={`p-2 rounded-xl transition-all relative group cursor-pointer border border-transparent ${
                isActive
                  ? item.activeColor
                  : `text-neutral-400 hover:bg-white/10 ${item.accentColor}`
              }`}
            >
              <Icon className="w-4 h-4" />
              {/* Tooltip */}
              <span className="absolute right-full mr-2.5 top-1/2 -translate-y-1/2 px-2.5 py-1 rounded-lg bg-neutral-900 text-neutral-200 text-[10px] font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none border border-neutral-800 shadow-xl z-50 flex items-center gap-1.5">
                <span>{item.label}</span>
                <span className="text-[9px] text-neutral-500 font-normal">
                  ({item.sublabel})
                </span>
              </span>
            </button>
          );
        })}

        {/* AI Auto-Clusterization Action Button */}
        <div className="pt-1 mt-1 border-t border-white/10">
          <button
            onClick={handleAutoCluster}
            disabled={isClustering}
            title="AI Auto-Clusterize Mind Map (LLM + Spatial Layout)"
            aria-label="AI Auto-Cluster"
            data-testid="btn-auto-cluster"
            className={`w-full p-2 rounded-xl transition-all relative group cursor-pointer border ${
              isClustering
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/50 cursor-wait'
                : 'text-amber-400 hover:text-amber-300 hover:bg-amber-500/10 border-amber-500/30'
            }`}
          >
            {isClustering ? (
              <Loader2 className="w-4 h-4 animate-spin mx-auto text-amber-400" />
            ) : (
              <Sparkles className="w-4 h-4 mx-auto" />
            )}
            {/* Tooltip */}
            <span className="absolute right-full mr-2.5 top-1/2 -translate-y-1/2 px-2.5 py-1 rounded-lg bg-neutral-900 text-neutral-200 text-[10px] font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none border border-neutral-800 shadow-xl z-50 flex items-center gap-1.5">
              <span>{isClustering ? 'Кластеризація...' : '✨ AI Кластеризація'}</span>
              <span className="text-[9px] text-amber-400 font-mono font-normal">Auto-Layout</span>
            </span>
          </button>
        </div>
      </div>
    </aside>
  );
}

