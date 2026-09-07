// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_app_taskdna_page"
// purpose: "Main TaskDNA Workspace page component wrapping WorkspaceShell and TaskDNADashboard"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-23"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import WorkspaceShell from '../../components/workspace/WorkspaceShell';
import TaskDNADashboard from '../../components/taskdna/TaskDNADashboard';

export default function TaskDNAPage() {
  const [workspaceId, setWorkspaceId] = useState<string>('ws-alpha-001');
  const [activeTab, setActiveTab] = useState<'taskdna' | 'analytics' | 'canvas'>('taskdna');

  return (
    <WorkspaceShell
      currentWorkspaceId={workspaceId}
      onWorkspaceChange={setWorkspaceId}
      activeTab={activeTab}
      onTabChange={setActiveTab}
    >
      {activeTab === 'taskdna' && <TaskDNADashboard workspaceId={workspaceId} />}
      {activeTab === 'canvas' && (
        <div className="p-8 bg-slate-900/40 border border-slate-800 rounded-2xl text-center text-slate-400 font-mono">
          Interactive Canvas Foundation Mode (Active task graph in TaskDNA view)
        </div>
      )}
      {activeTab === 'analytics' && (
        <div className="p-8 bg-slate-900/40 border border-slate-800 rounded-2xl text-center text-slate-400 font-mono">
          Navigate to /analytics for full Advanced Analytics Dashboard
        </div>
      )}
    </WorkspaceShell>
  );
}