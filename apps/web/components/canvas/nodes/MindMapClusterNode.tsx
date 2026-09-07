// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_MindMapClusterNode"
// purpose: "Mind Map Spatial Cluster Boundary Node with auto-layout framing, semantic header, color tagging, and glassmorphism styling"
// author: "DNK-e.com Maksym & Antigravity Mentor"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Layers, Sparkles, Hash, Edit2, Check, X } from 'lucide-react';
import { useCanvasStore } from '../../../store/canvasStore';

export interface MindMapClusterData {
  title?: string;
  name?: string;
  clusterId?: string;
  color?: string;
  nodeCount?: number;
  tags?: string[];
  description?: string;
  width?: number;
  height?: number;
  [key: string]: any;
}

export default function MindMapClusterNode({ id, data, selected }: NodeProps) {
  const nodeData = (data || {}) as MindMapClusterData;
  const updateNodeData = useCanvasStore((state) => state.updateNodeData);

  const clusterTitle = nodeData.title || nodeData.name || 'AI Cluster';
  const color = nodeData.color || '#3B82F6';
  const nodeCount = nodeData.nodeCount ?? 0;
  const width = Math.max(280, nodeData.width || 340);
  const height = Math.max(160, nodeData.height || 220);

  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(clusterTitle);

  const handleSaveTitle = useCallback(() => {
    if (editTitle.trim()) {
      updateNodeData(id, { title: editTitle.trim(), name: editTitle.trim() });
    }
    setIsEditing(false);
  }, [id, editTitle, updateNodeData]);

  return (
    <div
      style={{
        width: `${width}px`,
        height: `${height}px`,
        borderColor: selected ? color : `${color}55`,
        boxShadow: selected ? `0 0 30px ${color}33, inset 0 0 20px ${color}11` : `0 4px 20px rgba(0,0,0,0.3)`,
      }}
      className={`relative rounded-3xl border-2 border-dashed transition-all duration-200 pointer-events-auto bg-slate-950/25 backdrop-blur-[2px] group`}
      data-testid={`cluster-node-${id}`}
    >
      {/* 4-Way Handles for inter-cluster edges */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 rounded-full border-2 border-slate-900 transition-opacity opacity-0 group-hover:opacity-100"
        style={{ backgroundColor: color }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 rounded-full border-2 border-slate-900 transition-opacity opacity-0 group-hover:opacity-100"
        style={{ backgroundColor: color }}
      />
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 rounded-full border-2 border-slate-900 transition-opacity opacity-0 group-hover:opacity-100"
        style={{ backgroundColor: color }}
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 rounded-full border-2 border-slate-900 transition-opacity opacity-0 group-hover:opacity-100"
        style={{ backgroundColor: color }}
      />

      {/* Cluster Header Bar Floating at Top */}
      <div
        className="absolute -top-5 left-4 right-4 flex items-center justify-between px-3.5 py-1.5 rounded-xl border shadow-lg backdrop-blur-md select-none transition-transform group-hover:-translate-y-0.5"
        style={{
          backgroundColor: '#13141aee',
          borderColor: `${color}66`,
        }}
      >
        <div className="flex items-center gap-2 min-w-0">
          <div
            className="w-5 h-5 rounded-lg flex items-center justify-center shrink-0 shadow-sm"
            style={{ backgroundColor: `${color}25`, color }}
          >
            <Layers className="w-3.5 h-3.5" />
          </div>

          {isEditing ? (
            <div className="flex items-center gap-1 nodrag">
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveTitle();
                  if (e.key === 'Escape') setIsEditing(false);
                }}
                className="bg-black/50 border border-white/20 rounded px-2 py-0.5 text-xs text-white focus:outline-none focus:border-blue-400 w-44"
                autoFocus
              />
              <button
                onClick={handleSaveTitle}
                className="p-1 text-emerald-400 hover:text-emerald-300"
                title="Зберегти"
              >
                <Check className="w-3 h-3" />
              </button>
              <button
                onClick={() => setIsEditing(false)}
                className="p-1 text-neutral-400 hover:text-white"
                title="Скасувати"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ) : (
            <div
              className="flex items-center gap-1.5 cursor-pointer truncate"
              onClick={() => {
                setEditTitle(clusterTitle);
                setIsEditing(true);
              }}
              title="Натисніть для редагування назви"
            >
              <span className="text-xs font-semibold text-slate-100 truncate tracking-wide">
                {clusterTitle}
              </span>
              <Edit2 className="w-2.5 h-2.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
            </div>
          )}
        </div>

        <div className="flex items-center gap-1.5 shrink-0 ml-2">
          {nodeCount > 0 && (
            <div
              className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium border"
              style={{
                backgroundColor: `${color}18`,
                borderColor: `${color}40`,
                color,
              }}
            >
              <Hash className="w-2.5 h-2.5" />
              <span>{nodeCount}</span>
            </div>
          )}

          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: color }}
            title={`Cluster ${nodeData.clusterId || id}`}
          />
        </div>
      </div>

      {/* Cluster Footer Info */}
      <div className="absolute bottom-2 right-3 text-[10px] text-slate-500 font-mono tracking-tight pointer-events-none opacity-40 group-hover:opacity-80 transition-opacity flex items-center gap-1">
        <Sparkles className="w-3 h-3 text-slate-400" />
        <span>AI Auto-Cluster</span>
      </div>
    </div>
  );
}
