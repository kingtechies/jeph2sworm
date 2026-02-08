/**
 * DevTools types — network, console, and performance data structures.
 */

export interface NetworkEntry {
  url: string;
  method: string;
  status: number;
  time: number;
  size?: number;
  mimeType?: string;
  timestamp: number;
}

export interface ConsoleEntry {
  level: 'log' | 'warn' | 'error' | 'info' | 'debug';
  args: string[];
  timestamp: number;
  source?: string;
}

export interface PerformanceMetrics {
  dns: number;
  tcp: number;
  ttfb: number;
  domLoad: number;
  fullLoad: number;
  firstPaint?: number;
  firstContentfulPaint?: number;
  largestContentfulPaint?: number;
  cumulativeLayoutShift?: number;
  totalBlockingTime?: number;
}

export interface CoverageReport {
  url: string;
  totalBytes: number;
  usedBytes: number;
  percentUsed: number;
}
