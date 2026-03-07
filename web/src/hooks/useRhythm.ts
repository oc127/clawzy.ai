"use client";

import { useCallback, useRef } from "react";

type TimeOfDay = "morning" | "afternoon" | "evening" | "night";

function getTimeOfDay(): TimeOfDay {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return "morning";
  if (hour >= 12 && hour < 17) return "afternoon";
  if (hour >= 17 && hour < 22) return "evening";
  return "night";
}

const MILESTONES = [1, 5, 10, 25, 50] as const;

interface RhythmTexts {
  greetings: Record<TimeOfDay, string>;
  milestones: Record<number, string>;
}

export function useRhythm(texts: RhythmTexts) {
  const replyCountRef = useRef(0);
  const celebratedRef = useRef<Set<number>>(new Set());

  const timeOfDay = getTimeOfDay();
  const greeting = texts.greetings[timeOfDay];

  const onAssistantReply = useCallback((): string | null => {
    replyCountRef.current += 1;
    const count = replyCountRef.current;

    if (MILESTONES.includes(count as (typeof MILESTONES)[number]) && !celebratedRef.current.has(count)) {
      celebratedRef.current.add(count);
      return texts.milestones[count] || null;
    }
    return null;
  }, [texts.milestones]);

  return { timeOfDay, greeting, onAssistantReply };
}
