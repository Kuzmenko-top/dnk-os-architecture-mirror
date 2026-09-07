/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/teleprompter/TeleprompterPage.tsx"
// purpose: "Canonical Responsive PWA Teleprompter Page Controller (TELEPROMPTER-WEB-001 Vertical Slice)."
// canonical_source: true
// status: "Active"
// version: "1.1.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import type { ScriptDocument, ProsodyDocument } from '@dnk/video-audit-core';
import { reburnReferenceFixture } from '@dnk/video-audit-core';
import {
  TeleprompterRuntime,
  ScriptFlatteningService,
  SessionAnalyticsCollector,
} from '@dnk/teleprompter-core';
import type {
  RuntimeToken,
  TeleprompterSession,
  SessionAnalytics,
  ASRHypothesis,
  TeleprompterEvent,
} from '@dnk/teleprompter-core';

import { BrowserCapabilitiesProbe } from '../../adapters/teleprompter/capabilities';
import type { WebCapabilities } from '../../adapters/teleprompter/ports';
import {
  WebSpeechProvider,
  MockASRStreamProvider,
} from '../../adapters/teleprompter/web-speech-provider';
import { WebMediaRecorderAdapter } from '../../adapters/teleprompter/media-recorder-adapter';
import { BrowserRuntimeAdapter } from '../../adapters/teleprompter/runtime-adapter';
import { IndexedDbSessionStore } from '../../adapters/teleprompter/indexed-db-session-store';

import { PrompterViewport, type FontSizeOption } from './PrompterViewport';
import { PerformanceHud } from './PerformanceHud';
import { AlignmentStatus } from './AlignmentStatus';
import { SessionToolbar } from './SessionToolbar';
import { CameraPreview } from './CameraPreview';
import { ScriptLoader } from './ScriptLoader';
import { PermissionState } from './PermissionState';
import { SessionSummary } from './SessionSummary';

export const TeleprompterPage: React.FC = () => {
  // 1. Script & Prosody State
  const [scriptDoc, setScriptDoc] = useState<ScriptDocument>(reburnReferenceFixture.script);
  const [prosodyDoc, setProsodyDoc] = useState<ProsodyDocument | undefined>(
    reburnReferenceFixture.prosody
  );

  // 2. Capabilities & Hardware State
  const [capabilities, setCapabilities] = useState<WebCapabilities | null>(null);
  const [isPermissionGranted, setIsPermissionGranted] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [isCameraActive, setIsCameraActive] = useState(true);

  // 3. UI Display Options
  const [isMirror, setIsMirror] = useState(false);
  const [fontSize, setFontSize] = useState<FontSizeOption>('lg');
  const [providerType, setProviderType] = useState<'web-speech' | 'mock-stream'>('mock-stream');
  const [countdown, setCountdown] = useState<number | null>(null);

  // 4. Session & Machine State
  const [tokens, setTokens] = useState<RuntimeToken[]>([]);
  const [session, setSession] = useState<TeleprompterSession | null>(null);
  const [currentWpm, setCurrentWpm] = useState(130);
  const [analytics, setAnalytics] = useState<SessionAnalytics | null>(null);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);

  // 5. Alignment & ASR Live Feedback
  const [asrStatus, setAsrStatus] = useState<
    'idle' | 'listening' | 'processing' | 'paused' | 'error'
  >('idle');
  const [lastHypothesis, setLastHypothesis] = useState<ASRHypothesis | null>(null);
  const [recoveryMode, setRecoveryMode] = useState<
    'none' | 'local' | 'forward_jump' | 'manual_required'
  >('none');

  // 6. Adapters & Engine References
  const runtimeRef = useRef<TeleprompterRuntime | null>(null);
  const analyticsCollectorRef = useRef<SessionAnalyticsCollector>(
    new SessionAnalyticsCollector()
  );
  const webSpeechProviderRef = useRef<WebSpeechProvider | null>(null);
  const mockAsrProviderRef = useRef<MockASRStreamProvider | null>(null);
  const recorderAdapterRef = useRef<WebMediaRecorderAdapter>(new WebMediaRecorderAdapter());
  const runtimeAdapterRef = useRef<BrowserRuntimeAdapter>(new BrowserRuntimeAdapter());
  const storeRef = useRef<IndexedDbSessionStore>(new IndexedDbSessionStore());

  // 7. Initialize Capabilities on Mount
  useEffect(() => {
    const probe = BrowserCapabilitiesProbe.probe();
    setCapabilities(probe.capabilities);
    if (!probe.capabilities.speechRecognition) {
      setProviderType('mock-stream');
    }
  }, []);

  // 8. Rebuild Tokens and Engine when Script Changes
  const initializeEngine = useCallback((script: ScriptDocument, prosody?: ProsodyDocument) => {
    const flatteningService = new ScriptFlatteningService();
    const flattened = flatteningService.flatten(script, prosody);
    setTokens(flattened);

    const analyticsCollector = new SessionAnalyticsCollector();
    analyticsCollectorRef.current = analyticsCollector;

    const runtime = new TeleprompterRuntime(script, prosody, { targetWpm: 130 });
    runtimeRef.current = runtime;

    runtime.onEvent((event: TeleprompterEvent) => {
      analyticsCollector.recordEvent(event);
      if (event.type === 'TOKEN_STATUS_CHANGED') {
        setTokens((prev) =>
          prev.map((t) => (t.index === event.tokenIndex ? { ...t, status: event.newStatus } : t))
        );
      } else if (event.type === 'ALIGNMENT_MATCHED') {
        setRecoveryMode('none');
      } else if (event.type === 'ALIGNMENT_RECOVERY') {
        setRecoveryMode(event.strategy);
      } else if (event.type === 'PACING_DRIFT') {
        setCurrentWpm(Math.round(event.actualWpm));
      }
    });

    setSession(runtime.getSession());
    setAnalytics(null);
    setRecordedBlob(null);
  }, []);

  useEffect(() => {
    initializeEngine(scriptDoc, prosodyDoc);
  }, [scriptDoc, prosodyDoc, initializeEngine]);

  // 9. Camera & Mic Permission Request
  const handleRequestPermissions = async () => {
    try {
      if (typeof navigator === 'undefined' || !navigator.mediaDevices) return;
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' },
        audio: true,
      });
      setCameraStream(stream);
      setIsPermissionGranted(true);
      const probe = BrowserCapabilitiesProbe.probe();
      setCapabilities(probe.capabilities);
    } catch (err) {
      console.warn('Microphone/Camera permission not granted:', err);
      setIsPermissionGranted(false);
    }
  };

  // 10. Start Recording Cycle (Countdown -> Stream -> ASR -> Runtime)
  const handleStart = async () => {
    if (!runtimeRef.current) return;

    // Start 3-2-1 Countdown
    setCountdown(3);
    await runtimeAdapterRef.current.requestWakeLock();
    runtimeAdapterRef.current.vibrate([100]);

    let count = 3;
    const interval = setInterval(() => {
      count--;
      if (count > 0) {
        setCountdown(count);
        runtimeAdapterRef.current.vibrate([100]);
      } else {
        clearInterval(interval);
        setCountdown(null);
        runtimeAdapterRef.current.vibrate([200, 100, 200]);
        beginSessionRun();
      }
    }, 1000);
  };

  const beginSessionRun = async () => {
    if (!runtimeRef.current) return;

    runtimeRef.current.start();
    setSession({ ...runtimeRef.current.getSession() });
    setAsrStatus('listening');

    // Start Media Recording if camera/mic stream active
    if (cameraStream) {
      try {
        await recorderAdapterRef.current.start(cameraStream);
      } catch (e) {
        console.warn('MediaRecorder failed to start:', e);
      }
    }

    // Connect ASR Provider
    const onHypothesis = (hypothesis: ASRHypothesis) => {
      if (!runtimeRef.current) return;
      setLastHypothesis(hypothesis);
      runtimeRef.current.processHypothesis(hypothesis);
      setSession({ ...runtimeRef.current.getSession() });
    };

    if (providerType === 'web-speech' && capabilities?.speechRecognition) {
      const speechProvider = new WebSpeechProvider({ language: 'uk-UA' });
      webSpeechProviderRef.current = speechProvider;
      speechProvider.subscribe(onHypothesis);
      await speechProvider.start();
    } else {
      const mockProvider = new MockASRStreamProvider({
        scriptTokens: tokens,
        targetWpm: 130,
        enableInterim: true,
      });
      mockAsrProviderRef.current = mockProvider;
      mockProvider.subscribe(onHypothesis);
      await mockProvider.start();
    }
  };

  // 11. Pause / Resume / Finish / Reset Handlers
  const handlePause = () => {
    if (!runtimeRef.current) return;
    runtimeRef.current.pause();
    webSpeechProviderRef.current?.stop();
    mockAsrProviderRef.current?.stop();
    recorderAdapterRef.current.pause();
    setAsrStatus('paused');
    setSession({ ...runtimeRef.current.getSession() });
  };

  const handleResume = async () => {
    if (!runtimeRef.current) return;
    runtimeRef.current.resume();
    recorderAdapterRef.current.resume();
    setAsrStatus('listening');
    setSession({ ...runtimeRef.current.getSession() });

    const onHypothesis = (hypothesis: ASRHypothesis) => {
      if (!runtimeRef.current) return;
      setLastHypothesis(hypothesis);
      runtimeRef.current.processHypothesis(hypothesis);
      setSession({ ...runtimeRef.current.getSession() });
    };

    if (providerType === 'web-speech' && capabilities?.speechRecognition) {
      webSpeechProviderRef.current = new WebSpeechProvider({ language: 'uk-UA' });
      webSpeechProviderRef.current.subscribe(onHypothesis);
      await webSpeechProviderRef.current.start();
    } else {
      mockAsrProviderRef.current = new MockASRStreamProvider({
        scriptTokens: tokens,
        startIndex: runtimeRef.current.getSession().confirmedTokenIndex,
        targetWpm: 130,
      });
      mockAsrProviderRef.current.subscribe(onHypothesis);
      await mockAsrProviderRef.current.start();
    }
  };

  const handleFinish = async () => {
    if (!runtimeRef.current) return;
    runtimeRef.current.stop();
    webSpeechProviderRef.current?.stop();
    mockAsrProviderRef.current?.stop();
    setAsrStatus('idle');

    // Stop MediaRecorder and grab Blob
    let blob: Blob | null = null;
    if (recorderAdapterRef.current.isRecording()) {
      try {
        blob = await recorderAdapterRef.current.stop();
        setRecordedBlob(blob);
      } catch (e) {
        console.warn('Failed to get recorded blob:', e);
      }
    }

    // Release Wake Lock
    await runtimeAdapterRef.current.releaseWakeLock();

    // Compile Analytics
    const compiledAnalytics = analyticsCollectorRef.current.compile(
      runtimeRef.current.getSession(),
      tokens,
      130
    );
    setAnalytics(compiledAnalytics);

    const finalSession = runtimeRef.current.getSession();
    setSession({ ...finalSession });

    // Persist to IndexedDB
    try {
      await storeRef.current.saveSession(finalSession);
    } catch (e) {
      console.warn('Failed to persist session to IndexedDB:', e);
    }
  };

  const handleManualReset = (index: number) => {
    if (!runtimeRef.current) return;
    runtimeRef.current.resetToToken(index);
    setTokens((prev) =>
      prev.map((t) => ({
        ...t,
        status: t.index < index ? 'completed' : t.index === index ? 'confirmed' : 'upcoming',
      }))
    );
    setSession({ ...runtimeRef.current.getSession() });
  };

  const handleFullReset = () => {
    initializeEngine(scriptDoc, prosodyDoc);
    setRecordedBlob(null);
    setAnalytics(null);
    setAsrStatus('idle');
  };

  // Compute Active UI values
  const sessionStatusUI =
    session?.status === 'running'
      ? 'recording'
      : session?.status === 'paused'
      ? 'paused'
      : session?.status === 'completed'
      ? 'completed'
      : 'idle';

  const completedCount = tokens.filter((t) => t.status === 'completed').length;
  const elapsedSec = session?.startedAtMs ? Math.floor((Date.now() - session.startedAtMs) / 1000) : 0;
  const estimatedSec =
    tokens.length > 0 && currentWpm > 0
      ? Math.round(((tokens.length - completedCount) / currentWpm) * 60)
      : 0;

  return (
    <main className="relative min-h-screen bg-slate-950 text-slate-100 overflow-hidden select-none font-sans flex flex-col">
      {/* 1. Camera Background Preview */}
      <CameraPreview
        stream={cameraStream}
        isEnabled={isCameraActive && Boolean(cameraStream)}
        isMirrored={isMirror}
        opacity={0.35}
      />

      {/* 2. Top Performance HUD (during recording or paused) */}
      {session && session.status !== 'idle' && (
        <PerformanceHud
          currentWpm={currentWpm}
          targetWpm={130}
          elapsedSeconds={elapsedSec}
          estimatedRemainingSeconds={estimatedSec}
          completedTokensCount={completedCount}
          totalTokensCount={tokens.length}
          adherenceScore={session.confirmedTokenIndex > 0 ? 0.95 : 1.0}
          currentSceneRole="hook"
          isRecording={session.status === 'running'}
        />
      )}

      {/* 3. Main Viewport / Content */}
      <div className="flex-1 flex flex-col pt-16 pb-28 px-4 md:px-12 max-w-5xl mx-auto w-full relative z-10">
        {session?.status === 'idle' && (
          <div className="mb-6 space-y-4">
            <PermissionState
              capabilities={capabilities}
              onRequestPermissions={handleRequestPermissions}
              isPermissionGranted={isPermissionGranted}
            />
            <ScriptLoader
              currentScriptTitle={scriptDoc.title}
              totalTokensCount={tokens.length}
              onLoadScript={(s, p) => {
                setScriptDoc(s);
                setProsodyDoc(p);
              }}
            />
          </div>
        )}

        {/* Dynamic Text Display */}
        <PrompterViewport
          tokens={tokens}
          currentIndex={session?.confirmedTokenIndex ?? 0}
          isMirrorMode={isMirror}
          fontSize={fontSize}
          isRecording={session?.status === 'running'}
          onTokenClick={(tok) => handleManualReset(tok.index)}
        />
      </div>

      {/* 4. Live Alignment Status */}
      {session?.status === 'running' && (
        <AlignmentStatus
          lastHypothesis={lastHypothesis}
          recoveryMode={recoveryMode}
          asrProviderName={providerType === 'web-speech' ? 'Web Speech (uk-UA)' : 'Mock ASR Stream'}
          isListening={asrStatus === 'listening'}
        />
      )}

      {/* 5. Countdown Overlay */}
      {countdown !== null && (
        <div
          data-testid="countdown-overlay"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md animate-fade-in"
        >
          <div className="text-8xl md:text-9xl font-black text-rose-500 font-mono animate-bounce drop-shadow-[0_0_35px_rgba(244,63,94,0.6)]">
            {countdown}
          </div>
        </div>
      )}

      {/* 6. Session Summary Modal / Screen */}
      {session?.status === 'completed' && (
        <SessionSummary
          session={session}
          analytics={analytics}
          totalTokensCount={tokens.length}
          recordedVideoBlob={recordedBlob}
          onNewTake={handleFullReset}
        />
      )}

      {/* 7. Persistent Bottom Control Toolbar */}
      <SessionToolbar
        sessionStatus={sessionStatusUI}
        isCameraEnabled={isCameraActive}
        isMirrorMode={isMirror}
        fontSize={fontSize}
        asrProviderType={providerType}
        onStartRecording={handleStart}
        onPauseRecording={handlePause}
        onResumeRecording={handleResume}
        onFinishRecording={handleFinish}
        onResetSession={handleFullReset}
        onToggleCamera={() => setIsCameraActive((prev) => !prev)}
        onToggleMirror={() => setIsMirror((prev) => !prev)}
        onChangeFontSize={(sz) => setFontSize(sz)}
        onChangeAsrProvider={(prov) => setProviderType(prov)}
      />
    </main>
  );
};
