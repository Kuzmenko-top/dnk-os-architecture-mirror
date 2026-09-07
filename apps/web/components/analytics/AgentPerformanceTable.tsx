// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_agent_performance_table"
// purpose: "Render agent performance table with specific runs, success rates, and task statistics"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-12"
// --- END DNK-MRH-HEADER ---

import React from 'react';

interface AgentPerformance {
  agent_id: string;
  agent_name: string;
  total_runs: number;
  success_rate: number;
  avg_duration_seconds: number;
  tasks_count: number;
}

interface AgentPerformanceTableProps {
  agents: AgentPerformance[];
}

export default function AgentPerformanceTable({ agents }: AgentPerformanceTableProps) {
  return (
    <div className="bg-slate-900/30 border border-slate-800/60 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-md">
      <div className="p-5 border-b border-slate-800/60 bg-slate-900/20">
        <h3 className="text-base font-bold text-white tracking-wide">💼 Продуктивність Агентів</h3>
        <p className="text-xs text-slate-500 font-medium">Статистика успішності за окремими агентами</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800/60 text-slate-400 text-xs font-bold bg-slate-900/10">
              <th className="p-4">Назва Агента / ID</th>
              <th className="p-4">Запуски</th>
              <th className="p-4">Успішність</th>
              <th className="p-4">Середня Тривалість</th>
              <th className="p-4">Кількість Тасок</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/30">
            {agents.map((agent) => (
              <tr key={agent.agent_id} className="text-slate-300 hover:bg-slate-800/20 transition-all text-sm">
                <td className="p-4 flex flex-col gap-0.5">
                  <span className="font-extrabold text-white">{agent.agent_name}</span>
                  <span className="text-[10px] text-slate-500 font-mono tracking-tight">{agent.agent_id}</span>
                </td>
                <td className="p-4 font-bold">{agent.total_runs}</td>
                <td className="p-4">
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${
                          agent.success_rate >= 0.9 ? 'bg-emerald-500' : agent.success_rate >= 0.75 ? 'bg-blue-500' : 'bg-rose-500'
                        }`} 
                        style={{ width: `${agent.success_rate * 100}%` }}
                      />
                    </div>
                    <span className="font-mono text-xs font-semibold">{(agent.success_rate * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="p-4 font-mono text-xs text-slate-400 font-medium">{agent.avg_duration_seconds.toFixed(1)} с</td>
                <td className="p-4">
                  <span className="px-2 py-0.5 bg-slate-800 text-slate-400 text-xs rounded-md font-bold">{agent.tasks_count}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
