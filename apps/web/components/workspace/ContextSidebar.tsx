// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_workspace_ContextSidebar"
// purpose: "Note & Project Outline Navigator Sidebar for DNK OS Note-Based Canvas (Task 3) strictly in Shopify Design System"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "4.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { 
  FolderKanban, 
  FileText, 
  Dna, 
  Bot, 
  Database, 
  ShoppingBag, 
  ShieldCheck,
  Settings,
  Sparkles,
  Layers,
  BookOpen
} from 'lucide-react';

interface ContextSidebarProps {
  activeTab?: string;
  onSelectTab?: (tab: string) => void;
  isOpen?: boolean;
  onOpenSettings?: () => void;
}

export default function ContextSidebar({
  activeTab = 'notes',
  onSelectTab,
  isOpen = true,
  onOpenSettings
}: ContextSidebarProps) {
  const [currentTab, setCurrentTab] = useState(activeTab);

  const navItems = [
    { id: 'notes', label: 'Living Notes & Briefs', icon: FileText, count: '8' },
    { id: 'taskdna', label: 'TaskDNA Trees', icon: Dna, count: '12' },
    { id: 'projects', label: 'Projects & Stores', icon: FolderKanban, count: '3' },
    { id: 'agents', label: '14 Swarm Agents', icon: Bot, count: 'Live' },
    { id: 'memory', label: 'SCONES L3 Vault', icon: Database, count: '1.2k' },
    { id: 'artifacts', label: 'Verified Artifacts', icon: Layers, count: '48' },
  ];

  const handleTabClick = (id: string) => {
    setCurrentTab(id);
    onSelectTab?.(id);
  };

  if (!isOpen) return null;

  return (
    <aside className="w-68 bg-[#02090a]/95 backdrop-blur-2xl border-r border-[#1e2c31] text-slate-300 flex flex-col h-full z-20 select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#1e2c31] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-2xl bg-[#102620] border border-[#36f4a4]/40 flex items-center justify-center text-[#36f4a4] font-black text-xs shadow-md shadow-[#36f4a4]/20">
            🧬
          </div>
          <div>
            <h2 className="font-bold text-sm text-white tracking-wider font-mono">DNK OS</h2>
            <span className="text-[10px] text-[#36f4a4] font-semibold">NoteCanvas v3.0</span>
          </div>
        </div>
        <button
          onClick={onOpenSettings}
          className="p-1.5 rounded-full text-slate-400 hover:text-white hover:bg-[#102620] transition-colors cursor-pointer border border-[#1e2c31]"
          title="Open Settings & Models"
        >
          <Settings className="w-4 h-4 text-slate-300" />
        </button>
      </div>

      {/* Note & Document Navigator */}
      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-1">
        <span className="text-[10px] font-bold text-[#71717a] uppercase tracking-wider px-3 py-1 font-mono">
          NoteCanvas Index
        </span>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleTabClick(item.id)}
              className={`flex items-center justify-between px-3.5 py-2 rounded-full text-xs font-medium transition-all cursor-pointer ${
                isActive
                  ? 'bg-[#36f4a4]/15 text-[#36f4a4] border border-[#36f4a4]/50 font-semibold shadow-sm'
                  : 'text-[#a1a1aa] hover:bg-[#061a1c] hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${isActive ? 'text-[#36f4a4]' : 'text-[#71717a]'}`} />
                <span>{item.label}</span>
              </div>
              {item.count && (
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono ${
                  item.count === 'Live' 
                    ? 'bg-[#36f4a4]/20 text-[#36f4a4] font-bold border border-[#36f4a4]/30'
                    : 'bg-[#061a1c] text-[#a1a1aa] border border-[#1e2c31]'
                }`}>
                  {item.count}
                </span>
              )}
            </button>
          );
        })}

        {/* Active Note Project Card */}
        <div className="mt-4 p-3.5 rounded-2xl bg-[#061a1c] border border-[#1e2c31] text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-1.5 text-[#36f4a4] font-bold text-[11px]">
              <BookOpen className="w-3.5 h-3.5" />
              <span>Active Note Canvas</span>
            </div>
            <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-[#102620] text-[#36f4a4] border border-[#36f4a4]/30">
              Task 3
            </span>
          </div>
          <p className="font-semibold text-white truncate">ReBurn Smoker 360° Launch</p>
          <div className="mt-2.5 pt-2 border-t border-[#1e2c31] flex items-center justify-between text-[10px] text-[#a1a1aa] font-mono">
            <span>4 Living Notes Active</span>
            <span className="text-[#36f4a4] font-bold">● Live Sync</span>
          </div>
        </div>
      </div>

      {/* Footer System Health */}
      <div className="p-3 border-t border-[#1e2c31] text-[11px] text-[#a1a1aa] flex items-center justify-between font-mono bg-[#02090a]">
        <div className="flex items-center gap-1.5 text-[#36f4a4]">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Auditor Gate Active</span>
        </div>
        <span className="text-[#71717a]">Zero-Waste</span>
      </div>
    </aside>
  );
}
