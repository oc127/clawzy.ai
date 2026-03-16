import { cn } from "@/lib/cn";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
  className?: string;
}

export function Logo({ size = "md", showText = true, className }: LogoProps) {
  const sizes = {
    sm: { icon: 24, text: "text-base" },
    md: { icon: 32, text: "text-xl" },
    lg: { icon: 48, text: "text-3xl" },
  };

  const s = sizes[size];

  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <svg
        width={s.icon}
        height={s.icon}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        {/* Lobster claw - left pincer */}
        <path
          d="M14 8C8 8 4 14 4 20C4 26 8 30 12 30L16 26C12 26 8 24 8 20C8 16 10 12 14 12C18 12 20 16 20 20L24 16C22 10 18 8 14 8Z"
          fill="var(--primary)"
        />
        {/* Lobster claw - right pincer */}
        <path
          d="M34 8C40 8 44 14 44 20C44 26 40 30 36 30L32 26C36 26 40 24 40 20C40 16 38 12 34 12C30 12 28 16 28 20L24 16C26 10 30 8 34 8Z"
          fill="var(--primary)"
        />
        {/* Claw base / body */}
        <path
          d="M16 28C16 28 18 34 24 34C30 34 32 28 32 28L36 32C36 32 32 40 24 40C16 40 12 32 12 32L16 28Z"
          fill="var(--secondary)"
          opacity="0.9"
        />
        {/* Center dot - eye/joint */}
        <circle cx="24" cy="22" r="3" fill="var(--primary)" opacity="0.6" />
      </svg>
      {showText && (
        <span className={cn("font-bold tracking-tight", s.text)}>
          <span className="text-primary">Clawzy</span>
          <span className="text-muted-foreground">.ai</span>
        </span>
      )}
    </span>
  );
}

/** Icon-only version for favicon/small spaces */
export function LogoIcon({ size = 32 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M14 8C8 8 4 14 4 20C4 26 8 30 12 30L16 26C12 26 8 24 8 20C8 16 10 12 14 12C18 12 20 16 20 20L24 16C22 10 18 8 14 8Z"
        fill="#FF5A5F"
      />
      <path
        d="M34 8C40 8 44 14 44 20C44 26 40 30 36 30L32 26C36 26 40 24 40 20C40 16 38 12 34 12C30 12 28 16 28 20L24 16C26 10 30 8 34 8Z"
        fill="#FF5A5F"
      />
      <path
        d="M16 28C16 28 18 34 24 34C30 34 32 28 32 28L36 32C36 32 32 40 24 40C16 40 12 32 12 32L16 28Z"
        fill="#FFAB76"
        opacity="0.9"
      />
      <circle cx="24" cy="22" r="3" fill="#FF5A5F" opacity="0.6" />
    </svg>
  );
}
