/**
 * Screen Recorder — records tab activity using MediaRecorder API.
 */

export class ScreenRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private stream: MediaStream | null = null;

  async startRecording(tabId: number): Promise<void> {
    // Request tab capture
    this.stream = await (chrome.tabCapture as any).capture({
      audio: false,
      video: true,
      videoConstraints: {
        mandatory: { maxWidth: 1920, maxHeight: 1080, maxFrameRate: 30 },
      },
    });

    if (!this.stream) throw new Error('Failed to capture tab');

    this.chunks = [];
    this.mediaRecorder = new MediaRecorder(this.stream, {
      mimeType: 'video/webm;codecs=vp9',
      videoBitsPerSecond: 2500000,
    });

    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        this.chunks.push(e.data);
      }
    };

    this.mediaRecorder.start(1000); // Chunk every second
  }

  async stopRecording(): Promise<Blob> {
    return new Promise((resolve) => {
      if (!this.mediaRecorder) {
        resolve(new Blob());
        return;
      }

      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.chunks, { type: 'video/webm' });
        this.chunks = [];
        this.stream?.getTracks().forEach(t => t.stop());
        this.stream = null;
        this.mediaRecorder = null;
        resolve(blob);
      };

      this.mediaRecorder.stop();
    });
  }

  get isRecording(): boolean {
    return this.mediaRecorder?.state === 'recording';
  }
}
