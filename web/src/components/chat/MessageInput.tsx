"use client";

import { useState, type FormEvent } from "react";

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  streaming?: boolean;
  placeholder?: string;
  sendLabel?: string;
}

export default function MessageInput({
  onSend,
  disabled,
  streaming,
  placeholder,
  sendLabel = "Send",
}: MessageInputProps) {
  const [input, setInput] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || disabled || streaming) return;
    onSend(input.trim());
    setInput("");
  }

  return (
    <form onSubmit={handleSubmit} className="px-6 py-4 border-t border-border">
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className="flex-1 px-4 py-2.5 bg-surface border border-border rounded-lg text-foreground placeholder-muted text-sm focus:outline-none focus:border-accent disabled:opacity-40 transition-colors"
        />
        <button
          type="submit"
          disabled={disabled || streaming || !input.trim()}
          className="px-5 py-2.5 bg-accent hover:bg-accent-hover disabled:bg-surface disabled:text-muted text-white text-sm font-medium rounded-lg transition-colors"
        >
          {sendLabel}
        </button>
      </div>
    </form>
  );
}
