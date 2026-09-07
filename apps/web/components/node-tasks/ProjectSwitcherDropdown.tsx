// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/node-tasks/ProjectSwitcherDropdown.tsx"
// purpose: "Premium multi-tenant Project Switcher Dropdown with instant switching and project creation"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-06"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import React, { useState, useRef, useEffect } from 'react';
import {
  FolderKanban,
  ChevronDown,
  Check,
  Plus,
  Loader2,
  Sparkles,
  Layers,
  X,
} from 'lucide-react';
import { useNodeTasksStore } from '@/store/nodeTasksStore';
import { ProjectInfo } from '@/types/nodeTasks';

const COLOR_PRESETS = [
  '#3b82f6', // Blue (dnk_core)
  '#10b981', // Emerald (m_craft)
  '#8b5cf6', // Purple (brand_alpha)
  '#f59e0b', // Amber
  '#ec4899', // Pink
  '#06b6d4', // Cyan
  '#ef4444', // Red
];

export function ProjectSwitcherDropdown() {
  const {
    projects,
    activeProjectId,
    isProjectsLoading,
    setActiveProject,
    createProject,
  } = useNodeTasksStore();

  const [isOpen, setIsOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form state
  const [newId, setNewId] = useState('');
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newColor, setNewColor] = useState(COLOR_PRESETS[0]);

  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const activeProject: ProjectInfo | undefined = projects.find(
    (p) => p.id === activeProjectId
  ) || (projects.length > 0 ? projects[0] : undefined);

  const handleSelectProject = async (projectId: string) => {
    if (projectId === activeProjectId) {
      setIsOpen(false);
      return;
    }
    setIsOpen(false);
    await setActiveProject(projectId);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) {
      setErrorMessage('Назва проєкту обовʼязкова');
      return;
    }

    const generatedId = newId.trim()
      ? newId.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '_')
      : newName.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '_');

    setIsSubmitting(true);
    setErrorMessage(null);

    const res = await createProject({
      id: generatedId,
      name: newName.trim(),
      slug: generatedId.replace(/_/g, '-'),
      description: newDesc.trim() || undefined,
      color: newColor,
      is_active: true,
    });

    setIsSubmitting(false);

    if (res.success) {
      setShowCreateModal(false);
      setNewId('');
      setNewName('');
      setNewDesc('');
      setIsOpen(false);
    } else {
      setErrorMessage(res.error || 'Помилка створення проєкту');
    }
  };

  const displayColor = activeProject?.color || '#3b82f6';
  const displayName = activeProject?.name || activeProjectId || 'dnk_core';
  const displayTasksCount = activeProject?.tasks_count ?? 0;

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="group flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-zinc-900/90 hover:bg-zinc-800/90 border border-zinc-700/60 hover:border-zinc-500/80 backdrop-blur-md transition-all shadow-md active:scale-95 text-xs text-zinc-200"
        title="Перемкнути активний проєкт"
      >
        <span
          className="w-2.5 h-2.5 rounded-full ring-2 ring-black/40 shadow-sm transition-transform group-hover:scale-110"
          style={{ backgroundColor: displayColor }}
        />
        <FolderKanban className="w-3.5 h-3.5 text-zinc-400 group-hover:text-zinc-200 transition-colors" />
        <span className="font-semibold text-zinc-100 max-w-[140px] truncate">
          {displayName}
        </span>
        <span className="px-1.5 py-0.2 rounded-md bg-zinc-800 border border-zinc-700 text-[10px] font-mono text-zinc-400">
          {displayTasksCount}
        </span>
        {isProjectsLoading ? (
          <Loader2 className="w-3.5 h-3.5 text-zinc-400 animate-spin" />
        ) : (
          <ChevronDown
            className={`w-3.5 h-3.5 text-zinc-400 transition-transform duration-200 ${
              isOpen ? 'rotate-180 text-zinc-100' : ''
            }`}
          />
        )}
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute left-0 mt-2 w-72 rounded-2xl bg-zinc-950/95 border border-zinc-800/80 shadow-2xl backdrop-blur-xl z-50 p-1.5 animate-in fade-in zoom-in-95 duration-150">
          <div className="px-3 py-2 border-b border-zinc-800/60 mb-1 flex items-center justify-between">
            <span className="text-[11px] font-medium uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
              <Layers className="w-3 h-3 text-cyan-400" />
              Проєкти & Тенанти
            </span>
            <span className="text-[10px] font-mono text-zinc-500">
              {projects.length} активних
            </span>
          </div>

          <div className="max-h-60 overflow-y-auto space-y-1 py-1 custom-scrollbar">
            {projects.map((project) => {
              const isSelected = project.id === activeProjectId;
              const pColor = project.color || '#3b82f6';
              return (
                <button
                  key={project.id}
                  type="button"
                  onClick={() => handleSelectProject(project.id)}
                  className={`w-full text-left px-3 py-2 rounded-xl text-xs flex items-center justify-between gap-2.5 transition-all ${
                    isSelected
                      ? 'bg-zinc-800/90 text-white font-medium shadow-sm border border-zinc-700/60'
                      : 'text-zinc-300 hover:bg-zinc-900/80 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0 shadow-sm"
                      style={{ backgroundColor: pColor }}
                    />
                    <div className="min-w-0">
                      <div className="truncate font-medium">{project.name}</div>
                      <div className="text-[10px] text-zinc-500 font-mono truncate">
                        {project.id}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="px-1.5 py-0.5 rounded-md bg-zinc-900 border border-zinc-800 text-[10px] font-mono text-zinc-400">
                      {project.tasks_count ?? 0}
                    </span>
                    {isSelected && <Check className="w-3.5 h-3.5 text-cyan-400" />}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Action Row */}
          <div className="pt-2 mt-1 border-t border-zinc-800/60">
            <button
              type="button"
              onClick={() => {
                setShowCreateModal(true);
                setIsOpen(false);
              }}
              className="w-full py-2 px-3 rounded-xl bg-gradient-to-r from-cyan-950/60 to-blue-950/60 hover:from-cyan-900/80 hover:to-blue-900/80 border border-cyan-800/50 hover:border-cyan-600/70 text-cyan-200 hover:text-cyan-100 text-xs font-medium flex items-center justify-center gap-2 transition-all shadow-sm active:scale-[0.98]"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>+ Новий проєкт</span>
            </button>
          </div>
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-md bg-zinc-950 border border-zinc-800 rounded-2xl shadow-2xl overflow-hidden p-6 relative">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="absolute top-4 right-4 text-zinc-400 hover:text-zinc-200 transition-colors p-1 rounded-lg hover:bg-zinc-900"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-2.5 mb-5">
              <div className="w-9 h-9 rounded-xl bg-cyan-950/80 border border-cyan-800/60 flex items-center justify-center text-cyan-300">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-zinc-100">Створити новий проєкт</h3>
                <p className="text-[11px] text-zinc-400">
                  Ізольований робочий простір задач та DAG графа
                </p>
              </div>
            </div>

            {errorMessage && (
              <div className="mb-4 p-2.5 rounded-xl bg-red-950/70 border border-red-800/70 text-red-300 text-xs">
                {errorMessage}
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-1">
                  Назва проєкту <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="напр. Brand Alpha E-Com"
                  value={newName}
                  onChange={(e) => {
                    setNewName(e.target.value);
                    if (!newId) {
                      setNewId(
                        e.target.value
                          .toLowerCase()
                          .replace(/[^a-z0-9_-]/g, '_')
                          .slice(0, 30)
                      );
                    }
                  }}
                  className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-cyan-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-1">
                  Ідентифікатор (ID)
                </label>
                <input
                  type="text"
                  placeholder="напр. brand_alpha"
                  value={newId}
                  onChange={(e) => setNewId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-xs font-mono text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-cyan-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-1">
                  Опис (опціонально)
                </label>
                <textarea
                  rows={2}
                  placeholder="Короткий опис цілей та задач проєкту..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-cyan-500 transition-colors resize-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-2">
                  Колір проєкту
                </label>
                <div className="flex items-center gap-2">
                  {COLOR_PRESETS.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setNewColor(color)}
                      className={`w-6 h-6 rounded-full transition-transform ${
                        newColor === color
                          ? 'scale-125 ring-2 ring-white ring-offset-2 ring-offset-zinc-950'
                          : 'hover:scale-110 opacity-75 hover:opacity-100'
                      }`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs transition-colors"
                >
                  Скасувати
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-medium flex items-center gap-1.5 transition-all shadow-md active:scale-95"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Створення...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      Створити проєкт
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
