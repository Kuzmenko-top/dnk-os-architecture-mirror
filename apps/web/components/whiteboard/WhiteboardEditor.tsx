'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  MousePointer,
  Pencil,
  Square,
  Circle,
  ArrowUpRight,
  StickyNote,
  Type,
  Eraser,
  Download,
  Share2,
  Sparkles,
  Layers,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Bot,
  ShoppingBag,
  FolderTree,
  Code
} from 'lucide-react';
import { ShopifyCanvasSyncBar } from '../canvas/ShopifyCanvasSyncBar';
import { ShopifyThemeAssetTree } from '../shopify/ShopifyThemeAssetTree';
import { ShopifySectionEditor } from '../shopify/ShopifySectionEditor';
import {
  shopifyCanvasApi,
  ShopifyCanvasGraph,
  ThemeAssetTree,
  ThemeAsset
} from '../../lib/api/shopify_canvas_client';

export type ToolType = 'select' | 'pencil' | 'rect' | 'ellipse' | 'arrow' | 'note' | 'text' | 'eraser';

interface WhiteboardElement {
  id: string;
  type: ToolType;
  x: number;
  y: number;
  width?: number;
  height?: number;
  points?: { x: number; y: number }[];
  color: string;
  fill?: string;
  content?: string;
  author: string;
}

export default function WhiteboardEditor() {
  const [activeTool, setActiveTool] = useState<ToolType>('pencil');
  const [activeColor, setActiveColor] = useState<string>('#6366f1');
  const [elements, setElements] = useState<WhiteboardElement[]>([
    {
      id: 'init-note-1',
      type: 'note',
      x: 120,
      y: 100,
      width: 220,
      height: 160,
      color: '#4f46e5',
      content: '🧠 SOTA Whiteboard\nAssimilated from tldraw\n\n- Freehand canvas\n- Agent moodboards',
      author: 'gerych_researcher',
    },
    {
      id: 'init-note-2',
      type: 'note',
      x: 380,
      y: 100,
      width: 220,
      height: 160,
      color: '#059669',
      content: '🚀 Product Launch Reel\n- 9:16 Vertical\n- Spring Animations\n- High CTR Hooks',
      author: 'dnk_marketing_cmo',
    },
  ]);

  const [isDrawing, setIsDrawing] = useState(false);
  const [currentPath, setCurrentPath] = useState<{ x: number; y: number }[]>([]);
  const [zoom, setZoom] = useState(1);
  const [syncStatus, setSyncStatus] = useState<'synced' | 'syncing'>('synced');
  const svgRef = useRef<SVGSVGElement>(null);

  // Shopify Theme Live Sync State
  const [shopifyTree, setShopifyTree] = useState<ThemeAssetTree | null>(null);
  const [shopifyGraph, setShopifyGraph] = useState<ShopifyCanvasGraph | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<ThemeAsset | null>(null);
  const [assetContent, setAssetContent] = useState<string>('');
  const [isShopifyDrawerOpen, setIsShopifyDrawerOpen] = useState(false);
  const [isSyncingShopify, setIsSyncingShopify] = useState(false);

  useEffect(() => {
    // Initial fetch of Shopify theme tree & graph
    const loadShopifyData = async () => {
      const [treeRes, graphRes] = await Promise.all([
        shopifyCanvasApi.getThemeAssetTree(),
        shopifyCanvasApi.getCanvasGraph()
      ]);
      if (treeRes.data) setShopifyTree(treeRes.data);
      if (graphRes.data) setShopifyGraph(graphRes.data);
    };
    loadShopifyData();
  }, []);

  const handleSelectAsset = async (asset: ThemeAsset) => {
    setSelectedAsset(asset);
    const contentRes = await shopifyCanvasApi.getAssetContent('dnk-e-com.myshopify.com', '160000001', asset.key);
    if (contentRes.data?.value) {
      setAssetContent(contentRes.data.value);
    }
  };

  const handleSyncShopifyToWhiteboard = (graph: ShopifyCanvasGraph) => {
    setIsSyncingShopify(true);
    const newElements: WhiteboardElement[] = graph.nodes.map((node) => {
      const colorMap: Record<string, string> = {
        layout: '#6366f1',
        templates: '#06b6d4',
        sections: '#10b981',
        snippets: '#f59e0b',
      };

      return {
        id: `shopify-${node.id}`,
        type: 'note',
        x: node.position_x,
        y: node.position_y,
        width: 240,
        height: 140,
        color: colorMap[node.category] || '#6366f1',
        content: `🧩 [${node.category.toUpperCase()}]\n${node.label}\n\n• Settings: ${node.settings_count}\n• Dependencies: ${node.snippet_dependencies.join(', ') || 'None'}`,
        author: 'shopify_theme_sync',
      };
    });

    setElements((prev) => [...prev.filter((e) => !e.id.startsWith('shopify-')), ...newElements]);
    triggerSync();
    setTimeout(() => {
      setIsSyncingShopify(false);
    }, 400);
  };

  const colors = [
    '#6366f1', // Indigo
    '#06b6d4', // Cyan
    '#10b981', // Emerald
    '#f59e0b', // Amber
    '#ef4444', // Rose
    '#ec4899', // Pink
    '#f8fafc', // White
  ];

  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    if (activeTool === 'select') return;
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = (e.clientX - rect.left) / zoom;
    const y = (e.clientY - rect.top) / zoom;

    if (activeTool === 'pencil') {
      setIsDrawing(true);
      setCurrentPath([{ x, y }]);
    } else if (activeTool === 'note') {
      const newNote: WhiteboardElement = {
        id: `note-${Date.now()}`,
        type: 'note',
        x,
        y,
        width: 200,
        height: 140,
        color: activeColor,
        content: 'New Idea...',
        author: 'Maksym',
      };
      setElements((prev) => [...prev, newNote]);
      triggerSync();
    } else if (activeTool === 'rect') {
      const newRect: WhiteboardElement = {
        id: `rect-${Date.now()}`,
        type: 'rect',
        x,
        y,
        width: 180,
        height: 120,
        color: activeColor,
        author: 'Maksym',
      };
      setElements((prev) => [...prev, newRect]);
      triggerSync();
    } else if (activeTool === 'ellipse') {
      const newEllipse: WhiteboardElement = {
        id: `ellipse-${Date.now()}`,
        type: 'ellipse',
        x,
        y,
        width: 160,
        height: 120,
        color: activeColor,
        author: 'Maksym',
      };
      setElements((prev) => [...prev, newEllipse]);
      triggerSync();
    }
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!isDrawing || activeTool !== 'pencil') return;
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = (e.clientX - rect.left) / zoom;
    const y = (e.clientY - rect.top) / zoom;
    setCurrentPath((prev) => [...prev, { x, y }]);
  };

  const handleMouseUp = () => {
    if (isDrawing && activeTool === 'pencil' && currentPath.length > 1) {
      const newElement: WhiteboardElement = {
        id: `path-${Date.now()}`,
        type: 'pencil',
        x: currentPath[0].x,
        y: currentPath[0].y,
        points: currentPath,
        color: activeColor,
        author: 'Maksym',
      };
      setElements((prev) => [...prev, newElement]);
      triggerSync();
    }
    setIsDrawing(false);
    setCurrentPath([]);
  };

  const triggerSync = async () => {
    setSyncStatus('syncing');
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem('dnk_whiteboard_elements', JSON.stringify(elements));
      }
    } catch (e) {
      // Local storage fallback
    }
    setTimeout(() => {
      setSyncStatus('synced');
    }, 400);
  };

  const exportSvg = () => {
    if (!svgRef.current) return;
    const svgData = new XMLSerializer().serializeToString(svgRef.current);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const svgUrl = URL.createObjectURL(svgBlob);
    const downloadLink = document.createElement('a');
    downloadLink.href = svgUrl;
    downloadLink.download = `whiteboard_scene_${Date.now()}.svg`;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
  };

  const clearCanvas = () => {
    setElements([]);
    triggerSync();
  };

  return (
    <div className="relative w-full h-[calc(100vh-4rem)] bg-slate-950 overflow-hidden select-none font-sans text-slate-100">
      {/* Top Floating Toolbar */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 flex items-center gap-1.5 p-1.5 rounded-2xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl shadow-2xl">
        {[
          { id: 'select', icon: MousePointer, label: 'Select' },
          { id: 'pencil', icon: Pencil, label: 'Draw' },
          { id: 'rect', icon: Square, label: 'Rectangle' },
          { id: 'ellipse', icon: Circle, label: 'Ellipse' },
          { id: 'note', icon: StickyNote, label: 'Sticky Note' },
        ].map((tool) => {
          const Icon = tool.icon;
          const isActive = activeTool === tool.id;
          return (
            <button
              key={tool.id}
              onClick={() => setActiveTool(tool.id as ToolType)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
              title={tool.label}
            >
              <Icon size={16} />
              <span className="hidden sm:inline">{tool.label}</span>
            </button>
          );
        })}

        <div className="w-px h-6 bg-slate-800 mx-1" />

        {/* Color Palette */}
        <div className="flex items-center gap-1 px-1">
          {colors.map((c) => (
            <button
              key={c}
              onClick={() => setActiveColor(c)}
              className={`w-6 h-6 rounded-full transition-transform ${
                activeColor === c ? 'scale-125 ring-2 ring-indigo-400 ring-offset-2 ring-offset-slate-900' : 'hover:scale-110'
              }`}
              style={{ backgroundColor: c }}
            />
          ))}
        </div>

        <div className="w-px h-6 bg-slate-800 mx-1" />

        <button
          onClick={exportSvg}
          className="p-2 rounded-xl text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
          title="Export SVG"
        >
          <Download size={16} />
        </button>

        <button
          onClick={clearCanvas}
          className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
          title="Clear Board"
        >
          <Eraser size={16} />
        </button>
      </div>

      {/* Top Left Branding & OCC Badge */}
      <div className="absolute top-4 left-6 z-20 flex items-center gap-3">
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 backdrop-blur-md">
          <Sparkles size={16} className="text-indigo-400" />
          <span className="text-xs font-bold tracking-wide text-white">Whiteboard SOTA</span>
          <span className="text-[10px] text-slate-400 font-mono">v1.0 (tldraw)</span>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 backdrop-blur-md">
          <span
            className={`w-2 h-2 rounded-full ${
              syncStatus === 'synced' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400 animate-spin'
            }`}
          />
          <span className="text-[11px] font-mono text-slate-300 capitalize">{syncStatus} (OCC)</span>
        </div>
      </div>

      {/* Top Right Active Swarm Collaborators & Shopify Sync Button */}
      <div className="absolute top-4 right-6 z-20 flex items-center gap-2">
        <button
          onClick={() => setIsShopifyDrawerOpen((prev) => !prev)}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20 backdrop-blur-md transition-all text-xs font-semibold shadow-lg shadow-emerald-950/20"
        >
          <ShoppingBag size={14} className="text-emerald-400" />
          <span>Shopify Theme Assets</span>
        </button>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 backdrop-blur-md">
          <Bot size={14} className="text-emerald-400" />
          <span className="text-xs text-slate-300 font-medium">gerych_researcher</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
        </div>
      </div>

      {/* Floating Bottom Shopify Sync Bar */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 w-11/12 max-w-4xl">
        <ShopifyCanvasSyncBar
          graph={shopifyGraph}
          selectedStore="dnk-e-com.myshopify.com"
          selectedThemeId="160000001"
          onSyncToCanvas={handleSyncShopifyToWhiteboard}
          onOpenAssetTree={() => setIsShopifyDrawerOpen(true)}
          isSyncing={isSyncingShopify}
        />
      </div>

      {/* Shopify Theme Assets Drawer / Modal */}
      {isShopifyDrawerOpen && (
        <div className="absolute top-16 right-6 bottom-24 z-40 w-96 max-w-full flex flex-col gap-3 bg-slate-950/95 border border-slate-800 backdrop-blur-2xl rounded-2xl p-4 shadow-2xl overflow-hidden animate-in fade-in slide-in-from-right-4 duration-200">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <ShoppingBag size={16} className="text-emerald-400" />
              <h3 className="text-xs font-bold text-slate-200">Shopify Theme Inspector</h3>
            </div>
            <button
              onClick={() => setIsShopifyDrawerOpen(false)}
              className="text-slate-500 hover:text-slate-200 text-xs px-2 py-1 rounded hover:bg-slate-900"
            >
              ✕
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-1">
            <ShopifyThemeAssetTree
              tree={shopifyTree}
              selectedAssetKey={selectedAsset?.key}
              onSelectAsset={handleSelectAsset}
            />

            {selectedAsset && (
              <ShopifySectionEditor
                assetKey={selectedAsset.key}
                content={assetContent}
                contentType={selectedAsset.content_type}
                onAddToCanvas={(key) => {
                  if (shopifyGraph) handleSyncShopifyToWhiteboard(shopifyGraph);
                }}
              />
            )}
          </div>
        </div>
      )}

      {/* Main SVG Vector Canvas */}
      <svg
        ref={svgRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        className="w-full h-full cursor-crosshair"
      >
        {/* Background Dot Grid */}
        <defs>
          <pattern id="dot-grid" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" fill="#334155" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#dot-grid)" />

        {/* Rendered Elements */}
        {elements.map((el) => {
          if (el.type === 'pencil' && el.points) {
            const pathData = el.points.reduce((acc, pt, i) => (i === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`), '');
            return (
              <path
                key={el.id}
                d={pathData}
                stroke={el.color}
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
              />
            );
          }

          if (el.type === 'rect') {
            return (
              <rect
                key={el.id}
                x={el.x}
                y={el.y}
                width={el.width}
                height={el.height}
                stroke={el.color}
                strokeWidth="2"
                fill={`${el.color}15`}
                rx="12"
              />
            );
          }

          if (el.type === 'ellipse') {
            return (
              <ellipse
                key={el.id}
                cx={el.x + (el.width || 100) / 2}
                cy={el.y + (el.height || 100) / 2}
                rx={(el.width || 100) / 2}
                ry={(el.height || 100) / 2}
                stroke={el.color}
                strokeWidth="2"
                fill={`${el.color}15`}
              />
            );
          }

          if (el.type === 'note') {
            return (
              <g key={el.id} transform={`translate(${el.x}, ${el.y})`}>
                <rect
                  width={el.width}
                  height={el.height}
                  fill="#0f172a"
                  stroke={el.color}
                  strokeWidth="1.5"
                  rx="14"
                  className="filter drop-shadow-xl"
                />
                <circle cx="20" cy="20" r="4" fill={el.color} />
                <text x="32" y="24" fill="#94a3b8" fontSize="10" fontFamily="sans-serif" fontWeight="600">
                  {el.author}
                </text>
                <foreignObject x="16" y="36" width={(el.width || 200) - 32} height={(el.height || 140) - 48}>
                  <div className="text-xs text-slate-200 whitespace-pre-wrap font-sans leading-relaxed">
                    {el.content}
                  </div>
                </foreignObject>
              </g>
            );
          }

          return null;
        })}

        {/* Live Drawing Path */}
        {isDrawing && currentPath.length > 1 && (
          <path
            d={currentPath.reduce((acc, pt, i) => (i === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`), '')}
            stroke={activeColor}
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        )}
      </svg>
    </div>
  );
}
