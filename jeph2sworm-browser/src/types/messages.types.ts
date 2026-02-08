/**
 * Message types — internal messaging between extension components.
 */

export interface ExtensionMessage {
  type: string;
  [key: string]: unknown;
}

export interface BackgroundMessage extends ExtensionMessage {
  type:
    | 'connect'
    | 'disconnect'
    | 'get_status'
    | 'capture_screenshot'
    | 'crop_screenshot'
    | 'send_to_server'
    | 'devtools_panel_shown'
    | 'devtools_panel_hidden'
    | 'network_request'
    | 'console_entry';
}

export interface ContentMessage extends ExtensionMessage {
  type:
    | 'extract_dom'
    | 'highlight_element'
    | 'clear_highlights'
    | 'fill_form'
    | 'submit_form'
    | 'click_element'
    | 'evaluate_js';
}

export interface ServerMessage {
  type: string;
  agent?: string;
  data?: unknown;
  timestamp?: number;
}
