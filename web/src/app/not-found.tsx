import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
      <div className="text-center px-8">
        <h1 className="text-6xl font-bold tracking-tight text-accent">404</h1>
        <p className="text-lg text-muted mt-4 mb-8">
          Page not found
        </p>
        <Link
          href="/"
          className="inline-block px-6 py-2.5 bg-accent hover:bg-accent-hover text-white font-medium rounded-lg transition-colors text-sm"
        >
          Back to Home
        </Link>
      </div>
    </div>
  );
}
