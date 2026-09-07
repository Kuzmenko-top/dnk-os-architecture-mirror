// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_edges_ApprovalFlowEdge"
// purpose: "Security Gated Approval Flow Edge rendering lock badge and amber pulse"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { BaseEdge, EdgeProps, getSmoothStepPath } from '@xyflow/react';
import { Lock } from 'lucide-react';

export default function ApprovalFlowEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  label,
  markerEnd,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{ stroke: '#f59e0b', strokeWidth: 2.5, strokeDasharray: '4,4' }}
        className="animate-pulse"
      />
      <foreignObject
        width={130}
        height={26}
        x={labelX - 65}
        y={labelY - 13}
        className="pointer-events-none"
      >
        <div className="flex items-center justify-center h-full">
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-950 text-amber-300 border border-amber-500/50 text-[9px] font-mono shadow-lg font-bold">
            <Lock className="w-2.5 h-2.5 text-amber-400" />
            <span>{label || 'Approval Gate'}</span>
          </span>
        </div>
      </foreignObject>
    </>
  );
}
