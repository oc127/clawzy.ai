import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement>
>(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "flex h-11 w-full rounded-xl border border-[#b0b0b0] bg-white px-4 py-2.5 text-sm text-foreground",
        "placeholder:text-[#b0b0b0]",
        "transition-all duration-150",
        "focus-visible:outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20",
        "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-[#f7f7f7]",
        className,
      )}
      ref={ref}
      {...props}
    />
  );
});
Input.displayName = "Input";

export { Input };
