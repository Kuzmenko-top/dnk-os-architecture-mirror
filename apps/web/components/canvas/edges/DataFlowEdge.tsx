// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_edges_DataFlowEdge"
// purpose: "Animated Data Flow Edge rendering data streaming between canvas nodes"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { BaseEdge, EdgeProps, getBezierPath } from '@xyflow/react';

export default function DataFlowEdge({
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
  const [edgePath, labelX, labelY] = getBezierPath({
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
        style={{ stroke: '#818cf8', strokeWidth: 2, strokeDasharray: '6,6' }}
        className="animate-pulse"
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
            <span className="px-2 py-0.5 rounded-full bg-slate-900/90 text-indigo-300 border border-indigo-500/40 text-[9px] font-mono shadow-md">
              {label}
            </span>
          </div>
        </foreignObject>
      )}
    </>
  );
}
