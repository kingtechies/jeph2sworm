/**
 * Tester Agent — QA/Tester proxy.
 * Writes tests, runs 120 cycles, reports bugs, collects evidence.
 */

import { BaseAgent } from './base-agent';
import { WebSocketService } from '../services/websocket-service';

export class TesterAgent extends BaseAgent {
  constructor(ws: WebSocketService) {
    super('tester', ws);
  }

  get description(): string {
    return 'Writes and runs 120+ test cycles, reports bugs, and collects screenshot evidence';
  }

  get icon(): string {
    return '🧪';
  }

  async writeTests(target: string): Promise<void> {
    await this.sendCommand('write_tests', { target });
  }

  async runTestCycle(startRun: number, endRun: number): Promise<void> {
    await this.sendCommand('run_test_cycle', { start_run: startRun, end_run: endRun });
  }

  async runFullSuite(): Promise<void> {
    await this.sendCommand('run_full_suite');
  }

  async reportBug(description: string): Promise<void> {
    await this.sendCommand('report_bug', { description });
  }

  async captureEvidence(url: string): Promise<void> {
    await this.sendCommand('capture_evidence', { url });
  }
}
