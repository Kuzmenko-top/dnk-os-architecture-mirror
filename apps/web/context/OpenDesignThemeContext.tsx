// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_context_OpenDesignThemeContext"
// purpose: "Open Design Theme Context providing dynamic design systems (Stitch, Linear, Stripe, Luxury, Neon, Light) and brand accents"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export interface DesignSystemPreset {
  id: string;
  name: string;
  category: string;
  description: string;
  bgDark: string;
  cardBg: string;
  borderColor: string;
  primaryAccent: string;
  accentGradient: string;
  glowColor: string;
  badge: string;
}

export const OPEN_DESIGN_PRESETS: DesignSystemPreset[] = [
  {
    id: 'stitch',
    name: 'Google Stitch (Default)',
    category: 'Spatial AI',
    description: 'Глибокий нейтральний темно-сірий фон, мінімалістичні скляні плашки та фірмовий фіолетовий акцент.',
    bgDark: '#0e1017',
    cardBg: 'rgba(22, 25, 34, 0.85)',
    borderColor: 'rgba(255, 255, 255, 0.08)',
    primaryAccent: '#a855f7',
    accentGradient: 'from-purple-600 to-indigo-600',
    glowColor: 'rgba(168, 85, 247, 0.35)',
    badge: 'Stitch 2.0'
  },
  {
    id: 'linear',
    name: 'Linear Precision',
    category: 'Productivity',
    description: 'Надчистий темно-синій інтерфейс, висока щільність інструментів, індиго-акценти та швидкі шорткати.',
    bgDark: '#0b0c10',
    cardBg: 'rgba(18, 20, 29, 0.9)',
    borderColor: 'rgba(99, 102, 241, 0.15)',
    primaryAccent: '#6366f1',
    accentGradient: 'from-indigo-500 to-blue-600',
    glowColor: 'rgba(99, 102, 241, 0.3)',
    badge: 'Linear'
  },
  {
    id: 'stripe',
    name: 'Stripe Obsidian Aurora',
    category: 'Fintech & E-Com',
    description: 'Багатий неоново-смарагдовий та лазурний градієнтний меш, 3D картки та преміальне сяйво.',
    bgDark: '#070b14',
    cardBg: 'rgba(11, 18, 32, 0.88)',
    borderColor: 'rgba(16, 185, 129, 0.2)',
    primaryAccent: '#10b981',
    accentGradient: 'from-emerald-500 via-teal-500 to-cyan-500',
    glowColor: 'rgba(16, 185, 129, 0.35)',
    badge: 'Stripe'
  },
  {
    id: 'luxury',
    name: 'Luxury Midnight Gold',
    category: 'Brand & Identity',
    description: 'Глибокий преміальний чорний фон із теплими бурштиново-золотими акцентами для ReBurn Smoker.',
    bgDark: '#050507',
    cardBg: 'rgba(18, 16, 22, 0.92)',
    borderColor: 'rgba(245, 158, 11, 0.22)',
    primaryAccent: '#f59e0b',
    accentGradient: 'from-amber-500 to-orange-600',
    glowColor: 'rgba(245, 158, 11, 0.35)',
    badge: 'ReBurn Gold'
  },
  {
    id: 'neon',
    name: 'Cyberpunk Neon Studio',
    category: 'Media Creation',
    description: 'Висококонтрастний кіберпанк стиль з неоновим рожевим та електрик-ціаном для TikTok/Reels монтажу.',
    bgDark: '#080511',
    cardBg: 'rgba(25, 14, 38, 0.9)',
    borderColor: 'rgba(244, 63, 94, 0.3)',
    primaryAccent: '#f43f5e',
    accentGradient: 'from-pink-500 via-rose-500 to-purple-600',
    glowColor: 'rgba(244, 63, 94, 0.4)',
    badge: 'Viral Neon'
  },
  {
    id: 'clean_light',
    name: 'Clean Studio Light',
    category: 'Minimal Light',
    description: 'Світла тема в стилі Apple/Notion з м’якими тінями, високим контрастом та чистим читанням.',
    bgDark: '#f8fafc',
    cardBg: 'rgba(255, 255, 255, 0.95)',
    borderColor: 'rgba(0, 0, 0, 0.08)',
    primaryAccent: '#7c3aed',
    accentGradient: 'from-purple-600 to-indigo-600',
    glowColor: 'rgba(124, 58, 237, 0.2)',
    badge: 'Light'
  }
];

interface ThemeContextType {
  currentPreset: DesignSystemPreset;
  setPresetById: (id: string) => void;
  accentColor: string;
  setAccentColor: (color: string) => void;
  glassOpacity: number;
  setGlassOpacity: (val: number) => void;
  showLaunchpad: boolean;
  setShowLaunchpad: (val: boolean) => void;
  showProjects: boolean;
  setShowProjects: (val: boolean) => void;
  showMediaVault: boolean;
  setShowMediaVault: (val: boolean) => void;
  showTemplates: boolean;
  setShowTemplates: (val: boolean) => void;
}

const OpenDesignThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function OpenDesignThemeProvider({ children }: { children: React.ReactNode }) {
  const [currentPreset, setCurrentPreset] = useState<DesignSystemPreset>(OPEN_DESIGN_PRESETS[0]);
  const [accentColor, setAccentColor] = useState<string>(OPEN_DESIGN_PRESETS[0].primaryAccent);
  const [glassOpacity, setGlassOpacity] = useState<number>(85);
  
  // Custom Screen Layout Toggle Settings
  const [showLaunchpad, setShowLaunchpad] = useState(true);
  const [showProjects, setShowProjects] = useState(true);
  const [showMediaVault, setShowMediaVault] = useState(true);
  const [showTemplates, setShowTemplates] = useState(true);

  const setPresetById = (id: string) => {
    const found = OPEN_DESIGN_PRESETS.find(p => p.id === id);
    if (found) {
      setCurrentPreset(found);
      setAccentColor(found.primaryAccent);
    }
  };

  return (
    <OpenDesignThemeContext.Provider
      value={{
        currentPreset,
        setPresetById,
        accentColor,
        setAccentColor,
        glassOpacity,
        setGlassOpacity,
        showLaunchpad,
        setShowLaunchpad,
        showProjects,
        setShowProjects,
        showMediaVault,
        setShowMediaVault,
        showTemplates,
        setShowTemplates,
      }}
    >
      {children}
    </OpenDesignThemeContext.Provider>
  );
}

export function useOpenDesignTheme() {
  const context = useContext(OpenDesignThemeContext);
  if (!context) {
    throw new Error('useOpenDesignTheme must be used within OpenDesignThemeProvider');
  }
  return context;
}
