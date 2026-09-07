// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_WhiteboardOverlay"
// purpose: "Interactive high-fidelity transparent SVG Whiteboard & Sketch Overlay synchronized with React Flow viewport"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-03"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useRef, useEffect, MouseEvent } from 'react';
import { useViewport } from '@xyflow/react';
import { useCanvasStore, WhiteboardElement } from '../../store/canvasStore';
import { 
  Pencil, 
  Square, 
  Circle, 
  ArrowUpRight, 
  FileText, 
  Type, 
  Eraser, 
  Trash2, 
  Download, 
  X, 
  Check,
  Undo2,
  Redo2
} from 'lucide-react';

type ToolType = 'pencil' | 'rect' | 'ellipse' | 'arrow' | 'note' | 'text' | 'eraser';

const COLORS = [
  { name: 'white', value: '#ffffff', glow: 'shadow-[0_0_8px_rgba(255,255,255,0.4)]' },
  { name: 'indigo', value: '#818cf8', glow: 'shadow-[0_0_8px_rgba(129,140,248,0.4)]' },
  { name: 'cyan', value: '#22d3ee', glow: 'shadow-[0_0_8px_rgba(34,211,238,0.4)]' },
  { name: 'emerald', value: '#34d399', glow: 'shadow-[0_0_8px_rgba(52,211,153,0.4)]' },
  { name: 'amber', value: '#fbbf24', glow: 'shadow-[0_0_8px_rgba(251,191,38,0.4)]' },
  { name: 'rose', value: '#f43f5e', glow: 'shadow-[0_0_8px_rgba(244,63,94,0.4)]' },
  { name: 'pink', value: '#f472b6', glow: 'shadow-[0_0_8px_rgba(244,114,182,0.4)]' },
];

const STROKES = [
  { label: 'Thin', value: 2 },
  { label: 'Medium', value: 4 },
  { label: 'Thick', value: 8 },
];

export default function WhiteboardOverlay() {
  const {
    isWhiteboardActive,
    whiteboardElements,
    setWhiteboardActive,
    setWhiteboardElements,
    addWhiteboardElement,
    clearWhiteboard,
    undo,
    redo,
    historyIndex,
    history
  } = useCanvasStore();

  const viewport = useViewport();
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Drawing state
  const [tool, setTool] = useState<ToolType>('pencil');
  const [color, setColor] = useState<string>('#fbbf24'); // Default amber
  const [strokeWidth, setStrokeWidth] = useState<number>(4);
  const [isDrawing, setIsDrawing] = useState<boolean>(false);
  
  // Coordinates being drafted
  const [startPos, setStartPos] = useState<{ x: number; y: number } | null>(null);
  const [currentPoints, setCurrentPoints] = useState<{ x: number; y: number }[]>([]);
  const [previewElement, setPreviewElement] = useState<Partial<WhiteboardElement> | null>(null);

  // Text inputs overlay
  const [textInput, setTextInput] = useState<{ x: number; y: number; type: 'text' | 'note' } | null>(null);
  const [textValue, setTextInputValue] = useState<string>('');

  // W Hotkey and Escape listner
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Avoid firing when user is typing in inputs/textareas
      if (
        document.activeElement?.tagName === 'INPUT' || 
        document.activeElement?.tagName === 'TEXTAREA' ||
        (document.activeElement as HTMLElement)?.isContentEditable
      ) {
        return;
      }

      if (e.key.toLowerCase() === 'w') {
        e.preventDefault();
        setWhiteboardActive(!isWhiteboardActive);
      } else if (e.key === 'Escape' && isWhiteboardActive) {
        setWhiteboardActive(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isWhiteboardActive, setWhiteboardActive]);

  if (!isWhiteboardActive && whiteboardElements.length === 0) {
    return null;
  }

  // Convert screen coordinates to canvas space using useViewport
  const getCanvasCoords = (e: MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return { x: 0, y: 0 };
    const rect = svgRef.current.getBoundingClientRect();
    
    // Position relative to SVG element
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    // Transform using React Flow viewport (zoom + pan)
    const x = (clientX - viewport.x) / viewport.zoom;
    const y = (clientY - viewport.y) / viewport.zoom;

    return { x, y };
  };

  const handleMouseDown = (e: MouseEvent<SVGSVGElement>) => {
    if (!isWhiteboardActive) return;
    if (e.button !== 0) return; // Left click only
    
    // Close existing text inputs if clicking elsewhere
    if (textInput) {
      handleTextSubmit();
      return;
    }

    const coords = getCanvasCoords(e);
    setIsDrawing(true);
    setStartPos(coords);

    if (tool === 'pencil') {
      setCurrentPoints([coords]);
    } else if (tool === 'eraser') {
      handleEraseAt(coords);
    }
  };

  const handleMouseMove = (e: MouseEvent<SVGSVGElement>) => {
    if (!isWhiteboardActive || !isDrawing || !startPos) return;

    const coords = getCanvasCoords(e);

    if (tool === 'pencil') {
      const nextPoints = [...currentPoints, coords];
      setCurrentPoints(nextPoints);
      
      setPreviewElement({
        type: 'pencil',
        points: nextPoints,
        color,
        x: 0,
        y: 0
      });
    } else if (tool === 'eraser') {
      handleEraseAt(coords);
    } else if (tool === 'rect') {
      const x = Math.min(startPos.x, coords.x);
      const y = Math.min(startPos.y, coords.y);
      const width = Math.abs(startPos.x - coords.x);
      const height = Math.abs(startPos.y - coords.y);

      setPreviewElement({
        type: 'rect',
        x,
        y,
        width,
        height,
        color,
        fill: `${color}15`, // Light transparent fill
      });
    } else if (tool === 'ellipse') {
      const rx = Math.abs(startPos.x - coords.x) / 2;
      const ry = Math.abs(startPos.y - coords.y) / 2;
      const cx = Math.min(startPos.x, coords.x) + rx;
      const cy = Math.min(startPos.y, coords.y) + ry;

      setPreviewElement({
        type: 'ellipse',
        x: cx,
        y: cy,
        width: rx, // store rx in width
        height: ry, // store ry in height
        color,
        fill: `${color}15`,
      });
    } else if (tool === 'arrow') {
      setPreviewElement({
        type: 'arrow',
        x: startPos.x,
        y: startPos.y,
        points: [startPos, coords],
        color,
      });
    }
  };

  const handleMouseUp = (e: MouseEvent<SVGSVGElement>) => {
    if (!isWhiteboardActive || !isDrawing) return;
    setIsDrawing(false);

    const coords = getCanvasCoords(e);

    if (tool === 'pencil' && currentPoints.length > 1) {
      const newEl: WhiteboardElement = {
        id: `wb-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
        type: 'pencil',
        x: 0,
        y: 0,
        points: currentPoints,
        color,
        strokeWidth: strokeWidth || 2,
        author: 'User',
      };
      addWhiteboardElement(newEl);
    } else if (tool === 'rect' && startPos) {
      const x = Math.min(startPos.x, coords.x);
      const y = Math.min(startPos.y, coords.y);
      const width = Math.abs(startPos.x - coords.x);
      const height = Math.abs(startPos.y - coords.y);

      if (width > 4 || height > 4) {
        const newEl: WhiteboardElement = {
          id: `wb-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
          type: 'rect',
          x,
          y,
          width,
          height,
          color,
          fill: `${color}1a`,
          strokeWidth: strokeWidth || 2,
          author: 'User',
        };
        addWhiteboardElement(newEl);
      }
    } else if (tool === 'ellipse' && startPos) {
      const rx = Math.abs(startPos.x - coords.x) / 2;
      const ry = Math.abs(startPos.y - coords.y) / 2;
      const cx = Math.min(startPos.x, coords.x) + rx;
      const cy = Math.min(startPos.y, coords.y) + ry;

      if (rx > 2 || ry > 2) {
        const newEl: WhiteboardElement = {
          id: `wb-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
          type: 'ellipse',
          x: cx,
          y: cy,
          width: rx,
          height: ry,
          color,
          fill: `${color}1a`,
          strokeWidth: strokeWidth || 2,
          author: 'User',
        };
        addWhiteboardElement(newEl);
      }
    } else if (tool === 'arrow' && startPos) {
      const dist = Math.hypot(coords.x - startPos.x, coords.y - startPos.y);
      if (dist > 5) {
        const newEl: WhiteboardElement = {
          id: `wb-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
          type: 'arrow',
          x: startPos.x,
          y: startPos.y,
          points: [startPos, coords],
          color,
          strokeWidth: strokeWidth || 2,
          author: 'User',
        };
        addWhiteboardElement(newEl);
      }
    } else if ((tool === 'text' || tool === 'note') && startPos) {
      setTextInput({ x: coords.x, y: coords.y, type: tool });
      setTextInputValue('');
    }

    setStartPos(null);
    setCurrentPoints([]);
    setPreviewElement(null);
  };

  const handleEraseAt = (coords: { x: number; y: number }) => {
    // Eraser logic: remove elements close to eraser coords
    const radius = 15; // pixels
    const remaining = whiteboardElements.filter(el => {
      if (el.type === 'pencil' && el.points) {
        // Any point of pencil path close to eraser
        return !el.points.some(pt => Math.hypot(pt.x - coords.x, pt.y - coords.y) < radius);
      } else if (el.type === 'rect') {
        const inX = coords.x >= el.x && coords.x <= el.x + (el.width || 0);
        const inY = coords.y >= el.y && coords.y <= el.y + (el.height || 0);
        return !(inX && inY);
      } else if (el.type === 'ellipse') {
        const dx = (coords.x - el.x) / (el.width || 1);
        const dy = (coords.y - el.y) / (el.height || 1);
        return dx * dx + dy * dy > 1; // outside ellipse
      } else if (el.type === 'arrow' && el.points && el.points.length === 2) {
        const [p1, p2] = el.points;
        // Distance from point to line segment
        const A = coords.x - p1.x;
        const B = coords.y - p1.y;
        const C = p2.x - p1.x;
        const D = p2.y - p1.y;
        const dot = A * C + B * D;
        const lenSq = C * C + D * D;
        let param = -1;
        if (lenSq !== 0) param = dot / lenSq;
        let xx, yy;
        if (param < 0) {
          xx = p1.x;
          yy = p1.y;
        } else if (param > 1) {
          xx = p2.x;
          yy = p2.y;
        } else {
          xx = p1.x + param * C;
          yy = p1.y + param * D;
        }
        return Math.hypot(coords.x - xx, coords.y - yy) > radius;
      } else if (el.type === 'text' || el.type === 'note') {
        // Approximate bounds
        const withinX = Math.abs(coords.x - el.x) < 80;
        const withinY = Math.abs(coords.y - el.y) < 40;
        return !(withinX && withinY);
      }
      return true;
    });

    if (remaining.length !== whiteboardElements.length) {
      setWhiteboardElements(remaining);
    }
  };

  const handleTextSubmit = () => {
    if (!textInput || !textValue.trim()) {
      setTextInput(null);
      return;
    }

    const newEl: WhiteboardElement = {
      id: `wb-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
      type: textInput.type,
      x: textInput.x,
      y: textInput.y,
      content: textValue.trim(),
      color,
      fill: textInput.type === 'note' ? `${color}33` : undefined,
      strokeWidth: strokeWidth || 2,
      author: 'User',
    };

    addWhiteboardElement(newEl);
    setTextInput(null);
    setTextInputValue('');
  };

  const handleExportSVG = () => {
    if (!svgRef.current) return;
    try {
      const svgContent = svgRef.current.outerHTML;
      const blob = new Blob([svgContent], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `dnk-sketch-${Date.now()}.svg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export sketch SVG', err);
    }
  };

  // Build SVG path from points list
  const getPencilPath = (points: { x: number; y: number }[]) => {
    if (points.length === 0) return '';
    if (points.length === 1) return `M ${points[0].x} ${points[0].y} L ${points[0].x} ${points[0].y}`;
    
    let path = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      path += ` L ${points[i].x} ${points[i].y}`;
    }
    return path;
  };

  return (
    <div 
      ref={containerRef}
      className={`absolute inset-0 z-[20] transition-colors duration-200 ${
        isWhiteboardActive 
          ? 'bg-[#030909]/40 border-2 border-dashed border-amber-400/30' 
          : 'pointer-events-none'
      }`}
    >
      {/* Dynamic SVG Layer */}
      <svg
        ref={svgRef}
        className="w-full h-full"
        style={{ pointerEvents: isWhiteboardActive ? 'auto' : 'none' }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      >
        {/* SVG Marker Definitions for Arrows */}
        <defs>
          {COLORS.map(c => (
            <marker
              key={c.value}
              id={`arrow-head-${c.value.replace('#', '')}`}
              markerWidth="8"
              markerHeight="6"
              refX="6"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 8 3, 0 6" fill={c.value} />
            </marker>
          ))}
        </defs>

        {/* Viewport Scale/Transform Group matching React Flow */}
        <g transform={`translate(${viewport.x}, ${viewport.y}) scale(${viewport.zoom})`}>
          {/* Render Saved Elements */}
          {whiteboardElements.map((el) => {
            if (el.type === 'pencil' && el.points) {
              return (
                <path
                  key={el.id}
                  d={getPencilPath(el.points)}
                  fill="none"
                  stroke={el.color}
                  strokeWidth={strokeWidth}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="drop-shadow-[0_0_3px_rgba(251,191,36,0.15)]"
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
                  strokeWidth={2}
                  fill={el.fill || 'transparent'}
                  rx={4}
                  className="drop-shadow-[0_0_4px_rgba(0,0,0,0.3)]"
                />
              );
            }
            if (el.type === 'ellipse') {
              return (
                <ellipse
                  key={el.id}
                  cx={el.x}
                  cy={el.y}
                  rx={el.width}
                  ry={el.height}
                  stroke={el.color}
                  strokeWidth={2}
                  fill={el.fill || 'transparent'}
                  className="drop-shadow-[0_0_4px_rgba(0,0,0,0.3)]"
                />
              );
            }
            if (el.type === 'arrow' && el.points && el.points.length === 2) {
              const [p1, p2] = el.points;
              return (
                <line
                  key={el.id}
                  x1={p1.x}
                  y1={p1.y}
                  x2={p2.x}
                  y2={p2.y}
                  stroke={el.color}
                  strokeWidth={3}
                  markerEnd={`url(#arrow-head-${el.color.replace('#', '')})`}
                  className="drop-shadow-[0_0_4px_rgba(0,0,0,0.3)]"
                />
              );
            }
            if (el.type === 'text') {
              return (
                <text
                  key={el.id}
                  x={el.x}
                  y={el.y}
                  fill={el.color}
                  fontSize={14}
                  fontWeight="bold"
                  fontFamily="'Fira Code', monospace"
                  className="select-none filter drop-shadow-[0_1px_3px_rgba(0,0,0,0.8)]"
                >
                  {el.content}
                </text>
              );
            }
            if (el.type === 'note') {
              return (
                <g key={el.id} className="drop-shadow-[0_4px_10px_rgba(0,0,0,0.4)]">
                  <rect
                    x={el.x}
                    y={el.y}
                    width={150}
                    height={100}
                    fill={el.fill || '#fbbf2433'}
                    stroke={el.color}
                    strokeWidth={1}
                    rx={6}
                  />
                  <foreignObject x={el.x + 8} y={el.y + 8} width={134} height={84}>
                    <div className="text-[11px] font-sans text-white/95 overflow-hidden h-full break-words select-none leading-relaxed">
                      {el.content}
                    </div>
                  </foreignObject>
                </g>
              );
            }
            return null;
          })}

          {/* Render Active Drag Preview */}
          {isDrawing && previewElement && (
            <>
              {previewElement.type === 'pencil' && previewElement.points && (
                <path
                  d={getPencilPath(previewElement.points)}
                  fill="none"
                  stroke={previewElement.color}
                  strokeWidth={strokeWidth}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  opacity={0.8}
                />
              )}
              {previewElement.type === 'rect' && (
                <rect
                  x={previewElement.x}
                  y={previewElement.y}
                  width={previewElement.width}
                  height={previewElement.height}
                  stroke={previewElement.color}
                  strokeWidth={2}
                  fill={previewElement.fill}
                  strokeDasharray="4 4"
                  rx={4}
                />
              )}
              {previewElement.type === 'ellipse' && (
                <ellipse
                  cx={previewElement.x}
                  cy={previewElement.y}
                  rx={previewElement.width}
                  ry={previewElement.height}
                  stroke={previewElement.color}
                  strokeWidth={2}
                  fill={previewElement.fill}
                  strokeDasharray="4 4"
                />
              )}
              {previewElement.type === 'arrow' && previewElement.points && previewElement.points.length === 2 && (
                <line
                  x1={previewElement.points[0].x}
                  y1={previewElement.points[0].y}
                  x2={previewElement.points[1].x}
                  y2={previewElement.points[1].y}
                  stroke={previewElement.color}
                  strokeWidth={3}
                  markerEnd={`url(#arrow-head-${(previewElement.color || '#fff').replace('#', '')})`}
                  opacity={0.8}
                />
              )}
            </>
          )}
        </g>
      </svg>

      {/* Floating Active Text/Note Creator Overlay */}
      {isWhiteboardActive && textInput && (
        <div 
          className="absolute z-[25] p-3 rounded-lg bg-[#040e0f] border border-cyan-500/40 shadow-xl flex flex-col gap-2 w-64"
          style={{
            left: textInput.x * viewport.zoom + viewport.x,
            top: textInput.y * viewport.zoom + viewport.y,
          }}
        >
          <span className="text-[10px] text-cyan-400 font-semibold uppercase tracking-wider">
            Add {textInput.type === 'note' ? 'Sticky Note' : 'Text Annotation'}
          </span>
          <textarea
            autoFocus
            rows={textInput.type === 'note' ? 3 : 1}
            value={textValue}
            onChange={(e) => setTextInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleTextSubmit();
              } else if (e.key === 'Escape') {
                setTextInput(null);
              }
            }}
            className="w-full text-xs p-1.5 rounded bg-[#010606] text-white border border-slate-700 focus:border-cyan-500 focus:outline-none resize-none font-mono"
            placeholder={textInput.type === 'note' ? 'Write sticky note...' : 'Type text...'}
          />
          <div className="flex justify-end gap-1.5">
            <button
              onClick={() => setTextInput(null)}
              className="px-2 py-1 rounded text-[10px] hover:bg-white/5 text-slate-400"
            >
              Cancel
            </button>
            <button
              onClick={handleTextSubmit}
              className="px-2 py-1 rounded text-[10px] bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold flex items-center gap-1"
            >
              <Check className="w-3 h-3" /> Save
            </button>
          </div>
        </div>
      )}

      {/* Elegant HUD Controls Pallet */}
      {isWhiteboardActive && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[30] bg-[#020a0b]/90 backdrop-blur-md px-4 py-2.5 rounded-full border border-cyan-500/30 flex items-center gap-4 shadow-[0_0_24px_rgba(34,211,238,0.15)] select-none">
          {/* Active Status Badge */}
          <div className="flex items-center gap-2 pr-3 border-r border-slate-800">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            </span>
            <span className="text-[11px] font-bold text-amber-300 uppercase tracking-wide">Sketch Mode</span>
          </div>

          {/* Tools Group */}
          <div className="flex items-center gap-1.5">
            {[
              { id: 'pencil', icon: Pencil, label: 'Pencil' },
              { id: 'rect', icon: Square, label: 'Rectangle' },
              { id: 'ellipse', icon: Circle, label: 'Ellipse' },
              { id: 'arrow', icon: ArrowUpRight, label: 'Arrow' },
              { id: 'note', icon: FileText, label: 'Sticky Note' },
              { id: 'text', icon: Type, label: 'Text' },
              { id: 'eraser', icon: Eraser, label: 'Eraser' },
            ].map((t) => {
              const Icon = t.icon;
              const isActive = tool === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setTool(t.id as ToolType)}
                  className={`p-1.5 rounded-full transition-all cursor-pointer ${
                    isActive 
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 scale-105' 
                      : 'text-slate-400 hover:bg-[#041a1c] hover:text-white border border-transparent'
                  }`}
                  title={t.label}
                >
                  <Icon className="w-3.5 h-3.5" />
                </button>
              );
            })}
          </div>

          {/* Divider */}
          <div className="h-4 w-[1px] bg-slate-800"></div>

          {/* Colors Group */}
          <div className="flex items-center gap-1.5">
            {COLORS.map((c) => {
              const isActive = color === c.value;
              return (
                <button
                  key={c.value}
                  onClick={() => setColor(c.value)}
                  className={`w-4.5 h-4.5 rounded-full transition-all border cursor-pointer ${
                    isActive 
                      ? `${c.glow} border-white scale-110` 
                      : 'border-transparent hover:scale-105'
                  }`}
                  style={{ backgroundColor: c.value }}
                  title={c.name}
                />
              );
            })}
          </div>

          {/* Stroke Width Group */}
          {tool === 'pencil' && (
            <>
              <div className="h-4 w-[1px] bg-slate-800"></div>
              <div className="flex items-center gap-1">
                {STROKES.map((s) => {
                  const isActive = strokeWidth === s.value;
                  return (
                    <button
                      key={s.value}
                      onClick={() => setStrokeWidth(s.value)}
                      className={`px-2 py-0.5 rounded text-[10px] transition-all cursor-pointer ${
                        isActive 
                          ? 'bg-white/10 text-white font-bold' 
                          : 'text-slate-500 hover:text-slate-300'
                      }`}
                    >
                      {s.label}
                    </button>
                  );
                })}
              </div>
            </>
          )}

          {/* Divider */}
          <div className="h-4 w-[1px] bg-slate-800"></div>

          {/* History & Extra Controls Group */}
          <div className="flex items-center gap-1">
            <button
              onClick={undo}
              disabled={historyIndex <= 0}
              className={`p-1.5 rounded-full cursor-pointer transition-all ${
                historyIndex > 0 ? 'text-slate-300 hover:bg-white/5' : 'text-slate-600 cursor-not-allowed'
              }`}
              title="Undo Sketch/Node Action"
            >
              <Undo2 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={redo}
              disabled={historyIndex >= history.length - 1}
              className={`p-1.5 rounded-full cursor-pointer transition-all ${
                historyIndex < history.length - 1 ? 'text-slate-300 hover:bg-white/5' : 'text-slate-600 cursor-not-allowed'
              }`}
              title="Redo Sketch/Node Action"
            >
              <Redo2 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={clearWhiteboard}
              disabled={whiteboardElements.length === 0}
              className={`p-1.5 rounded-full cursor-pointer transition-all ${
                whiteboardElements.length > 0 ? 'text-rose-400 hover:bg-rose-500/10' : 'text-slate-600 cursor-not-allowed'
              }`}
              title="Clear All Sketches"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleExportSVG}
              className="p-1.5 rounded-full hover:bg-white/5 text-slate-300 transition-all cursor-pointer"
              title="Export Drawings as SVG"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Done Close Button */}
          <button
            onClick={() => setWhiteboardActive(false)}
            className="flex items-center gap-1 px-3 py-1 rounded-full bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-extrabold text-[11px] transition-all cursor-pointer shadow-[0_2px_8px_rgba(34,211,238,0.25)] ml-2"
          >
            <Check className="w-3.5 h-3.5" /> Done
          </button>
        </div>
      )}
    </div>
  );
}
