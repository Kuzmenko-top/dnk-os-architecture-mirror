// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_BaseMindMapNode"
// purpose: "Unified foundational React Flow custom node with 4-way handles, glassmorphism design system, inline-editing, nodrag handling, and Zustand updateNodeData persistence"
// author: "DNK-e.com Maksym & Antigravity Mentor"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { useCanvasStore } from '../../../store/canvasStore';
import { MoreVertical, X, Check, Edit2 } from 'lucide-react';

export type MindMapThemeColor = 'amber' | 'emerald' | 'blue' | 'orange' | 'purple' | 'slate';

export interface BaseMindMapNodeData {
  title?: string;
  description?: string;
  category?: string;
  status?: string;
  [key: string]: any;
}

export interface BaseMindMapNodeProps extends NodeProps {
  themeColor: MindMapThemeColor;
  icon: React.ReactNode;
  categoryLabel: string;
  children?: React.ReactNode;
  headerActions?: React.ReactNode;
}

const THEME_STYLES: Record<MindMapThemeColor, {
  border: string;
  borderSelected: string;
  glowSelected: string;
  badgeBg: string;
  badgeText: string;
  badgeBorder: string;
  handleBg: string;
  handleShadow: string;
  headerIconText: string;
}> = {
  amber: {
    border: 'border-amber-500/30',
    borderSelected: 'border-amber-400',
    glowSelected: 'shadow-[0_0_25px_rgba(245,158,11,0.3)] ring-2 ring-amber-400/40',
    badgeBg: 'bg-amber-950/60',
    badgeText: 'text-amber-300',
    badgeBorder: 'border-amber-500/30',
    handleBg: 'bg-amber-400',
    handleShadow: 'shadow-[0_0_8px_#fbbf24]',
    headerIconText: 'text-amber-400',
  },
  emerald: {
    border: 'border-emerald-500/30',
    borderSelected: 'border-emerald-400',
    glowSelected: 'shadow-[0_0_25px_rgba(16,185,129,0.3)] ring-2 ring-emerald-400/40',
    badgeBg: 'bg-emerald-950/60',
    badgeText: 'text-emerald-300',
    badgeBorder: 'border-emerald-500/30',
    handleBg: 'bg-emerald-400',
    handleShadow: 'shadow-[0_0_8px_#34d399]',
    headerIconText: 'text-emerald-400',
  },
  blue: {
    border: 'border-blue-500/30',
    borderSelected: 'border-blue-400',
    glowSelected: 'shadow-[0_0_25px_rgba(59,130,246,0.3)] ring-2 ring-blue-400/40',
    badgeBg: 'bg-blue-950/60',
    badgeText: 'text-blue-300',
    badgeBorder: 'border-blue-500/30',
    handleBg: 'bg-blue-400',
    handleShadow: 'shadow-[0_0_8px_#60a5fa]',
    headerIconText: 'text-blue-400',
  },
  orange: {
    border: 'border-orange-500/30',
    borderSelected: 'border-orange-400',
    glowSelected: 'shadow-[0_0_25px_rgba(249,115,22,0.3)] ring-2 ring-orange-400/40',
    badgeBg: 'bg-orange-950/60',
    badgeText: 'text-orange-300',
    badgeBorder: 'border-orange-500/30',
    handleBg: 'bg-orange-400',
    handleShadow: 'shadow-[0_0_8px_#fb923c]',
    headerIconText: 'text-orange-400',
  },
  purple: {
    border: 'border-purple-500/30',
    borderSelected: 'border-purple-400',
    glowSelected: 'shadow-[0_0_25px_rgba(168,85,247,0.3)] ring-2 ring-purple-400/40',
    badgeBg: 'bg-purple-950/60',
    badgeText: 'text-purple-300',
    badgeBorder: 'border-purple-500/30',
    handleBg: 'bg-purple-400',
    handleShadow: 'shadow-[0_0_8px_#c084fc]',
    headerIconText: 'text-purple-400',
  },
  slate: {
    border: 'border-slate-700/50',
    borderSelected: 'border-slate-400',
    glowSelected: 'shadow-[0_0_20px_rgba(148,163,184,0.2)] ring-2 ring-slate-400/40',
    badgeBg: 'bg-slate-900/60',
    badgeText: 'text-slate-300',
    badgeBorder: 'border-slate-700/40',
    handleBg: 'bg-slate-400',
    handleShadow: 'shadow-[0_0_8px_#94a3b8]',
    headerIconText: 'text-slate-400',
  },
};

export default function BaseMindMapNode({
  id,
  data,
  selected,
  themeColor,
  icon,
  categoryLabel,
  children,
  headerActions,
}: BaseMindMapNodeProps) {
  const nodeData = (data || {}) as BaseMindMapNodeData;
  const updateNodeData = useCanvasStore((state) => state.updateNodeData);
  const removeNode = useCanvasStore((state) => state.removeNode);

  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleText, setTitleText] = useState(nodeData.title || categoryLabel);

  const [isEditingDesc, setIsEditingDesc] = useState(false);
  const [descText, setDescText] = useState(nodeData.description || '');

  const styles = THEME_STYLES[themeColor] || THEME_STYLES.slate;

  const handleSaveTitle = useCallback(() => {
    setIsEditingTitle(false);
    if (titleText.trim() !== nodeData.title) {
      updateNodeData(id, { title: titleText.trim() });
    }
  }, [id, titleText, nodeData.title, updateNodeData]);

  const handleSaveDesc = useCallback(() => {
    setIsEditingDesc(false);
    if (descText.trim() !== nodeData.description) {
      updateNodeData(id, { description: descText.trim() });
    }
  }, [id, descText, nodeData.description, updateNodeData]);

  return (
    <div
      className={`w-[320px] rounded-2xl bg-[#0e121b]/95 backdrop-blur-2xl border p-4 text-slate-200 shadow-2xl transition-all font-sans relative group ${
        styles.border
      } ${selected ? `${styles.borderSelected} ${styles.glowSelected}` : 'hover:border-slate-600'}`}
    >
      {/* 4-Way Smooth Multi-Handles */}
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        className={`w-3 h-3 ${styles.handleBg} border-2 border-[#0e121b] rounded-full ${styles.handleShadow} transition-transform hover:scale-125`}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        className={`w-3 h-3 ${styles.handleBg} border-2 border-[#0e121b] rounded-full ${styles.handleShadow} transition-transform hover:scale-125`}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        className={`w-3 h-3 ${styles.handleBg} border-2 border-[#0e121b] rounded-full ${styles.handleShadow} transition-transform hover:scale-125`}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        className={`w-3 h-3 ${styles.handleBg} border-2 border-[#0e121b] rounded-full ${styles.handleShadow} transition-transform hover:scale-125`}
      />

      {/* Header Bar */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800/80">
        <div className="flex items-center gap-2 min-w-0">
          <div className={styles.headerIconText}>{icon}</div>
          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-mono border uppercase tracking-wider ${styles.badgeBg} ${styles.badgeText} ${styles.badgeBorder}`}
          >
            {categoryLabel}
          </span>
        </div>

        <div className="flex items-center gap-1">
          {headerActions}
          <button
            onClick={() => removeNode(id)}
            title="Delete Node"
            className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-red-950/40 transition-colors nodrag cursor-pointer opacity-0 group-hover:opacity-100"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Inline Editable Title */}
      <div className="mb-2">
        {isEditingTitle ? (
          <div className="flex items-center gap-1 nodrag">
            <input
              type="text"
              value={titleText}
              onChange={(e) => setTitleText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSaveTitle();
                if (e.key === 'Escape') {
                  setTitleText(nodeData.title || categoryLabel);
                  setIsEditingTitle(false);
                }
              }}
              autoFocus
              className="w-full bg-[#161c28] border border-slate-700 rounded px-2 py-1 text-sm font-semibold text-white focus:outline-none focus:border-amber-400"
            />
            <button
              onClick={handleSaveTitle}
              className="p-1 text-emerald-400 hover:bg-emerald-950/40 rounded cursor-pointer"
            >
              <Check className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <div
            onDoubleClick={() => setIsEditingTitle(true)}
            className="group/title flex items-center justify-between cursor-pointer py-0.5 rounded hover:bg-slate-800/40 px-1 -mx-1"
          >
            <h4 className="font-semibold text-sm text-white truncate">{nodeData.title || titleText}</h4>
            <Edit2 className="w-3 h-3 text-slate-500 opacity-0 group-hover/title:opacity-100 transition-opacity" />
          </div>
        )}
      </div>

      {/* Inline Editable Description */}
      <div className="mb-3">
        {isEditingDesc ? (
          <div className="flex flex-col gap-1 nodrag">
            <textarea
              value={descText}
              onChange={(e) => setDescText(e.target.value)}
              rows={2}
              autoFocus
              className="w-full bg-[#161c28] border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 focus:outline-none focus:border-amber-400 resize-none"
            />
            <div className="flex justify-end gap-1">
              <button
                onClick={() => {
                  setDescText(nodeData.description || '');
                  setIsEditingDesc(false);
                }}
                className="px-2 py-0.5 text-[10px] text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveDesc}
                className="px-2 py-0.5 text-[10px] bg-slate-700 hover:bg-slate-600 text-white rounded"
              >
                Save
              </button>
            </div>
          </div>
        ) : (
          <p
            onDoubleClick={() => setIsEditingDesc(true)}
            className="text-xs text-slate-400 line-clamp-2 cursor-pointer hover:text-slate-300 py-0.5 rounded hover:bg-slate-800/30 px-1 -mx-1"
          >
            {nodeData.description || 'Double-click to add details or hypothesis...'}
          </p>
        )}
      </div>

      {/* Specialized Content / Children Slot */}
      {children && <div className="pt-2 border-t border-slate-800/60 nodrag">{children}</div>}
    </div>
  );
}
