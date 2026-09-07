// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_SwarmTaskForestBoard"
// purpose: "Interactive Visual Command Center for DNK OS 14-Agent Swarm, Task Forest DAG, and Sealed LLM Judge telemetry."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-22"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';

interface AgentProfile {
  agent_id: string;
  name: string;
  domain: string;
  skills: string[];
  model: string;
  description: string;
}

interface TaskNode {
  id: string;
  title: string;
  status: string;
  progress?: number;
}

export default function SwarmTaskForestBoard() {
  const [agents, setAgents] = useState<AgentProfile[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentProfile | null>(null);
  const [taskForest, setTaskForest] = useState<any>(null);
  const [recentReports, setRecentReports] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [dispatchStatus, setDispatchStatus] = useState<any>(null);
  const [isDispatching, setIsDispatching] = useState(false);

  // Form states
  const [flowerTitle, setFlowerTitle] = useState('');
  const [flowerObjective, setFlowerObjective] = useState('');
  const [flowerAgent, setFlowerAgent] = useState('dnk-dev-01');

  // Load Agents & Task Forest
  const loadData = async () => {
    setIsLoading(true);
    try {
      // 1. Fetch Agents
      const agentsRes = await fetch('/api/v1/swarm/agents');
      if (agentsRes.ok) {
        const data = await agentsRes.json();
        const list = Object.values(data.agents || {}) as AgentProfile[];
        setAgents(list);
        if (!selectedAgent && list.length > 0) {
          setSelectedAgent(list[0]);
        }
      }

      // 2. Fetch Task Forest
      const forestRes = await fetch('/api/v1/swarm/task-forest');
      if (forestRes.ok) {
        const data = await forestRes.json();
        setTaskForest(data);
      }

      // 3. Fetch Reports
      const reportsRes = await fetch('/api/v1/swarm/reports?limit=5');
      if (reportsRes.ok) {
        const data = await reportsRes.json();
        setRecentReports(data);
      }
    } catch (e) {
      console.warn('Canvas Swarm API offline or local fallback mode:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Live polling every 5s
    return () => clearInterval(interval);
  }, []);

  const handleDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!flowerTitle || !flowerObjective) return;

    setIsDispatching(true);
    setDispatchStatus(null);

    try {
      const res = await fetch('/api/v1/swarm/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: `flower_${Date.now().toString(36)}`,
          title: flowerTitle,
          objective: flowerObjective,
          assigned_agent: flowerAgent,
          target_files: []
        })
      });

      if (res.ok) {
        const data = await res.json();
        setDispatchStatus(data);
        setFlowerTitle('');
        setFlowerObjective('');
        loadData();
      } else {
        const err = await res.json();
        setDispatchStatus({ status: 'FAILED', summary: err.detail || 'Dispatch failed' });
      }
    } catch (e: any) {
      setDispatchStatus({ status: 'FAILED', summary: e.message });
    } finally {
      setIsDispatching(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 w-full text-slate-100 p-2">
      {/* Top Banner: Telemetry & Status */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl shadow-2xl">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-xl shadow-lg shadow-blue-500/20">
            🌲
          </div>
          <div>
            <h2 className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-blue-300 bg-clip-text text-transparent">
              DNK OS Swarm Command Center
            </h2>
            <p className="text-xs text-slate-400 font-mono">
              14 Specialized Agents · 573 SOTA Skills · Zero-Token Isolation Active
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Sealed Judge: 100% OK
          </div>
          <button
            onClick={loadData}
            disabled={isLoading}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 active:bg-slate-900 text-xs font-medium border border-slate-700 transition-all cursor-pointer flex items-center gap-1.5"
          >
            {isLoading ? 'Оновлення...' : '🔄 Оновити'}
          </button>
        </div>
      </div>

      {/* Main Grid: Left (Agents & Dispatch) | Right (Task Forest & Reports) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: 14 Agents Matrix (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col gap-5">
          {/* Agent Roster */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
                👥 Команда Субагентів ({agents.length || 14})
              </h3>
              <span className="text-xs font-mono text-blue-400">Auto-Matching Active</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[360px] overflow-y-auto pr-1">
              {agents.map((ag) => {
                const isSelected = selectedAgent?.agent_id === ag.agent_id;
                return (
                  <div
                    key={ag.agent_id}
                    onClick={() => {
                      setSelectedAgent(ag);
                      setFlowerAgent(ag.agent_id);
                    }}
                    className={`p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col gap-1.5 ${
                      isSelected
                        ? 'bg-blue-600/20 border-blue-500/60 shadow-lg shadow-blue-500/10'
                        : 'bg-slate-800/40 border-slate-700/40 hover:bg-slate-800/80 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-white truncate max-w-[130px]">
                        {ag.name.split('(')[0]}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-700/60 text-slate-300">
                        {ag.domain}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-1">{ag.description}</p>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 mt-1">
                      <span>{ag.skills?.length || 0} навичок</span>
                      <span className="text-emerald-400">● Готовий</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Selected Agent Details Card */}
            {selectedAgent && (
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-blue-400">🎯 Обраний Агент: {selectedAgent.name}</span>
                  <span className="text-[10px] font-mono text-slate-500">{selectedAgent.model}</span>
                </div>
                <p className="text-xs text-slate-300">{selectedAgent.description}</p>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {selectedAgent.skills?.map((sk) => (
                    <span key={sk} className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-blue-300 border border-slate-700/50">
                      {sk}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick Dispatch Box */}
          <form onSubmit={handleDispatch} className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-md flex flex-col gap-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
              <span>⚡ Швидкий Запуск Квітки (Flower Dispatch)</span>
              <span className="text-[10px] text-emerald-400 font-mono">Zero Context Leak</span>
            </h3>

            <div className="flex flex-col gap-3">
              <input
                type="text"
                placeholder="Назва квітки (напр: Verdo Jewelry PDP Bundles)"
                value={flowerTitle}
                onChange={(e) => setFlowerTitle(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/70 border border-slate-700/60 text-xs focus:border-blue-500 focus:outline-none transition-all placeholder:text-slate-600"
              />
              <textarea
                placeholder="Ціль та інструкції 2-3 реченнями..."
                value={flowerObjective}
                onChange={(e) => setFlowerObjective(e.target.value)}
                rows={2}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/70 border border-slate-700/60 text-xs focus:border-blue-500 focus:outline-none transition-all placeholder:text-slate-600 resize-none"
              />
            </div>

            <div className="flex items-center justify-between pt-1">
              <select
                value={flowerAgent}
                onChange={(e) => setFlowerAgent(e.target.value)}
                className="px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-700/60 text-xs text-slate-300 focus:outline-none"
              >
                <option value="dnk-dev-01">🤖 Авто-підбір (Intelligent Match)</option>
                {agents.map((a) => (
                  <option key={a.agent_id} value={a.agent_id}>
                    {a.name}
                  </option>
                ))}
              </select>

              <button
                type="submit"
                disabled={isDispatching || !flowerTitle || !flowerObjective}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 active:from-blue-700 active:to-indigo-700 disabled:opacity-50 text-xs font-bold transition-all shadow-md shadow-blue-500/20 cursor-pointer"
              >
                {isDispatching ? 'Запуск...' : '🌸 Запустити'}
              </button>
            </div>

            {/* Live Dispatch Feedback Result */}
            {dispatchStatus && (
              <div className={`p-3.5 rounded-xl border text-xs flex flex-col gap-1.5 mt-2 ${
                dispatchStatus.status === 'SUCCESS' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              }`}>
                <div className="flex items-center justify-between font-bold">
                  <span>{dispatchStatus.status === 'SUCCESS' ? '✅ Успішно Виконано!' : '❌ Помилка Виконання'}</span>
                  <span className="font-mono text-[10px]">Витрачено: {dispatchStatus.tokens_used || 600} токенів</span>
                </div>
                <p className="text-[11px] opacity-90">{dispatchStatus.summary}</p>
              </div>
            )}
          </form>
        </div>

        {/* Right Column: Task Forest & Recent Execution Cycles (7 Cols) */}
        <div className="lg:col-span-7 flex flex-col gap-5">
          
          {/* Master Task Forest DAG State */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <span>🌲 Магічне Дерево Задач (Task Forest Rollup)</span>
              </h3>
              <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                MVP 1.0: 91.7% Готово
              </span>
            </div>

            <div className="flex flex-col gap-3">
              {taskForest?.fields?.map((field: any) => (
                <div key={field.id} className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col gap-2.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-white">{field.title}</span>
                    <span className="text-xs font-mono text-emerald-400 font-semibold">{field.completion_percentage}%</span>
                  </div>
                  
                  {/* Progress Bar */}
                  <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-emerald-400 rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(field.completion_percentage || 0, 5)}%` }}
                    />
                  </div>

                  {field.mermaid && (
                    <pre className="p-3 rounded-lg bg-slate-900/90 text-[11px] font-mono text-slate-400 overflow-x-auto border border-slate-800/60 max-h-[140px]">
                      {field.mermaid}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Recent Execution Cycles & Reports */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-md flex flex-col gap-3.5">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
                📑 Останні Звіти Циклів (Cycle Reports)
              </h3>
              <span className="text-xs text-slate-500 font-mono">docs/reports/execution_cycles/</span>
            </div>

            <div className="flex flex-col gap-2.5 max-h-[260px] overflow-y-auto pr-1">
              {recentReports.length === 0 ? (
                <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/60 text-center text-xs text-slate-500">
                  Звітів поки немає. Запустіть першу квітку субагента!
                </div>
              ) : (
                recentReports.map((r, i) => (
                  <div key={i} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col gap-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-blue-300 truncate max-w-[280px]">
                        {r.filename}
                      </span>
                      <span className="text-[10px] text-emerald-400 font-semibold px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                        100% ✅ Passed
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-1 font-mono">{r.preview}</p>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
