// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_SmartNoteNode"
// purpose: "Spatial Smart Note Node in authentic Shopify Design System from Open Design (Deep Teal #02090a, Dark Forest #061a1c, Neon Green #36F4A4)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  FileText, 
  CheckSquare, 
  Square, 
  Plus, 
  Trash2, 
  Tag, 
  Sparkles, 
  Pin
} from 'lucide-react';

export interface ChecklistItem {
  id: string;
  text: string;
  completed: boolean;
}

export interface SmartNoteData {
  title?: string;
  content?: string;
  category?: string;
  checklist?: ChecklistItem[];
}

export default function SmartNoteNode({ data, selected }: NodeProps) {
  const nodeData = (data || {}) as SmartNoteData;
  const [title, setTitle] = useState<string>(
    typeof nodeData.title === 'string' ? nodeData.title : 'Shopify OS Architecture Plan'
  );
  const [content, setContent] = useState<string>(
    typeof nodeData.content === 'string' ? nodeData.content : 'Implant Infinite Canvas Engine with authentic Shopify Design System from Open Design.'
  );
  const [category] = useState<string>(
    typeof nodeData.category === 'string' ? nodeData.category : 'architecture'
  );

  const [checklist, setChecklist] = useState<ChecklistItem[]>(
    Array.isArray(nodeData.checklist) ? nodeData.checklist : [
      { id: '1', text: 'Import tokens.css from Open Design', completed: true },
      { id: '2', text: 'Set Void #000000 and Deep Teal #02090a surfaces', completed: true },
      { id: '3', text: 'Apply Neon Green #36F4A4 highlights & full pill buttons', completed: true },
      { id: '4', text: 'Connect Swarm live chat with Liquid AST compiler', completed: true },
    ]
  );

  const [newChecklistText, setNewChecklistText] = useState('');

  const toggleChecklist = (id: string) => {
    setChecklist((prev) =>
      prev.map((item) => (item.id === id ? { ...item, completed: !item.completed } : item))
    );
  };

  const addChecklistItem = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newChecklistText.trim()) return;
    setChecklist((prev) => [
      ...prev,
      { id: String(Date.now()), text: newChecklistText.trim(), completed: false }
    ]);
    setNewChecklistText('');
  };

  const removeChecklistItem = (id: string) => {
    setChecklist((prev) => prev.filter((item) => item.id !== id));
  };

  const completedCount = checklist.filter((item) => item.completed).length;

  return (
    <div className={`w-[400px] rounded-3xl bg-[#02090a]/95 backdrop-blur-2xl border border-[#1e2c31] p-4 text-white shadow-[0_12px_45px_rgba(0,0,0,0.85)] transition-all duration-200 ${selected ? 'border-[#36f4a4] shadow-[0_0_30px_rgba(54,244,164,0.3)] ring-1 ring-[#36f4a4]' : ''}`}>
      {/* 4-Way Handles */}
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="target" position={Position.Left} id="left" className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="source" position={Position.Right} id="right" className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#1e2c31] pb-3 mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-[#102620] border border-[#36f4a4]/40 flex items-center justify-center text-[#36f4a4]">
            <FileText className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="font-bold text-sm text-white bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-[#36f4a4] rounded px-1"
          />
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-[#102620] text-[#36f4a4] border border-[#36f4a4]/30 font-semibold">
            {category}
          </span>
          <Pin className="w-3.5 h-3.5 text-[#36f4a4]" />
        </div>
      </div>

      {/* Content Textarea */}
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={3}
        className="w-full text-xs font-mono text-[#a1a1aa] bg-[#061a1c] border border-[#1e2c31] rounded-2xl p-2.5 focus:outline-none focus:border-[#36f4a4] focus:text-white transition-all resize-none mb-3"
      />

      {/* Interactive Action Checklist */}
      <div className="space-y-1.5 mb-3">
        <div className="flex items-center justify-between text-[11px] font-mono text-[#a1a1aa] px-1">
          <span className="flex items-center gap-1 text-white font-semibold">
            <Sparkles className="w-3 h-3 text-[#36f4a4]" /> Action Checklist ({completedCount}/{checklist.length})
          </span>
          <span className="text-[#36f4a4]">Live Sync</span>
        </div>

        <div className="space-y-1 max-h-[120px] overflow-y-auto pr-1">
          {checklist.map((item) => (
            <div
              key={item.id}
              className={`flex items-center justify-between p-2 rounded-xl text-xs font-mono transition-all border ${
                item.completed
                  ? 'bg-[#102620]/60 border-[#36f4a4]/30 text-[#a1a1aa] line-through'
                  : 'bg-[#061a1c] border-[#1e2c31] text-white hover:border-[#36f4a4]/40'
              }`}
            >
              <button
                type="button"
                onClick={() => toggleChecklist(item.id)}
                className="flex items-center gap-2 flex-1 text-left cursor-pointer"
              >
                {item.completed ? (
                  <CheckSquare className="w-4 h-4 text-[#36f4a4]" />
                ) : (
                  <Square className="w-4 h-4 text-[#71717a]" />
                )}
                <span>{item.text}</span>
              </button>
              <button
                type="button"
                onClick={() => removeChecklistItem(item.id)}
                className="text-[#71717a] hover:text-red-400 p-0.5 transition-colors cursor-pointer"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>

        {/* Add Checklist Item Input */}
        <form onSubmit={addChecklistItem} className="flex items-center gap-1.5 pt-1">
          <input
            type="text"
            value={newChecklistText}
            onChange={(e) => setNewChecklistText(e.target.value)}
            placeholder="Add new subtask..."
            className="flex-1 px-3 py-1.5 rounded-full bg-[#061a1c] border border-[#1e2c31] text-xs text-white placeholder-[#71717a] focus:outline-none focus:border-[#36f4a4]"
          />
          <button
            type="submit"
            className="p-1.5 rounded-full bg-[#36f4a4] hover:bg-[#2de097] text-black font-bold cursor-pointer transition-all shadow-md shadow-[#36f4a4]/20"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>

      {/* Footer */}
      <div className="pt-2 border-t border-[#1e2c31] flex items-center justify-between text-[10px] font-mono text-[#a1a1aa]">
        <div className="flex items-center gap-1 text-[#36f4a4]">
          <Tag className="w-3 h-3" />
          <span>Shopify Design System</span>
        </div>
        <span className="text-[#71717a]">4-Way Interconnect</span>
      </div>
    </div>
  );
}
