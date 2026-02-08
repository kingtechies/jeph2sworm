/**
 * Messaging — Chrome extension internal messaging utilities.
 */

type MessageHandler = (message: any, sender: chrome.runtime.MessageSender) => Promise<any> | any;

const handlers = new Map<string, MessageHandler>();

export function onMessage(type: string, handler: MessageHandler): void {
  handlers.set(type, handler);
}

export function initMessageRouter(): void {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    const handler = handlers.get(message.type);
    if (!handler) return false;

    const result = handler(message, sender);
    if (result instanceof Promise) {
      result.then(sendResponse).catch(err => sendResponse({ error: err.message }));
      return true; // Keeps channel open for async response
    }

    sendResponse(result);
    return false;
  });
}

export function sendToBackground(type: string, data?: Record<string, unknown>): Promise<any> {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type, ...data }, resolve);
  });
}

export function sendToTab(tabId: number, type: string, data?: Record<string, unknown>): Promise<any> {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, { type, ...data }, resolve);
  });
}

export function sendToAllTabs(type: string, data?: Record<string, unknown>): void {
  chrome.tabs.query({}, (tabs) => {
    for (const tab of tabs) {
      if (tab.id) {
        chrome.tabs.sendMessage(tab.id, { type, ...data }).catch(() => {});
      }
    }
  });
}
