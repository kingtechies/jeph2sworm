/**
 * useVsCodeApi — hook to access the VS Code webview API.
 */

import { useCallback, useEffect, useRef } from 'react';

type VsCodeApi = ReturnType<typeof acquireVsCodeApi>;

let api: VsCodeApi | undefined;

function getApi(): VsCodeApi {
  if (!api) {
    api = acquireVsCodeApi();
  }
  return api;
}

export function useVsCodeApi() {
  return getApi();
}

export function usePostMessage() {
  const vscode = useVsCodeApi();
  return useCallback(
    (command: string, data?: Record<string, unknown>) => {
      vscode.postMessage({ command, ...data });
    },
    [vscode]
  );
}

export function useMessageListener(
  handler: (message: { command: string; [key: string]: unknown }) => void
) {
  const savedHandler = useRef(handler);
  savedHandler.current = handler;

  useEffect(() => {
    const listener = (event: MessageEvent) => {
      savedHandler.current(event.data);
    };
    window.addEventListener('message', listener);
    return () => window.removeEventListener('message', listener);
  }, []);
}
