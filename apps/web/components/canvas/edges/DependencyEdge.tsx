// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_edges_DependencyEdge"
// purpose: "Dependency Flow Edge with blocked state dashed styling and directional arrow"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { BaseEdge, EdgeProps, getSmoothStepPath, MarkerType } from '@xyflow/react';

export interface DependencyEdgeData {
  isBlocked?: boolean;
  blocked?: boolean;
  status?: string;
  label?: string;
  [key: string]: unknown;
}

export default function DependencyEdge({
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
  data,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const edgeData = data as DependencyEdgeData | undefined;
  const isBlocked = Boolean(
    edgeData?.isBlocked ||
    edgeData?.blocked ||
    edgeData?.status === 'blocked'
  );

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd || MarkerType.ArrowClosed}
        style={{
          stroke: '#ef4444',
          strokeWidth: 2,
          ...(isBlocked ? { strokeDasharray: '5 5' } : {}),
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
            <span className="px-2 py-0.5 rounded-full bg-slate-900/90 text-red-300 border border-red-500/40 text-[9px] font-mono shadow-md">
              {label}
            </span>
          </div>
        </foreignObject>
      )}
    </>
  );
}
