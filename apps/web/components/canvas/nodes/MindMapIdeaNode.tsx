// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_MindMapIdeaNode"
// purpose: "Mind Map Idea Card (Yellow/Amber sticker) with interactive tags and confidence rating score"
// author: "DNK-e.com Maksym & Antigravity Mentor"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { NodeProps } from '@xyflow/react';
import { Lightbulb, Star, Tag, Plus } from 'lucide-react';
import BaseMindMapNode from './BaseMindMapNode';
import { useCanvasStore } from '../../../store/canvasStore';

export interface MindMapIdeaData {
  title?: string;
  description?: string;
  tags?: string[];
  confidence_score?: number; // 1 - 5
  [key: string]: any;
}

export default function MindMapIdeaNode(props: NodeProps) {
  const { id, data } = props;
  const nodeData = (data || {}) as MindMapIdeaData;
  const updateNodeData = useCanvasStore((state) => state.updateNodeData);

  const tags = nodeData.tags || ['#innovation', '#hypothesis'];
  const confidence = nodeData.confidence_score || 4;

  const [newTag, setNewTag] = useState('');
  const [isAddingTag, setIsAddingTag] = useState(false);

  const handleSetConfidence = (score: number) => {
    updateNodeData(id, { confidence_score: score });
  };

  const handleAddTag = () => {
    if (newTag.trim()) {
      const formatted = newTag.trim().startsWith('#') ? newTag.trim() : `#${newTag.trim()}`;
      if (!tags.includes(formatted)) {
        updateNodeData(id, { tags: [...tags, formatted] });
      }
      setNewTag('');
      setIsAddingTag(false);
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    updateNodeData(id, { tags: tags.filter((t) => t !== tagToRemove) });
  };

  return (
    <BaseMindMapNode
      {...props}
      themeColor="amber"
      icon={<Lightbulb className="w-4 h-4" />}
      categoryLabel="Idea"
    >
      <div className="flex flex-col gap-2.5">
        {/* Confidence Stars */}
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-amber-300/80 font-medium">Confidence</span>
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => handleSetConfidence(star)}
                className="p-0.5 hover:scale-125 transition-transform cursor-pointer"
                title={`Confidence: ${star}/5`}
              >
                <Star
                  className={`w-3.5 h-3.5 ${
                    star <= confidence ? 'fill-amber-400 text-amber-400' : 'text-slate-600'
                  }`}
                />
              </button>
            ))}
          </div>
        </div>

        {/* Tags List */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          {tags.map((tag) => (
            <span
              key={tag}
              className="group/tag inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-950/40 border border-amber-500/20 text-[10px] text-amber-300 font-mono"
            >
              {tag}
              <button
                onClick={() => handleRemoveTag(tag)}
                className="opacity-40 hover:opacity-100 hover:text-red-400 ml-0.5"
              >
                ×
              </button>
            </span>
          ))}

          {isAddingTag ? (
            <div className="inline-flex items-center gap-1">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAddTag();
                  if (e.key === 'Escape') setIsAddingTag(false);
                }}
                placeholder="tag"
                autoFocus
                className="w-16 bg-[#161c28] border border-amber-500/40 rounded px-1.5 py-0.5 text-[10px] text-amber-200 focus:outline-none"
              />
            </div>
          ) : (
            <button
              onClick={() => setIsAddingTag(true)}
              className="p-0.5 rounded text-amber-400/60 hover:text-amber-300 hover:bg-amber-950/40 transition-colors"
              title="Add Tag"
            >
              <Plus className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    </BaseMindMapNode>
  );
}
