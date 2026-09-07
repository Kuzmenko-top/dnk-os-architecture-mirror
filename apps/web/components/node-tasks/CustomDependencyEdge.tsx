// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/node-tasks/CustomDependencyEdge.tsx"
// purpose: "Custom ReactFlow Edge component with relationship styling, hover tooltips, and interactive removal"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.1.0"
// updated_at: "2026-09-06"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { memo } from 'react';
import {
  EdgeProps,
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
} from '@xyflow/react';
import { X, Info, Flame } from 'lucide-react';
import { DependencyType } from '@/types/nodeTasks';
import { useNodeTasksStore } from '@/store/nodeTasksStore';

interface EdgeCustomData {
  dependency_type?: DependencyType;
  description?: string;
  is_satisfied?: boolean;
}

export const CustomDependencyEdge = memo(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  data,
  markerEnd,
}: EdgeProps) => {
  const edgeData = (data || {}) as EdgeCustomData;
  const depType = edgeData.dependency_type || 'depends_on';
  const isSatisfied = edgeData.is_satisfied ?? true;
  const deleteEdge = useNodeTasksStore((s) => s.deleteEdge);
  const showCriticalPath = useNodeTasksStore((s) => s.showCriticalPath);
  const criticalEdgeIds = useNodeTasksStore((s) => s.criticalEdgeIds);

  const isCriticalEdge = showCriticalPath && criticalEdgeIds.includes(id);

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  // Determine colors & stroke styles
  let strokeColor = '#38bdf8'; // sky-400
  let strokeDasharray = undefined;
  let labelBg = 'bg-zinc-800 text-zinc-300 border-zinc-700';

  if (isCriticalEdge) {
    strokeColor = '#f43f5e'; // rose-500
    labelBg = 'bg-rose-950 text-rose-200 border-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.5)]';
  } else if (depType === 'depends_on') {
    if (!isSatisfied) {
      strokeColor = '#f43f5e'; // rose-500
      strokeDasharray = '5 5';
      labelBg = 'bg-rose-950 text-rose-300 border-rose-700/60';
    } else {
      strokeColor = '#10b981'; // emerald-500
      labelBg = 'bg-emerald-950 text-emerald-300 border-emerald-700/60';
    }
  } else if (depType === 'spawns_from') {
    strokeColor = '#c084fc'; // purple-400
    strokeDasharray = '4 4';
    labelBg = 'bg-purple-950 text-purple-300 border-purple-700/60';
  } else if (depType === 'blocks') {
    strokeColor = '#ef4444'; // red-500
    strokeDasharray = '6 3';
    labelBg = 'bg-red-950 text-red-300 border-red-700/60';
  } else if (depType === 'relates_to') {
    strokeColor = '#71717a'; // zinc-500
    strokeDasharray = '3 3';
    labelBg = 'bg-zinc-850 text-zinc-400 border-zinc-700';
  }

  const customStyle: React.CSSProperties = {
    ...style,
    stroke: strokeColor,
    strokeWidth: isCriticalEdge ? 3.5 : 2,
    strokeDasharray: isCriticalEdge ? undefined : strokeDasharray,
    filter: isCriticalEdge ? 'drop-shadow(0 0 6px rgba(244,63,94,0.8))' : undefined,
    opacity: showCriticalPath && !isCriticalEdge ? 0.35 : 1,
  };

  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={customStyle} />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'all',
          }}
          className="group relative flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[9px] font-mono border border-zinc-800/80 bg-zinc-950/90 backdrop-blur-sm shadow-md transition-all duration-150 select-none hover:border-zinc-600 hover:scale-105"
        >
          <span className={`px-1.5 py-0.5 rounded-full border text-[9px] flex items-center gap-1 ${labelBg}`}>
            {isCriticalEdge && <Flame className="w-2.5 h-2.5 text-rose-300 animate-pulse" />}
            {depType.replace('_', ' ')}
          </span>

          {/* Description tooltip on hover */}
          {edgeData.description && (
            <div className="relative group/tooltip">
              <Info className="w-2.5 h-2.5 text-zinc-500 hover:text-cyan-300 cursor-help" />
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover/tooltip:block w-48 p-2 rounded-lg bg-zinc-900 border border-zinc-700 text-[10px] font-sans text-zinc-200 shadow-xl z-50 pointer-events-none">
                {edgeData.description}
              </div>
            </div>
          )}

          {/* Delete edge button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              deleteEdge(id);
            }}
            title="Delete dependency link"
            className="hidden group-hover:flex items-center justify-center w-3.5 h-3.5 rounded-full bg-red-900/80 text-red-200 hover:bg-red-600 transition-colors"
          >
            <X className="w-2.5 h-2.5" />
          </button>
        </div>
      </EdgeLabelRenderer>
    </>
  );
});

CustomDependencyEdge.displayName = 'CustomDependencyEdge';
