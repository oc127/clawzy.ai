"use client";

import StreamingText from "./StreamingText";

interface MessageBubbleProps {
  role: "user" | "assistant" | "system";
  content: string;
  isStreaming?: boolean;
  thinkingText?: string;
}

export default function MessageBubble({ role, content, isStreaming }: MessageBubbleProps) {
  if (role === "system") {
    return (
      <div className="text-center py-2">
        <span className="text-xs text-muted/70 tracking-wide">{content}</span>
      </div>
    );
  }

  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[65%] px-4 py-2.5 transition-colors ${
          isUser
            ? "bg-accent text-white rounded-2xl rounded-br-md"
            : "bg-surface text-foreground rounded-2xl rounded-bl-md"
        }`}
      >
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
  );
}
