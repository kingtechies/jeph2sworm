/**
 * NetworkMonitor — captures and forwards network requests from devtools.
 */

interface NetworkEntry {
  id: string;
  method: string;
  url: string;
  status: number;
  statusText: string;
  type: string;
  size: number;
  duration: number;
  requestHeaders: Record<string, string>;
  responseHeaders: Record<string, string>;
  requestBody?: string;
  responseBody?: string;
  timestamp: number;
}

export class NetworkMonitor {
  private entries: NetworkEntry[] = [];
  private listeners: Array<(entry: NetworkEntry) => void> = [];
  private maxEntries = 500;

  start(): void {
    chrome.devtools.network.onRequestFinished.addListener((request) => {
      const entry: NetworkEntry = {
        id: `net-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        method: request.request.method,
        url: request.request.url,
        status: request.response.status,
        statusText: request.response.statusText,
        type: request.response.content.mimeType,
        size: request.response.content.size,
        duration: request.time ?? 0,
        requestHeaders: this.headersToRecord(request.request.headers),
        responseHeaders: this.headersToRecord(request.response.headers),
        requestBody: request.request.postData?.text,
        timestamp: Date.now(),
      };

      // Attempt to get response body
      request.getContent((content) => {
        if (content) {
          entry.responseBody = content.slice(0, 10000); // limit size
        }
        this.addEntry(entry);
      });
    });
  }

  private addEntry(entry: NetworkEntry): void {
    this.entries.push(entry);
    if (this.entries.length > this.maxEntries) {
      this.entries = this.entries.slice(-this.maxEntries);
    }
    this.listeners.forEach((l) => l(entry));
  }

  onEntry(listener: (entry: NetworkEntry) => void): void {
    this.listeners.push(listener);
  }

  getEntries(): NetworkEntry[] {
    return [...this.entries];
  }

  getApiCalls(): NetworkEntry[] {
    return this.entries.filter(
      (e) =>
        e.type.includes('json') ||
        e.url.includes('/api/') ||
        e.url.includes('/graphql')
    );
  }

  getErrors(): NetworkEntry[] {
    return this.entries.filter((e) => e.status >= 400);
  }

  clear(): void {
    this.entries = [];
  }

  private headersToRecord(headers: Array<{ name: string; value: string }>): Record<string, string> {
    const record: Record<string, string> = {};
    for (const h of headers) {
      record[h.name.toLowerCase()] = h.value;
    }
    return record;
  }
}
