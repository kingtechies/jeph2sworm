/**
 * Terminal Manager — manages VS Code terminal instances for agent commands.
 */

import * as vscode from 'vscode';
import { RulesEngine } from './rules-engine';

interface ManagedTerminal {
  terminal: vscode.Terminal;
  agent: string;
  busy: boolean;
}

export class TerminalManager {
  private terminals = new Map<string, ManagedTerminal>();
  private rulesEngine: RulesEngine;

  constructor(workspaceRoot: string) {
    this.rulesEngine = new RulesEngine(workspaceRoot);

    // Clean up disposed terminals
    vscode.window.onDidCloseTerminal(t => {
      for (const [key, mt] of this.terminals) {
        if (mt.terminal === t) {
          this.terminals.delete(key);
          break;
        }
      }
    });
  }

  getOrCreateTerminal(agent: string): vscode.Terminal {
    let mt = this.terminals.get(agent);
    if (mt) { return mt.terminal; }

    const terminal = vscode.window.createTerminal({
      name: `jeph2sworm: ${agent}`,
      iconPath: new vscode.ThemeIcon('robot'),
    });

    mt = { terminal, agent, busy: false };
    this.terminals.set(agent, mt);
    return terminal;
  }

  async runCommand(agent: string, command: string): Promise<void> {
    const check = this.rulesEngine.validateCommand(command);
    if (!check.valid) {
      vscode.window.showErrorMessage(`Blocked: ${check.reason}`);
      return;
    }

    const terminal = this.getOrCreateTerminal(agent);
    const mt = this.terminals.get(agent)!;
    mt.busy = true;
    terminal.sendText(command);
    terminal.show(true);
    mt.busy = false;
  }

  showTerminal(agent: string): void {
    this.terminals.get(agent)?.terminal.show();
  }

  disposeAll(): void {
    for (const mt of this.terminals.values()) {
      mt.terminal.dispose();
    }
    this.terminals.clear();
  }

  getActiveAgents(): string[] {
    return Array.from(this.terminals.keys());
  }
}
