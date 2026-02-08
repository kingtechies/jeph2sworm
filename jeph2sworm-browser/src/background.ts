/**
 * Background service worker for the Jeph2Sworm browser extension.
 *
 * Uses modular WebSocketClient, CommandQueue, and TabManager for
 * reliable backend communication, queued command execution, and tab control.
 */

import { WebSocketClient } from "./background/websocket-client";
import { CommandQueue } from "./background/command-queue";
import { TabManager } from "./background/tab-manager";

const DEFAULT_WS_URL = "ws://127.0.0.1:8765/ws";

interface SwarmMessage {
  type: string;
  data?: Record<string, unknown>;
  [key: string]: unknown;
}

// ── Module Instances ──────────────────────────────────────────────

const clientId = `browser-${Date.now()}`;
const wsClient = new WebSocketClient(`${DEFAULT_WS_URL}/${clientId}?client_type=browser`);
const commandQueue = new CommandQueue();
const tabManager = new TabManager();

// ── WebSocket Event Handlers ──────────────────────────────────────

wsClient.on("connected", () => {
  console.log("[Jeph2Sworm] Connected to backend");
  broadcastToSidePanel({ type: "connection_status", data: { connected: true } });
});

wsClient.on("disconnected", () => {
  console.log("[Jeph2Sworm] Disconnected.");
  broadcastToSidePanel({ type: "connection_status", data: { connected: false } });
});

wsClient.on("browser_command", (msg: any) => {
  handleBrowserCommand(msg.data || msg);
});

wsClient.on("*", (msg: any) => {
  // Forward all backend messages to side panel
  broadcastToSidePanel(msg);
});

// ── Command Queue Handlers ────────────────────────────────────────

commandQueue.registerHandler("navigate", async (params) => {
  const url = params.url as string;
  const tab = await tabManager.getActiveTab();
  if (tab?.id) {
    await tabManager.navigateTo(tab.id, url);
    wsClient.send({ type: "browser_action", action: { type: "navigated", url } });
  }
  return { ok: true, url };
});

commandQueue.registerHandler("screenshot", async () => {
  const dataUrl = await chrome.tabs.captureVisibleTab();
  wsClient.send({ type: "browser_action", action: { type: "screenshot", data: dataUrl } });
  return { ok: true, data: dataUrl };
});

commandQueue.registerHandler("get_content", async () => {
  const tab = await tabManager.getActiveTab();
  if (tab?.id) {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.documentElement.outerHTML,
    });
    if (results[0]?.result) {
      wsClient.send({
        type: "browser_action",
        action: { type: "page_content", html: results[0].result },
      });
      return { ok: true };
    }
  }
  return { ok: false };
});

commandQueue.registerHandler("click", async (params) => {
  await sendToActiveTab("click", { selector: params.selector });
  return { ok: true };
});

commandQueue.registerHandler("fill", async (params) => {
  await sendToActiveTab("fill", { selector: params.selector, value: params.value });
  return { ok: true };
});

commandQueue.registerHandler("extract", async (params) => {
  await sendToActiveTab("extract", { selector: params.selector });
  return { ok: true };
});

// ── Message Handling ──────────────────────────────────────────────

async function handleBrowserCommand(data: Record<string, unknown>): Promise<void> {
  const action = data.action as string;
  try {
    await commandQueue.enqueue(action, data);
  } catch (err) {
    console.warn(`[Jeph2Sworm] Command failed: ${action}`, err);
  }
}

async function sendToActiveTab(action: string, data: Record<string, unknown>): Promise<void> {
  const tab = await tabManager.getActiveTab();
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

// Listen for messages from side panel, popup, and content scripts
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "connect") {
    wsClient.connect();
    sendResponse({ ok: true });
  } else if (msg.type === "disconnect") {
    wsClient.disconnect();
    sendResponse({ ok: true });
  } else if (msg.type === "send_to_backend") {
    wsClient.send(msg.data);
    sendResponse({ ok: true });
  } else if (msg.type === "get_status" || msg.type === "get_connection_status") {
    sendResponse({ connected: wsClient.isConnected, pendingCommands: commandQueue.pendingCount, url: `${DEFAULT_WS_URL}/${clientId}` });
  } else if (msg.type === "capture_screenshot" || msg.type === "take_screenshot") {
    commandQueue.enqueue("screenshot", {}).then(() => sendResponse({ ok: true })).catch(() => sendResponse({ ok: false }));
    return true; // async response
  } else if (msg.type === "content_action") {
    wsClient.send({
      type: "browser_action",
      action: { type: msg.action, ...msg.data, url: msg.url },
    });
    sendResponse({ ok: true });
  } else if (msg.type === "start_recording") {
    // Forward recording request — capture tab and record
    chrome.tabs.captureVisibleTab().then((dataUrl) => {
      wsClient.send({ type: "browser_action", action: { type: "recording_started", tabId: msg.tabId } });
      broadcastToSidePanel({ type: "recording_status", data: { recording: true } });
      sendResponse({ ok: true });
    }).catch(() => sendResponse({ ok: false }));
    return true;
  } else if (msg.type === "stop_recording") {
    wsClient.send({ type: "browser_action", action: { type: "recording_stopped", tabId: msg.tabId } });
    broadcastToSidePanel({ type: "recording_status", data: { recording: false } });
    sendResponse({ ok: true });
  } else if (msg.type === "create_tab") {
    tabManager.createTab(msg.url, msg.purpose || "automation")
      .then((tabId) => sendResponse({ ok: true, tabId }))
      .catch(() => sendResponse({ ok: false }));
    return true;
  } else if (msg.type === "close_managed_tabs") {
    tabManager.closeAll().then(() => sendResponse({ ok: true }));
    return true;
  } else if (msg.type === "get_managed_tabs") {
    sendResponse({ tabs: tabManager.getAllManaged() });
  } else if (msg.type === "devtools_panel_shown" || msg.type === "devtools_panel_hidden") {
    // Track devtools panel state
    wsClient.send({ type: "browser_action", action: { type: msg.type } });
    sendResponse({ ok: true });
  } else if (msg.type === "network_request") {
    // Forward network request data from devtools panel to backend
    wsClient.send({ type: "browser_action", action: { type: "network_request", ...msg.data } });
    sendResponse({ ok: true });
  } else if (msg.type === "crop_screenshot") {
    // Handle screenshot cropping for element captures
    sendResponse({ ok: true, data: msg.data }); // Pass through — cropping done client-side
  }
  return true;
});

// Auto-connect on startup
wsClient.connect();
