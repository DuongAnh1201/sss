import {AgentUIState} from '../types/voiceAgent.types';
import {VoiceAgentOrb} from './VoiceAgentOrb';

export function ConversationPanel({
  uiState,
  hintText,
  onOrbClick,
}: {
  uiState: AgentUIState;
  hintText: string;
  onOrbClick: () => void;
}) {
  return (
    <section
      className="flex min-h-[320px] flex-col border-b xl:min-h-0 xl:border-b-0 xl:border-r"
      style={{borderColor: 'var(--voice-agent-border)'}}
    >
      <div
        className="border-b px-4 pb-[17px] pt-4"
        style={{borderColor: 'var(--voice-agent-border)'}}
      >
        <span className="royal-display text-[15px] italic tracking-[0.1em] text-(--voice-agent-gold)">
          Briefing
        </span>
      </div>

      <div
        className="relative flex flex-1 items-center justify-center px-4 py-10 xl:min-h-0"
        style={{
          background:
            'radial-gradient(circle at 50% 42%, rgba(200,164,92,0.10) 0%, rgba(200,164,92,0.03) 28%, rgba(10,10,12,0) 60%), #0a0a0c',
        }}
      >
        <VoiceAgentOrb uiState={uiState} onClick={onOrbClick} />
        <div
          className="absolute bottom-8 left-0 right-0 px-6 text-center text-[11px] uppercase tracking-[1.1px] text-[#525252]"
          style={{fontFamily: 'var(--font-voice-agent-mono)'}}
        >
          {uiState === 'listening' || uiState === 'processing' || uiState === 'executing'
            ? 'Reading the room\u2026'
            : hintText}
        </div>
      </div>
    </section>
  );
}
