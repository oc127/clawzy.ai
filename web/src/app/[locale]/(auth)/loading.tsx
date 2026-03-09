export default function AuthLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-sm space-y-6 animate-pulse">
        <div className="text-center space-y-3">
          <div className="h-5 w-16 bg-surface-hover rounded mx-auto" />
          <div className="h-7 w-40 bg-surface-hover rounded mx-auto" />
        </div>
        <div className="space-y-3">
          <div className="h-11 w-full bg-surface-hover rounded-lg" />
          <div className="h-11 w-full bg-surface-hover rounded-lg" />
          <div className="h-11 w-full bg-surface-hover rounded-lg" />
        </div>
      </div>
    </div>
  );
}
