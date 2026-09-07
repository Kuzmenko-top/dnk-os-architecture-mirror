// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_workspace_CommandBar"
// purpose: "Command Bar (⌘K) for natural-language goal intake and Workflow Composer triggering"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import { 
  Command, 
  Sparkles, 
  Search, 
  ArrowRight, 
  X, 
  ShoppingBag, 
  Film, 
  Code, 
  ShieldCheck,
  Bot
} from 'lucide-react';

interface CommandBarProps {
  isOpen: boolean;
  onClose: () => void;
  onComposeWorkflow: (goal: string) => void;
  isLoading?: boolean;
}

const PRESET_GOALS = [
  {
    icon: ShoppingBag,
    title: 'Створити промо-сторінку для нової коптильні ReBurn і підготувати запуск у Shopify',
    category: 'Shopify E-Commerce'
  },
  {
    icon: Film,
    title: 'Змонтувати та відрендерити 9:16 Remotion відеоролик для маркетингової кампанії',
    category: 'Video AI Studio'
  },
  {
    icon: Code,
    title: 'Декомпозувати нову функцію API через TaskDNA та створити Pull Request',
    category: 'Fullstack Swarm'
  },
  {
    icon: ShieldCheck,
    title: 'Провести Clean-Room патентний аудит та перевірити ліцензії сторонніх бібліотек',
    category: 'Patent Shield'
  }
];

export default function CommandBar({
  isOpen,
  onClose,
  onComposeWorkflow,
  isLoading = false
}: CommandBarProps) {
  const [goal, setGoal] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else {
          // Open triggered from parent
        }
      } else if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim() || isLoading) return;
    onComposeWorkflow(goal);
    onClose();
  };

  const handleSelectPreset = (text: string) => {
    setGoal(text);
    onComposeWorkflow(text);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-start justify-center pt-24 z-50 p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-slate-900 border border-purple-500/50 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Input Bar */}
        <form onSubmit={handleSubmit} className="flex items-center gap-3 p-4 border-b border-slate-800 bg-slate-950/60">
          <Sparkles className="w-5 h-5 text-purple-400 shrink-0 animate-pulse" />
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Опишіть бізнес-ціль або дію для Workflow Composer (напр. 'Запустити промо-кампанію Shopify')..."
            className="flex-1 bg-transparent text-sm text-white placeholder-slate-400 outline-none font-medium"
            autoFocus
          />
          {goal && (
            <button
              type="button"
              onClick={() => setGoal('')}
              className="text-slate-500 hover:text-slate-300 p-1"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            type="submit"
            disabled={!goal.trim() || isLoading}
            className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold disabled:opacity-40 transition-all cursor-pointer"
          >
            <span>Скласти DAG</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Preset Suggestions */}
        <div className="p-3 flex flex-col gap-1 max-h-80 overflow-y-auto">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider px-2 py-1">
            Швидкі сценарії Workflow Composer
          </span>
          {PRESET_GOALS.map((preset, idx) => {
            const Icon = preset.icon;
            return (
              <button
                key={idx}
                onClick={() => handleSelectPreset(preset.title)}
                className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-slate-800 text-left transition-colors group cursor-pointer"
              >
                <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-purple-400 group-hover:border-purple-500/40 shrink-0">
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-200 group-hover:text-purple-300 transition-colors">
                      {preset.title}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500 bg-slate-950 px-2 py-0.5 rounded-md border border-slate-800">
                      {preset.category}
                    </span>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Footer shortcuts */}
        <div className="p-2.5 bg-slate-950 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center justify-between font-mono">
          <span>Натисніть <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">Enter</kbd> для генерації</span>
          <span><kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">Esc</kbd> закрити</span>
        </div>
      </div>
    </div>
  );
}
