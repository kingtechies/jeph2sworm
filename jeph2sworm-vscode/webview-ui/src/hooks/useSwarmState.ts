/**
 * useSwarmState — hook to subscribe to swarm state updates.
 */

import { useEffect, useState } from 'react';
import { useMessageListener } from './useVsCodeApi';

export interface AgentState {
  role: string;
  status: 'idle' | 'working' | 'error';
  currentTask?: string;
}

export interface SwarmState {
  connected: boolean;
  agents: AgentState[];
  progress: number;
  phase: string;
}

const DEFAULT_STATE: SwarmState = {
  connected: false,
  agents: [],
  progress: 0,
  phase: 'idle',
};

export function useSwarmState(): SwarmState {
  const [state, setState] = useState<SwarmState>(DEFAULT_STATE);

  useMessageListener((msg) => {
    if (msg.command === 'swarmState') {
      setState(msg.state as SwarmState);
    }
    if (msg.command === 'agentUpdate') {
      setState((prev) => {
        const agents = [...prev.agents];
        const idx = agents.findIndex((a) => a.role === msg.role);
        const update = msg as unknown as AgentState;
        if (idx >= 0) {
          agents[idx] = { ...agents[idx], ...update };
        } else {
          agents.push(update);
        }
        return { ...prev, agents };
      });
    }
  });

  return state;
}
