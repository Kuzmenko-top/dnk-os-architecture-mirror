// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/stitch/index.ts"
// purpose: "Unified export barrel for Spatial Stitch components in apps/web."
// canonical_source: true
// status: "Active"
// version: "2.2.0"
// updated_at: "2026-09-06"
// author: "Antigravity & Maxim"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

export { default as StitchSwarmCommandCenter, DEFAULT_AGENTS } from './StitchSwarmCommandCenter';
export type { AgentTelemetry, SwarmCommandCenterProps } from './StitchSwarmCommandCenter';

export { default as StitchKineticTimeline } from './StitchKineticTimeline';
export type { TimelineTrack, KineticTimelineProps } from './StitchKineticTimeline';

export { default as StitchSmartInspector, StitchSmartInspector as SmartInspectorNamed } from './StitchSmartInspector';
export type { StitchSmartInspectorProps, SmartInspectorProps } from './StitchSmartInspector';

export { default as StitchShopifyPreviewDrawer, StitchShopifyPreviewDrawer as ShopifyPreviewDrawerNamed } from './StitchShopifyPreviewDrawer';
export type { StitchShopifyPreviewDrawerProps } from './StitchShopifyPreviewDrawer';

export { default as StitchBiAnalystDrawer, StitchBiAnalystDrawer as BiAnalystDrawerNamed } from './StitchBiAnalystDrawer';
export type { AnalysisResult, StitchBiAnalystDrawerProps } from './StitchBiAnalystDrawer';

export { default as StitchTaskForestDrawer, StitchTaskForestDrawer as TaskForestDrawerNamed } from './StitchTaskForestDrawer';
export type { StitchTaskForestDrawerProps } from './StitchTaskForestDrawer';

export { default as StitchRemotionVideoDrawer, StitchRemotionVideoDrawer as RemotionVideoDrawerNamed } from './StitchRemotionVideoDrawer';
export type { StitchRemotionVideoDrawerProps, VideoTemplate } from './StitchRemotionVideoDrawer';

