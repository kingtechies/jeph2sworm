/**
 * Validators — client-side input validation utilities.
 */

export function isValidProjectName(name: string): boolean {
  return /^[a-zA-Z][a-zA-Z0-9_-]{2,64}$/.test(name);
}

export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

export function isValidPort(port: number): boolean {
  return Number.isInteger(port) && port >= 1 && port <= 65535;
}

export function isValidAgentRole(role: string): boolean {
  const roles = ['pm', 'brain', 'backend', 'frontend', 'ux', 'tester', 'devops'];
  return roles.includes(role.toLowerCase());
}

export function sanitizeFilename(name: string): string {
  return name.replace(/[^a-zA-Z0-9._-]/g, '_').substring(0, 255);
}

export function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

export function isValidJson(str: string): boolean {
  try {
    JSON.parse(str);
    return true;
  } catch {
    return false;
  }
}

export function validateServerConfig(host: string, port: number): string | null {
  if (!host || host.trim().length === 0) {
    return 'Server host cannot be empty';
  }
  if (!isValidPort(port)) {
    return 'Port must be between 1 and 65535';
  }
  return null;
}
