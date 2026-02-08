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

      case "highlight_mode":
        // Interactive element picker — highlight on hover, report on click
        enableHighlightMode();
        sendResponse({ ok: true });
        break;

      case "a11y_check":
        // Run basic accessibility audit on the page
        sendResponse({ ok: true, data: runAccessibilityCheck() });
        break;

      case "evaluate_js":
        // Evaluate arbitrary JavaScript in the page context
        try {
          const evalResult = eval(msg.value || "");
          sendResponse({ ok: true, data: String(evalResult) });
        } catch (err: any) {
          sendResponse({ ok: false, error: err.message });
        }
        break;

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

// ── Highlight Mode (Interactive Element Picker) ──────────────────

let highlightModeActive = false;

function enableHighlightMode(): void {
  if (highlightModeActive) return;
  highlightModeActive = true;

  const overlay = document.createElement("div");
  overlay.id = "j2s-highlight-overlay";
  overlay.style.cssText = "position:fixed;top:0;left:0;right:0;bottom:0;z-index:999998;cursor:crosshair;";
  document.body.appendChild(overlay);

  const label = document.createElement("div");
  label.id = "j2s-highlight-label";
  label.style.cssText = "position:fixed;z-index:999999;background:#1e1e1e;color:#4ec9b0;font-size:11px;padding:4px 8px;border-radius:4px;pointer-events:none;display:none;";
  document.body.appendChild(label);

  const onMove = (e: MouseEvent) => {
    overlay.style.pointerEvents = "none";
    const el = document.elementFromPoint(e.clientX, e.clientY);
    overlay.style.pointerEvents = "auto";
    if (el && el !== overlay && el !== label) {
      const rect = el.getBoundingClientRect();
      overlay.style.outline = "2px solid #4ec9b0";
      overlay.style.outlineOffset = "-2px";
      label.style.display = "block";
      label.style.top = `${rect.top - 24}px`;
      label.style.left = `${rect.left}px`;
      label.textContent = `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${el.className ? '.' + String(el.className).split(' ')[0] : ''}`;
    }
  };

  const onClick = (e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    overlay.style.pointerEvents = "none";
    const el = document.elementFromPoint(e.clientX, e.clientY);
    overlay.style.pointerEvents = "auto";
    if (el && el !== overlay && el !== label) {
      const selector = buildSelector(el);
      notifyBackground("element_inspected", {
        selector,
        tag: el.tagName.toLowerCase(),
        text: (el.textContent || "").trim().substring(0, 200),
        attributes: Array.from(el.attributes).reduce((acc: Record<string, string>, a) => { acc[a.name] = a.value; return acc; }, {}),
        rect: el.getBoundingClientRect(),
      });
    }
    disableHighlightMode(overlay, label, onMove, onClick, onKey);
  };

  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      disableHighlightMode(overlay, label, onMove, onClick, onKey);
    }
  };

  overlay.addEventListener("mousemove", onMove);
  overlay.addEventListener("click", onClick);
  document.addEventListener("keydown", onKey);
}

function disableHighlightMode(
  overlay: HTMLElement, label: HTMLElement,
  onMove: (e: MouseEvent) => void, onClick: (e: MouseEvent) => void, onKey: (e: KeyboardEvent) => void
): void {
  highlightModeActive = false;
  overlay.removeEventListener("mousemove", onMove);
  overlay.removeEventListener("click", onClick);
  document.removeEventListener("keydown", onKey);
  overlay.remove();
  label.remove();
}

function buildSelector(el: Element): string {
  if (el.id) return `#${el.id}`;
  const tag = el.tagName.toLowerCase();
  const cls = el.className ? `.${String(el.className).trim().split(/\s+/).join('.')}` : '';
  const parent = el.parentElement;
  if (!parent) return tag + cls;
  const siblings = Array.from(parent.children).filter(c => c.tagName === el.tagName);
  if (siblings.length === 1) return `${buildSelector(parent)} > ${tag}${cls}`;
  const idx = siblings.indexOf(el) + 1;
  return `${buildSelector(parent)} > ${tag}:nth-child(${idx})`;
}

// ── Accessibility Check ──────────────────────────────────────────

function runAccessibilityCheck(): Record<string, unknown> {
  const issues: Array<{ type: string; severity: string; element: string; message: string }> = [];

  // Images without alt text
  document.querySelectorAll("img").forEach((img) => {
    if (!img.alt) {
      issues.push({ type: "missing-alt", severity: "error", element: `img[src="${img.src.substring(0, 80)}"]`, message: "Image missing alt text" });
    }
  });

  // Form inputs without labels
  document.querySelectorAll("input, select, textarea").forEach((input) => {
    const el = input as HTMLInputElement;
    const id = el.id;
    const ariaLabel = el.getAttribute("aria-label");
    const ariaLabelledBy = el.getAttribute("aria-labelledby");
    const hasLabel = id ? document.querySelector(`label[for="${id}"]`) : null;
    if (!hasLabel && !ariaLabel && !ariaLabelledBy && el.type !== "hidden") {
      issues.push({ type: "missing-label", severity: "error", element: `${el.tagName.toLowerCase()}[name="${el.name || ""}"]`, message: "Form control missing label" });
    }
  });

  // Buttons without accessible names
  document.querySelectorAll("button, [role=button]").forEach((btn) => {
    const text = (btn.textContent || "").trim();
    const ariaLabel = btn.getAttribute("aria-label");
    if (!text && !ariaLabel) {
      issues.push({ type: "missing-button-text", severity: "warning", element: btn.outerHTML.substring(0, 80), message: "Button has no accessible name" });
    }
  });

  // Heading hierarchy
  const headings = Array.from(document.querySelectorAll("h1,h2,h3,h4,h5,h6"));
  let lastLevel = 0;
  for (const h of headings) {
    const level = parseInt(h.tagName[1]);
    if (level > lastLevel + 1) {
      issues.push({ type: "heading-skip", severity: "warning", element: h.tagName, message: `Heading skips from h${lastLevel} to h${level}` });
    }
    lastLevel = level;
  }

  // Color contrast (basic check — look for very light text)
  const interactive = document.querySelectorAll("a, button, [role=button], [tabindex]");

  return {
    totalIssues: issues.length,
    errors: issues.filter(i => i.severity === "error").length,
    warnings: issues.filter(i => i.severity === "warning").length,
    issues,
    headingCount: headings.length,
    imageCount: document.querySelectorAll("img").length,
    formCount: document.querySelectorAll("form").length,
    interactiveCount: interactive.length,
    lang: document.documentElement.lang || "missing",
  };
}
