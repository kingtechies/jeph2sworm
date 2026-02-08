/**
 * Tab Manager — tracks and manages browser tabs for automation.
 */

export class TabManager {
  private managedTabs = new Map<number, { url: string; title: string; purpose: string }>();

  async createTab(url: string, purpose: string): Promise<number> {
    const tab = await chrome.tabs.create({ url, active: false });
    if (tab.id) {
      this.managedTabs.set(tab.id, { url, title: tab.title || '', purpose });
    }
    return tab.id!;
  }

  async navigateTo(tabId: number, url: string): Promise<void> {
    await chrome.tabs.update(tabId, { url });
    const info = this.managedTabs.get(tabId);
    if (info) { info.url = url; }
  }

  async closeTab(tabId: number): Promise<void> {
    try {
      await chrome.tabs.remove(tabId);
    } catch { /* tab already closed */ }
    this.managedTabs.delete(tabId);
  }

  async getActiveTab(): Promise<chrome.tabs.Tab | undefined> {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab;
  }

  async captureTab(tabId: number): Promise<string> {
    return chrome.tabs.captureVisibleTab({ format: 'png' });
  }

  isManaged(tabId: number): boolean {
    return this.managedTabs.has(tabId);
  }

  getAllManaged(): Array<{ tabId: number; url: string; title: string; purpose: string }> {
    return Array.from(this.managedTabs.entries()).map(([tabId, info]) => ({
      tabId,
      ...info,
    }));
  }

  async closeAll(): Promise<void> {
    const ids = Array.from(this.managedTabs.keys());
    for (const id of ids) {
      await this.closeTab(id);
    }
  }
}
