/**
 * ConsoleCapture — intercepts console messages from the inspected page.
 */

interface ConsoleEntry {
  id: string;
  level: 'log' | 'warn' | 'error' | 'info' | 'debug';
  message: string;
  source: string;
  line: number;
  column: number;
  timestamp: number;
  stackTrace?: string;
}

export class ConsoleCapture {
  private entries: ConsoleEntry[] = [];
  private listeners: Array<(entry: ConsoleEntry) => void> = [];
  private maxEntries = 1000;
  private capturing = false;

  start(): void {
    if (this.capturing) { return; }
    this.capturing = true;

    // Inject console interceptor into inspected page
    const interceptScript = `
      (function() {
        if (window.__j2sConsoleHooked) return;
        window.__j2sConsoleHooked = true;
        const orig = {};
        ['log', 'warn', 'error', 'info', 'debug'].forEach(level => {
          orig[level] = console[level];
          console[level] = function(...args) {
            orig[level].apply(console, args);
            try {
              window.postMessage({
                type: '__j2s_console',
                level,
                message: args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' '),
                timestamp: Date.now()
              }, '*');
            } catch(e) {}
          };
        });

        window.addEventListener('error', function(e) {
          window.postMessage({
            type: '__j2s_console',
            level: 'error',
            message: e.message,
            source: e.filename || '',
            line: e.lineno || 0,
            column: e.colno || 0,
            stackTrace: e.error?.stack || '',
            timestamp: Date.now()
          }, '*');
        });

        window.addEventListener('unhandledrejection', function(e) {
          window.postMessage({
            type: '__j2s_console',
            level: 'error',
            message: 'Unhandled Promise Rejection: ' + String(e.reason),
            timestamp: Date.now()
          }, '*');
        });
      })();
    `;

    chrome.devtools.inspectedWindow.eval(interceptScript);

    // Listen for forwarded messages via content script
    chrome.runtime.onMessage.addListener((msg) => {
      if (msg.type === '__j2s_console') {
        this.addEntry({
          id: `con-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          level: msg.level,
          message: msg.message,
          source: msg.source ?? '',
          line: msg.line ?? 0,
          column: msg.column ?? 0,
          timestamp: msg.timestamp,
          stackTrace: msg.stackTrace,
        });
      }
    });
  }

  stop(): void {
    this.capturing = false;
  }

  private addEntry(entry: ConsoleEntry): void {
    this.entries.push(entry);
    if (this.entries.length > this.maxEntries) {
      this.entries = this.entries.slice(-this.maxEntries);
    }
    this.listeners.forEach((l) => l(entry));
  }

  onEntry(listener: (entry: ConsoleEntry) => void): void {
    this.listeners.push(listener);
  }

  getEntries(): ConsoleEntry[] {
    return [...this.entries];
  }

  getErrors(): ConsoleEntry[] {
    return this.entries.filter((e) => e.level === 'error');
  }

  getWarnings(): ConsoleEntry[] {
    return this.entries.filter((e) => e.level === 'warn');
  }

  clear(): void {
    this.entries = [];
  }
}
