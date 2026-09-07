// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_edges_RelationEdge"
// purpose: "Smooth Bezier Relation Edge in cyan for semantic associations"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { BaseEdge, EdgeProps, getBezierPath } from '@xyflow/react';

export default function RelationEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  label,
  markerEnd,
  style,
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
        style={{
          stroke: '#06b6d4',
          strokeWidth: 2,
          ...style,
        }}
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
            <span className="px-2 py-0.5 rounded-full bg-slate-900/90 text-cyan-300 border border-cyan-500/40 text-[9px] font-mono shadow-md">
              {label}
            </span>
          </div>
        </foreignObject>
      )}
    </>
  );
}
