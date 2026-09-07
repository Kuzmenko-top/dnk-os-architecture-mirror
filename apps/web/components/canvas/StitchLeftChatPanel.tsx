// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_StitchLeftChatPanel"
// purpose: "Left Floating AI Conversation Panel with 14 Swarm Agents Dispatcher for DNK OS"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { 
  Sparkles, 
  Copy, 
  ChevronDown, 
  ChevronUp, 
  Check, 
  Send,
  Loader2,
  Bot
} from 'lucide-react';
import { DNK_SWARM_AGENTS, dispatchTaskToSwarm, DNKSwarmAgent } from '../../lib/swarm';

interface StitchLeftChatPanelProps {
  onSelectSuggestion?: (text: string) => void;
}

export default function StitchLeftChatPanel({ onSelectSuggestion }: StitchLeftChatPanelProps) {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<DNKSwarmAgent>(DNK_SWARM_AGENTS[0]);
  const [inputText, setInputText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState<Array<{ sender: string; text: string; time: string }>>([
    {
      sender: 'gerych_prime',
      text: '🧬 Вiтаю! Я Герич (Chief Builder). Готовий оркеструвати 14 Swarm-агентів для вашого проєкту.',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const handleCopy = () => {
    navigator.clipboard.writeText(messages[messages.length - 1]?.text || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDispatch = async () => {
    if (!inputText.trim() || isSending) return;
    const userPrompt = inputText.trim();
    setInputText('');

    const userMsg = {
      sender: 'user',
      text: userPrompt,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsSending(true);

    try {
      const res = await dispatchTaskToSwarm(userPrompt, selectedAgent.id, {
        source: 'StitchLeftChatPanel',
      });

      const responseText =
        res.output ||
        `[${selectedAgent.name}] Задачу прийнято до виконання (Task ID: ${res.task_id || 'DISPATCH_OK'}).`;

      setMessages((prev) => [
        ...prev,
        {
          sender: selectedAgent.id,
          text: responseText,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: selectedAgent.id,
          text: `❌ Помилка зв'язку з Gateway: ${err instanceof Error ? err.message : String(err)}`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="w-[340px] bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border border-slate-200/80 dark:border-slate-800/80 rounded-2xl p-4 shadow-2xl text-slate-800 dark:text-slate-100 flex flex-col gap-3.5 transition-all duration-300 pointer-events-auto">
      {/* Active Agent & Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800/80">
        <div className="flex items-center gap-2">
          <div
            className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white shadow-sm"
            style={{ backgroundColor: selectedAgent.color }}
          >
            {selectedAgent.avatar}
          </div>
          <div className="flex flex-col">
            <select
              value={selectedAgent.id}
              onChange={(e) => {
                const found = DNK_SWARM_AGENTS.find((a) => a.id === e.target.value);
                if (found) setSelectedAgent(found);
              }}
              className="bg-transparent text-xs font-semibold text-slate-900 dark:text-slate-100 cursor-pointer focus:outline-none"
            >
              {DNK_SWARM_AGENTS.map((agent) => (
                <option key={agent.id} value={agent.id} className="bg-slate-900 text-white">
                  {agent.avatar} {agent.name}
                </option>
              ))}
            </select>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono truncate max-w-[170px]">
              {selectedAgent.role}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1 text-slate-400">
          <button
            onClick={handleCopy}
            className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Copy message"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Conversation Messages */}
      {isExpanded && (
        <div className="flex flex-col gap-2.5 max-h-[260px] overflow-y-auto pr-1 text-xs leading-relaxed">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`p-2.5 rounded-xl border text-[11.5px] ${
                msg.sender === 'user'
                  ? 'bg-purple-500/10 border-purple-500/20 text-purple-900 dark:text-purple-200 ml-4'
                  : 'bg-slate-50 dark:bg-slate-800/60 border-slate-200/60 dark:border-slate-700/60 text-slate-800 dark:text-slate-200 mr-2'
              }`}
            >
              <div className="flex justify-between text-[10px] opacity-70 mb-1 font-mono">
                <span>{msg.sender}</span>
                <span>{msg.time}</span>
              </div>
              <p className="whitespace-pre-wrap">{msg.text}</p>
            </div>
          ))}
        </div>
      )}

      {/* Input Composer */}
      <div className="flex items-center gap-2 pt-1 border-t border-slate-100 dark:border-slate-800/80">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleDispatch()}
          placeholder={`Запитати ${selectedAgent.name}...`}
          className="flex-1 bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-purple-500"
        />
        <button
          onClick={handleDispatch}
          disabled={isSending || !inputText.trim()}
          className="p-2 rounded-xl bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white transition-colors flex items-center justify-center shrink-0"
        >
          {isSending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
        </button>
      </div>
    </div>
  );
}
