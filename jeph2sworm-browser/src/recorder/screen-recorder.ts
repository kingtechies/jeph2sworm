/**
 * Screen Recorder — records tab activity using MV3-compatible APIs.
 *
 * In Manifest V3, chrome.tabCapture.capture() is unavailable from service workers.
 * Instead we use chrome.tabCapture.getMediaStreamId() which returns a stream ID
 * that can be used in an offscreen document or page context.
 *
 * This class is designed to be used from the side panel or popup context
 * (not the service worker), where navigator.mediaDevices is available.
 */

export class ScreenRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private stream: MediaStream | null = null;

  /**
   * Start recording using a streamId obtained from chrome.tabCapture.getMediaStreamId().
   * Must be called from a context with navigator.mediaDevices (popup, sidepanel, offscreen).
   */
  async startRecording(tabId: number): Promise<void> {
    // Get a media stream ID for the tab via the MV3 API
    const streamId = await new Promise<string>((resolve, reject) => {
      chrome.tabCapture.getMediaStreamId({ targetTabId: tabId }, (id) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(id);
        }
      });
    });

    // Use the stream ID to get the actual MediaStream
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        mandatory: {
          chromeMediaSource: 'tab',
          chromeMediaSourceId: streamId,
          maxWidth: 1920,
          maxHeight: 1080,
          maxFrameRate: 30,
        },
      } as any,
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
