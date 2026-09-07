// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_edges_ControlFlowEdge"
// purpose: "Directed Control Flow Execution Edge for DNK Canvas"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { BaseEdge, EdgeProps, getSmoothStepPath } from '@xyflow/react';

export default function ControlFlowEdge({
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
        style={{ stroke: '#a855f7', strokeWidth: 2 }}
      />
      {label && (
        <foreignObject
          width={120}
          height={24}
          x={labelX - 60}
          y={labelY - 12}
          className="pointer-events-none"
        >
          <div className="flex items-center justify-center h-full">
            <span className="px-2 py-0.5 rounded-full bg-slate-900/90 text-purple-300 border border-purple-500/40 text-[9px] font-mono shadow-md">
              {label}
            </span>
          </div>
        </foreignObject>
      )}
    </>
  );
}
