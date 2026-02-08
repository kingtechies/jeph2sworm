/**
 * Rules Engine Client — validates actions client-side before sending to server.
 * Mirrors Python security/rules_engine.py rules.
 */

const FORBIDDEN_COMMANDS = [
  /\brm\s+-rf\b/,
  /\bsudo\b/,
  /\bmkfs\b/,
  /\bdd\s+if=/,
  /\bformat\b/,
  /\b>\s*\/dev\/sd/,
  /\bchmod\s+777\b/,
  /\bcurl\b.*\|\s*bash/,
];

const PROTECTED_EXTENSIONS = ['.env', '.pem', '.key', '.cert', '.p12'];

export class RulesEngine {
  private workspaceRoot: string;

  constructor(workspaceRoot: string) {
    this.workspaceRoot = workspaceRoot;
  }

  validateCommand(command: string): { valid: boolean; reason?: string } {
    for (const pattern of FORBIDDEN_COMMANDS) {
      if (pattern.test(command)) {
        return { valid: false, reason: `Blocked dangerous command pattern: ${pattern.source}` };
      }
    }
    return { valid: true };
  }

  validateFilePath(filePath: string): { valid: boolean; reason?: string } {
    if (!filePath.startsWith(this.workspaceRoot)) {
      return { valid: false, reason: 'File access outside workspace is not allowed' };
    }
    return { valid: true };
  }

  validateFileDelete(filePath: string): { valid: boolean; reason?: string } {
    return { valid: false, reason: 'File deletion is not allowed — agents can only create and modify files' };
  }

  isProtectedFile(filePath: string): boolean {
    return PROTECTED_EXTENSIONS.some(ext => filePath.endsWith(ext));
  }
}
