/**
 * Content script - injected into every page for DOM interaction.
 *
 * Receives commands from the background service worker to
 * click, fill, extract, and interact with page elements.
 */

interface ContentMessage {
  type: string;
  selector?: string;
  value?: string;
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

      case "extract":
        const data = handleExtract(msg.selector || "");
        sendResponse({ ok: true, data });
        break;

      case "get_dom_info":
        sendResponse({ ok: true, data: getDomInfo() });
        break;

      case "highlight":
        handleHighlight(msg.selector || "");
        sendResponse({ ok: true });
        break;

      default:
        sendResponse({ ok: false, error: `Unknown command: ${msg.type}` });
    }
    return true;
  }
);

// ── DOM Actions ───────────────────────────────────────────────────

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

function handleHighlight(selector: string): void {
  // Remove previous highlights
  document
    .querySelectorAll(".jeph2sworm-highlight")
    .forEach((el) => el.classList.remove("jeph2sworm-highlight"));

  const el = document.querySelector(selector);
  if (el instanceof HTMLElement) {
    el.style.outline = "3px solid #4f46e5";
    el.style.outlineOffset = "2px";
    el.classList.add("jeph2sworm-highlight");

    // Remove highlight after 3 seconds
    setTimeout(() => {
      el.style.outline = "";
      el.style.outlineOffset = "";
      el.classList.remove("jeph2sworm-highlight");
    }, 3000);
  }
}

function getDomInfo(): Record<string, unknown> {
  return {
    title: document.title,
    url: window.location.href,
    forms: Array.from(document.forms).map((form) => ({
      id: form.id,
      action: form.action,
      inputs: Array.from(form.elements).map((el) => ({
        tag: el.tagName.toLowerCase(),
        type: (el as HTMLInputElement).type || "",
        name: (el as HTMLInputElement).name || "",
        id: el.id,
      })),
    })),
    links: Array.from(document.links)
      .slice(0, 50)
      .map((a) => ({ href: a.href, text: a.textContent?.trim() })),
    buttons: Array.from(document.querySelectorAll("button, [role=button]"))
      .slice(0, 30)
      .map((b) => ({
        text: b.textContent?.trim(),
        id: b.id,
        class: b.className,
      })),
  };
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
