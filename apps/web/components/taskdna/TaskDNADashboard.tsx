// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_taskdna_TaskDNADashboard"
// purpose: "Main TaskDNA Dashboard component for DNK OS Visual Workspace (DNK-OS-001)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-23"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import CanvasGraphViewer from './CanvasGraphViewer';

interface TaskSummary {
  id: string;
  workspace_id: string;
  title: string;
  phase: string;
  status: string;
  owner: string;
  supervisor_name: string;
  worker_name: string;
  branch: string;
  pr_number?: number;
  pr_state?: string;
  gates_passed: number;
  gates_total: number;
  dod_percentage: number;
  updated_at: string;
}

interface ValidationGate {
  id: string;
  name: string;
  status: string;
  evidence_ref: string;
  completed_at?: string;
}

interface TaskDNADetail {
  id: string;
  workspace_id: string;
  title: string;
  phase: string;
  status: string;
  owner: string;
  supervisor: { id: string; name: string; role: string; status: string };
  worker: { id: string; name: string; role: string; status: string };
  git_context: {
    repository: string;
    branch: string;
    base_branch: string;
    base_sha: string;
    head_sha: string;
  };
  validation_gates: ValidationGate[];
  pull_request?: {
    number: number;
    title: string;
    state: string;
    head_sha: string;
    checks_status: string;
    base_branch?: string;
  };
  dod_progress: { total: number; completed: number; percentage: number };
  created_at: string;
  updated_at: string;
}

interface TaskTimelineEvent {
  id: string;
  timestamp: string;
  event_type: string;
  actor: string;
  summary: string;
}

interface TaskDNADashboardProps {
  workspaceId: string;
}

export default function TaskDNADashboard({ workspaceId }: TaskDNADashboardProps) {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [taskDetail, setTaskDetail] = useState<TaskDNADetail | null>(null);
  const [timeline, setTimeline] = useState<TaskTimelineEvent[]>([]);
  const [graphData, setGraphData] = useState<any>(null);

  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch task list with X-Workspace-ID header
  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/tasks?workspace_id=${workspaceId}`, {
        headers: {
          'X-Workspace-ID': workspaceId,
          'Content-Type': 'application/json',
        },
      });

      if (!res.ok) {
        if (res.status === 403) {
          throw new Error('403 Forbidden: Missing or invalid X-Workspace-ID security gate header');
        }
        throw new Error(`Failed to load tasks: HTTP ${res.status}`);
      }

      const data: TaskSummary[] = await res.json();
      setTasks(data);

      if (data.length > 0 && !selectedTaskId) {
        setSelectedTaskId(data[0].id);
      }
    } catch (e: any) {
      setError(e.message || 'Error loading tasks');
    } finally {
      setLoading(false);
    }
  };

  // Fetch detail, timeline, and graph for selected task
  const fetchTaskDetail = async (id: string) => {
    try {
      const headers = { 'X-Workspace-ID': workspaceId };

      const [detailRes, timelineRes, graphRes] = await Promise.all([
        fetch(`/api/tasks/${id}`, { headers }),
        fetch(`/api/tasks/${id}/timeline`, { headers }),
        fetch(`/api/tasks/${id}/graph`, { headers }),
      ]);

      if (detailRes.ok) {
        setTaskDetail(await detailRes.json());
      }
      if (timelineRes.ok) {
        setTimeline(await timelineRes.json());
      }
      if (graphRes.ok) {
        setGraphData(await graphRes.json());
      }
    } catch (e) {
      console.error('Failed to load task details:', e);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [workspaceId]);

  useEffect(() => {
    if (selectedTaskId) {
      fetchTaskDetail(selectedTaskId);
    }
  }, [selectedTaskId, workspaceId]);

  const filteredTasks = tasks.filter((t: TaskSummary) => {
    const matchesStatus = filterStatus === 'ALL' || t.status.toUpperCase() === filterStatus.toUpperCase();
    const matchesQuery =
      searchQuery === '' ||
      t.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.title.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesQuery;
  });

  if (loading && tasks.length === 0) {
    return (
      <div className="flex h-96 items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-10 w-12 border-b-2 border-blue-500" />
          <div className="text-sm font-mono">Завантаження TaskDNA Dashboard...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-950/40 border border-rose-800/80 rounded-2xl text-rose-300 font-mono flex flex-col gap-3 shadow-2xl">
        <div className="flex items-center gap-2 text-lg font-bold">
          <span>🛡️ Security Gate Error</span>
        </div>
        <p className="text-sm text-rose-200">{error}</p>
        <button
          onClick={fetchTasks}
          className="self-start px-4 py-2 bg-rose-700 hover:bg-rose-600 text-white rounded-xl text-xs font-bold transition-all cursor-pointer"
        >
          Спробувати знову (Retry)
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Top Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900/60 border border-slate-800/80 rounded-2xl backdrop-blur-md flex flex-col gap-1 shadow-lg">
          <span className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider">
            Всього Задач (Total Tasks)
          </span>
          <span className="text-2xl font-black text-white">{tasks.length}</span>
          <span className="text-[10px] text-slate-400">Workspace: {workspaceId}</span>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800/80 rounded-2xl backdrop-blur-md flex flex-col gap-1 shadow-lg">
          <span className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider">
            Активні (In Progress)
          </span>
          <span className="text-2xl font-black text-blue-400">
            {tasks.filter((t) => t.status === 'IN_PROGRESS').length}
          </span>
          <span className="text-[10px] text-blue-400/80 font-mono">Active Phase Execution</span>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800/80 rounded-2xl backdrop-blur-md flex flex-col gap-1 shadow-lg">
          <span className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider">
            Завершені (Completed)
          </span>
          <span className="text-2xl font-black text-emerald-400">
            {tasks.filter((t) => t.status === 'COMPLETED').length}
          </span>
          <span className="text-[10px] text-emerald-400/80 font-mono">100% Gates Passed</span>
        </div>

        <div className="p-4 bg-slate-900/60 border border-slate-800/80 rounded-2xl backdrop-blur-md flex flex-col gap-1 shadow-lg">
          <span className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider">
            Gate Pass Rate
          </span>
          <span className="text-2xl font-black text-indigo-300">
            {tasks.reduce((a, b) => a + b.gates_passed, 0)} /{' '}
            {tasks.reduce((a, b) => a + b.gates_total, 0)}
          </span>
          <span className="text-[10px] text-indigo-400/80 font-mono">Fail-Closed Security</span>
        </div>
      </div>

      {/* Main Workspace Split: Task List & Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Task List / Navigator (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          {/* Filters & Search */}
          <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-2xl flex flex-col gap-3">
            <input
              type="text"
              placeholder="Пошук задачі за ID / Title..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />

            <div className="flex gap-2">
              {['ALL', 'IN_PROGRESS', 'COMPLETED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setFilterStatus(st)}
                  className={`flex-1 py-1.5 rounded-lg text-[10px] font-mono font-bold transition-all cursor-pointer ${
                    filterStatus === st
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-slate-800/60 text-slate-400 hover:text-white'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* Task Cards List */}
          <div className="flex flex-col gap-3">
            {filteredTasks.length === 0 ? (
              <div className="p-6 bg-slate-900/40 border border-slate-800/60 rounded-2xl text-center text-xs text-slate-500">
                Жодної задачі не знайдено
              </div>
            ) : (
              filteredTasks.map((task) => {
                const isSelected = selectedTaskId === task.id;
                return (
                  <div
                    key={task.id}
                    onClick={() => setSelectedTaskId(task.id)}
                    className={`p-4 rounded-2xl border transition-all cursor-pointer flex flex-col gap-2 shadow-md ${
                      isSelected
                        ? 'bg-blue-950/40 border-blue-500/80 ring-1 ring-blue-500/30'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-mono font-bold text-blue-400">{task.id}</span>
                      <span
                        className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                          task.status === 'COMPLETED'
                            ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                            : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                        }`}
                      >
                        {task.status}
                      </span>
                    </div>

                    <h4 className="font-bold text-sm text-white line-clamp-2 leading-snug">
                      {task.title}
                    </h4>

                    <div className="text-[11px] text-slate-400 font-mono truncate">
                      {task.phase}
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-2 border-t border-slate-800/60">
                      <span>
                        Gates: {task.gates_passed}/{task.gates_total}
                      </span>
                      <span>DoD: {task.dod_percentage}%</span>
                      {task.pr_number && (
                        <span className="text-indigo-400 font-bold">
                          PR #{task.pr_number} ({task.pr_state})
                        </span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Selected Task Detail View (8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          {taskDetail ? (
            <>
              {/* Task Detail Card Header */}
              <div className="p-6 bg-slate-900/60 border border-slate-800/80 rounded-2xl backdrop-blur-md flex flex-col gap-4 shadow-xl">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono font-bold px-2.5 py-1 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-lg">
                      {taskDetail.id}
                    </span>
                    <span className="text-xs font-mono text-slate-400">
                      Workspace: {taskDetail.workspace_id}
                    </span>
                  </div>

                  <span
                    className={`text-xs font-mono font-bold px-3 py-1 rounded-lg border uppercase ${
                      taskDetail.status === 'COMPLETED'
                        ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                        : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                    }`}
                  >
                    {taskDetail.status}
                  </span>
                </div>

                <div>
                  <h2 className="text-xl font-extrabold text-white leading-tight">
                    {taskDetail.title}
                  </h2>
                  <p className="text-xs text-slate-400 font-mono mt-1">{taskDetail.phase}</p>
                </div>

                {/* Agents & Owner Meta */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-800/80 text-xs">
                  <div>
                    <span className="text-slate-500 font-mono text-[10px] block">Owner:</span>
                    <span className="font-bold text-slate-200">{taskDetail.owner}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 font-mono text-[10px] block">
                      Supervisor Agent:
                    </span>
                    <span className="font-bold text-indigo-300">
                      🤖 {taskDetail.supervisor.name} ({taskDetail.supervisor.role})
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 font-mono text-[10px] block">Worker Agent:</span>
                    <span className="font-bold text-emerald-300">
                      ⚙️ {taskDetail.worker.name} ({taskDetail.worker.role})
                    </span>
                  </div>
                </div>

                {/* Git Context Banner */}
                <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl text-xs font-mono flex flex-wrap gap-4 items-center justify-between">
                  <div>
                    <span className="text-slate-500">Repo:</span>{' '}
                    <span className="text-slate-200 font-bold">
                      {taskDetail.git_context.repository}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Branch:</span>{' '}
                    <span className="text-blue-400 font-bold">
                      {taskDetail.git_context.branch}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">HEAD:</span>{' '}
                    <span className="text-indigo-300 font-bold">
                      {taskDetail.git_context.head_sha.substring(0, 9)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Validation Gates Table */}
              <div className="p-6 bg-slate-900/60 border border-slate-800/80 rounded-2xl backdrop-blur-md flex flex-col gap-4 shadow-xl">
                <h3 className="text-base font-extrabold text-white flex items-center justify-between">
                  <span>🛡️ Гейти Валідації (Validation Gates)</span>
                  <span className="text-xs font-mono font-bold text-slate-400">
                    {taskDetail.validation_gates.filter((g) => g.status === 'PASSED').length} /{' '}
                    {taskDetail.validation_gates.length} PASSED
                  </span>
                </h3>

                <div className="flex flex-col gap-2.5">
                  {taskDetail.validation_gates.map((gate) => (
                    <div
                      key={gate.id}
                      className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl flex items-center justify-between text-xs font-mono"
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            gate.status === 'PASSED'
                              ? 'bg-emerald-400'
                              : gate.status === 'IN_PROGRESS'
                              ? 'bg-blue-400 animate-pulse'
                              : 'bg-slate-600'
                          }`}
                        />
                        <div>
                          <div className="font-bold text-slate-200">{gate.name}</div>
                          <div className="text-[10px] text-slate-500">{gate.evidence_ref}</div>
                        </div>
                      </div>

                      <span
                        className={`text-[10px] font-bold px-2.5 py-0.5 rounded border uppercase ${
                          gate.status === 'PASSED'
                            ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                            : gate.status === 'IN_PROGRESS'
                            ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                            : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
                        }`}
                      >
                        {gate.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* PR Status Widget */}
              {taskDetail.pull_request && (
                <div className="p-6 bg-slate-900/60 border border-slate-800/80 rounded-2xl backdrop-blur-md flex flex-col gap-3 shadow-xl">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                      <span>🔀 Pull Request Status</span>
                    </h3>
                    <span
                      className={`text-xs font-mono font-bold px-3 py-1 rounded-lg border uppercase ${
                        taskDetail.pull_request.state === 'MERGED'
                          ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                          : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                      }`}
                    >
                      PR #{taskDetail.pull_request.number} {taskDetail.pull_request.state}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 font-bold">{taskDetail.pull_request.title}</p>

                  <div className="text-xs font-mono text-slate-400 flex items-center gap-4 pt-2 border-t border-slate-800">
                    <span>
                      CI Checks:{' '}
                      <strong className="text-emerald-400">
                        {taskDetail.pull_request.checks_status}
                      </strong>
                    </span>
                    <span>
                      Base Branch: <strong>{taskDetail.pull_request.base_branch}</strong>
                    </span>
                  </div>
                </div>
              )}

              {/* Interactive Canvas Graph Viewer */}
              {graphData && (
                <CanvasGraphViewer
                  taskId={taskDetail.id}
                  nodes={graphData.nodes}
                  edges={graphData.edges}
                />
              )}

              {/* Task Timeline Feed */}
              <div className="p-6 bg-slate-900/60 border border-slate-800/80 rounded-2xl backdrop-blur-md flex flex-col gap-4 shadow-xl">
                <h3 className="text-base font-extrabold text-white">
                  ⏱️ Стрічка Подій (Task Timeline Stream)
                </h3>

                <div className="flex flex-col gap-3">
                  {timeline.map((evt) => (
                    <div
                      key={evt.id}
                      className="p-3 bg-slate-950/60 border border-slate-800/60 rounded-xl flex flex-col gap-1 text-xs"
                    >
                      <div className="flex justify-between items-center font-mono text-[10px] text-slate-500">
                        <span className="text-blue-400 font-bold">{evt.event_type}</span>
                        <span>{evt.timestamp}</span>
                      </div>
                      <p className="text-slate-200 font-medium">{evt.summary}</p>
                      <span className="text-[10px] text-slate-500 font-mono">Actor: {evt.actor}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="p-12 bg-slate-900/40 border border-slate-800/60 rounded-2xl text-center text-slate-500 font-mono">
              Виберіть задачу з лівого списку для перегляду TaskDNA та графа.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}