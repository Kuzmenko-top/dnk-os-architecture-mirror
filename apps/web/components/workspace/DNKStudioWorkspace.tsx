// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_workspace_DNKStudioWorkspace"
// purpose: "Pixel-perfect Google Stitch Canvas Workspace with full-bleed canvas, floating controls, and artboards."
// author: "DNK-e.com Maksym"
// status: "Active"
// version: "3.2.0"
// updated_at: "2026-09-03"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import { Node } from '@xyflow/react';
import CanvasEngine from '../canvas/CanvasEngine';
import StitchTopNav from '../canvas/StitchTopNav';
import StitchSpatialToolbar from '../canvas/StitchSpatialToolbar';
import StitchPromptDock from '../canvas/StitchPromptDock';
import StitchCanvasControls from '../canvas/StitchCanvasControls';
import StitchGenerationStatusCard from '../canvas/StitchGenerationStatusCard';
import StitchAgentLog from '../canvas/StitchAgentLog';
import { useCanvasStore } from '../../store/canvasStore';
import {
  StitchSwarmCommandCenter,
  StitchKineticTimeline,
  StitchSmartInspector,
  StitchShopifyPreviewDrawer,
  StitchBiAnalystDrawer,
  StitchTaskForestDrawer
} from '../stitch';

// Initial Google Stitch High-Fidelity Artboards replicating reference UI
const INITIAL_STITCH_NODES: Node[] = [
  {
    id: 'stitch-thumb-metrics',
    type: 'stitchArtboard',
    position: { x: 50, y: 120 },
    data: {
      title: 'DNK-ECOM 202... (Thumb 1)',
      artboardType: 'thumb-metrics',
      status: 'Ready',
    },
  },
  {
    id: 'stitch-thumb-typo',
    type: 'stitchArtboard',
    position: { x: 380, y: 120 },
    data: {
      title: 'DNK-ECOM 202... (Thumb 2)',
      artboardType: 'thumb-typo',
      status: 'Ready',
    },
  },
  {
    id: 'stitch-design-system',
    type: 'stitchArtboard',
    position: { x: 710, y: 120 },
    data: {
      title: 'DNK-ECOM 202... Obsidian Flow',
      artboardType: 'design-system',
      status: 'Design System',
    },
  },
  {
    id: 'stitch-mobile-home',
    type: 'stitchArtboard',
    position: { x: 1780, y: 120 },
    data: {
      title: 'Головна (...',
      artboardType: 'mobile-home',
      status: 'Mobile 1',
    },
  },
  {
    id: 'stitch-mobile-exec',
    type: 'stitchArtboard',
    position: { x: 2150, y: 120 },
    data: {
      title: 'Executive ...',
      artboardType: 'mobile-exec',
      status: 'Mobile 2',
    },
  },
  {
    id: 'stitch-desktop-report',
    type: 'stitchArtboard',
    position: { x: 2530, y: 120 },
    data: {
      title: 'Executive Mentor Report (Desktop)',
      artboardType: 'desktop-report',
      status: 'Executive Terminal',
    },
  },
];

export default function DNKStudioWorkspace() {
  const [activeTool, setActiveTool] = useState<string>('select');
  const [showStatusCard, setShowStatusCard] = useState<boolean>(false);
  const [activeDrawer, setActiveDrawer] = useState<'swarm' | 'timeline' | 'inspector' | 'shopify' | 'bi' | 'forest' | null>(null);
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'info' | 'warning' | 'error' } | null>(null);
  const { nodes, setNodes, setEdges } = useCanvasStore();

  const handleNotification = (msg: { text: string; type: 'success' | 'info' | 'warning' | 'error' }) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 4000);
  };

  const toggleDrawer = (drawer: 'swarm' | 'timeline' | 'inspector' | 'shopify' | 'bi' | 'forest') => {
    setActiveDrawer((prev) => (prev === drawer ? null : drawer));
  };

  useEffect(() => {
    // If nodes are empty or have legacy single node, initialize with Google Stitch Artboard layouts
    if (!nodes || nodes.length === 0 || nodes.some((n) => n.id === 'root-agent-1' || n.type === 'strategyNode')) {
      setNodes(INITIAL_STITCH_NODES);
      setEdges([]);
    }
  }, [nodes, setNodes, setEdges]);

  return (
    <div className="flex flex-col w-screen h-screen overflow-hidden bg-[#0e1014] select-none text-white font-sans">
      {/* 1. Google Stitch Top Navigation Bar */}
      <StitchTopNav
        projectName="Custom Main Screen Redesign"
        onExport={() => alert('Exporting Google Stitch Canvas Artifacts...')}
        onShare={() => alert('Project share link copied to clipboard!')}
        onPlayPreview={() => alert('Opening Live Design Preview...')}
        onToggleSwarm={() => toggleDrawer('swarm')}
        onToggleTimeline={() => toggleDrawer('timeline')}
        onToggleShopify={() => toggleDrawer('shopify')}
        onToggleBi={() => toggleDrawer('bi')}
        onToggleForest={() => toggleDrawer('forest')}
        activeDrawer={activeDrawer}
      />

      {/* 2. Full-Bleed Infinite Canvas Workspace */}
      <div className="relative flex-1 w-full h-full overflow-hidden bg-[#0e1014]">
        {/* Full Interactive Canvas Surface */}
        <CanvasEngine />

        {/* 3. Top-Left: Google Stitch AI Generation Status Card */}
        {showStatusCard && (
          <StitchGenerationStatusCard
            userPrompt="прибери останній к..."
            errorMessage="Something unexpected happened, and Stitch couldn't complete your generation. Please try again in a moment."
            onRetry={() => {
              console.log('Retrying generation in Stitch Canvas...');
            }}
          />
        )}

        {/* 4. Bottom-Left: Google Stitch Agent Log Pill Widget */}
        <div className="absolute bottom-6 left-6 z-30">
          <StitchAgentLog />
        </div>

        {/* 5. Left/Floating: Google Stitch Spatial Toolbar */}
        <StitchSpatialToolbar
          activeTool={activeTool}
          onSelectTool={(tool) => {
            setActiveTool(tool);
          }}
        />

        {/* 6. Center Bottom: Google Stitch Prompt Command Dock */}
        <StitchPromptDock
          onSubmitPrompt={(prompt) => {
            handleNotification({
              text: `✨ Запит передано в Рій Агентів: "${prompt.slice(0, 35)}..."`,
              type: 'info'
            });
            setShowStatusCard(false);
          }}
          isLoading={false}
        />

        {/* 7. Bottom Right: Google Stitch Canvas Controls (Undo, Redo, Zoom %, Help) */}
        <StitchCanvasControls />

        {/* 8. Floating Toast Notification Banner */}
        {toastMessage && (
          <div className="absolute top-20 right-6 z-50 flex items-center gap-2.5 px-4 py-2.5 rounded-xl border backdrop-blur-xl shadow-2xl transition-all animate-in fade-in slide-in-from-top-2 bg-[#161921]/95 border-emerald-500/40 text-emerald-300 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>{toastMessage.text}</span>
          </div>
        )}

        {/* 9. Interactive Spatial Drawers */}
        <StitchSwarmCommandCenter
          isOpen={activeDrawer === 'swarm'}
          onClose={() => setActiveDrawer(null)}
          onNotification={handleNotification}
        />

        {activeDrawer === 'timeline' && (
          <div className="absolute bottom-24 left-6 right-6 z-40">
            <StitchKineticTimeline
              onNotification={handleNotification}
            />
          </div>
        )}

        {activeDrawer === 'inspector' && (
          <div className="absolute top-20 right-6 z-40 w-96">
            <StitchSmartInspector
              onClose={() => setActiveDrawer(null)}
              onNotification={handleNotification}
            />
          </div>
        )}

        {activeDrawer === 'shopify' && (
          <StitchShopifyPreviewDrawer
            onClose={() => setActiveDrawer(null)}
            onNotification={handleNotification}
          />
        )}

        {activeDrawer === 'bi' && (
          <StitchBiAnalystDrawer
            onClose={() => setActiveDrawer(null)}
            onNotification={handleNotification}
          />
        )}

        {activeDrawer === 'forest' && (
          <StitchTaskForestDrawer
            onClose={() => setActiveDrawer(null)}
            onNotification={handleNotification}
          />
        )}
      </div>
    </div>
  );
}

export { DNKStudioWorkspace };
