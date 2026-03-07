interface AgentCardProps {
  name: string;
  modelName: string;
  status: string;
  brainLabel: string;
  statusLabel: string;
  onClick?: () => void;
}

const STATUS_DOT: Record<string, string> = {
  running: "bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.4)]",
  stopped: "bg-neutral-500",
  creating: "bg-yellow-500 animate-pulse",
  error: "bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.4)]",
};

export default function AgentCard({
  name,
  status,
  brainLabel,
  statusLabel,
  onClick,
}: AgentCardProps) {
  const dot = STATUS_DOT[status] || STATUS_DOT.stopped;

  return (
    <div
      onClick={onClick}
      className={`group border border-border rounded-xl px-5 py-4 transition-all duration-200 ${
        onClick
          ? "cursor-pointer hover:bg-surface/60 hover:border-accent/20 hover:shadow-[0_2px_12px_rgba(0,0,0,0.15)]"
          : ""
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${dot} transition-shadow`} />
          <div>
            <h3 className="text-sm font-medium text-foreground">{name}</h3>
            <p className="text-xs text-muted mt-0.5">{brainLabel}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted">{statusLabel}</span>
          {onClick && (
            <svg
              className="w-3.5 h-3.5 text-muted/40 group-hover:text-accent/60 transition-colors"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          )}
        </div>
      </div>
    </div>
  );
}
