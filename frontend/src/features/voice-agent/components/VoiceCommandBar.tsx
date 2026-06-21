import { FormEvent } from "react";
import { AgentUIState } from "../types/voiceAgent.types";
import {
  voiceAgentLayoutTokens,
  voiceAgentMicCopy,
} from "../utils/voiceAgentLayoutTokens";
import { VoiceAgentIcon } from "./VoiceAgentIcons";

function micButtonTone(uiState: AgentUIState) {
  switch (uiState) {
    case "idle":
      return {
        backgroundColor: "#171717",
        color: "#737373",
      };
    case "error":
      return {
        backgroundColor: "#2a1515",
        color: "#ef4444",
      };
    default:
      return {
        backgroundColor: "var(--voice-agent-live-accent)",
        color: "#ffffff",
      };
  }
}

export function VoiceCommandBar({
  uiState,
  transcriptPreview,
  onMicClick,
  onSubmitText,
  isSessionActive = false,
}: {
  uiState: AgentUIState;
  transcriptPreview: string;
  onMicClick: () => void;
  onSubmitText?: (text: string) => void;
  isSessionActive?: boolean;
}) {
  const micTone = micButtonTone(uiState);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const input = form.elements.namedItem("command") as HTMLInputElement | null;
    const text = input?.value.trim() ?? "";
    if (!text || !onSubmitText) {
      return;
    }
    onSubmitText(text);
    form.reset();
  };

  return (
    <footer
      className="flex items-center justify-center border-t bg-[var(--voice-agent-shell)] px-6"
      style={{
        height: voiceAgentLayoutTokens.footerHeight,
        borderColor: "var(--voice-agent-border)",
      }}
    >
      <form
        className="flex h-14 w-full items-center gap-4 rounded-full border bg-[#111111] px-[25px]"
        style={{ borderColor: "var(--voice-agent-border)" }}
        onSubmit={handleSubmit}
      >
        <div className="w-[26px]" />
        {isSessionActive && onSubmitText ? (
          <input
            name="command"
            type="text"
            autoComplete="off"
            placeholder="Type an instruction…"
            className="min-w-0 flex-1 bg-transparent text-[12.8px] italic text-[#e5e5e5] outline-none placeholder:text-[#525252]"
          />
        ) : (
          <div className="min-w-0 flex-1 truncate text-[12.8px] italic text-[#a3a3a3]">
            {transcriptPreview}
          </div>
        )}
        <div className="flex shrink-0 items-center gap-2">
          <span
            className="text-[10px] uppercase tracking-[-0.5px] text-[#525252]"
            style={{ fontFamily: "var(--font-voice-agent-mono)" }}
          >
            {voiceAgentMicCopy[uiState]}
          </span>
          <button
            type="button"
            onClick={onMicClick}
            aria-label="Toggle voice session"
            className="flex h-8 w-8 items-center justify-center rounded-full"
            style={micTone}
          >
            <VoiceAgentIcon name="waveform" className="h-3.5 w-3.5" />
          </button>
        </div>
      </form>
    </footer>
  );
}
