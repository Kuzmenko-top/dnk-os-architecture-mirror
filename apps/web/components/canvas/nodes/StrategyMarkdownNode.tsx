// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_StrategyMarkdownNode"
// purpose: "CapCut Strategy Markdown Note Card (Card 1) supporting header bullets, interactive task checklist, and syntax-highlighted code blocks"
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
  MoreVertical, 
  CheckSquare, 
  Square, 
  Code2, 
  Sparkles,
  Copy,
  Check
} from 'lucide-react';
import { CopilotToolbar } from '../../../src/canvas/copilot/CopilotToolbar';

export default function StrategyMarkdownNode({ id, data, selected }: NodeProps) {
  const hypotheses = data?.hypotheses as string[] | undefined;
  const title = data?.title as string | undefined;

  const [tasks, setTasks] = useState([
    { id: '1', text: 'Tasks in a template', completed: true },
    { id: '2', text: 'Tasks with complete', completed: false },
    { id: '3', text: 'Tasks connected', completed: false },
  ]);

  const [copied, setCopied] = useState(false);

  const toggleTask = (id: string) => {
    setTasks(prev => prev.map(t => t.id === id ? { ...t, completed: !t.completed } : t));
  };

  const copyCode = () => {
    navigator.clipboard.writeText("const plan = {\n  key: 'value'\n};");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`w-[320px] rounded-2xl bg-[#121620]/95 backdrop-blur-2xl border border-[#232938] p-4 text-slate-200 shadow-2xl transition-all font-sans ${
      selected ? 'border-indigo-500 ring-2 ring-indigo-500/30 shadow-[0_0_30px_rgba(99,102,241,0.25)]' : ''
    }`}>
      {/* 4-Way Smooth Handles */}
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-indigo-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#818cf8]" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-indigo-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#818cf8]" />
      <Handle type="target" position={Position.Left} id="left" className="w-2.5 h-2.5 bg-indigo-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#818cf8]" />
      <Handle type="source" position={Position.Right} id="right" className="w-2.5 h-2.5 bg-indigo-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#818cf8]" />

      {/* Header */}
      <div className="flex items-center justify-between mb-2 pb-2 border-b border-[#232938]">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-indigo-400" />
          <span className="font-bold text-sm text-white">{title || 'Project Alpha Strategy'}</span>
        </div>
        <button className="p-1 rounded text-slate-500 hover:text-white transition-colors cursor-pointer">
          <MoreVertical className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Category Pill Badge */}
      <div className="mb-3">
        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#1c2230] text-indigo-300 border border-indigo-500/30">
          Text/Markdown
        </span>
      </div>

      {/* Header & Bullets */}
      <div className="mb-3 text-xs">
        <span className="font-semibold text-white block mb-1 text-xs">Goal & Hypotheses</span>
        {hypotheses ? (
          <ul className="space-y-1 text-indigo-300 pl-3 list-disc text-[11px] leading-relaxed">
            {hypotheses.map((h: string, i: number) => (
              <li key={i}>{h}</li>
            ))}
          </ul>
        ) : (
          <ul className="space-y-1 text-slate-400 pl-3 list-disc text-[11px] leading-relaxed">
            <li>Impact on online strategy</li>
            <li>Develop experience</li>
            <li>Culture and implementation</li>
          </ul>
        )}
      </div>

      {/* Tasks Checklist */}
      <div className="mb-3 text-xs">
        <span className="font-semibold text-white block mb-1 text-xs">Tasks</span>
        <div className="space-y-1.5">
          {tasks.map(task => (
            <div
              key={task.id}
              onClick={() => toggleTask(task.id)}
              className="flex items-center gap-2 text-[11px] text-slate-300 cursor-pointer hover:text-white transition-colors"
            >
              {task.completed ? (
                <div className="w-3.5 h-3.5 rounded bg-indigo-600 text-white flex items-center justify-center text-[9px] font-bold">
                  ✓
                </div>
              ) : (
                <div className="w-3.5 h-3.5 rounded border border-slate-600 hover:border-indigo-400" />
              )}
              <span className={task.completed ? 'text-slate-400 line-through' : ''}>{task.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Code Snippet Box */}
      <div className="rounded-xl bg-[#090b10] border border-[#1a1f2c] p-2.5 font-mono text-[11px] text-emerald-400 relative group">
        <div className="flex items-center justify-between text-[9px] text-slate-500 mb-1 font-sans">
          <span>javascript</span>
          <button onClick={copyCode} className="text-slate-500 hover:text-white transition-colors cursor-pointer">
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          </button>
        </div>
        <pre className="text-slate-300">
          <span className="text-pink-400">const</span> plan = {'{\n'}
          {'  '}key: <span className="text-emerald-300">'value'</span>
          {'\n}'};
        </pre>
      </div>

      <CopilotToolbar
        nodeId={id}
        nodeType="StrategyMarkdownNode"
        defaultAgentId="dnk_marketing_cmo"
      />
    </div>
  );
}
