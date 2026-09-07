// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_ApprovalNode"
// purpose: "Human Approval Gate Node enforcing explicit authorization before executing high-risk operations"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { ShieldAlert, ShieldCheck, Check, X, Lock, AlertTriangle } from 'lucide-react';

export default function ApprovalNode({ data, selected }: NodeProps) {
  const nodeData = (data || {}) as Record<string, any>;
  const [approved, setApproved] = useState(nodeData.state === 'approved');
  const actionTarget = String(nodeData.config?.action || 'shopify.theme.deploy');

  const handleApprove = () => {
    setApproved(true);
    if (typeof nodeData.onApprove === 'function') nodeData.onApprove();
  };

  const handleReject = () => {
    setApproved(false);
    if (typeof nodeData.onReject === 'function') nodeData.onReject();
  };

  return (
    <div className={`w-[320px] rounded-2xl bg-gradient-to-b from-amber-950/90 via-slate-900/90 to-slate-950/90 backdrop-blur-xl border border-amber-500/60 p-4 text-white shadow-2xl transition-all ${selected ? 'ring-2 ring-amber-400 scale-[1.02]' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3 bg-amber-400 border-2 border-white rounded-full" />
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-emerald-400 border-2 border-white rounded-full" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-amber-500/30 pb-2 mb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-300">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <span className="font-bold text-xs uppercase tracking-wider text-amber-300 font-mono">
            Approval Gate
          </span>
        </div>
        <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-rose-950/80 text-rose-300 border border-rose-500/40 font-mono font-bold">
          High Risk
        </span>
      </div>

      {/* Title */}
      <h4 className="font-bold text-sm text-slate-100 mb-1">
        {String(nodeData.title || 'Release Authorization Required')}
      </h4>
      <p className="text-[11px] text-slate-400 mb-3 leading-snug">
        Action requires explicit human sign-off before modifying external production assets.
      </p>

      {/* Action Target Details */}
      <div className="p-2.5 rounded-xl bg-slate-950/70 border border-amber-900/40 text-[11px] font-mono mb-3.5">
        <div className="flex justify-between items-center text-slate-400">
          <span>Action:</span>
          <span className="text-amber-300 font-bold">{actionTarget}</span>
        </div>
      </div>

      {/* Action Buttons */}
      {approved ? (
        <div className="flex items-center justify-center gap-2 py-2 rounded-xl bg-emerald-950/80 border border-emerald-500/60 text-emerald-300 text-xs font-bold">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Authorized by Operator</span>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <button
            onClick={handleApprove}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/30 transition-all cursor-pointer"
          >
            <Check className="w-3.5 h-3.5 stroke-[3]" />
            <span>Approve Action</span>
          </button>
          <button
            onClick={handleReject}
            className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-rose-950 hover:text-rose-300 text-slate-400 text-xs font-semibold border border-slate-700 transition-all cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
