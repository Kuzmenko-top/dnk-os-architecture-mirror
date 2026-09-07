// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/node-tasks/GerychTaskChatDrawer.tsx"
// purpose: "CapCut & Stitch style slide-out Chat with Gerych for conversational Task & Ideas DAG creation"
// author: "DNK-e.com Maksym"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { useNodeTasksStore } from '@/store/nodeTasksStore';
import {
  MessageSquare,
  X,
  Send,
  Loader2,
  Sparkles,
  Bot,
  User,
  GitBranch,
  Layers,
  ShieldCheck,
  Zap,
} from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'gerych';
  text: string;
  timestamp: string;
  createdCount?: number;
}

interface GerychTaskChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function GerychTaskChatDrawer({ isOpen, onClose }: GerychTaskChatDrawerProps) {
  const [input, setInput] = useState('');
  const {
    isChatIntakeLoading,
    chatIntake,
    chatMessages,
    isChatOpen,
    setIsChatOpen,
  } = useNodeTasksStore();

  const activeOpen = isOpen !== undefined ? isOpen : isChatOpen;
  const handleClose = onClose || (() => setIsChatOpen(false));

  if (!activeOpen) return null;

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isChatIntakeLoading) return;

    const userText = input;
    setInput('');
    await chatIntake(userText);
  };

  return (
    <div className="absolute top-0 left-0 bottom-0 z-40 w-full sm:w-[420px] bg-[#0c0e14]/98 border-r border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.8)] backdrop-blur-2xl flex flex-col animate-in slide-in-from-left duration-200">
      {/* Header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between bg-zinc-950/60">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-[#33EE75]">
            <Sparkles className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-1.5">
              <span>Чат з Геричем</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/15 text-emerald-400 font-mono">
                DAG Intake
              </span>
            </h3>
            <p className="text-[11px] text-zinc-400">Генерація та декомпозиція задач у реальному часі</p>
          </div>
        </div>
        <button
          onClick={handleClose}
          className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5 transition-colors"
          title="Закрити чат та повернутися до доку"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5 scrollbar-thin scrollbar-thumb-zinc-800">
        {chatMessages.map((m) => {
          const isUser = m.sender === 'user';
          return (
            <div
              key={m.id}
              className={`flex items-start gap-2.5 ${isUser ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs ${
                  isUser
                    ? 'bg-blue-600/20 border border-blue-500/40 text-blue-400'
                    : 'bg-emerald-600/20 border border-emerald-500/40 text-[#33EE75]'
                }`}
              >
                {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>

              <div
                className={`max-w-[85%] rounded-2xl p-3 text-xs leading-relaxed ${
                  isUser
                    ? 'bg-blue-600/20 border border-blue-500/30 text-blue-50 rounded-tr-none'
                    : 'bg-[#151821] border border-white/10 text-zinc-200 rounded-tl-none shadow-md'
                }`}
              >
                <div className="whitespace-pre-wrap font-sans">{m.text}</div>
                <div
                  className={`mt-1.5 text-[10px] font-mono flex items-center justify-between ${
                    isUser ? 'text-blue-300/70' : 'text-zinc-500'
                  }`}
                >
                  <span>{m.timestamp}</span>
                  {m.createdCount !== undefined && m.createdCount > 0 && (
                    <span className="text-emerald-400 flex items-center gap-1 font-sans">
                      <GitBranch className="w-3 h-3" /> +{m.createdCount} вузлів у DAG
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {isChatIntakeLoading && (
          <div className="flex items-center gap-2 text-xs text-zinc-400 p-2 rounded-xl bg-white/5 border border-white/5 w-fit">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-[#33EE75]" />
            <span>Герич аналізує та структурує задачу...</span>
          </div>
        )}
      </div>

      {/* Suggested Quick Starters */}
      <div className="px-4 py-2 border-t border-white/5 bg-zinc-950/40 flex items-center gap-1.5 overflow-x-auto text-[11px]">
        <button
          onClick={() => setInput('Ідея: ')}
          className="px-2 py-1 rounded bg-zinc-800/60 hover:bg-zinc-800 text-zinc-300 shrink-0 transition-colors"
        >
          💡 Нова ідея
        </button>
        <button
          onClick={() => setInput('Задача: ')}
          className="px-2 py-1 rounded bg-zinc-800/60 hover:bg-zinc-800 text-zinc-300 shrink-0 transition-colors"
        >
          🎯 Нова задача
        </button>
        <button
          onClick={() => setInput('Провести аудит безпеки та якості')}
          className="px-2 py-1 rounded bg-zinc-800/60 hover:bg-zinc-800 text-zinc-300 shrink-0 transition-colors"
        >
          🛡️ Гейт аудиту
        </button>
      </div>

      {/* Input Box */}
      <form onSubmit={handleSend} className="p-3 border-t border-white/10 bg-[#0e1017]">
        <div className="flex items-center gap-2 bg-[#171a24] border border-white/10 rounded-xl px-3 py-2 focus-within:border-[#33EE75]/50 transition-colors">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Напиши задачу чи ідею..."
            className="flex-1 bg-transparent border-none outline-none text-xs text-zinc-100 placeholder:text-zinc-500"
            disabled={isChatIntakeLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isChatIntakeLoading}
            className="p-1.5 rounded-lg bg-[#33EE75] hover:bg-[#2bd966] disabled:bg-zinc-800 disabled:text-zinc-600 text-black transition-colors"
            title="Надіслати"
          >
            {isChatIntakeLoading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
