"use client";

import { useEffect, useState } from "react";
import Lottie from "lottie-react";

interface LottieIconProps {
  src: string;
  className?: string;
  loop?: boolean;
  autoplay?: boolean;
  fallback?: React.ReactNode;
}

export function LottieIcon({
  src,
  className = "w-16 h-16",
  loop = true,
  autoplay = true,
  fallback,
}: LottieIconProps) {
  const [animationData, setAnimationData] = useState<object | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch(src)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load animation");
        return res.json();
      })
      .then((data) => {
        if (!cancelled) setAnimationData(data);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => { cancelled = true; };
  }, [src]);

  if (error) return <>{fallback ?? null}</>;
  if (!animationData) {
    return (
      <div
        className={`${className} rounded-2xl skeleton-shimmer`}
        aria-hidden="true"
      />
    );
  }

  return (
    <Lottie
      animationData={animationData}
      loop={loop}
      autoplay={autoplay}
      className={className}
    />
  );
}
