/**
 * Storage — chrome.storage wrapper with typed access.
 */

export async function get<T>(key: string, defaultValue?: T): Promise<T | undefined> {
  const result = await chrome.storage.local.get(key);
  return (result[key] as T) ?? defaultValue;
}

export async function set(key: string, value: unknown): Promise<void> {
  await chrome.storage.local.set({ [key]: value });
}

export async function remove(key: string): Promise<void> {
  await chrome.storage.local.remove(key);
}

export async function getAll(): Promise<Record<string, unknown>> {
  return chrome.storage.local.get();
}

export async function clear(): Promise<void> {
  await chrome.storage.local.clear();
}

// Config helpers
export interface ExtensionConfig {
  serverHost: string;
  serverPort: number;
  autoConnect: boolean;
  captureNetwork: boolean;
  captureConsole: boolean;
}

const DEFAULT_CONFIG: ExtensionConfig = {
  serverHost: 'localhost',
  serverPort: 8000,
  autoConnect: true,
  captureNetwork: true,
  captureConsole: true,
};

export async function getConfig(): Promise<ExtensionConfig> {
  const stored = await get<Partial<ExtensionConfig>>('config');
  return { ...DEFAULT_CONFIG, ...stored };
}

export async function setConfig(config: Partial<ExtensionConfig>): Promise<void> {
  const current = await getConfig();
  await set('config', { ...current, ...config });
}
