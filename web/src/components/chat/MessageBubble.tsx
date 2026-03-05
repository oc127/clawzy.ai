interface MessageBubbleProps {
  role: "user" | "assistant" | "system";
  content: string;
  isStreaming?: boolean;
  thinkingText?: string;
}

export default function MessageBubble({ role, content, isStreaming, thinkingText }: MessageBubbleProps) {
  if (role === "system") {
    return (
      <div className="text-center py-1">
        <span className="text-xs text-muted">{content}</span>
      </div>
    );
  }

  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[65%] rounded-xl px-4 py-2.5 ${
          role === "user"
            ? "bg-accent text-white"
            : "bg-surface text-foreground"
        }`}
      >
        <p className="whitespace-pre-wrap text-sm leading-relaxed">
          {content || (isStreaming ? thinkingText || "" : "")}
        </p>
      </div>
    </div>
  );
}
