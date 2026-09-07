/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/teleprompter/PrompterViewport.tsx"
// purpose: "Responsive Teleprompter Text Viewport with Auto-Scroll, Mirror Mode, and Touch Navigation."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

'use client';

import React, { useEffect, useRef } from 'react';
import type { RuntimeToken } from '@dnk/teleprompter-core';
import { ProsodyToken } from './ProsodyToken';

export type FontSizeOption = 'sm' | 'md' | 'lg' | 'xl' | '2xl';

interface PrompterViewportProps {
  tokens: RuntimeToken[];
  currentIndex: number;
  isMirrorMode?: boolean;
  fontSize?: FontSizeOption;
  isRecording?: boolean;
  onTokenClick?: (token: RuntimeToken) => void;
}

const fontSizeMap: Record<FontSizeOption, string> = {
  sm: 'text-lg leading-relaxed',
  md: 'text-2xl leading-relaxed',
  lg: 'text-3xl leading-loose',
  xl: 'text-4xl leading-loose',
  '2xl': 'text-5xl leading-loose',
};

export const PrompterViewport: React.FC<PrompterViewportProps> = ({
  tokens,
  currentIndex,
  isMirrorMode = false,
  fontSize = 'lg',
  onTokenClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeTokenRef = useRef<HTMLSpanElement | null>(null);

  // Group tokens by Scene -> Paragraph
  const groupedScenes = React.useMemo(() => {
    const scenes: {
      sceneId: string;
      sceneRole?: string;
      paragraphs: {
        paragraphId: string;
        speakerRole?: string;
        tokens: RuntimeToken[];
      }[];
    }[] = [];

    let currentScene: (typeof scenes)[0] | null = null;
    let currentParagraph: (typeof scenes)[0]['paragraphs'][0] | null = null;

    for (const token of tokens) {
      if (!currentScene || currentScene.sceneId !== token.sceneId) {
        currentScene = {
          sceneId: token.sceneId,
          sceneRole: token.sceneRole,
          paragraphs: [],
        };
        scenes.push(currentScene);
        currentParagraph = null;
      }

      if (!currentParagraph || currentParagraph.paragraphId !== token.paragraphId) {
        currentParagraph = {
          paragraphId: token.paragraphId,
          speakerRole: token.speakerRole,
          tokens: [],
        };
        currentScene.paragraphs.push(currentParagraph);
      }

      currentParagraph.tokens.push(token);
    }

    return scenes;
  }, [tokens]);

  // Auto-scroll effect: smooth center active token in viewport
  useEffect(() => {
    if (activeTokenRef.current && containerRef.current) {
      const container = containerRef.current;
      const element = activeTokenRef.current;
      const containerHeight = container.clientHeight;
      const elementTop = element.offsetTop;
      const elementHeight = element.offsetHeight;

      const targetScrollTop = elementTop - containerHeight / 2 + elementHeight / 2;
      container.scrollTo({
        top: Math.max(0, targetScrollTop),
        behavior: 'smooth',
      });
    }
  }, [currentIndex]);

  return (
    <div
      ref={containerRef}
      data-testid="prompter-viewport"
      className={`relative w-full h-full overflow-y-auto px-4 md:px-12 py-32 md:py-48 transition-transform duration-200 ${
        isMirrorMode ? '-scale-x-100' : ''
      }`}
      style={{
        WebkitOverflowScrolling: 'touch',
        scrollBehavior: 'smooth',
      }}
    >
      {/* Visual Center Reader Line Indicator */}
      <div className="pointer-events-none sticky top-1/2 left-0 right-0 -translate-y-1/2 border-y border-emerald-500/20 bg-emerald-500/5 h-20 -mx-12 z-0" />

      <div className={`relative z-10 max-w-4xl mx-auto space-y-10 font-sans ${fontSizeMap[fontSize]}`}>
        {groupedScenes.map((scene) => (
          <section
            key={scene.sceneId}
            data-scene-id={scene.sceneId}
            className="p-4 md:p-6 rounded-2xl bg-slate-900/40 backdrop-blur-sm border border-slate-800/60 shadow-xl"
          >
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800/80 text-xs font-mono text-slate-400">
              <span className="font-semibold text-emerald-400">
                SCENE: {scene.sceneId.toUpperCase()}
              </span>
              {scene.sceneRole && (
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  Role: {scene.sceneRole}
                </span>
              )}
            </div>

            <div className="space-y-6">
              {scene.paragraphs.map((para) => (
                <div key={para.paragraphId} className="space-y-2">
                  {para.speakerRole && (
                    <div className="text-xs font-mono text-indigo-400 font-semibold tracking-wide uppercase">
                      🎙️ {para.speakerRole}
                    </div>
                  )}
                  <div className="flex flex-wrap items-baseline content-start">
                    {para.tokens.map((token) => {
                      const isCurrent = token.index === currentIndex;
                      return (
                        <span
                          key={token.index}
                          ref={isCurrent ? activeTokenRef : null}
                          className="inline-block"
                        >
                          <ProsodyToken
                            token={token}
                            isCurrent={isCurrent}
                            onTokenClick={onTokenClick}
                          />
                        </span>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
};
