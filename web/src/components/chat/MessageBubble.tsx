interface MessageBubbleProps {
  role: "user" | "assistant" | "system";
  content: string;
  isStreaming?: boolean;
  thinkingText?: string;
}

export default function MessageBubble({ role, content, isStreaming, thinkingText }: MessageBubbleProps) {
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
        <p className="whitespace-pre-wrap text-sm leading-relaxed">
          {content || (isStreaming ? thinkingText || "" : "")}
        </p>
      </div>
    </div>
  );
}
