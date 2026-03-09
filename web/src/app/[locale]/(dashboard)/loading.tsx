export default function DashboardLoading() {
  return (
    <div className="p-10 max-w-4xl animate-pulse">
      <div className="h-7 w-48 bg-surface-hover rounded mb-8" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="border border-border rounded-lg p-5">
            <div className="h-5 w-32 bg-surface-hover rounded mb-3" />
            <div className="h-4 w-full bg-surface-hover rounded mb-2" />
            <div className="h-4 w-2/3 bg-surface-hover rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
