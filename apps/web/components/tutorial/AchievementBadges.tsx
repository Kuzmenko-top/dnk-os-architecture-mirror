// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/tutorial/AchievementBadges.tsx"
// purpose: "Achievement Badges System with Collection Gallery, Shareable Cards, and LocalStorage State"
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
import {
  Target,
  Zap,
  Trophy,
  Palette,
  Share2,
  Check,
  Lock,
  ExternalLink,
  Sparkles,
  Copy,
  Users
} from 'lucide-react';

export interface AchievementBadge {
  id: string;
  title: string;
  iconName: string;
  emoji: string;
  description: string;
  criteria: string;
  isUnlocked: boolean;
  unlockedAt?: string;
  category: 'tutorial' | 'speed' | 'onboarding' | 'mastery';
}

export const INITIAL_BADGES: AchievementBadge[] = [
  {
    id: 'first-canvas',
    title: 'First Canvas',
    iconName: 'Target',
    emoji: '🎯',
    description: 'Створив перше полотно',
    criteria: 'Створіть свій перший Canvas у робочому просторі DNK OS.',
    isUnlocked: false,
    category: 'tutorial'
  },
  {
    id: 'quick-learner',
    title: 'Quick Learner',
    iconName: 'Zap',
    emoji: '⚡',
    description: 'Пройшов tutorial < 5 хв',
    criteria: 'Завершіть інтерактивний тур менш ніж за 5 хвилин.',
    isUnlocked: false,
    category: 'speed'
  },
  {
    id: 'onboarding-complete',
    title: 'Onboarding Complete',
    iconName: 'Trophy',
    emoji: '🏆',
    description: 'Завершив onboarding',
    criteria: 'Пройдіть усі етапи онбордингу та підготуйте робочий простір.',
    isUnlocked: false,
    category: 'onboarding'
  },
  {
    id: 'creative-mind',
    title: 'Creative Mind',
    iconName: 'Palette',
    emoji: '🎨',
    description: 'Створив 3+ canvases',
    criteria: 'Згенеруйте 3 або більше різних віртуальних полотен.',
    isUnlocked: false,
    category: 'mastery'
  }
];

export interface AchievementBadgesProps {
  badges?: AchievementBadge[];
  onShareBadge?: (badge: AchievementBadge) => void;
  className?: string;
  showCollectionPage?: boolean;
}

export const AchievementBadges: React.FC<AchievementBadgesProps> = ({
  badges = INITIAL_BADGES,
  onShareBadge,
  className = '',
  showCollectionPage = false
}) => {
  const [selectedBadge, setSelectedBadge] = useState<AchievementBadge | null>(null);
  const isModalOpen = selectedBadge !== null;
  const [copiedBadgeId, setCopiedBadgeId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'collection'>(showCollectionPage ? 'collection' : 'grid');

  const unlockedCount = badges.filter(b => b.isUnlocked).length;

  const handleShare = (badge: AchievementBadge) => {
    if (onShareBadge) {
      onShareBadge(badge);
    }
    const shareText = `Я щойно розблокував бейдж "${badge.emoji} ${badge.title}" у DNK OS! 🚀 #DNK_OS #AI_Swarm`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(shareText).then(() => {
        setCopiedBadgeId(badge.id);
        setTimeout(() => setCopiedBadgeId(null), 3000);
      }).catch(() => {});
    }
  };

  const getBadgeIcon = (iconName: string, isUnlocked: boolean) => {
    const iconClass = isUnlocked ? 'w-5 h-5 text-white' : 'w-5 h-5 text-gray-500';
    switch (iconName) {
      case 'Target':
        return <Target className={iconClass} aria-hidden="true" />;
      case 'Zap':
        return <Zap className={iconClass} aria-hidden="true" />;
      case 'Trophy':
        return <Trophy className={iconClass} aria-hidden="true" />;
      case 'Palette':
        return <Palette className={iconClass} aria-hidden="true" />;
      default:
        return <Sparkles className={iconClass} aria-hidden="true" />;
    }
  };

  return (
    <div
      role="region"
      aria-label="Колекція бейджів досягнень"
      className={`w-full ${className}`}
    >
      {/* Header with collection count & view toggle */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Trophy className="w-4 h-4 text-amber-400" aria-hidden="true" />
          <h4 className="text-sm font-bold text-white">Колекція досягнень</h4>
          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20 font-mono">
            {unlockedCount} / {badges.length}
          </span>
        </div>

        <div className="flex items-center gap-1 bg-white/5 rounded-lg p-0.5 border border-white/10">
          <button
            type="button"
            onClick={() => setViewMode('grid')}
            aria-pressed={viewMode === 'grid'}
            className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
              viewMode === 'grid'
                ? 'bg-cyan-500 text-black font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Огляд
          </button>
          <button
            type="button"
            onClick={() => setViewMode('collection')}
            aria-pressed={viewMode === 'collection'}
            className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
              viewMode === 'collection'
                ? 'bg-cyan-500 text-black font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Колекція
          </button>
        </div>
      </div>

      {/* Grid View */}
      {viewMode === 'grid' && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {badges.map((badge) => {
            const isUnlocked = badge.isUnlocked;
            return (
              <div
                key={badge.id}
                role="article"
                aria-label={`Бейдж: ${badge.title}, ${isUnlocked ? 'Розблоковано' : 'Заблоковано'}`}
                tabIndex={0}
                onClick={() => setSelectedBadge(badge)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    setSelectedBadge(badge);
                  }
                }}
                className={`p-3 rounded-xl border text-center transition-all cursor-pointer relative group focus:outline-none focus:ring-2 focus:ring-cyan-400 ${
                  isUnlocked
                    ? 'bg-gradient-to-b from-cyan-950/40 to-[#0b0f19] border-cyan-500/40 hover:border-cyan-400 shadow-lg shadow-cyan-950/30'
                    : 'bg-white/[0.02] border-white/10 opacity-70 hover:opacity-90'
                }`}
              >
                {/* Badge Icon / Emoji */}
                <div
                  className={`w-10 h-10 mx-auto rounded-xl flex items-center justify-center mb-2 transition-transform group-hover:scale-105 ${
                    isUnlocked
                      ? 'bg-gradient-to-tr from-cyan-500 to-blue-600 shadow-md shadow-cyan-500/30'
                      : 'bg-gray-800 text-gray-500'
                  }`}
                >
                  {isUnlocked ? (
                    <span className="text-xl" role="img" aria-label={badge.title}>
                      {badge.emoji}
                    </span>
                  ) : (
                    <Lock className="w-4 h-4 text-gray-500" aria-hidden="true" />
                  )}
                </div>

                <div className="text-xs font-bold text-white truncate mb-0.5">
                  {badge.title}
                </div>
                <div className="text-[10px] text-gray-400 line-clamp-1">
                  {badge.description}
                </div>

                {isUnlocked && (
                  <div className="mt-1.5 flex justify-center">
                    <span className="inline-flex items-center gap-0.5 text-[9px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded-full">
                      <Check className="w-2.5 h-2.5" />
                      Отримано
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Collection Detailed View */}
      {viewMode === 'collection' && (
        <div className="space-y-2.5">
          {badges.map((badge) => {
            const isUnlocked = badge.isUnlocked;
            const isCopied = copiedBadgeId === badge.id;
            return (
              <div
                key={badge.id}
                role="article"
                aria-label={`Бейдж: ${badge.title}, ${isUnlocked ? 'Розблоковано' : 'Заблоковано'}`}
                className={`p-3.5 rounded-xl border flex items-center justify-between gap-3 transition-all ${
                  isUnlocked
                    ? 'bg-cyan-950/20 border-cyan-500/30'
                    : 'bg-white/[0.02] border-white/5 opacity-60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${
                      isUnlocked
                        ? 'bg-gradient-to-tr from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20'
                        : 'bg-gray-800'
                    }`}
                  >
                    {isUnlocked ? (
                      <span className="text-2xl" role="img" aria-label={badge.title}>
                        {badge.emoji}
                      </span>
                    ) : (
                      <Lock className="w-5 h-5 text-gray-500" aria-hidden="true" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h5 className="text-sm font-bold text-white">{badge.title}</h5>
                      {isUnlocked ? (
                        <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                          Unlocked ✅
                        </span>
                      ) : (
                        <span className="text-[10px] text-gray-500 bg-gray-800 px-1.5 py-0.5 rounded">
                          Locked 🔒
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-300 mt-0.5">{badge.description}</p>
                    <p className="text-[11px] text-gray-500 font-mono mt-0.5">{badge.criteria}</p>
                  </div>
                </div>

                {isUnlocked && (
                  <button
                    type="button"
                    onClick={() => handleShare(badge)}
                    aria-label={`Поділитися бейджем ${badge.title}`}
                    className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-cyan-300 hover:text-white border border-cyan-500/30 text-xs font-medium focus:outline-none focus:ring-2 focus:ring-cyan-400 transition-colors"
                  >
                    {isCopied ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-300">Скопійовано!</span>
                      </>
                    ) : (
                      <>
                        <Share2 className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Поділитися</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Selected Badge Modal / Card Preview */}
      {selectedBadge && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="badge-modal-title"
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn"
          onClick={() => setSelectedBadge(null)}
        >
          <div
            className="bg-[#0b0f19] border border-cyan-500/40 rounded-2xl p-6 max-w-sm w-full text-center shadow-2xl relative"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center mb-4 shadow-lg shadow-cyan-500/30">
              <span className="text-3xl" role="img" aria-label={selectedBadge.title}>
                {selectedBadge.emoji}
              </span>
            </div>

            <h3 id="badge-modal-title" className="text-lg font-bold text-white mb-1">
              {selectedBadge.title}
            </h3>
            <p className="text-sm text-cyan-300 mb-2">{selectedBadge.description}</p>
            <p className="text-xs text-gray-400 bg-white/5 p-3 rounded-xl border border-white/10 mb-5">
              {selectedBadge.criteria}
            </p>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setSelectedBadge(null)}
                className="flex-1 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 text-xs font-semibold transition-colors"
              >
                Закрити
              </button>
              {selectedBadge.isUnlocked && (
                <button
                  type="button"
                  onClick={() => handleShare(selectedBadge)}
                  className="flex-1 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Share2 className="w-3.5 h-3.5" />
                  <span>Поділитися</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AchievementBadges;
