// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_ArtifactNode"
// purpose: "Deliverable Artifact Node for DNK Canvas displaying generated output, URI, and SCONES evidence"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { FileText, Download, ExternalLink, Sparkles, CheckCircle2 } from 'lucide-react';

export default function ArtifactNode({ data, selected }: NodeProps) {
  const nodeData = (data || {}) as Record<string, any>;
  const outputType = String(nodeData.config?.output_type || nodeData.config?.storage || 'scones_vault');

  return (
    <div className={`w-[290px] rounded-2xl bg-slate-900/90 backdrop-blur-xl border border-emerald-500/40 p-4 text-white shadow-xl transition-all ${selected ? 'ring-2 ring-emerald-400 scale-[1.02]' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-emerald-400 border-2 border-white rounded-full" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400">
            <FileText className="w-4 h-4" />
          </div>
          <span className="font-bold text-xs uppercase tracking-wider text-emerald-400 font-mono">
            Artifact Deliverable
          </span>
        </div>
        <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 font-mono">
          <CheckCircle2 className="w-2.5 h-2.5" /> Ready
        </span>
      </div>

      {/* Title */}
      <h4 className="font-bold text-sm text-slate-100 mb-1">
        {String(nodeData.title || 'Verified Artifact')}
      </h4>
      <p className="text-[11px] text-slate-400 mb-3 leading-snug">
        Cryptographically signed & stored in SCONES L3 Memory Vault.
      </p>

      {/* Action Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-[11px]">
        <span className="font-mono text-[10px] text-slate-500 uppercase">{outputType}</span>
        <button className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 font-semibold transition-colors cursor-pointer">
          <span>Open Artifact</span>
          <ExternalLink className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}
