// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_edges_MilestoneEdge"
// purpose: "Milestone Flow Edge with purple directional arrow and centered badge via EdgeLabelRenderer"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { BaseEdge, EdgeProps, EdgeLabelRenderer, getBezierPath, MarkerType } from '@xyflow/react';

export default function MilestoneEdge({
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
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const displayLabel =
    label ||
    ((data as Record<string, unknown> | undefined)?.label as string) ||
    ((data as Record<string, unknown> | undefined)?.milestone as string) ||
    'Milestone';

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd || MarkerType.ArrowClosed}
        style={{
          stroke: '#a855f7',
          strokeWidth: 2,
          ...style,
        }}
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
        >
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-slate-950/90 text-purple-300 border border-purple-500/50 text-[10px] font-mono font-medium shadow-lg backdrop-blur-sm">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
            <span>{displayLabel}</span>
          </div>
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
