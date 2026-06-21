import {AgentUIState} from '../types/voiceAgent.types';

export const voiceAgentLayoutTokens = {
  headerHeight: 56,
  footerHeight: 96,
  panelWidth: 320,
  outerPadding: 24,
  timelinePadding: 32,
  cardPadding: 17,
  borderRadius: 4,
  orbSize: 240,
  colors: {
    shell: '#08080a',
    centerShell: '#0a0a0c',
    panel: '#101013',
    panelRaised: '#16161a',
    border: '#2a2620',
    text: '#f5f0e6',
    mutedText: '#b8ad97',
    dimText: '#8a8170',
    subtleText: '#5f5949',
    accent: '#c8a45c',
    success: '#6fae7a',
    warning: '#d8a85a',
    danger: '#c0584f',
  },
} as const;

export const voiceAgentStatusCopy: Record<AgentUIState, string> = {
  idle: 'AT YOUR SERVICE',
  listening: 'LISTENING',
  processing: 'DECIPHERING',
  executing: 'IN THE FIELD',
  waiting_approval: 'AWAITING YOUR WORD',
  completed: 'MISSION COMPLETE',
  error: 'COMPROMISED',
};

export const voiceAgentMicCopy: Record<AgentUIState, string> = {
  idle: 'READY',
  listening: 'LISTENING',
  processing: 'PROCESSING',
  executing: 'EXECUTING',
  waiting_approval: 'PENDING',
  completed: 'COMPLETE',
  error: 'ERROR',
};

export const voiceAgentStatusTone: Record<AgentUIState, string> = {
  idle: '#5f5949',
  listening: 'var(--voice-agent-live-accent)',
  processing: 'var(--voice-agent-live-accent)',
  executing: 'var(--voice-agent-live-accent)',
  waiting_approval: '#d8a85a',
  completed: '#6fae7a',
  error: '#c0584f',
};
