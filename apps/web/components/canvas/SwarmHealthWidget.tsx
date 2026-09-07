// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_SwarmHealthWidget"
// purpose: "Live Swarm Health HUD Widget & Popover for Canvas Engine showing 14 agents, Sentinel watchdog, SpendGuard, and Canvas Bridge"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-06"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { useSwarmHealthStream } from '../../lib/api/swarm_health_client';
import { 
  Activity, 
  ShieldAlert, 
  Coins, 
  Wifi, 
  WifiOff, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  X, 
  Cpu, 
  Users 
} from 'lucide-react';

interface SwarmHealthWidgetProps {
  workspaceId?: string;
  className?: string;
}

export const SwarmHealthWidget: React.FC<SwarmHealthWidgetProps> = ({
  workspaceId = 'ws-alpha-001',
  className = '',
}) => {
  const { health, connected, loading, error, refresh, heal } = useSwarmHealthStream(workspaceId);
  const [isOpen, setIsOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isHealing, setIsHealing] = useState(false);

  const handleManualRefresh = () => {
    setIsRefreshing(true);
    refresh();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const handleAutoHeal = async () => {
    setIsHealing(true);
    try {
      await heal('all');
    } catch (e) {
      console.error('Failed to trigger auto-heal:', e);
    } finally {
      setTimeout(() => setIsHealing(false), 800);
    }
  };

  const status = health?.overall_status || 'healthy';
  const activeWorkersCount = health?.active_workers?.ready_count ?? 14;
  const totalWorkersCount = health?.active_workers?.total_agents ?? 14;
  const criticalAlerts = health?.sentinel?.critical_alerts_count ?? 0;
  const warningAlerts = health?.sentinel?.warning_alerts_count ?? 0;
  const spendUsd = health?.accounting?.total_cost_usd ?? 0;
  const spendSaturation = health?.accounting?.spend_saturation_pct ?? 0;
  const activeWsClients = health?.canvas_bridge?.active_connections ?? 0;

  // Status-dependent colors
  const statusColorMap = {
    healthy: {
      border: 'border-emerald-500/40',
      bg: 'bg-emerald-950/70',
      text: 'text-emerald-300',
      dot: 'bg-emerald-400',
      ping: 'bg-emerald-400',
      icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
    },
    degraded: {
      border: 'border-amber-500/40',
      bg: 'bg-amber-950/70',
      text: 'text-amber-300',
      dot: 'bg-amber-400',
      ping: 'bg-amber-400',
      icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />,
    },
    unhealthy: {
      border: 'border-rose-500/50',
      bg: 'bg-rose-950/80',
      text: 'text-rose-300',
      dot: 'bg-rose-500',
      ping: 'bg-rose-500',
      icon: <XCircle className="w-3.5 h-3.5 text-rose-400" />,
    },
  };

  const currentTheme = statusColorMap[status] || statusColorMap.healthy;

  return (
    <div className={`relative font-sans text-xs ${className}`}>
      {/* HUD Pill Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${currentTheme.border} ${currentTheme.bg} hover:brightness-125 transition-all shadow-lg backdrop-blur-md cursor-pointer select-none`}
        title={`Swarm Health: ${status.toUpperCase()} (${connected ? 'WS Live' : 'Polling'})`}
      >
        {/* Pulsing Status Dot */}
        <span className="relative flex h-2 w-2">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${currentTheme.ping} opacity-75`} />
          <span className={`relative inline-flex rounded-full h-2 w-2 ${currentTheme.dot}`} />
        </span>

        {/* Swarm Agents Badge */}
        <span className={`font-mono font-semibold ${currentTheme.text} flex items-center gap-1`}>
          <Users className="w-3.5 h-3.5 opacity-80" />
          <span>{activeWorkersCount}/{totalWorkersCount}</span>
        </span>

        {/* Sentinel Warning Flag (if alerts exist) */}
        {criticalAlerts > 0 ? (
          <span className="flex items-center gap-0.5 px-1.5 py-0.2 rounded bg-rose-900/80 text-rose-200 border border-rose-600 text-[10px] font-mono font-bold animate-pulse">
            <ShieldAlert className="w-3 h-3" />
            {criticalAlerts}
          </span>
        ) : warningAlerts > 0 ? (
          <span className="flex items-center gap-0.5 px-1.5 py-0.2 rounded bg-amber-900/80 text-amber-200 border border-amber-600 text-[10px] font-mono font-bold">
            <ShieldAlert className="w-3 h-3" />
            {warningAlerts}
          </span>
        ) : null}

        {/* SpendGuard Pill */}
        <span className="font-mono text-slate-400 hidden sm:inline-flex items-center gap-1 border-l border-slate-700/60 pl-2">
          <Coins className="w-3 h-3 text-amber-400/80" />
          <span>${spendUsd.toFixed(2)}</span>
        </span>

        {/* WebSocket Live Indicator */}
        <span className="opacity-70 ml-0.5" title={connected ? 'Connected to WebSocket stream' : 'WebSocket connecting / fallback'}>
          {connected ? (
            <Wifi className="w-3 h-3 text-emerald-400" />
          ) : (
            <WifiOff className="w-3 h-3 text-slate-500" />
          )}
        </span>
      </button>

      {/* Expanded Swarm Health Matrix Popover */}
      {isOpen && (
        <div className="absolute top-11 right-0 w-[420px] max-w-[90vw] bg-slate-950/95 border border-slate-800 rounded-xl shadow-2xl backdrop-blur-xl p-4 z-50 text-slate-200 animate-in fade-in zoom-in-95 duration-150">
          {/* Popover Header */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h3 className="font-bold text-sm tracking-wide text-white">DNK Swarm Health Matrix</h3>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${currentTheme.bg} ${currentTheme.text} border ${currentTheme.border}`}>
                {status}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={handleManualRefresh}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                title="Refresh Swarm Diagnostics"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                title="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800/80 flex flex-col">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">SpendGuard</span>
              <span className="text-sm font-mono font-bold text-amber-300 mt-0.5">${spendUsd.toFixed(3)}</span>
              <span className="text-[10px] text-slate-400 font-mono mt-0.5">Budget: {spendSaturation.toFixed(1)}%</span>
            </div>

            <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800/80 flex flex-col justify-between">
              <div>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Sentinel Watchdog</span>
                <div className={`text-sm font-mono font-bold mt-0.5 ${criticalAlerts > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {criticalAlerts} crit / {warningAlerts} warn
                </div>
              </div>
              <div className="flex items-center justify-between mt-1 pt-1 border-t border-slate-800">
                <span className="text-[10px] text-slate-400 font-mono">
                  Heal: {health?.sentinel?.self_heal_plans_count ?? 0} active
                </span>
                {(criticalAlerts > 0 || warningAlerts > 0) && (
                  <button
                    onClick={handleAutoHeal}
                    disabled={isHealing}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-rose-950/80 border border-rose-500/50 text-rose-300 hover:bg-rose-900 transition-all font-mono font-bold cursor-pointer disabled:opacity-50"
                    title="Run Auto-Healing & Resolve Alerts"
                  >
                    {isHealing ? 'Healing...' : '⚡ Heal'}
                  </button>
                )}
              </div>
            </div>

            <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800/80 flex flex-col">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Canvas Bridge</span>
              <span className="text-sm font-mono font-bold text-cyan-300 mt-0.5">
                {activeWsClients} {activeWsClients === 1 ? 'client' : 'clients'}
              </span>
              <span className="text-[10px] text-slate-400 font-mono mt-0.5">
                {health?.canvas_bridge?.total_events_broadcast ?? 0} events
              </span>
            </div>
          </div>

          {/* System & Memory Row */}
          <div className="flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-slate-900/50 border border-slate-800/60 mb-3 text-[11px] text-slate-400 font-mono">
            <span className="flex items-center gap-1">
              <Cpu className="w-3 h-3 text-indigo-400" />
              <span>RAM: {health?.system?.memory_rss_mb?.toFixed(1) ?? '0.0'} MB</span>
            </span>
            <span>Uptime: {Math.floor((health?.system?.uptime_seconds ?? 0) / 60)}m</span>
            <span>WS: {connected ? 'Streaming (100ms)' : 'Polling'}</span>
          </div>

          {/* 14 Swarm Workers Grid */}
          <div className="mb-1">
            <div className="flex items-center justify-between mb-1.5 px-0.5">
              <span className="text-[11px] font-semibold text-slate-300 tracking-wide uppercase">
                Active Swarm Agents ({activeWorkersCount}/{totalWorkersCount})
              </span>
              <span className="text-[10px] text-slate-400">Mesh v4.5.0</span>
            </div>

            <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1 custom-scrollbar">
              {health?.active_workers?.workers?.map((w) => {
                const badgeColor = w.hex_color || w.hex || '#94A3B8';
                return (
                  <div
                    key={w.agent_id}
                    className="flex items-center justify-between px-2.5 py-1.5 rounded-md bg-slate-900/70 border border-slate-800/80 hover:border-slate-700 transition-all text-[11px]"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: badgeColor }}
                      />
                      <span className="font-semibold text-slate-200">{w.name}</span>
                      <span className="text-[10px] font-mono text-slate-400 hidden sm:inline">
                        [{w.badge || w.agent_id}]
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 font-mono text-[10px]">
                      <span className={`px-1.5 py-0.2 rounded font-semibold ${
                        w.status === 'ready' 
                          ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-700/60' 
                          : 'bg-amber-950/80 text-amber-300 border border-amber-700/60'
                      }`}>
                        {w.status}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Footer Status Reasons if not clean */}
          {health?.status_reasons && health.status_reasons.length > 0 && (
            <div className="mt-2.5 pt-2 border-t border-slate-800/80 text-[10px] font-mono text-amber-300/90 flex flex-col gap-0.5">
              <span className="font-bold text-amber-400">Diagnosis Notes:</span>
              {health.status_reasons.map((r, idx) => (
                <span key={idx}>• {r}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SwarmHealthWidget;
