/**
 * DOM Extractor — extracts structured data from web pages for agent analysis.
 */

export interface DOMData {
  title: string;
  url: string;
  headings: Array<{ level: number; text: string }>;
  links: Array<{ text: string; href: string }>;
  forms: Array<{ id: string; action: string; inputs: Array<{ name: string; type: string; value: string }> }>;
  images: Array<{ alt: string; src: string }>;
  text: string;
  meta: Record<string, string>;
}

export function extractDOM(): DOMData {
  const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6')).map(el => ({
    level: parseInt(el.tagName[1]),
    text: el.textContent?.trim() || '',
  }));

  const links = Array.from(document.querySelectorAll('a[href]')).slice(0, 100).map(el => ({
    text: el.textContent?.trim() || '',
    href: (el as HTMLAnchorElement).href,
  }));

  const forms = Array.from(document.querySelectorAll('form')).map(form => ({
    id: form.id || '',
    action: (form as HTMLFormElement).action || '',
    inputs: Array.from(form.querySelectorAll('input,select,textarea')).map(inp => ({
      name: (inp as HTMLInputElement).name || '',
      type: (inp as HTMLInputElement).type || 'text',
      value: (inp as HTMLInputElement).value || '',
    })),
  }));

  const images = Array.from(document.querySelectorAll('img')).slice(0, 50).map(img => ({
    alt: (img as HTMLImageElement).alt || '',
    src: (img as HTMLImageElement).src || '',
  }));

  const meta: Record<string, string> = {};
  document.querySelectorAll('meta[name],meta[property]').forEach(m => {
    const key = m.getAttribute('name') || m.getAttribute('property') || '';
    meta[key] = m.getAttribute('content') || '';
  });

  return {
    title: document.title,
    url: location.href,
    headings,
    links,
    forms,
    images,
    text: document.body?.innerText?.substring(0, 10000) || '',
    meta,
  };
}
