"use client";

import { cn } from "@/lib/cn";

const MOOD_CONFIG: Record<string, { eyes: string; mouth: string; blush: boolean; color: string }> = {
  happy:   { eyes: "^  ^", mouth: "◡", blush: true,  color: "#ff385c" },
  excited: { eyes: "★  ★", mouth: "▽", blush: true,  color: "#ff8c69" },
  curious: { eyes: "◉  ◉", mouth: "○", blush: false, color: "#3b82f6" },
  calm:    { eyes: "–  –", mouth: "◡", blush: false, color: "#14b8a6" },
  playful: { eyes: "◠  ◠", mouth: "ω", blush: true,  color: "#f59e0b" },
  focused: { eyes: "◉  ◉", mouth: "—", blush: false, color: "#8b5cf6" },
  loving:  { eyes: "♡  ♡", mouth: "◡", blush: true,  color: "#ec4899" },
  neutral: { eyes: "•  •", mouth: "—", blush: false, color: "#717171" },
  shy:     { eyes: ">  <", mouth: "◡", blush: true,  color: "#f472b6" },
  sad:     { eyes: "•  •", mouth: "︵", blush: false, color: "#6b7280" },
  missing: { eyes: "·  ·", mouth: "◡", blush: false, color: "#a78bfa" },
  tired:   { eyes: "–  –", mouth: "~", blush: false, color: "#9ca3af" },
};

export function LucyAvatar({
  mood = "neutral",
  size = "md",
  className,
}: {
  mood?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const config = MOOD_CONFIG[mood] ?? MOOD_CONFIG.neutral;
  const sizeClass = size === "sm" ? "h-12 w-12" : size === "lg" ? "h-24 w-24" : "h-16 w-16";
  const fontSize = size === "sm" ? "text-[8px]" : size === "lg" ? "text-base" : "text-xs";
  const mouthSize = size === "sm" ? "text-[10px]" : size === "lg" ? "text-xl" : "text-sm";

  return (
    <div
      className={cn(
        sizeClass,
        "relative flex flex-col items-center justify-center rounded-full transition-all duration-500",
        "animate-lucy-breathe",
        className,
      )}
      style={{ background: `linear-gradient(135deg, ${config.color}22, ${config.color}44)`, border: `2px solid ${config.color}66` }}
    >
      <span className={cn(fontSize, "font-mono leading-none tracking-widest select-none")} style={{ color: config.color }}>
        {config.eyes}
      </span>
      <span className={cn(mouthSize, "font-mono leading-none select-none mt-0.5")} style={{ color: config.color }}>
        {config.mouth}
      </span>
      {config.blush && (
        <>
          <span
            className="absolute rounded-full opacity-30 animate-lucy-blush"
            style={{
              background: config.color,
              width: size === "lg" ? "8px" : "5px",
              height: size === "lg" ? "5px" : "3px",
              left: size === "lg" ? "15%" : "18%",
              top: "52%",
            }}
          />
          <span
            className="absolute rounded-full opacity-30 animate-lucy-blush"
            style={{
              background: config.color,
              width: size === "lg" ? "8px" : "5px",
              height: size === "lg" ? "5px" : "3px",
              right: size === "lg" ? "15%" : "18%",
              top: "52%",
            }}
          />
        </>
      )}
    </div>
  );
}
