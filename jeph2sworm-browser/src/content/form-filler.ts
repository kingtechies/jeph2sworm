/**
 * Form Filler — automatically fills form fields for testing.
 */

export interface FormData {
  [selector: string]: string;
}

export function fillForm(data: FormData): { filled: string[]; failed: string[] } {
  const filled: string[] = [];
  const failed: string[] = [];

  for (const [selector, value] of Object.entries(data)) {
    const el = document.querySelector<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(selector);
    if (!el) {
      failed.push(selector);
      continue;
    }

    if (el instanceof HTMLSelectElement) {
      const option = Array.from(el.options).find(o => o.value === value || o.text === value);
      if (option) {
        el.value = option.value;
        el.dispatchEvent(new Event('change', { bubbles: true }));
        filled.push(selector);
      } else {
        failed.push(selector);
      }
    } else if (el.type === 'checkbox' || el.type === 'radio') {
      const shouldCheck = value === 'true' || value === '1';
      if ((el as HTMLInputElement).checked !== shouldCheck) {
        (el as HTMLInputElement).click();
      }
      filled.push(selector);
    } else {
      // Text, email, password, textarea, etc.
      el.focus();
      el.value = '';
      // Simulate realistic typing via input events
      for (const char of value) {
        el.value += char;
        el.dispatchEvent(new Event('input', { bubbles: true }));
      }
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.blur();
      filled.push(selector);
    }
  }

  return { filled, failed };
}

export function submitForm(formSelector: string): boolean {
  const form = document.querySelector<HTMLFormElement>(formSelector);
  if (!form) return false;

  const submitBtn = form.querySelector<HTMLButtonElement>('button[type="submit"], input[type="submit"]');
  if (submitBtn) {
    submitBtn.click();
  } else {
    form.submit();
  }
  return true;
}

export function clearForm(formSelector: string): void {
  const form = document.querySelector<HTMLFormElement>(formSelector);
  if (form) { form.reset(); }
}

export function getFormValues(formSelector: string): Record<string, string> {
  const form = document.querySelector<HTMLFormElement>(formSelector);
  if (!form) return {};
  const fd = new globalThis.FormData(form);
  const result: Record<string, string> = {};
  fd.forEach((value, key) => { result[key] = String(value); });
  return result;
}
