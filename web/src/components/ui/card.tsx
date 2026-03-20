import { cn } from "@/lib/cn";
import { type HTMLAttributes } from "react";

export function Card({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-[#ebebeb] bg-white p-6 text-foreground",
        "shadow-[0_2px_8px_rgba(0,0,0,0.08)]",
        "transition-all duration-200",
        className,
      )}
      {...props}
    />
  );
}
