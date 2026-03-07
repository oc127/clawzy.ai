export default function Skeleton({ className = "h-4 w-full" }: { className?: string }) {
  return <div className={`bg-surface animate-pulse rounded ${className}`} />;
}
