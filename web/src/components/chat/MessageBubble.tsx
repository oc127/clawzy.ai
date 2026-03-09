"use client";

import StreamingText from "./StreamingText";

interface MessageBubbleProps {
  role: "user" | "assistant" | "system";
  content: string;
  isStreaming?: boolean;
  thinkingText?: string;
  agentName?: string;
}

export default function MessageBubble({ role, content, isStreaming, agentName }: MessageBubbleProps) {
  // --- Platform notification (system messages) ---
  if (role === "system") {
    return (
      <div className="flex justify-center py-1.5">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 text-[11px] text-muted/60 border border-dashed border-border/50 rounded-full">
          {content}
        </span>
      </div>
    );
  }

  const isUser = role === "user";

  // --- User message ---
  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[65%] px-4 py-2.5 bg-accent text-white rounded-2xl rounded-br-md">
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{content}</p>
        </div>
      </div>
    );
  }

  // --- Lobster (assistant) message ---
  return (
    <div className="flex justify-start gap-2.5">
      {/* Avatar */}
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-surface-hover flex items-center justify-center text-sm mt-0.5">
        🦞
      </div>

      <div className="max-w-[65%]">
        {/* Agent name label */}
        {agentName && (
          <p className="text-[11px] text-muted mb-1 ml-1">{agentName}</p>
        )}

        {/* Bubble with left accent bar */}
        <div className="relative bg-surface text-foreground rounded-2xl rounded-bl-md pl-4 pr-4 py-2.5">
          {/* Accent bar */}
          <div className="absolute left-0 top-3 bottom-3 w-[3px] rounded-full bg-accent/40" />

          {!content && isStreaming ? (
            <span className="inline-flex items-center gap-1.5 py-0.5">
              <span className="lobster-dot" style={{ animationDelay: "0s" }} />
              <span className="lobster-dot" style={{ animationDelay: "0.15s" }} />
              <span className="lobster-dot" style={{ animationDelay: "0.3s" }} />
            </span>
          ) : isStreaming && content ? (
            <StreamingText text={content} />
          ) : (
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{content}</p>
          )}
        </div>
      </div>
    </div>
  );
}
