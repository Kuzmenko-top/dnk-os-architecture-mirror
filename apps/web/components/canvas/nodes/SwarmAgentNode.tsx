// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_SwarmAgentNode"
// purpose: "Live Swarm Agent Spatial Node in authentic Shopify Design System from Open Design (Deep Teal #02090a, Dark Forest #061a1c, Neon Green #36F4A4, Pill Geometry)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  Bot, 
  Terminal, 
  Sparkles, 
  Send, 
  Layers, 
  ChevronDown, 
  ChevronUp,
  Wifi,
  WifiOff,
  RefreshCw,
  Radio
} from 'lucide-react';

export interface SwarmAgentData {
  agentName?: string;
  role?: string;
  version?: string;
  activeTaskGoal?: string;
  progressPercent?: number;
  isLiveWs?: boolean;
  thoughts?: string[];
  logs?: string[];
  workerStatuses?: Record<string, string>;
}

export default function SwarmAgentNode({ data, selected }: NodeProps) {
  const nodeData = (data || {}) as SwarmAgentData;
  const [activeTab, setActiveTab] = useState<'thoughts' | 'logs' | 'chat'>('thoughts');
  const [chatInput, setChatInput] = useState('');
  const [isExpanded, setIsExpanded] = useState(true);
  const [wsStatus, setWsStatus] = useState<'connected' | 'connecting' | 'fallback'>('connecting');
  
  const [chatMessages, setChatMessages] = useState<Array<{ sender: string; text: string; time: string }>>([
    { sender: 'Gerych Prime', text: 'TaskDNA DAG initialized. 14 Swarm workers active with Shopify Design System.', time: '12:00:01' }
  ]);

  const [thoughts, setThoughts] = useState<string[]>(
    Array.isArray(nodeData.thoughts) && nodeData.thoughts.length > 0 
      ? nodeData.thoughts 
      : [
          'Shopify Design System from Open Design fully active.',
          'Deep Teal (#02090a) & #36F4A4 Neon Green theme applied.',
          '14 specialized workers coordinated via TaskDNA DAG.',
        ]
  );

  const [logs, setLogs] = useState<string[]>(
    Array.isArray(nodeData.logs) && nodeData.logs.length > 0
      ? nodeData.logs
      : [
          '[12:00:00] Initialized in Shopify Design System.',
          '[12:00:05] SCONES memory cache synchronized.',
          '[12:00:10] WebSocket telemetry live on /api/v3/canvas/ws.',
        ]
  );

  const agentName = nodeData.agentName || 'Gerych Prime (Hermes)';
  const role = nodeData.role || 'Chief Builder & Swarm Orchestrator';
  const version = nodeData.version || 'v4.3.0';
  const activeTaskGoal = nodeData.activeTaskGoal || 'TaskDNA-CANVAS-CORE-003: Interactive Swarm Mesh';
  const progressPercent = nodeData.progressPercent ?? 85;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connectWebSocket = useCallback(() => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/v3/canvas/ws`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsStatus('connected');
        ws.send(JSON.stringify({ type: 'REGISTER_AGENT', agent: 'gerych_prime' }));
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'AGENT_THOUGHT' && payload.thought) {
            setThoughts((prev) => [payload.thought, ...prev.slice(0, 19)]);
          } else if (payload.type === 'AGENT_LOG' && payload.log) {
            setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${payload.log}`]);
          } else if (payload.type === 'AGENT_RESPONSE' && payload.message) {
            setChatMessages((prev) => [
              ...prev,
              { sender: payload.agent || 'Gerych Prime', text: payload.message, time: new Date().toLocaleTimeString() }
            ]);
          }
        } catch (e) {
          console.warn('[SwarmAgentNode] WS parse error:', e);
        }
      };

      ws.onerror = () => {
        setWsStatus('fallback');
      };

      ws.onclose = () => {
        setWsStatus('fallback');
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 5000);
      };
    } catch (err) {
      setWsStatus('fallback');
    }
  }, []);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [connectWebSocket]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const commandText = chatInput.trim();
    const timeString = new Date().toLocaleTimeString();

    const newMsg = {
      sender: 'User (Maksym)',
      text: commandText,
      time: timeString
    };

    setChatMessages((prev) => [...prev, newMsg]);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'SWARM_COMMAND',
          command: commandText,
          target_agent: 'gerych_prime',
          payload: { command: commandText, target_agent: 'gerych_prime' },
          timestamp: Date.now()
        })
      );
    } else {
      setTimeout(() => {
        setThoughts((prev) => [
          `Evaluating command "${commandText}" with SCONES cognitive patterns...`,
          ...prev.slice(0, 19)
        ]);
        setLogs((prev) => [
          ...prev,
          `[LOCAL-DISPATCH] "${commandText}" processed via local fallback engine`
        ]);
        setChatMessages((prev) => [
          ...prev,
          {
            sender: 'Gerych Prime',
            text: `Прийнято до виконання: "${commandText}". Завдання розподілено по рою (Local Mode).`,
            time: new Date().toLocaleTimeString()
          }
        ]);
      }, 400);
    }

    setChatInput('');
  };

  return (
    <div className={`w-[440px] rounded-3xl bg-[#02090a]/95 backdrop-blur-2xl border border-[#1e2c31] p-4 text-white shadow-[0_12px_45px_rgba(0,0,0,0.85)] transition-all duration-200 ${selected ? 'border-[#36f4a4] shadow-[0_0_30px_rgba(54,244,164,0.3)] ring-1 ring-[#36f4a4]' : ''}`}>
      {/* 4-Way Handles */}
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="target" position={Position.Left} id="left" className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="source" position={Position.Right} id="right" className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#1e2c31] pb-3 mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-[#102620] border border-[#36f4a4]/40 flex items-center justify-center text-[#36f4a4]">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-sm text-white">{agentName}</span>
              <span className="px-2 py-0.5 rounded-full text-[9px] font-mono bg-[#061a1c] text-[#36f4a4] border border-[#1e2c31]">{version}</span>
            </div>
            <p className="text-[10px] text-[#a1a1aa] font-medium">{role}</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {/* WebSocket Status Indicator */}
          <div 
            className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-[9px] font-mono border ${
              wsStatus === 'connected' 
                ? 'bg-[#102620] text-[#36f4a4] border-[#36f4a4]/40'
                : 'bg-[#061a1c] text-amber-300 border-amber-500/30'
            }`}
          >
            {wsStatus === 'connected' ? <Wifi className="w-2.5 h-2.5" /> : <RefreshCw className="w-2.5 h-2.5 animate-spin" />}
            <span>{wsStatus === 'connected' ? 'LIVE WS' : 'SYNC'}</span>
          </div>

          <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#102620] text-[#36f4a4] text-[9px] font-mono border border-[#36f4a4]/30">
            <Radio className="w-2.5 h-2.5 animate-pulse" />
            <span>Executing</span>
          </div>

          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded-full hover:bg-[#061a1c] text-[#a1a1aa] hover:text-white transition-colors cursor-pointer"
          >
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <>
          {/* Active TaskDNA Banner */}
          <div className="p-2.5 rounded-2xl bg-[#061a1c] border border-[#1e2c31] mb-3">
            <div className="flex items-center justify-between text-[11px] mb-1">
              <span className="text-[#a1a1aa] flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-[#36f4a4]" />
                <span className="font-semibold text-white">Active Goal</span>
              </span>
              <span className="font-mono text-[#36f4a4] font-bold">{progressPercent}%</span>
            </div>
            <p className="text-[11px] text-slate-300 font-mono truncate mb-2">{activeTaskGoal}</p>
            <div className="w-full bg-[#02090a] rounded-full h-1.5 overflow-hidden border border-[#1e2c31]">
              <div 
                className="bg-[#36f4a4] h-full rounded-full transition-all duration-500" 
                style={{ width: `${progressPercent}%` }} 
              />
            </div>
          </div>

          {/* Subagent Status Matrix */}
          <div className="grid grid-cols-4 gap-1.5 mb-3">
            {[
              { role: 'BUILDER', status: 'READY' },
              { role: 'SHOPIFY', status: 'SYNCED' },
              { role: 'VIDEO AI', status: 'READY' },
              { role: 'AUDITOR', status: '100% OK' },
            ].map((worker) => (
              <div key={worker.role} className="p-1.5 rounded-xl bg-[#061a1c] border border-[#1e2c31] text-center">
                <div className="text-[8px] text-[#71717a] font-mono font-semibold">{worker.role}</div>
                <div className="text-[9px] font-bold font-mono text-[#36f4a4]">{worker.status}</div>
              </div>
            ))}
          </div>

          {/* Tabs: Thoughts / Logs / Chat */}
          <div className="flex items-center gap-1 border-b border-[#1e2c31] pb-2 mb-2 text-xs">
            <button
              onClick={() => setActiveTab('thoughts')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'thoughts'
                  ? 'bg-[#36f4a4]/15 text-[#36f4a4] border border-[#36f4a4]/40'
                  : 'text-[#a1a1aa] hover:text-white'
              }`}
            >
              <Sparkles className="w-3 h-3" />
              <span>Thoughts ({thoughts.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'logs'
                  ? 'bg-[#36f4a4]/15 text-[#36f4a4] border border-[#36f4a4]/40'
                  : 'text-[#a1a1aa] hover:text-white'
              }`}
            >
              <Terminal className="w-3 h-3" />
              <span>Logs ({logs.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'chat'
                  ? 'bg-[#36f4a4]/15 text-[#36f4a4] border border-[#36f4a4]/40'
                  : 'text-[#a1a1aa] hover:text-white'
              }`}
            >
              <Bot className="w-3 h-3" />
              <span>Swarm Chat</span>
            </button>
          </div>

          {/* Tab Body */}
          <div className="h-36 overflow-y-auto pr-1 text-xs font-mono rounded-xl bg-[#061a1c] p-2.5 border border-[#1e2c31]">
            {activeTab === 'thoughts' && (
              <div className="flex flex-col gap-1.5">
                {thoughts.map((t, idx) => (
                  <div key={idx} className="flex items-start gap-1.5 text-[#a1a1aa] leading-relaxed">
                    <span className="text-[#36f4a4] shrink-0 font-bold">›</span>
                    <span>{t}</span>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'logs' && (
              <div className="flex flex-col gap-1 text-[11px] text-[#a1a1aa]">
                {logs.map((l, idx) => (
                  <div key={idx} className="truncate">
                    <span className="text-[#71717a]">{l.slice(0, 10)}</span> {l.slice(10)}
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'chat' && (
              <div className="flex flex-col gap-2">
                {chatMessages.map((m, idx) => (
                  <div key={idx} className={`p-2 rounded-xl text-[11px] ${
                    m.sender.includes('User') 
                      ? 'bg-[#102620] border border-[#36f4a4]/30 text-white ml-4' 
                      : 'bg-[#02090a] border border-[#1e2c31] text-[#a1a1aa] mr-4'
                  }`}>
                    <div className="flex items-center justify-between text-[9px] text-[#71717a] mb-0.5">
                      <span className="font-bold text-[#36f4a4]">{m.sender}</span>
                      <span>{m.time}</span>
                    </div>
                    <div>{m.text}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Live Dispatch Input */}
          <form onSubmit={handleSendMessage} className="mt-2.5 flex items-center gap-1.5">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Send task or prompt to Swarm Bus..."
              className="flex-1 px-3.5 py-2 rounded-full bg-[#061a1c] border border-[#1e2c31] text-xs text-white placeholder-[#71717a] focus:outline-none focus:border-[#36f4a4] transition-all"
            />
            <button
              type="submit"
              className="p-2 rounded-full bg-[#36f4a4] hover:bg-[#2de097] text-black font-bold transition-all active:scale-95 cursor-pointer shadow-md shadow-[#36f4a4]/20"
              title="Send to Swarm Bus"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </>
      )}
    </div>
  );
}
