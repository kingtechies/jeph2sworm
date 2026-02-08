/**
 * Recording Manager — manages recording sessions and storage.
 */

import { ScreenRecorder } from './screen-recorder';

interface Recording {
  id: string;
  tabId: number;
  startTime: number;
  endTime?: number;
  url: string;
  blobUrl?: string;
}

export class RecordingManager {
  private recorder = new ScreenRecorder();
  private recordings: Recording[] = [];
  private currentRecording: Recording | null = null;

  async startRecording(tabId: number, url: string): Promise<string> {
    if (this.recorder.isRecording) {
      await this.stopRecording();
    }

    const id = `rec-${Date.now()}`;
    this.currentRecording = {
      id,
      tabId,
      startTime: Date.now(),
      url,
    };

    await this.recorder.startRecording(tabId);
    return id;
  }

  async stopRecording(): Promise<Recording | null> {
    if (!this.currentRecording) return null;

    const blob = await this.recorder.stopRecording();
    const blobUrl = URL.createObjectURL(blob);

    this.currentRecording.endTime = Date.now();
    this.currentRecording.blobUrl = blobUrl;
    this.recordings.push(this.currentRecording);

    const recording = { ...this.currentRecording };
    this.currentRecording = null;
    return recording;
  }

  getRecordings(): Recording[] {
    return [...this.recordings];
  }

  getRecording(id: string): Recording | undefined {
    return this.recordings.find(r => r.id === id);
  }

  deleteRecording(id: string): void {
    const idx = this.recordings.findIndex(r => r.id === id);
    if (idx >= 0) {
      const rec = this.recordings[idx];
      if (rec.blobUrl) { URL.revokeObjectURL(rec.blobUrl); }
      this.recordings.splice(idx, 1);
    }
  }

  get isRecording(): boolean {
    return this.recorder.isRecording;
  }

  clearAll(): void {
    for (const rec of this.recordings) {
      if (rec.blobUrl) { URL.revokeObjectURL(rec.blobUrl); }
    }
    this.recordings = [];
  }
}
