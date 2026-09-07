/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/analyzers/aggregate-status.ts"
# purpose: "Canonical Aggregate Status, Partial Success Policy, and Analyzer Execution Status Matrix."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export const AnalysisAggregateStatusSchema = z.enum([
  'completed',
  'partial',
  'failed',
  'manual_review'
]);

export type AnalysisAggregateStatus = z.infer<typeof AnalysisAggregateStatusSchema>;

export interface AnalysisRequirements {
  transcript: 'required' | 'optional';
  scenes: 'required' | 'optional';
  ocr: 'required' | 'optional';
  audio: 'required' | 'optional';
}

export const DEFAULT_ANALYSIS_REQUIREMENTS: AnalysisRequirements = {
  transcript: 'optional',
  scenes: 'required',
  ocr: 'optional',
  audio: 'optional'
};

export interface StreamStatus {
  state: 'completed' | 'empty' | 'missing' | 'failed';
  isDegraded?: boolean;
}

export interface AnalysisStreams {
  scenes: StreamStatus;
  ocr: StreamStatus;
  audio: StreamStatus;
  transcript: StreamStatus;
}

export interface AnalyzerStatuses {
  transcriptionStatus?: string;
  sceneExtractionStatus?: string;
  ocrStatus?: string;
  audioFeatureStatus?: string;
}

export function computeAnalysisAggregateStatus(
  input: AnalysisStreams | AnalyzerStatuses,
  requirements: AnalysisRequirements = DEFAULT_ANALYSIS_REQUIREMENTS
): AnalysisAggregateStatus {
  let streams: AnalysisStreams;

  if (input && 'scenes' in input) {
    streams = input as AnalysisStreams;
  } else {
    const old = (input || {}) as AnalyzerStatuses;
    
    const mapState = (status?: string): 'completed' | 'empty' | 'missing' | 'failed' => {
      if (!status || status === 'missing') return 'missing';
      if (status === 'failed') return 'failed';
      if (status === 'empty') return 'empty';
      return 'completed';
    };

    streams = {
      scenes: { state: mapState(old.sceneExtractionStatus) },
      ocr: { state: mapState(old.ocrStatus) },
      audio: {
        state: mapState(old.audioFeatureStatus),
        isDegraded: old.audioFeatureStatus === 'degraded'
      },
      transcript: { state: mapState(old.transcriptionStatus) }
    };
  }

  // 1. Check for required streams
  const keys: (keyof AnalysisStreams)[] = ['scenes', 'ocr', 'audio', 'transcript'];
  
  let hasMissingRequired = false;
  let hasFailedRequired = false;

  for (const key of keys) {
    const req = requirements[key];
    const stream = streams[key];

    if (req === 'required') {
      if (stream.state === 'missing') {
        hasMissingRequired = true;
      } else if (stream.state === 'failed') {
        hasFailedRequired = true;
      }
    }
  }

  if (hasFailedRequired) {
    return 'failed';
  }
  if (hasMissingRequired) {
    return 'manual_review';
  }

  // 2. Check for degraded audio or any other degraded stream
  if (streams.audio.isDegraded) {
    return 'partial';
  }

  // 3. Check optional streams
  let hasMissingOptional = false;
  let hasFailedOptional = false;

  for (const key of keys) {
    const req = requirements[key];
    const stream = streams[key];

    if (req === 'optional') {
      if (stream.state === 'missing') {
        hasMissingOptional = true;
      } else if (stream.state === 'failed') {
        hasFailedOptional = true;
      }
    }
  }

  if (hasFailedOptional || hasMissingOptional) {
    return 'partial';
  }

  // 4. If all streams are completed or empty, return completed
  return 'completed';
}
