'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Search,
  Layout,
  Pencil,
  BarChart3,
  Terminal,
  Layers,
  Sparkles,
  Bot,
  Zap,
  X,
  ArrowRight
} from 'lucide-react';

export default function CommandBar() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const router = useRouter();

  // Keyboard shortcut Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const commands = [
    {
      id: 'canvas',
      name: 'Agent Flow Canvas',
      category: 'Navigation',
      icon: Layout,
      action: () => { router.push('/canvas'); setIsOpen(false); },
    },
    {
      id: 'whiteboard',
      name: 'Freehand Whiteboard & Moodboard',
      category: 'Navigation',
      icon: Pencil,
      action: () => { router.push('/whiteboard'); setIsOpen(false); },
    },
    {
      id: 'analytics',
      name: 'Live Analytics & Telemetry',
      category: 'Navigation',
      icon: BarChart3,
      action: () => { router.push('/analytics'); setIsOpen(false); },
    },
    {
      id: 'terminal',
      name: 'Gerych Autonomous Terminal',
      category: 'Navigation',
      icon: Terminal,
      action: () => { router.push('/terminal'); setIsOpen(false); },
    },
    {
      id: 'tasks',
      name: 'TaskDNA Evolutionary DAG',
      category: 'Navigation',
      icon: Layers,
      action: () => { router.push('/tasks'); setIsOpen(false); },
    },
    {
      id: 'launch-product',
      name: 'One-Click Product Launch Pipeline',
      category: 'Swarm Action',
      icon: Zap,
      action: () => { router.push('/tasks'); setIsOpen(false); },
    },
  ];

  const filteredCommands = commands.filter((cmd) =>
    cmd.name.toLowerCase().includes(query.toLowerCase()) ||
    cmd.category.toLowerCase().includes(query.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-150">
      <div className="w-full max-w-2xl rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden font-sans text-slate-100">
        {/* Search Input */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-slate-800">
          <Search size={20} className="text-slate-400" />
          <input
            type="text"
            placeholder="Type a command or jump to workspace... (Cmd+K)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            className="flex-1 bg-transparent border-none outline-none text-base text-slate-100 placeholder-slate-500 font-medium"
          />
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X size={18} />
          </button>
        </div>

        {/* Command List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {filteredCommands.length > 0 ? (
            filteredCommands.map((cmd) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={cmd.id}
                  onClick={cmd.action}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-xl hover:bg-slate-800/80 text-left transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                      <Icon size={18} />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-slate-200 group-hover:text-white">
                        {cmd.name}
                      </div>
                      <div className="text-xs text-slate-500">
                        {cmd.category}
                      </div>
                    </div>
                  </div>
                  <ArrowRight size={16} className="text-slate-500 group-hover:text-slate-300 transition-transform group-hover:translate-x-1" />
                </button>
              );
            })
          ) : (
            <div className="py-8 text-center text-slate-500 text-sm">
              No matching commands or destinations found.
            </div>
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="px-5 py-3 bg-slate-950/60 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono text-[10px]">↑↓</span>
            <span>Navigate</span>
            <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono text-[10px] ml-2">↵</span>
            <span>Select</span>
          </div>
          <div className="flex items-center gap-1 text-indigo-400 font-medium">
            <Sparkles size={12} />
            <span>DNK OS High-Velocity Swarm</span>
          </div>
        </div>
      </div>
    </div>
  );
}
