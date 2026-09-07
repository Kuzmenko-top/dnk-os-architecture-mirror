/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/teleprompter/CameraPreview.tsx"
// purpose: "Underlay/Overlay Responsive Camera Feed Preview with Facing Mode and Mirror Controls."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

'use client';

import React, { useEffect, useRef } from 'react';

interface CameraPreviewProps {
  stream: MediaStream | null;
  isEnabled: boolean;
  opacity?: number; // 0 to 1
  isMirrored?: boolean;
}

export const CameraPreview: React.FC<CameraPreviewProps> = ({
  stream,
  isEnabled,
  opacity = 0.35,
  isMirrored = true,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current) {
      if (isEnabled && stream) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch((err) => {
          console.warn('Auto-play camera stream failed:', err);
        });
      } else {
        videoRef.current.srcObject = null;
      }
    }
  }, [stream, isEnabled]);

  if (!isEnabled) {
    return null;
  }

  return (
    <div
      data-testid="camera-preview-container"
      className="absolute inset-0 pointer-events-none overflow-hidden z-0 bg-black"
    >
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        data-testid="camera-video-feed"
        className={`w-full h-full object-cover transition-opacity duration-300 ${
          isMirrored ? '-scale-x-100' : ''
        }`}
        style={{ opacity: stream ? opacity : 0 }}
      />
      {/* Subtle vignette darkening towards edges */}
      <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/70 to-slate-950/90" />
    </div>
  );
};
