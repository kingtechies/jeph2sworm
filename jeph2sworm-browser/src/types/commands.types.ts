/**
 * Command types — messages between background, content, devtools, and server.
 */

export interface BrowserCommand {
  id: string;
  type: CommandType;
  params: Record<string, unknown>;
  tabId?: number;
}

export type CommandType =
  | 'navigate'
  | 'click'
  | 'fill'
  | 'screenshot'
  | 'extract_dom'
  | 'highlight'
  | 'clear_highlights'
  | 'fill_form'
  | 'submit_form'
  | 'evaluate_js'
  | 'start_recording'
  | 'stop_recording'
  | 'get_network_log'
  | 'get_console_log'
  | 'get_performance';

export interface CommandResult {
  id: string;
  success: boolean;
  data?: unknown;
  error?: string;
}
