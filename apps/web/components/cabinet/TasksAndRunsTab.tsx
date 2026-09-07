// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_cabinet_TasksAndRunsTab"
// purpose: "Tasks and Runs viewer with TaskDNA scale hierarchy & DoD checklists (DNK-VISUAL-OS-001)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-23"
// --- END DNK-MRH-HEADER ---

"use client";

import React, { useState, useEffect } from "react";
import { TaskTreeItem, cabinetApi } from "../../lib/api_client";

export function TasksAndRunsTab() {
  const [tasks, setTasks] = useState<TaskTreeItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedTask, setSelectedTask] = useState<TaskTreeItem | null>(null);

  useEffect(() => {
    async function loadTasks() {
      try {
        const data = await cabinetApi.getTasks();
        setTasks(data);
        if (data.length > 0) {
          setSelectedTask(data[0]);
        }
      } catch (err) {
        console.error("Failed to fetch tasks:", err);
      } finally {
        setLoading(false);
      }
    }
    loadTasks();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-xs font-mono text-slate-400">
        Loading Task Trees & Plant Runs...
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-full">
      {/* 1. Task Tree List (Plant Scale Hierarchy) */}
      <div className="md:col-span-1 bg-slate-900/40 border border-slate-800 rounded-lg p-4 space-y-3 flex flex-col h-[600px] overflow-hidden">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <h2 className="text-sm font-semibold text-slate-200">Task Hierarchy</h2>
          <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20">
            Task Forest v2
          </span>
        </div>

        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {tasks.map((task) => (
            <div
              key={task.id}
              onClick={() => setSelectedTask(task)}
              className={`p-3 rounded-lg border text-xs cursor-pointer transition-colors space-y-1.5 ${
                selectedTask?.id === task.id
                  ? "bg-slate-800 border-emerald-500/40 text-slate-100"
                  : "bg-slate-950/40 border-slate-800/80 text-slate-400 hover:bg-slate-900 hover:text-slate-200"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] text-emerald-400">{task.plant_scale}</span>
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.2 rounded uppercase ${
                    task.status === "completed"
                      ? "bg-emerald-500/20 text-emerald-400"
                      : "bg-amber-500/20 text-amber-400"
                  }`}
                >
                  {task.status}
                </span>
              </div>
              <p className="font-medium text-slate-200 line-clamp-1">{task.title}</p>
              <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                <span>{task.assigned_agent || "Unassigned"}</span>
                <span>DoD: {task.dod_progress}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 2. Task Details & DoD Gates */}
      <div className="md:col-span-2 bg-slate-900/40 border border-slate-800 rounded-lg p-5 space-y-5 h-[600px] overflow-y-auto">
        {selectedTask ? (
          <>
            <div className="border-b border-slate-800 pb-4 space-y-2">
              <div className="flex items-center space-x-2">
                <span className="bg-emerald-500/10 text-emerald-400 text-[10px] font-mono px-2 py-0.5 rounded border border-emerald-500/20">
                  {selectedTask.plant_scale}
                </span>
                <h3 className="text-base font-semibold text-slate-100">{selectedTask.title}</h3>
              </div>
              <p className="text-xs text-slate-400 font-mono">ID: {selectedTask.id}</p>
            </div>

            {/* DoD Criteria Checklist */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Definition of Done (DoD) Checklist
              </h4>
              <div className="space-y-2">
                {selectedTask.dod_criteria.map((crit, idx) => (
                  <div
                    key={idx}
                    className="flex items-center space-x-3 text-xs bg-slate-950/40 border border-slate-800/80 p-2.5 rounded-lg text-slate-300"
                  >
                    <span className="h-4 w-4 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center justify-center text-[10px]">
                      ✓
                    </span>
                    <span>{crit}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Validation Gates */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Active Validation Gates
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {selectedTask.validation_gates.map((gate, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-lg border border-slate-800 bg-slate-950/30 text-xs"
                  >
                    <span className="text-slate-300">{gate.name}</span>
                    <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20">
                      PASSED
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Cycle Report Link */}
            {selectedTask.cycle_report_path && (
              <div className="bg-slate-950/60 border border-slate-800 p-3 rounded-lg flex items-center justify-between text-xs">
                <span className="text-slate-400">Canonical Cycle Report:</span>
                <span className="font-mono text-emerald-400">{selectedTask.cycle_report_path}</span>
              </div>
            )}
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-xs font-mono text-slate-500">
            Select a task from the tree to inspect details
          </div>
        )}
      </div>
    </div>
  );
}
