// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_NoteDocumentNode"
// purpose: "Universal Living Note Document Node for DNK OS Note-Based Canvas (Task 3) supporting Markdown editor, TaskDNA checklists, tags, attachments, and embedded agent actions"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  FileText, 
  Sparkles, 
  CheckSquare, 
  Square, 
  Plus, 
  Trash2, 
  Bot, 
  Tag, 
  Paperclip, 
  ChevronDown, 
  ChevronUp,
  Pin,
  Send,
  CheckCircle2,
  ExternalLink
} from 'lucide-react';

export interface ChecklistItem {
  id: string;
  text: string;
  completed: boolean;
}

export interface NoteDocumentData {
  title?: string;
  subtitle?: string;
  category?: 'brief' | 'architecture' | 'spec' | 'marketing' | 'notes';
  tags?: string[];
  content?: string;
  checklist?: ChecklistItem[];
  attachedFiles?: string[];
  assignedAgent?: string;
  lastEditedBy?: string;
  updatedAt?: string;
}

export default function NoteDocumentNode({ data, selected }: NodeProps) {
  const nodeData = (data || {}) as NoteDocumentData;
  
  const [title, setTitle] = useState<string>(nodeData.title || 'Project Brief & Strategy');
  const [subtitle, setSubtitle] = useState<string>(nodeData.subtitle || 'Core architectural directives & target KPIs');
  const [content, setContent] = useState<string>(
    nodeData.content ||
    `### 🎯 Objective\nLaunch a high-converting 360° E-Commerce ecosystem for ReBurn Smoker with automated Liquid generation and 9:16 UGC video pipeline.\n\n### 💡 Key Directives\n- **Target AOV**: $120+ via 3-in-1 bundle discount selector.\n- **Design Standard**: Shopify Cinematic Theme with #36F4A4 Neon Green highlights.\n- **Agent Orchestrator**: Gerych Prime (Hermes) with 14 specialized workers.`
  );
  const [category] = useState<string>(nodeData.category || 'brief');
  const [tags, setTags] = useState<string[]>(nodeData.tags || ['E-Com', 'ReBurn', 'Shopify', 'Q3-Launch']);
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [isAgentExecuting, setIsAgentExecuting] = useState<boolean>(false);

  const [checklist, setChecklist] = useState<ChecklistItem[]>(
    Array.isArray(nodeData.checklist) && nodeData.checklist.length > 0
      ? nodeData.checklist
      : [
          { id: '1', text: 'Define Brand Tone of Voice & ICP Target', completed: true },
          { id: '2', text: 'Compile Liquid OS 2.0 Product & Bundle Sections', completed: true },
          { id: '3', text: 'Generate 9:16 UGC kinetic video reels with Remotion', completed: false },
          { id: '4', text: 'Pass Fail-Closed Security & Quality Audit Gate', completed: false },
        ]
  );

  const [newChecklistText, setNewChecklistText] = useState('');
  const [agentPrompt, setAgentPrompt] = useState('');

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

  const handleRunAgentOnNote = () => {
    if (!agentPrompt.trim()) return;
    setIsAgentExecuting(true);
    setTimeout(() => {
      setContent((prev) => `${prev}\n\n> **Agent Output (${new Date().toLocaleTimeString()})**:\n> ${agentPrompt.trim()} synthesized successfully.`);
      setAgentPrompt('');
      setIsAgentExecuting(false);
    }, 1000);
  };

  const completedCount = checklist.filter((item) => item.completed).length;

  return (
    <div className={`w-[440px] rounded-3xl bg-[#02090a]/95 backdrop-blur-2xl border border-[#1e2c31] p-5 text-white shadow-[0_16px_50px_rgba(0,0,0,0.9)] transition-all duration-200 ${
      selected ? 'border-[#36f4a4] ring-1 ring-[#36f4a4] shadow-[0_0_35px_rgba(54,244,164,0.25)]' : ''
    }`}>
      {/* 4-Way Semantic Handles */}
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="target" position={Position.Left} id="left" className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="source" position={Position.Right} id="right" className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />

      {/* Note Document Header */}
      <div className="flex items-start justify-between border-b border-[#1e2c31] pb-3 mb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-2xl bg-[#102620] border border-[#36f4a4]/40 flex items-center justify-center text-[#36f4a4] shadow-sm">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="font-bold text-sm text-white bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-[#36f4a4] rounded px-1 w-full"
            />
            <input
              type="text"
              value={subtitle}
              onChange={(e) => setSubtitle(e.target.value)}
              className="text-[11px] text-[#a1a1aa] bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-[#36f4a4] rounded px-1 w-full truncate"
            />
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <span className="text-[9px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-[#102620] text-[#36f4a4] border border-[#36f4a4]/30 font-bold">
            {category}
          </span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded-full hover:bg-[#061a1c] text-[#a1a1aa] hover:text-white transition-colors cursor-pointer"
          >
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Tags Bar */}
      <div className="flex flex-wrap items-center gap-1.5 mb-3">
        {tags.map((tag, idx) => (
          <span key={idx} className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#061a1c] text-[#a1a1aa] border border-[#1e2c31]">
            <Tag className="w-2.5 h-2.5 text-[#36f4a4]" />
            <span>{tag}</span>
          </span>
        ))}
      </div>

      {isExpanded && (
        <>
          {/* Note Document Markdown Content Box */}
          <div className="mb-3">
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={6}
              className="w-full text-xs font-mono leading-relaxed text-[#d4d4d8] bg-[#061a1c] border border-[#1e2c31] rounded-2xl p-3 focus:outline-none focus:border-[#36f4a4] transition-all resize-none shadow-inner"
              placeholder="Write specifications, briefs, and notes in Markdown..."
            />
          </div>

          {/* Interactive Living Checklist */}
          <div className="space-y-1.5 mb-3">
            <div className="flex items-center justify-between text-[11px] font-mono text-[#a1a1aa] px-1">
              <span className="flex items-center gap-1 text-white font-semibold">
                <CheckSquare className="w-3.5 h-3.5 text-[#36f4a4]" />
                <span>Action Checklist ({completedCount}/{checklist.length})</span>
              </span>
              <span className="text-[#36f4a4] font-bold">{Math.round((completedCount / (checklist.length || 1)) * 100)}%</span>
            </div>

            <div className="space-y-1 max-h-[130px] overflow-y-auto pr-1">
              {checklist.map((item) => (
                <div
                  key={item.id}
                  className={`flex items-center justify-between p-2 rounded-xl text-xs font-mono transition-all border ${
                    item.completed
                      ? 'bg-[#102620]/50 border-[#36f4a4]/30 text-[#a1a1aa] line-through'
                      : 'bg-[#061a1c] border-[#1e2c31] text-white hover:border-[#36f4a4]/40'
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => toggleChecklist(item.id)}
                    className="flex items-center gap-2 flex-1 text-left cursor-pointer"
                  >
                    {item.completed ? (
                      <CheckSquare className="w-3.5 h-3.5 text-[#36f4a4]" />
                    ) : (
                      <Square className="w-3.5 h-3.5 text-[#71717a]" />
                    )}
                    <span className="font-sans text-[11px]">{item.text}</span>
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

            {/* Quick Add Subtask Input */}
            <form onSubmit={addChecklistItem} className="flex items-center gap-1.5 pt-1">
              <input
                type="text"
                value={newChecklistText}
                onChange={(e) => setNewChecklistText(e.target.value)}
                placeholder="Add new subtask to document..."
                className="flex-1 px-3.5 py-1.5 rounded-full bg-[#061a1c] border border-[#1e2c31] text-xs text-white placeholder-[#71717a] focus:outline-none focus:border-[#36f4a4]"
              />
              <button
                type="submit"
                className="p-1.5 rounded-full bg-[#36f4a4] hover:bg-[#2de097] text-black font-bold cursor-pointer transition-all shadow-md shadow-[#36f4a4]/20"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>

          {/* Embedded Agent Dispatch Inside Note */}
          <div className="p-2.5 rounded-2xl bg-[#061a1c] border border-[#1e2c31] mt-2">
            <div className="flex items-center justify-between text-[10px] font-mono text-[#a1a1aa] mb-1.5 px-1">
              <span className="flex items-center gap-1 text-[#36f4a4] font-semibold">
                <Bot className="w-3 h-3" />
                <span>Execute Agent Directive on this Note</span>
              </span>
              <span>Gerych Prime</span>
            </div>
            <div className="flex items-center gap-1.5">
              <input
                type="text"
                value={agentPrompt}
                onChange={(e) => setAgentPrompt(e.target.value)}
                placeholder="e.g. Expand marketing copy, refine ICP, or compile spec..."
                className="flex-1 px-3 py-1.5 rounded-full bg-[#02090a] border border-[#1e2c31] text-xs text-white placeholder-[#71717a] focus:outline-none focus:border-[#36f4a4]"
              />
              <button
                onClick={handleRunAgentOnNote}
                disabled={isAgentExecuting}
                className="px-3.5 py-1.5 rounded-full bg-[#36f4a4] hover:bg-[#2de097] text-black font-bold text-xs flex items-center gap-1 transition-all cursor-pointer shadow-md shadow-[#36f4a4]/20 active:scale-95"
              >
                <Sparkles className="w-3 h-3" />
                <span>{isAgentExecuting ? 'Running...' : 'Run'}</span>
              </button>
            </div>
          </div>
        </>
      )}

      {/* Note Document Footer */}
      <div className="mt-3 pt-2.5 border-t border-[#1e2c31] flex items-center justify-between text-[10px] font-mono text-[#a1a1aa]">
        <div className="flex items-center gap-1 text-[#36f4a4]">
          <CheckCircle2 className="w-3 h-3" />
          <span>Living Note Document</span>
        </div>
        <span className="text-[#71717a]">Auto-Synced to SCONES</span>
      </div>
    </div>
  );
}
