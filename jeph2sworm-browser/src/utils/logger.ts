/**
 * Logger — extension logging with level support.
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LEVEL_ORDER: Record<LogLevel, number> = { debug: 0, info: 1, warn: 2, error: 3 };
let minLevel: LogLevel = 'info';

export function setLogLevel(level: LogLevel): void {
  minLevel = level;
}

function shouldLog(level: LogLevel): boolean {
  return LEVEL_ORDER[level] >= LEVEL_ORDER[minLevel];
}

function log(level: LogLevel, message: string, data?: unknown): void {
  if (!shouldLog(level)) return;
  const ts = new Date().toISOString();
  const prefix = `[jeph2sworm] [${ts}] [${level.toUpperCase()}]`;
  const fn = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;
  if (data !== undefined) {
    fn(prefix, message, data);
  } else {
    fn(prefix, message);
  }
}

export function debug(msg: string, data?: unknown): void { log('debug', msg, data); }
export function info(msg: string, data?: unknown): void { log('info', msg, data); }
export function warn(msg: string, data?: unknown): void { log('warn', msg, data); }
export function error(msg: string, data?: unknown): void { log('error', msg, data); }
