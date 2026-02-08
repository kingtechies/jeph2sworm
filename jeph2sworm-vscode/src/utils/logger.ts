/**
 * Extension Logger — structured logging for the extension output channel.
 */

import * as vscode from 'vscode';

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

let outputChannel: vscode.OutputChannel | undefined;
let currentLevel = LogLevel.INFO;

export function initLogger(level: LogLevel = LogLevel.INFO): vscode.OutputChannel {
  if (!outputChannel) {
    outputChannel = vscode.window.createOutputChannel('jeph2sworm');
  }
  currentLevel = level;
  return outputChannel;
}

function log(level: LogLevel, label: string, message: string, data?: unknown): void {
  if (level < currentLevel || !outputChannel) { return; }
  const ts = new Date().toISOString();
  let line = `[${ts}] [${label}] ${message}`;
  if (data !== undefined) {
    line += ` ${JSON.stringify(data)}`;
  }
  outputChannel.appendLine(line);
}

export function debug(message: string, data?: unknown): void { log(LogLevel.DEBUG, 'DEBUG', message, data); }
export function info(message: string, data?: unknown): void { log(LogLevel.INFO, 'INFO', message, data); }
export function warn(message: string, data?: unknown): void { log(LogLevel.WARN, 'WARN', message, data); }
export function error(message: string, data?: unknown): void { log(LogLevel.ERROR, 'ERROR', message, data); }

export function show(): void { outputChannel?.show(); }
