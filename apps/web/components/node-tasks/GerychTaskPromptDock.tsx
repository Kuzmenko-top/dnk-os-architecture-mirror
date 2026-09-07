// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/node-tasks/GerychTaskPromptDock.tsx"
// purpose: "CapCut & Google Stitch style floating prompt dock for Gerych conversational task intake into DAG"
// author: "DNK-e.com Maksym"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { useNodeTasksStore } from '@/store/nodeTasksStore';
import { Sparkles, ArrowUp, Loader2, Lightbulb, CheckCircle2, X, MessageSquareCode, Bot } from 'lucide-react';

export function GerychTaskPromptDock() {
  const [prompt, setPrompt] = useState('');
  const [showReplyPopup, setShowReplyPopup] = useState(false);
  const {
    isChatIntakeLoading,
    chatIntake,
    chatIntakeReply,
    isChatOpen,
    setIsChatOpen,
  } = useNodeTasksStore();

  // If full Chat Drawer is open, do not duplicate chat inputs on the screen
  if (isChatOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isChatIntakeLoading) return;

    const currentPrompt = prompt;
    setPrompt('');
    setShowReplyPopup(true);
    await chatIntake(currentPrompt);
  };

  const handleQuickPill = (prefix: string) => {
    setPrompt(prev => prev ? `${prefix} ${prev}` : `${prefix} `);
  };

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 w-full max-w-3xl px-4 pointer-events-auto">
      {/* Response Balloon from Gerych */}
      {chatIntakeReply && showReplyPopup && (
        <div className="mb-3 p-4 rounded-2xl bg-[#12141c]/95 border border-[#33EE75]/40 shadow-2xl backdrop-blur-2xl text-xs text-zinc-200 animate-in fade-in slide-in-from-bottom-2 duration-200 relative">
          <button
            onClick={() => setShowReplyPopup(false)}
            className="absolute top-3 right-3 text-zinc-400 hover:text-white p-1 rounded-md hover:bg-white/5 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
          <div className="flex items-start gap-3">
            <div className="w-7 h-7 rounded-lg bg-[#33EE75]/20 border border-[#33EE75]/40 flex items-center justify-center shrink-0">
              <Sparkles className="w-4 h-4 text-[#33EE75]" />
            </div>
            <div className="space-y-1.5 max-h-48 overflow-y-auto pr-6">
              <div className="font-semibold text-emerald-400 flex items-center gap-1.5">
                <span>🤖 Герич (Task Intake Assistant)</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#33EE75]/10 border border-[#33EE75]/20 text-[#33EE75]">
                  Синхронізовано з DAG
                </span>
              </div>
              <div className="whitespace-pre-wrap text-zinc-300 leading-relaxed font-sans">
                {chatIntakeReply}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main CapCut & Stitch Command Bar */}
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-3 bg-[#12141c]/95 border border-white/10 rounded-full py-2.5 px-4 shadow-[0_12px_40px_rgba(0,0,0,0.8)] backdrop-blur-2xl focus-within:border-[#33EE75]/60 transition-all duration-200"
      >
        {/* Left Agent Indicator */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="w-7 h-7 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-xs">
            <Sparkles className="w-3.5 h-3.5 text-[#33EE75] animate-pulse" />
          </div>
          <span className="text-xs font-semibold text-zinc-300 hidden sm:inline">
            Герич AI:
          </span>
        </div>

        <div className="h-4 w-px bg-white/10 hidden sm:block" />

        {/* Quick Suggestion Pills */}
        <div className="hidden md:flex items-center gap-1.5 shrink-0 text-[11px]">
          <button
            type="button"
            onClick={() => handleQuickPill('Ідея:')}
            className="px-2 py-0.5 rounded-full bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-amber-300 flex items-center gap-1 transition-colors"
          >
            <Lightbulb className="w-3 h-3" />
            Ідея
          </button>
          <button
            type="button"
            onClick={() => handleQuickPill('Завдання:')}
            className="px-2 py-0.5 rounded-full bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 text-indigo-300 flex items-center gap-1 transition-colors"
          >
            <CheckCircle2 className="w-3 h-3" />
            Задача
          </button>
          <button
            type="button"
            onClick={() => handleQuickPill('Декомпозувати та протестувати:')}
            className="px-2 py-0.5 rounded-full bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-emerald-300 flex items-center gap-1 transition-colors"
          >
            <MessageSquareCode className="w-3 h-3" />
            Декомпозиція
          </button>
          <button
            type="button"
            onClick={() => setIsChatOpen(true)}
            className="px-2 py-0.5 rounded-full bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 text-cyan-300 flex items-center gap-1 transition-colors"
            title="Розгорнути історію діалогу"
          >
            <Bot className="w-3 h-3" />
            Історія
          </button>
        </div>

        <div className="h-4 w-px bg-white/10 hidden md:block" />

        {/* Input */}
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Повідомте Геричу задачу чи ідею (напр. 'Зробити темну тему і протестувати')..."
          className="flex-1 bg-transparent border-none outline-none text-xs sm:text-sm text-zinc-100 placeholder:text-zinc-500"
          disabled={isChatIntakeLoading}
        />

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!prompt.trim() || isChatIntakeLoading}
          className="w-8 h-8 rounded-full bg-[#33EE75] hover:bg-[#2bd966] disabled:bg-zinc-800 disabled:text-zinc-600 text-black flex items-center justify-center shrink-0 transition-all duration-200 shadow-md hover:shadow-[0_0_15px_rgba(51,238,117,0.4)]"
          title="Створити задачу через Герича"
        >
          {isChatIntakeLoading ? (
            <Loader2 className="w-4 h-4 animate-spin text-black" />
          ) : (
            <ArrowUp className="w-4 h-4" />
          )}
        </button>
      </form>
    </div>
  );
}
