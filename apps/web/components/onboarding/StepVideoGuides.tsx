// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/onboarding/StepVideoGuides.tsx"
// purpose: "Video Guides Step 3 for DNK OS Interactive Onboarding Wizard"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Play, Clock, ExternalLink, ArrowRight, ArrowLeft, Video, CheckCircle2 } from 'lucide-react';

export interface StepVideoGuidesProps {
  onNext: () => void;
  onBack: () => void;
  onSkip: () => void;
}

interface VideoItem {
  id: string;
  title: string;
  duration: string;
  description: string;
  youtubeId: string;
  badgeColor: string;
}

const VIDEOS: VideoItem[] = [
  {
    id: 'intro',
    title: 'DNK OS за 5 хвилин',
    duration: '5:32',
    description: 'Огляд архітектури, рою з 14 агентів та можливостей швидкого старту.',
    youtubeId: 'dQw4w9WgXcQ',
    badgeColor: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
  },
  {
    id: 'first_canvas',
    title: 'Як створити перший canvas',
    duration: '8:15',
    description: 'Покроковий гайд по роботі з вузлами полотна, шаблонами та генерацією.',
    youtubeId: 'dQw4w9WgXcQ',
    badgeColor: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
  },
  {
    id: 'advanced_features',
    title: 'Advanced features overview',
    duration: '12:45',
    description: 'Оркестрація рою, WebSocket sync, Remotion генерація та аудит безпеки.',
    youtubeId: 'dQw4w9WgXcQ',
    badgeColor: 'bg-purple-500/20 text-purple-300 border-purple-500/30'
  }
];

export const StepVideoGuides: React.FC<StepVideoGuidesProps> = ({ onNext, onBack, onSkip }) => {
  const [activeVideo, setActiveVideo] = useState<VideoItem | null>(null);

  return (
    <section
      aria-label="Відеопосібники DNK OS"
      className="flex flex-col py-4 px-3 max-w-2xl mx-auto w-full"
    >
      <div className="text-center mb-5">
        <h2 className="text-2xl font-bold text-white mb-2 flex items-center justify-center gap-2">
          <Video className="w-6 h-6 text-indigo-400" aria-hidden="true" />
          Відеоінструкції та швидкий старт
        </h2>
        <p className="text-sm text-gray-300">
          Опануйте ключові інструменти платформи за допомогою коротких та інформативних відеогідів.
        </p>
      </div>

      {/* Video Modal or Active Video Player */}
      {activeVideo ? (
        <div className="mb-5 bg-[#0b0f19] border border-white/15 rounded-2xl p-4 shadow-2xl">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-white/10">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-white">{activeVideo.title}</span>
              <span className="text-[11px] font-mono text-gray-400">({activeVideo.duration})</span>
            </div>
            <button
              onClick={() => setActiveVideo(null)}
              type="button"
              className="text-xs text-gray-400 hover:text-white px-2 py-1 rounded bg-white/5"
            >
              Закрити відео
            </button>
          </div>
          <div className="relative aspect-video w-full rounded-xl overflow-hidden bg-black/60 flex items-center justify-center border border-white/10">
            <iframe
              src={`https://www.youtube-nocookie.com/embed/${activeVideo.youtubeId}?autoplay=1`}
              title={activeVideo.title}
              className="w-full h-full border-0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        </div>
      ) : null}

      {/* Videos List */}
      <div className="grid grid-cols-1 gap-3 mb-5">
        {VIDEOS.map((video) => (
          <div
            key={video.id}
            className="flex items-center justify-between p-3.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/10 hover:border-white/20 transition-all group"
          >
            <div className="flex items-start gap-3.5 pr-2">
              <button
                onClick={() => setActiveVideo(video)}
                type="button"
                aria-label={`Дивитися відео: ${video.title}`}
                className="w-10 h-10 rounded-xl bg-indigo-600/30 group-hover:bg-indigo-600 text-indigo-300 group-hover:text-white flex items-center justify-center flex-shrink-0 transition-colors border border-indigo-500/40"
              >
                <Play className="w-5 h-5 ml-0.5 fill-current" />
              </button>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-semibold text-white group-hover:text-indigo-300 transition-colors">
                    {video.title}
                  </h3>
                  {/* Duration Badge */}
                  <span className={`inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-md border ${video.badgeColor}`}>
                    <Clock className="w-3 h-3" />
                    {video.duration}
                  </span>
                </div>
                <p className="text-xs text-gray-400 leading-snug">{video.description}</p>
              </div>
            </div>

            <button
              onClick={() => setActiveVideo(video)}
              type="button"
              className="text-xs font-medium text-cyan-400 hover:text-cyan-300 flex items-center gap-1 flex-shrink-0 px-2.5 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 transition-colors"
            >
              <span>Дивитися</span>
              <Play className="w-3 h-3 fill-current" />
            </button>
          </div>
        ))}
      </div>

      {/* External Catalog Link / CTA */}
      <div className="flex items-center justify-center mb-6">
        <a
          href="/docs/user-guides/VIDEO_TUTORIALS.md"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-xs font-medium text-gray-300 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] px-4 py-2 rounded-xl border border-white/10 transition-colors"
        >
          <span>Дивитися всі відео</span>
          <ExternalLink className="w-3.5 h-3.5 text-gray-400" />
        </a>
      </div>

      {/* Navigation Footer */}
      <div className="flex items-center justify-between w-full pt-2">
        <button
          onClick={onBack}
          type="button"
          className="px-4 py-2.5 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-gray-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Назад</span>
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={onSkip}
            type="button"
            className="px-3 py-2 text-gray-400 hover:text-gray-200 text-xs transition-colors"
          >
            Пропустити
          </button>
          <button
            onClick={onNext}
            type="button"
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-cyan-500/20 transition-all"
          >
            <span>Далі</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </section>
  );
};

export default StepVideoGuides;
