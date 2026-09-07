/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/adapters/teleprompter/media-recorder-adapter.ts"
// purpose: "Web MediaRecorder Adapter for In-Browser Video and Audio Recording."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

import type { MediaRecorderPort } from './ports';

export class WebMediaRecorderAdapter implements MediaRecorderPort {
  private mediaRecorder: MediaRecorder | null = null;
  private recordedChunks: Blob[] = [];
  private recordedBlob: Blob | null = null;
  private selectedMimeType = '';
  private isCurrentlyRecording = false;

  constructor() {
    this.selectedMimeType = this.detectSupportedMimeType();
  }

  private detectSupportedMimeType(): string {
    if (typeof window === 'undefined' || typeof MediaRecorder === 'undefined') {
      return '';
    }

    const candidateTypes = [
      'video/webm;codecs=vp9,opus',
      'video/webm;codecs=vp8,opus',
      'video/webm',
      'video/mp4;codecs=avc1,mp4a.40.2',
      'video/mp4',
    ];

    for (const type of candidateTypes) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }

    return '';
  }

  getMimeType(): string {
    return this.selectedMimeType;
  }

  getRecordedBlob(): Blob | null {
    return this.recordedBlob;
  }

  isRecording(): boolean {
    return this.isCurrentlyRecording;
  }

  async start(stream: MediaStream): Promise<void> {
    if (typeof window === 'undefined' || typeof MediaRecorder === 'undefined') {
      throw new Error('MediaRecorder API is not available in this environment.');
    }

    this.recordedChunks = [];
    this.recordedBlob = null;

    const options: MediaRecorderOptions = {};
    if (this.selectedMimeType) {
      options.mimeType = this.selectedMimeType;
    }

    this.mediaRecorder = new MediaRecorder(stream, options);

    this.mediaRecorder.ondataavailable = (event: BlobEvent) => {
      if (event.data && event.data.size > 0) {
        this.recordedChunks.push(event.data);
      }
    };

    this.mediaRecorder.start(500); // chunk every 500ms
    this.isCurrentlyRecording = true;
  }

  async stop(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder || this.mediaRecorder.state === 'inactive') {
        if (this.recordedBlob) {
          resolve(this.recordedBlob);
          return;
        }
        reject(new Error('MediaRecorder is not active or has already been stopped.'));
        return;
      }

      this.mediaRecorder.onstop = () => {
        this.isCurrentlyRecording = false;
        const mimeType = this.selectedMimeType || 'video/webm';
        this.recordedBlob = new Blob(this.recordedChunks, { type: mimeType });
        resolve(this.recordedBlob);
      };

      this.mediaRecorder.onerror = (event: Event) => {
        this.isCurrentlyRecording = false;
        reject(new Error(`MediaRecorder error: ${(event as ErrorEvent).message || 'unknown'}`));
      };

      try {
        this.mediaRecorder.stop();
      } catch (err) {
        this.isCurrentlyRecording = false;
        reject(err);
      }
    });
  }

  pause(): void {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.pause();
    }
  }

  resume(): void {
    if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
      this.mediaRecorder.resume();
    }
  }
}
