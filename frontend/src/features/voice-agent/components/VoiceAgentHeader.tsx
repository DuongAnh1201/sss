import { AgentUIState } from "../types/voiceAgent.types";
import { voiceAgentLayoutTokens } from "../utils/voiceAgentLayoutTokens";
import { SystemStatusBadge } from "./SystemStatusBadge";
import { VoiceAgentIcon } from "./VoiceAgentIcons";

export function VoiceAgentHeader({ uiState }: { uiState: AgentUIState }) {
  return (
    <header
      className="relative flex items-center justify-between border-b bg-(--voice-agent-shell) px-6"
      style={{
        height: voiceAgentLayoutTokens.headerHeight,
        borderColor: "var(--voice-agent-border)",
      }}
    >
      <div className="flex items-center gap-3">
        <div className="crest-frame flex h-8 w-8 items-center justify-center rounded-full text-(--voice-agent-gold-bright)">
          <VoiceAgentIcon name="moneypenny" className="h-4 w-4" />
        </div>
        <div className="flex flex-col leading-none">
          <span className="royal-display text-[22px] font-semibold tracking-[0.14em] text-(--voice-agent-gold-bright)">
            MONEYPENNY
          </span>
          <span className="mt-0.5 text-[8px] font-medium uppercase tracking-[3px] text-[#8a8170]">
            On Her Majesty&rsquo;s Service
          </span>
        </div>
      </div>

      <div className="absolute left-1/2 hidden -translate-x-1/2 md:flex">
        <SystemStatusBadge uiState={uiState} />
      </div>

      <div className="flex items-center gap-4 text-[#737373]">
        <div className="md:hidden">
          <SystemStatusBadge uiState={uiState} />
        </div>
        <button
          type="button"
          aria-label="Settings"
          className="transition-colors hover:text-white"
        >
          <VoiceAgentIcon name="settings" className="h-4.5 w-4.5" />
        </button>
        <button
          type="button"
          aria-label="Profile"
          className="transition-colors hover:text-white"
        >
          <VoiceAgentIcon name="user" className="h-4.5 w-4.5" />
        </button>
      </div>
    </header>
  );
}
