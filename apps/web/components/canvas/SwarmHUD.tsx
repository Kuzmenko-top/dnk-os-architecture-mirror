// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_SwarmHUD"
// purpose: "Visual Swarm HUD & Live Worktree Inspector displaying Git Worktree Isolation, Sangha Consensus, Ledger & Audit Trail"
// author: "DNK-e.com Maksym & Gerych Prime"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-06"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  GitBranch,
  ShieldCheck,
  ShieldAlert,
  Database,
  History,
  RefreshCw,
  FolderGit2,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  X,
  FileCode,
  Layers,
} from 'lucide-react';

export interface WorktreeItem {
  task_id: string;
  worktree_path: string;
  branch: string;
  exists_on_disk: boolean;
}

export interface AuditEvent {
  event_type: string;
  task_id?: string;
  agent?: string;
  timestamp: string;
  payload: Record<string, any>;
}

export interface LedgerArtifact {
  id: string;
  key: string;
  category: string;
  producer_agent: string;
  task_id?: string;
  content_hash: string;
  created_at: number;
}

export interface HUDSummary {
  status: string;
  active_worktrees_count: number;
  total_audit_events: number;
  total_ledger_artifacts: number;
  consensus_stats: Record<string, number>;
  timestamp: number;
}

interface SwarmHUDProps {
  className?: string;
  isOpen?: boolean;
  onClose?: () => void;
}

export const SwarmHUD: React.FC<SwarmHUDProps> = ({
  className = '',
  isOpen = true,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'worktrees' | 'consensus' | 'ledger' | 'audit'>('worktrees');
  const [summary, setSummary] = useState<HUDSummary | null>(null);
  const [worktrees, setWorktrees] = useState<WorktreeItem[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [artifacts, setArtifacts] = useState<LedgerArtifact[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHUDData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, wtRes, audRes, ledRes] = await Promise.all([
        fetch('/api/v1/swarm/hud-summary').then((r) => (r.ok ? r.json() : null)),
        fetch('/api/v1/swarm/worktrees').then((r) => (r.ok ? r.json() : [])),
        fetch('/api/v1/swarm/audit-trail?limit=30').then((r) => (r.ok ? r.json() : { events: [] })),
        fetch('/api/v1/swarm/ledger').then((r) => (r.ok ? r.json() : { artifacts: [] })),
      ]);

      if (sumRes) setSummary(sumRes);
      if (Array.isArray(wtRes)) setWorktrees(wtRes);
      if (audRes?.events) setAuditEvents(audRes.events);
      if (ledRes?.artifacts) setArtifacts(ledRes.artifacts);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch swarm HUD telemetry');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHUDData();
    const interval = setInterval(fetchHUDData, 6000);
    return () => clearInterval(interval);
  }, [fetchHUDData]);

  if (!isOpen) return null;

  return (
    <div
      className={`fixed bottom-14 right-6 w-[480px] max-h-[580px] bg-slate-950/95 border border-cyan-500/30 rounded-xl shadow-2xl backdrop-blur-md flex flex-col z-50 text-slate-100 font-sans text-xs ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-500/20 bg-slate-900/60 rounded-t-xl">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-cyan-400 animate-pulse" />
          <span className="font-semibold tracking-wide text-cyan-300">Swarm HUD & Isolation Inspector</span>
          <span className="px-1.5 py-0.5 text-[10px] bg-cyan-950/80 border border-cyan-500/40 text-cyan-300 rounded font-mono">
            {summary?.active_worktrees_count ?? 0} Worktrees
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchHUDData}
            title="Refresh HUD"
            className="p-1 text-slate-400 hover:text-cyan-300 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          {onClose && (
            <button onClick={onClose} className="p-1 text-slate-400 hover:text-rose-400 transition-colors">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Metric Badges */}
      <div className="grid grid-cols-4 gap-2 px-3 py-2 bg-slate-900/40 border-b border-slate-800 text-center font-mono">
        <div className="p-1.5 rounded bg-slate-900/80 border border-slate-800">
          <div className="text-[10px] text-slate-400">Worktrees</div>
          <div className="text-cyan-400 font-bold">{summary?.active_worktrees_count ?? 0}</div>
        </div>
        <div className="p-1.5 rounded bg-slate-900/80 border border-slate-800">
          <div className="text-[10px] text-slate-400">Consensus</div>
          <div className="text-emerald-400 font-bold">{summary?.consensus_stats?.APPROVED ?? 0} ✓</div>
        </div>
        <div className="p-1.5 rounded bg-slate-900/80 border border-slate-800">
          <div className="text-[10px] text-slate-400">Ledger</div>
          <div className="text-amber-400 font-bold">{summary?.total_ledger_artifacts ?? 0}</div>
        </div>
        <div className="p-1.5 rounded bg-slate-900/80 border border-slate-800">
          <div className="text-[10px] text-slate-400">Audit Logs</div>
          <div className="text-indigo-400 font-bold">{summary?.total_audit_events ?? 0}</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-slate-800 text-[11px] font-medium">
        <button
          onClick={() => setActiveTab('worktrees')}
          className={`flex-1 py-2 px-2 flex items-center justify-center space-x-1.5 transition-colors ${
            activeTab === 'worktrees'
              ? 'text-cyan-400 border-b-2 border-cyan-400 bg-cyan-950/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <GitBranch className="w-3.5 h-3.5" />
          <span>Worktrees</span>
        </button>
        <button
          onClick={() => setActiveTab('consensus')}
          className={`flex-1 py-2 px-2 flex items-center justify-center space-x-1.5 transition-colors ${
            activeTab === 'consensus'
              ? 'text-emerald-400 border-b-2 border-emerald-400 bg-emerald-950/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Sangha Gate</span>
        </button>
        <button
          onClick={() => setActiveTab('ledger')}
          className={`flex-1 py-2 px-2 flex items-center justify-center space-x-1.5 transition-colors ${
            activeTab === 'ledger'
              ? 'text-amber-400 border-b-2 border-amber-400 bg-amber-950/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>Ledger</span>
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`flex-1 py-2 px-2 flex items-center justify-center space-x-1.5 transition-colors ${
            activeTab === 'audit'
              ? 'text-indigo-400 border-b-2 border-indigo-400 bg-indigo-950/20'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <History className="w-3.5 h-3.5" />
          <span>Audit Stream</span>
        </button>
      </div>

      {/* Tab Content */}
      <div className="p-3 overflow-y-auto max-h-[320px] space-y-2">
        {error && (
          <div className="p-2 rounded bg-rose-950/50 border border-rose-500/40 text-rose-300 text-[11px] flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Worktrees View */}
        {activeTab === 'worktrees' && (
          <div className="space-y-2">
            {worktrees.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <FolderGit2 className="w-8 h-8 mx-auto mb-2 opacity-40 text-slate-400" />
                <p>No active git worktrees currently running.</p>
                <p className="text-[10px] text-slate-600 mt-1">Parallel worker tasks spawn transient trees in .worktrees/</p>
              </div>
            ) : (
              worktrees.map((wt) => (
                <div
                  key={wt.task_id}
                  className="p-2.5 rounded-lg bg-slate-900/80 border border-cyan-500/20 flex flex-col space-y-1 hover:border-cyan-500/40 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-semibold text-cyan-300">{wt.task_id}</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-cyan-950 text-cyan-400 border border-cyan-800">
                      {wt.branch}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-400 truncate">{wt.worktree_path}</div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Sangha Gate View */}
        {activeTab === 'consensus' && (
          <div className="space-y-2">
            {auditEvents
              .filter((ev) => ev.event_type.includes('CONSENSUS'))
              .length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <ShieldCheck className="w-8 h-8 mx-auto mb-2 opacity-40 text-emerald-400" />
                <p>No consensus evaluations recorded in current window.</p>
              </div>
            ) : (
              auditEvents
                .filter((ev) => ev.event_type.includes('CONSENSUS'))
                .map((ev, idx) => {
                  const payload = ev.payload || {};
                  const isApproved = payload.consensus_verdict === 'APPROVED';
                  return (
                    <div
                      key={idx}
                      className={`p-2.5 rounded-lg border text-[11px] ${
                        isApproved
                          ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300'
                          : 'bg-rose-950/30 border-rose-500/30 text-rose-300'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold flex items-center space-x-1">
                          {isApproved ? (
                            <CheckCircle className="w-3.5 h-3.5 text-emerald-400 inline" />
                          ) : (
                            <ShieldAlert className="w-3.5 h-3.5 text-rose-400 inline" />
                          )}
                          <span>Verdict: {payload.consensus_verdict || 'QUARANTINED'}</span>
                        </span>
                        <span className="font-mono text-[10px] text-slate-400">{ev.task_id || 'general'}</span>
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Auditor: {payload.auditor_feedback || 'Passed all path hygiene & syntax gates'}
                      </div>
                    </div>
                  );
                })
            )}
          </div>
        )}

        {/* Ledger View */}
        {activeTab === 'ledger' && (
          <div className="space-y-2">
            {artifacts.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <FileCode className="w-8 h-8 mx-auto mb-2 opacity-40 text-amber-400" />
                <p>No artifacts in Swarm Shared Memory Ledger.</p>
              </div>
            ) : (
              artifacts.map((art) => (
                <div
                  key={art.id}
                  className="p-2.5 rounded-lg bg-slate-900/80 border border-amber-500/20 hover:border-amber-500/40 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono font-semibold text-amber-300 truncate max-w-[280px]">
                      {art.key}
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-950 text-amber-400 border border-amber-800">
                      {art.category}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span>By: <span className="text-slate-300">{art.producer_agent}</span></span>
                    <span className="font-mono text-[9px] text-slate-500">{art.content_hash.slice(0, 10)}...</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Audit Stream View */}
        {activeTab === 'audit' && (
          <div className="space-y-1.5 font-mono text-[10px]">
            {auditEvents.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <p>Audit stream is empty.</p>
              </div>
            ) : (
              auditEvents.map((ev, idx) => (
                <div
                  key={idx}
                  className="p-1.5 rounded bg-slate-900/60 border border-slate-800/80 flex items-start space-x-2"
                >
                  <ChevronRight className="w-3 h-3 text-cyan-400 shrink-0 mt-0.5" />
                  <div className="flex-1 truncate">
                    <span className="text-cyan-300 font-semibold">{ev.event_type}</span>{' '}
                    <span className="text-slate-400">[{ev.agent || 'coordinator'}]</span>{' '}
                    <span className="text-slate-500">{ev.task_id}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SwarmHUD;
