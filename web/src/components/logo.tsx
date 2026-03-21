import { cn } from "@/lib/cn";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function Logo({ size = "md", className }: LogoProps) {
  const textSize = {
    sm: "text-base",
    md: "text-xl",
    lg: "text-3xl",
  }[size];

  const iconSize = {
    sm: 28,
    md: 36,
    lg: 52,
  }[size];

  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <LogoMark size={iconSize} />
      <span className={cn("font-extrabold tracking-tight leading-none", textSize)}>
        <span style={{ color: "#FF385C" }}>Nippon</span>
        <span style={{ color: "#222222" }}>Claw</span>
      </span>
    </span>
  );
}

export function LogoMark({ size = 36 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* Background circle */}
      <circle cx="20" cy="20" r="20" fill="#FF385C" />

      {/* Stylized claw/N shape in white */}
      {/* Left arm */}
      <path
        d="M10 28 L10 16 Q10 12 14 11 Q17 10 18 13 L18 20"
        stroke="white"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      {/* Right arm */}
      <path
        d="M30 28 L30 16 Q30 12 26 11 Q23 10 22 13 L22 20"
        stroke="white"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      {/* Bottom claw */}
      <path
        d="M14 26 Q14 31 20 32 Q26 31 26 26"
        stroke="white"
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />
      {/* Center dot */}
      <circle cx="20" cy="22" r="2.5" fill="white" opacity="0.9" />
    </svg>
  );
}

/** For backward compat */
export function LogoIcon({ size = 32 }: { size?: number }) {
  return <LogoMark size={size} />;
}
