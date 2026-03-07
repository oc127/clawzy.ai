"use client";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
      <div className="text-center px-8">
        <h1 className="text-6xl font-bold tracking-tight text-accent">500</h1>
        <p className="text-lg text-muted mt-4 mb-8">
          Something went wrong
        </p>
        <button
          onClick={() => reset()}
          className="inline-block px-6 py-2.5 bg-accent hover:bg-accent-hover text-white font-medium rounded-lg transition-colors text-sm"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
