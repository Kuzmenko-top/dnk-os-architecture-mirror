// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_workspace_CapCutSidebar"
// purpose: "Authentic CapCut-styled Navigation Sidebar with Brand Icon, Search bar, Online Collaborators (Alex K, Maya R, David S), Workspace Navigator, Folders, Tags, Recent, and Settings/Help triggers"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { 
  Search, 
  FolderKanban, 
  Folder, 
  Tag, 
  Clock, 
  Settings, 
  HelpCircle, 
  ChevronLeft, 
  ChevronRight,
  LayoutGrid,
  Sparkles,
  Users
} from 'lucide-react';

interface CapCutSidebarProps {
  isOpen?: boolean;
  onToggle?: () => void;
  activeNav?: string;
  onSelectNav?: (navId: string) => void;
  onOpenSettings?: () => void;
}

export interface Collaborator {
  id: string;
  name: string;
  role: string;
  avatarColor: string;
  status: 'online' | 'busy' | 'idle';
}

const COLLABORATORS: Collaborator[] = [
  { id: '1', name: 'Alex K.', role: 'Lead Architect', avatarColor: 'bg-emerald-500', status: 'online' },
  { id: '2', name: 'Maya R.', role: 'AI Specialist', avatarColor: 'bg-pink-500', status: 'online' },
  { id: '3', name: 'David S.', role: 'E-Com Builder', avatarColor: 'bg-cyan-500', status: 'online' },
];

export default function CapCutSidebar({
  isOpen = true,
  onToggle,
  activeNav = 'workspace',
  onSelectNav,
  onOpenSettings
}: CapCutSidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentNav, setCurrentNav] = useState(activeNav);

  const navItems = [
    { id: 'workspace', label: 'Workspace', icon: LayoutGrid },
    { id: 'folders', label: 'Folders', icon: Folder },
    { id: 'tags', label: 'Tags', icon: Tag },
    { id: 'recent', label: 'Recent', icon: Clock },
  ];

  const handleNavClick = (id: string) => {
    setCurrentNav(id);
    onSelectNav?.(id);
  };

  if (!isOpen) {
    return (
      <aside className="w-14 bg-[#0d1017] border-r border-[#1a1f2c] flex flex-col items-center py-4 justify-between h-full z-20 select-none">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-400 flex items-center justify-center text-white font-black text-sm shadow-md cursor-pointer" onClick={onToggle}>
            C
          </div>
          <button onClick={onToggle} className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-[#161b26] transition-colors cursor-pointer">
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
        <div className="flex flex-col items-center gap-2">
          <button onClick={onOpenSettings} className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-[#161b26] transition-colors cursor-pointer">
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-60 bg-[#0d1017] border-r border-[#1a1f2c] text-[#9ca3af] flex flex-col h-full z-20 select-none font-sans">
      {/* Top Header: Logo & Collapse */}
      <div className="p-3.5 border-b border-[#1a1f2c] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-400 flex items-center justify-center text-white font-black text-xs shadow-md shadow-indigo-500/20">
            C
          </div>
          <span className="font-bold text-sm text-white tracking-wide">CapCut Studio</span>
        </div>
        <button
          onClick={onToggle}
          className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-[#161b26] transition-colors cursor-pointer"
          title="Collapse Sidebar"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* Search Bar */}
      <div className="p-3">
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[#161b26] border border-[#232938] text-xs text-slate-200 focus-within:border-indigo-500 transition-all">
          <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search..."
            className="bg-transparent border-none outline-none text-xs text-white placeholder-slate-500 w-full"
          />
        </div>
      </div>

      {/* Live Collaborators / Swarm Members */}
      <div className="px-3 py-2 border-b border-[#1a1f2c]">
        <div className="flex items-center justify-between text-[11px] font-semibold text-slate-400 mb-2 px-1">
          <span className="flex items-center gap-1.5">
            <Users className="w-3 h-3 text-indigo-400" />
            <span>Users</span>
          </span>
          <span className="text-[10px] font-mono text-emerald-400">● 3 Online</span>
        </div>
        <div className="space-y-1.5">
          {COLLABORATORS.map((user) => (
            <div key={user.id} className="flex items-center justify-between px-2.5 py-1.5 rounded-xl hover:bg-[#161b26] transition-colors cursor-pointer text-xs">
              <div className="flex items-center gap-2.5">
                <div className={`w-6 h-6 rounded-full ${user.avatarColor} text-white font-bold text-[10px] flex items-center justify-center shadow-sm relative`}>
                  {user.name.split(' ').map(n => n[0]).join('')}
                  <span className="absolute bottom-0 right-0 w-2 h-2 rounded-full bg-emerald-400 ring-1 ring-[#0d1017]" />
                </div>
                <span className="font-medium text-slate-200 text-xs">{user.name}</span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">{user.role.split(' ')[0]}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentNav === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                isActive
                  ? 'bg-[#1b2234] text-white font-semibold border border-indigo-500/40 shadow-sm'
                  : 'text-slate-400 hover:bg-[#161b26] hover:text-slate-200'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Bottom Footer: Settings & Help */}
      <div className="p-3 border-t border-[#1a1f2c] flex flex-col gap-1 text-xs">
        <button
          onClick={onOpenSettings}
          className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-400 hover:bg-[#161b26] hover:text-white transition-colors cursor-pointer w-full text-left"
        >
          <Settings className="w-4 h-4" />
          <span>Settings</span>
        </button>
        <button
          className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-400 hover:bg-[#161b26] hover:text-white transition-colors cursor-pointer w-full text-left"
        >
          <HelpCircle className="w-4 h-4" />
          <span>Help</span>
        </button>
      </div>
    </aside>
  );
}
