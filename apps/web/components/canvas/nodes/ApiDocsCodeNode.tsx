// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_ApiDocsCodeNode"
// purpose: "CapCut API Docs & Code Note Card (Card 6) supporting syntax-highlighted code blocks, endpoint documentation, and MCP runner triggers"
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
  Code2, 
  MoreVertical, 
  Copy, 
  Check, 
  Play, 
  Terminal 
} from 'lucide-react';
import { CopilotToolbar } from '../../../src/canvas/copilot/CopilotToolbar';

export default function ApiDocsCodeNode({ id, data, selected }: NodeProps) {
  const code = data?.code as string | undefined;
  const title = data?.title as string | undefined;

  const [copied, setCopied] = useState(false);

  const copyCode = () => {
    navigator.clipboard.writeText("const plan = {\n  key: 'value'\n};");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`w-[300px] rounded-2xl bg-[#121620]/95 backdrop-blur-2xl border border-[#232938] p-4 text-slate-200 shadow-2xl transition-all font-sans ${
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
          <Code2 className="w-4 h-4 text-indigo-400" />
          <span className="font-bold text-sm text-white">{title || 'API Docs'}</span>
        </div>
        <button className="p-1 rounded text-slate-500 hover:text-white transition-colors cursor-pointer">
          <MoreVertical className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Category Pill Badge */}
      <div className="mb-3">
        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#1c2230] text-indigo-300 border border-indigo-500/30">
          Text/Code
        </span>
      </div>

      <p className="text-[11px] text-slate-400 mb-3 font-sans leading-relaxed">
        Text/code snippet for authorized endpoint payload schema.
      </p>

      {/* Code Snippet Box */}
      <div className="rounded-xl bg-[#090b10] border border-[#1a1f2c] p-3 font-mono text-[11px] text-emerald-400 relative group">
        <div className="flex items-center justify-between text-[9px] text-slate-500 mb-1.5 font-sans">
          <span>payload.json</span>
          <button onClick={copyCode} className="text-slate-500 hover:text-white transition-colors cursor-pointer">
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          </button>
        </div>
        <pre className="text-slate-300 overflow-x-auto whitespace-pre-wrap">
          {code || `const plan = {\n  key: 'value'\n};`}
        </pre>
      </div>

      <CopilotToolbar
        nodeId={id}
        nodeType="ApiDocsCodeNode"
        defaultAgentId="dnk_shopify"
      />
    </div>
  );
}
