"use client";

import { useEffect, useState } from "react";

interface CreditsBadgeProps {
  balance: number;
  label?: string;
  pulse?: boolean;
}

export default function CreditsBadge({ balance, label = "Energy", pulse }: CreditsBadgeProps) {
  const [animating, setAnimating] = useState(false);

  useEffect(() => {
    if (pulse) {
      setAnimating(true);
      const timer = setTimeout(() => setAnimating(false), 600);
      return () => clearTimeout(timer);
    }
  }, [pulse, balance]);

  return (
    <span
      className={`inline-block text-xs transition-all duration-300 ${
        animating ? "text-accent scale-110" : "text-muted"
      }`}
    >
      {balance} {label}
    </span>
  );
}
