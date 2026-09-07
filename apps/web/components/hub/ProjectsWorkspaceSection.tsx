// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_hub_ProjectsWorkspaceSection"
// purpose: "Projects & Folders workspace matching CapCut /my-edit & Excalidraw #6 specification"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.1.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  FolderKanban, 
  Film, 
  ShoppingBag, 
  Play, 
  MoreVertical, 
  Clock, 
  Plus, 
  FolderPlus,
  ExternalLink,
  Layers,
  CheckCircle2,
  LayoutGrid,
  List,
  Sparkles,
  ChevronRight
} from 'lucide-react';

interface ProjectsWorkspaceSectionProps {
  onOpenProject: (projectId: string) => void;
}

const INITIAL_PROJECTS = [
  {
    id: 'proj_reburn_video_01',
    title: 'ReBurn Smoker v2 — Vertical Video Ad',
    folder: 'ReBurn Smoker v2',
    category: 'video',
    format: '9:16 (1080x1920)',
    duration: '0:30',
    tracksCount: '6 треків',
    updatedAt: '12 хв тому',
    status: 'Ready',
    thumbnailGradient: 'from-pink-950/70 via-purple-950/40 to-[#12151e]',
    icon: Film,
    iconColor: 'text-pink-400'
  },
  {
    id: 'proj_shopify_theme_02',
    title: 'Obsidian Aurora — Shopify Theme Liquid',
    folder: 'Shopify Themes',
    category: 'shopify',
    format: 'Liquid AST v2',
    duration: 'Multi-Section',
    tracksCount: '8 блоків',
    updatedAt: '2 години тому',
    status: 'Synced',
    thumbnailGradient: 'from-emerald-950/70 via-teal-950/40 to-[#12151e]',
    icon: ShoppingBag,
    iconColor: 'text-emerald-400'
  },
  {
    id: 'proj_dna_sequencer_03',
    title: 'Nano-Bio Reactor — 4K Equipment Promo',
    folder: 'Hardware Launch',
    category: 'video',
    format: '16:9 (4K UHD)',
    duration: '1:00',
    tracksCount: '4 треки',
    updatedAt: 'Вчора',
    status: 'Draft',
    thumbnailGradient: 'from-cyan-950/70 via-blue-950/40 to-[#12151e]',
    icon: Film,
    iconColor: 'text-cyan-400'
  },
  {
    id: 'proj_reburn_brief_04',
    title: 'ReBurn Customer Persona & Market Brief',
    folder: 'ReBurn Smoker v2',
    category: 'taskdna',
    format: 'SCONES Vault',
    duration: 'Doc Artifact',
    tracksCount: 'Verified',
    updatedAt: '2 дні тому',
    status: 'Verified',
    thumbnailGradient: 'from-indigo-950/70 via-purple-950/40 to-[#12151e]',
    icon: FolderKanban,
    iconColor: 'text-indigo-400'
  }
];

export default function ProjectsWorkspaceSection({ onOpenProject }: ProjectsWorkspaceSectionProps) {
  const [selectedFolder, setSelectedFolder] = useState('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [projects] = useState(INITIAL_PROJECTS);

  const folders = [
    { id: 'all', label: 'Всі проєкти (4)' },
    { id: 'ReBurn Smoker v2', label: '📁 ReBurn Smoker v2 (2)' },
    { id: 'Shopify Themes', label: '🛍️ Shopify Themes (1)' },
    { id: 'Hardware Launch', label: '🎬 Hardware Launch (1)' }
  ];

  const filteredProjects = selectedFolder === 'all'
    ? projects
    : projects.filter(p => p.folder === selectedFolder);

  return (
    <section className="mb-9" id="projects">
      {/* Section Header (Matching Excalidraw #6) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="font-bold text-lg text-white tracking-wide flex items-center gap-2 font-sans">
            <FolderKanban className="w-5 h-5 text-purple-400" />
            <span>Робочий кабінет конкретного Проєкту та папки</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5 font-sans">
            Усі ваші активні кампанії, відеоролики, лендінги та проєктні файли
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-white/5 text-slate-400">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-purple-600/30 text-white' : 'hover:text-white'}`}
              title="Сітка"
            >
              <LayoutGrid className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-purple-600/30 text-white' : 'hover:text-white'}`}
              title="Список"
            >
              <List className="w-3.5 h-3.5" />
            </button>
          </div>

          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-850 border border-white/10 text-xs font-semibold text-slate-200 transition-colors cursor-pointer shadow-sm">
            <FolderPlus className="w-3.5 h-3.5 text-purple-400" />
            <span>Нова папка</span>
          </button>
        </div>
      </div>

      {/* Folder Chips Filter */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 mb-4 scrollbar-none">
        {folders.map(f => (
          <button
            key={f.id}
            onClick={() => setSelectedFolder(f.id)}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all cursor-pointer ${
              selectedFolder === f.id
                ? 'bg-purple-600/25 text-purple-200 border border-purple-500/50 shadow-sm'
                : 'bg-[#141722]/80 text-slate-400 border border-white/5 hover:text-slate-200 hover:bg-[#1a1e2c]'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {filteredProjects.map((proj) => {
          const Icon = proj.icon;
          return (
            <div
              key={proj.id}
              className="rounded-2xl bg-[#141722]/90 border border-white/8 hover:border-purple-500/50 overflow-hidden group transition-all duration-250 hover:shadow-2xl hover:-translate-y-0.5 flex flex-col justify-between"
            >
              {/* Card Preview Header */}
              <div className={`h-36 bg-gradient-to-b ${proj.thumbnailGradient} p-3.5 flex flex-col justify-between relative overflow-hidden`}>
                <div className="flex items-center justify-between z-10">
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-slate-950/80 text-slate-300 border border-white/10">
                    {proj.format}
                  </span>
                  <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-500/30">
                    <CheckCircle2 className="w-2.5 h-2.5" />
                    {proj.status}
                  </span>
                </div>

                {/* Hover Play / Open Actions Overlay */}
                <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2.5">
                  <button
                    onClick={() => onOpenProject(proj.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold shadow-xl hover:scale-105 transition-transform cursor-pointer"
                    title="Відкрити в Студії Редагування"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Студія</span>
                  </button>
                  <Link
                    href="/os"
                    className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 shadow-xl hover:scale-105 transition-transform"
                    title="Відкрити на Stitch Canvas"
                  >
                    <Layers className="w-4 h-4 text-purple-300" />
                  </Link>
                </div>

                <div className="flex items-center justify-between z-10 text-[11px] font-mono text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <Icon className={`w-4 h-4 ${proj.iconColor}`} />
                    <span>{proj.duration}</span>
                  </div>
                  <span className="text-[10px] text-slate-500">{proj.tracksCount}</span>
                </div>
              </div>

              {/* Card Body */}
              <div className="p-3.5 flex flex-col justify-between flex-1">
                <div>
                  <span className="text-[10px] font-mono text-purple-400 uppercase font-semibold">
                    {proj.folder}
                  </span>
                  <h3 className="font-semibold text-xs text-white group-hover:text-purple-300 transition-colors mt-0.5 line-clamp-2 leading-tight">
                    {proj.title}
                  </h3>
                </div>

                <div className="mt-3.5 pt-2.5 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-600" />
                    <span>{proj.updatedAt}</span>
                  </div>
                  <button className="text-slate-500 hover:text-slate-300 p-0.5">
                    <MoreVertical className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
