// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_MindMapGoalNode"
// purpose: "Mind Map Goal Card (Emerald green card) with deadline tracking, progress bar, and quantifiable KPIs"
// author: "DNK-e.com Maksym & Antigravity Mentor"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { NodeProps } from '@xyflow/react';
import { Target, Calendar, TrendingUp, Plus } from 'lucide-react';
import BaseMindMapNode from './BaseMindMapNode';
import { useCanvasStore } from '../../../store/canvasStore';

export interface MindMapGoalData {
  title?: string;
  description?: string;
  deadline?: string;
  progress?: number; // 0 - 100
  metrics?: string[];
  status?: string;
  [key: string]: any;
}

export default function MindMapGoalNode(props: NodeProps) {
  const { id, data } = props;
  const nodeData = (data || {}) as MindMapGoalData;
  const updateNodeData = useCanvasStore((state) => state.updateNodeData);

  const deadline = nodeData.deadline || '2026-09-30';
  const progress = Math.min(100, Math.max(0, nodeData.progress ?? 45));
  const metrics = nodeData.metrics || ['$10k MRR', '100 Active Users'];

  const handleUpdateProgress = (e: React.ChangeEvent<HTMLInputElement>) => {
    updateNodeData(id, { progress: Number(e.target.value) });
  };

  return (
    <BaseMindMapNode
      {...props}
      themeColor="emerald"
      icon={<Target className="w-4 h-4" />}
      categoryLabel="Goal"
    >
      <div className="flex flex-col gap-2.5">
        {/* Progress Bar & Percentage */}
        <div>
          <div className="flex items-center justify-between text-[11px] mb-1">
            <span className="text-emerald-300/80 font-medium">Target Progress</span>
            <span className="font-mono font-bold text-emerald-400">{progress}%</span>
          </div>
          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <input
            type="range"
            min={0}
            max={100}
            value={progress}
            onChange={handleUpdateProgress}
            className="w-full mt-1 accent-emerald-400 cursor-pointer h-1 bg-transparent"
          />
        </div>

        {/* Deadline & Target Metrics */}
        <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[10px]">
          <div className="flex items-center gap-1 text-slate-400">
            <Calendar className="w-3 h-3 text-emerald-400" />
            <span className="font-mono">{deadline}</span>
          </div>
          <div className="flex items-center gap-1 text-emerald-300/90 font-medium">
            <TrendingUp className="w-3 h-3" />
            <span>{metrics[0] || 'Target KPI'}</span>
          </div>
        </div>
      </div>
    </BaseMindMapNode>
  );
}
