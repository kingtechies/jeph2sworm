/**
 * Background service worker for the Jeph2Sworm browser extension.
 *
 * Maintains WebSocket connection to the backend, routes commands
 * to content scripts, and manages browser automation.
 */

const DEFAULT_WS_URL = "ws://127.0.0.1:7777/ws";

interface SwarmMessage {
  type: string;
  data?: Record<string, unknown>;
  [key: string]: unknown;
}

let ws: WebSocket | null = null;
let connected = false;
let clientId = `browser-${Date.now()}`;

// ── WebSocket Connection ──────────────────────────────────────────

function connectToBackend(): void {
  const url = `${DEFAULT_WS_URL}/${clientId}?client_type=browser`;
  ws = new WebSocket(url);

  ws.onopen = () => {
    connected = true;
    console.log("[Jeph2Sworm] Connected to backend");
    broadcastToSidePanel({ type: "connection_status", data: { connected: true } });
  };

  ws.onmessage = (event) => {
    try {
      const msg: SwarmMessage = JSON.parse(event.data as string);
      handleBackendMessage(msg);
    } catch {
      // Ignore malformed messages
    }
  };

  ws.onclose = () => {
    connected = false;
    console.log("[Jeph2Sworm] Disconnected. Reconnecting in 3s...");
    broadcastToSidePanel({ type: "connection_status", data: { connected: false } });
    setTimeout(connectToBackend, 3000);
  };

  ws.onerror = () => {
    // onclose will fire after this
  };
}

function sendToBackend(msg: SwarmMessage): void {
  if (ws && connected) {
    ws.send(JSON.stringify(msg));
  }
}

// ── Message Handling ──────────────────────────────────────────────

function handleBackendMessage(msg: SwarmMessage): void {
  // Forward to side panel
  broadcastToSidePanel(msg);

  // Handle browser-specific commands
  if (msg.type === "browser_command") {
    handleBrowserCommand(msg.data || {});
  }
}

async function handleBrowserCommand(data: Record<string, unknown>): Promise<void> {
  const action = data.action as string;

  switch (action) {
    case "navigate":
      await navigateTab(data.url as string);
      break;
    case "screenshot":
      await captureScreenshot();
      break;
    case "get_content":
      await getPageContent();
      break;
    case "click":
      await sendToActiveTab("click", { selector: data.selector });
      break;
    case "fill":
      await sendToActiveTab("fill", { selector: data.selector, value: data.value });
      break;
    case "extract":
      await sendToActiveTab("extract", { selector: data.selector });
      break;
    default:
      console.warn(`[Jeph2Sworm] Unknown browser command: ${action}`);
  }
}

// ── Browser Actions ───────────────────────────────────────────────

async function navigateTab(url: string): Promise<void> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    await chrome.tabs.update(tab.id, { url });
    sendToBackend({
      type: "browser_action",
      action: { type: "navigated", url },
    });
  }
}

async function captureScreenshot(): Promise<void> {
  const dataUrl = await chrome.tabs.captureVisibleTab();
  sendToBackend({
    type: "browser_action",
    action: { type: "screenshot", data: dataUrl },
  });
}

async function getPageContent(): Promise<void> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.documentElement.outerHTML,
    });
    if (results[0]?.result) {
      sendToBackend({
        type: "browser_action",
        action: { type: "page_content", html: results[0].result },
      });
    }
  }
}

async function sendToActiveTab(action: string, data: Record<string, unknown>): Promise<void> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    chrome.tabs.sendMessage(tab.id, { type: action, ...data });
  }
}

// ── Side Panel Communication ──────────────────────────────────────

function broadcastToSidePanel(msg: SwarmMessage): void {
  chrome.runtime.sendMessage(msg).catch(() => {
    // Side panel may not be open
  });
}

// ── Extension Lifecycle ───────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
  console.log("[Jeph2Sworm] Extension installed");
  chrome.sidePanel.setOptions({ enabled: true });
});

chrome.action.onClicked.addListener(async (tab) => {
  if (tab.id) {
    await chrome.sidePanel.open({ tabId: tab.id });
  }
});

// Listen for messages from side panel and content scripts
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "connect") {
    connectToBackend();
    sendResponse({ ok: true });
  } else if (msg.type === "send_to_backend") {
    sendToBackend(msg.data);
    sendResponse({ ok: true });
  } else if (msg.type === "get_status") {
    sendResponse({ connected });
  }
  return true;
});

// Auto-connect on startup
connectToBackend();
