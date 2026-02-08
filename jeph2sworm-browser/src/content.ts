/**
 * Content script - injected into every page for DOM interaction.
 *
 * Uses modular DOM extractors, form filler, and element highlighter
 * for structured page interaction.
 */

import { extractDOM } from "./content/dom-extractor";
import { fillForm, submitForm, getFormValues, clearForm } from "./content/form-filler";
import { highlightElement, highlightMultiple, clearHighlights } from "./content/element-highlighter";
import { captureScreenshot, captureElement } from "./content/screenshot";

interface ContentMessage {
  type: string;
  selector?: string;
  value?: string;
  formData?: Record<string, string>;
  selectors?: Array<{ selector: string; label?: string }>;
  [key: string]: unknown;
}

// Listen for commands from background
chrome.runtime.onMessage.addListener(
  (msg: ContentMessage, _sender, sendResponse) => {
    switch (msg.type) {
      case "click":
        handleClick(msg.selector || "");
        sendResponse({ ok: true });
        break;

      case "fill":
        handleFill(msg.selector || "", msg.value || "");
        sendResponse({ ok: true });
        break;

      case "fill_form":
        if (msg.formData) {
          const result = fillForm(msg.formData);
          sendResponse({ ok: true, data: result });
        } else {
          sendResponse({ ok: false, error: "Missing formData" });
        }
        break;

      case "submit_form":
        const submitted = submitForm(msg.selector || "form");
        sendResponse({ ok: submitted });
        break;

      case "get_form_values":
        sendResponse({ ok: true, data: getFormValues(msg.selector || "form") });
        break;

      case "clear_form":
        clearForm(msg.selector || "form");
        sendResponse({ ok: true });
        break;

      case "extract":
        const data = handleExtract(msg.selector || "");
        sendResponse({ ok: true, data });
        break;

      case "extract_dom":
        const domData = extractDOM();
        sendResponse({ ok: true, data: domData });
        break;

      case "get_dom_info":
        sendResponse({ ok: true, data: extractDOM() });
        break;

      case "highlight":
        highlightElement(msg.selector || "", msg.value);
        sendResponse({ ok: true });
        break;

      case "highlight_multiple":
        if (msg.selectors) {
          highlightMultiple(msg.selectors);
        }
        sendResponse({ ok: true });
        break;

      case "clear_highlights":
        clearHighlights();
        sendResponse({ ok: true });
        break;

      case "screenshot":
        captureScreenshot()
          .then((dataUrl) => sendResponse({ ok: true, dataUrl }))
          .catch((err) => sendResponse({ ok: false, error: err.message }));
        return true; // async response

      case "screenshot_element":
        captureElement(msg.selector || "")
          .then((dataUrl) => sendResponse({ ok: true, dataUrl }))
          .catch((err) => sendResponse({ ok: false, error: err.message }));
        return true; // async response

      default:
        sendResponse({ ok: false, error: `Unknown command: ${msg.type}` });
    }
    return true;
  }
);

// ── DOM Actions (inline — minimal wrappers) ─────────────────────

function handleClick(selector: string): void {
  const el = document.querySelector(selector);
  if (el instanceof HTMLElement) {
    el.click();
    notifyBackground("clicked", { selector });
  } else {
    notifyBackground("error", { message: `Element not found: ${selector}` });
  }
}

function handleFill(selector: string, value: string): void {
  const el = document.querySelector(selector);
  if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
    el.value = value;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    notifyBackground("filled", { selector, value });
  } else if (el instanceof HTMLSelectElement) {
    el.value = value;
    el.dispatchEvent(new Event("change", { bubbles: true }));
    notifyBackground("filled", { selector, value });
  } else {
    notifyBackground("error", { message: `Cannot fill element: ${selector}` });
  }
}

function handleExtract(selector: string): string[] {
  const elements = document.querySelectorAll(selector);
  return Array.from(elements).map((el) => el.textContent?.trim() || "");
}

// ── Communication ─────────────────────────────────────────────────

function notifyBackground(action: string, data: Record<string, unknown>): void {
  chrome.runtime.sendMessage({
    type: "content_action",
    action,
    data,
    url: window.location.href,
  });
}

// Announce content script is ready
notifyBackground("content_ready", { url: window.location.href });
