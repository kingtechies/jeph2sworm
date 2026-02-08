/**
 * Screenshot — captures visible tab as base64 PNG from content script context.
 */

export async function captureScreenshot(): Promise<string> {
  // Content scripts can't capture directly — request via background
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({ type: 'capture_screenshot' }, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else if (response?.dataUrl) {
        resolve(response.dataUrl);
      } else {
        reject(new Error('Screenshot capture failed'));
      }
    });
  });
}

export async function captureElement(selector: string): Promise<string | null> {
  const el = document.querySelector<HTMLElement>(selector);
  if (!el) return null;

  // Scroll element into view  
  el.scrollIntoView({ behavior: 'instant', block: 'center' });

  // Wait for scroll
  await new Promise(r => setTimeout(r, 200));

  // Capture via background
  const fullScreenshot = await captureScreenshot();

  // Calculate element bounds for cropping info
  const rect = el.getBoundingClientRect();
  const cropInfo = {
    x: Math.round(rect.x * devicePixelRatio),
    y: Math.round(rect.y * devicePixelRatio),
    width: Math.round(rect.width * devicePixelRatio),
    height: Math.round(rect.height * devicePixelRatio),
  };

  // Send crop info back — cropping happens on background/server side
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({
      type: 'crop_screenshot',
      dataUrl: fullScreenshot,
      crop: cropInfo,
    }, (response) => {
      if (response?.dataUrl) {
        resolve(response.dataUrl);
      } else {
        resolve(fullScreenshot); // Fallback: return full screenshot
      }
    });
  });
}
