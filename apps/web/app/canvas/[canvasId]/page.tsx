// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_app_canvas_page"
// purpose: "Interactive Visual Shell (Robochyi Kabinet) page component mounting CanvasEditor and ArtifactPanel"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-11"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import dynamic from 'next/dynamic';
const CanvasEditor = dynamic(() => import('../../../components/canvas/CanvasEditor'), { ssr: false });
import ArtifactPanel from '../../../components/canvas/ArtifactPanel';

export default function CanvasPage() {
  const params = useParams();
  const canvasId = (params?.canvasId as string) || 'default-canvas-id';
  
  const [canvasData, setCanvasData] = useState<any>(null);
  const [artifactData, setArtifactData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isRunningAgent, setIsRunningAgent] = useState(false);
  const [flowLog, setFlowLog] = useState<string[]>([]);

  // Load Canvas & Artifact data
  const loadData = async () => {
    try {
      const canvasRes = await fetch(`/api/canvas/${canvasId}`);
      if (canvasRes.ok) {
        const cData = await canvasRes.json();
        setCanvasData(cData);
      } else {
        // Fallback for clean MVP run
        setCanvasData({ id: canvasId, name: 'Моя Робоча Область (MVP)', elements: { nodes: [] } });
      }

      const artRes = await fetch(`/api/artifact/${canvasId}`);
      if (artRes.ok) {
        const aData = await artRes.json();
        setArtifactData(aData);
      }
    } catch (e) {
      console.error('Failed to load canvas data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [canvasId]);

  const handleRunAgent = async () => {
    setIsRunningAgent(true);
    setFlowLog(['🚀 Запуск агентного флоу...', '🔍 Крок 1: Дослідження (Research)...']);
    try {
      const res = await fetch('/api/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          canvas_id: canvasId,
          flow_type: 'research_write_validate',
          query: 'Агентна архітектура DNK OS'
        })
      });
      
      const data = await res.json();
      if (res.ok && data.success) {
        setFlowLog(prev => [
          ...prev,
          '✍️ Крок 2: Генерація та Запис артефакту (Write)...',
          '🛡️ Перевірка Security Gate пройдена успішно!',
          '✅ Крок 3: Валідація (Validate) пройдена!',
          '🎉 Флоу завершено!'
        ]);
        setArtifactData({ canvas_id: canvasId, content: data.content });
      } else {
        setFlowLog(prev => [...prev, `❌ Помилка запуску агента: ${data.detail || 'Невідома помилка'}`]);
      }
    } catch (e: any) {
      setFlowLog(prev => [...prev, `❌ Мережева помилка: ${e.message}`]);
    } finally {
      setIsRunningAgent(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-white font-sans">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
          <div className="text-slate-400 text-sm">Завантаження кабінету...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col p-6 gap-6 selection:bg-blue-600/30">
      <header className="flex justify-between items-center bg-slate-900/40 border border-slate-800/60 p-4 rounded-2xl backdrop-blur-md">
        <div className="flex items-center gap-3">
          <span className="text-3xl">💻</span>
          <div>
            <h1 className="text-xl font-extrabold text-white tracking-wide">Герич: Робочий Кабінет</h1>
            <p className="text-xs text-slate-500 font-medium">Visual Shell v1.0.0 (Robochyi Kabinet MVP)</p>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleRunAgent}
            disabled={isRunningAgent}
            className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 active:scale-95 disabled:opacity-50 transition-all rounded-xl font-bold tracking-wide shadow-lg cursor-pointer"
          >
            {isRunningAgent ? '🤖 Агент працює...' : '🤖 Запустити Агента'}
          </button>
        </div>
      </header>

      {flowLog.length > 0 && (
        <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-2xl font-mono text-xs text-blue-400 space-y-1">
          {flowLog.map((log, idx) => (
            <div key={idx}>{log}</div>
          ))}
        </div>
      )}

      <main className="flex-grow grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[500px]">
        <CanvasEditor
          canvasId={canvasId}
          canvasData={canvasData}
          onUpdate={(updated) => setCanvasData(updated)}
        />
        <ArtifactPanel
          canvasId={canvasId}
          artifactData={artifactData}
          onUpdate={(updated) => setArtifactData(updated)}
        />
      </main>
    </div>
  );
}
