/**
 * Performance — collects performance metrics from the inspected page.
 */

interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  timestamp: number;
}

interface PerformanceSnapshot {
  id: string;
  url: string;
  timestamp: number;
  metrics: PerformanceMetric[];
  lcp?: number;
  fcp?: number;
  cls?: number;
  fid?: number;
  ttfb?: number;
  domContentLoaded?: number;
  load?: number;
  jsHeapSize?: number;
  domNodes?: number;
}

export class PerformanceMonitor {
  private snapshots: PerformanceSnapshot[] = [];
  private listeners: Array<(snapshot: PerformanceSnapshot) => void> = [];

  async capture(): Promise<PerformanceSnapshot> {
    return new Promise((resolve) => {
      const script = `
        (function() {
          const perf = performance;
          const nav = perf.getEntriesByType('navigation')[0] || {};
          const paint = perf.getEntriesByType('paint');
          const fcp = paint.find(p => p.name === 'first-contentful-paint');

          return {
            url: location.href,
            metrics: perf.getEntriesByType('measure').map(m => ({
              name: m.name, value: m.duration, unit: 'ms', timestamp: Date.now()
            })),
            fcp: fcp ? fcp.startTime : null,
            domContentLoaded: nav.domContentLoadedEventEnd || null,
            load: nav.loadEventEnd || null,
            ttfb: nav.responseStart || null,
            jsHeapSize: performance.memory ? performance.memory.usedJSHeapSize : null,
            domNodes: document.querySelectorAll('*').length,
          };
        })();
      `;

      chrome.devtools.inspectedWindow.eval(script, (result: Record<string, unknown>, err: unknown) => {
        if (err) {
          resolve(this.emptySnapshot());
          return;
        }
        const data = result as Record<string, unknown>;
        const snapshot: PerformanceSnapshot = {
          id: `perf-${Date.now()}`,
          url: (data.url as string) ?? '',
          timestamp: Date.now(),
          metrics: (data.metrics as PerformanceMetric[]) ?? [],
          fcp: data.fcp as number | undefined,
          domContentLoaded: data.domContentLoaded as number | undefined,
          load: data.load as number | undefined,
          ttfb: data.ttfb as number | undefined,
          jsHeapSize: data.jsHeapSize as number | undefined,
          domNodes: data.domNodes as number | undefined,
        };
        this.snapshots.push(snapshot);
        this.listeners.forEach((l) => l(snapshot));
        resolve(snapshot);
      });
    });
  }

  onSnapshot(listener: (snapshot: PerformanceSnapshot) => void): void {
    this.listeners.push(listener);
  }

  getSnapshots(): PerformanceSnapshot[] {
    return [...this.snapshots];
  }

  getLatest(): PerformanceSnapshot | undefined {
    return this.snapshots[this.snapshots.length - 1];
  }

  clear(): void {
    this.snapshots = [];
  }

  private emptySnapshot(): PerformanceSnapshot {
    return {
      id: `perf-${Date.now()}`,
      url: '',
      timestamp: Date.now(),
      metrics: [],
    };
  }
}
