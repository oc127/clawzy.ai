"use client";

import { useEffect, useState } from "react";

interface StreamingTextProps {
  text: string;
  speed?: number;
}

/**
 * Displays text with a typing animation effect.
 * Used for streaming assistant responses.
 */
export default function StreamingText({ text, speed = 20 }: StreamingTextProps) {
  const [displayedLength, setDisplayedLength] = useState(0);

  useEffect(() => {
    // When new text arrives, animate from current position
    if (displayedLength < text.length) {
      const timer = setTimeout(() => {
        setDisplayedLength((prev) => Math.min(prev + 1, text.length));
      }, speed);
      return () => clearTimeout(timer);
    }
  }, [text, displayedLength, speed]);

  // Reset when text shrinks (new message)
  useEffect(() => {
    if (text.length < displayedLength) {
      setDisplayedLength(0);
    }
  }, [text, displayedLength]);

  return (
    <span className="whitespace-pre-wrap text-sm leading-relaxed">
      {text.slice(0, displayedLength)}
      {displayedLength < text.length && (
        <span className="inline-block w-1.5 h-4 bg-accent/60 animate-pulse ml-0.5 align-middle" />
      )}
    </span>
  );
}
