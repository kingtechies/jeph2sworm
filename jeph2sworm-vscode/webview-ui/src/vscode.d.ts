/**
 * Type declarations for the VS Code webview API.
 * `acquireVsCodeApi` is injected by VS Code into all webviews.
 */

interface VsCodeApi {
  postMessage(message: unknown): void;
  getState(): unknown;
  setState(state: unknown): void;
}

declare function acquireVsCodeApi(): VsCodeApi;
