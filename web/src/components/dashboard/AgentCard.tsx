interface AgentCardProps {
  name: string;
  modelName: string;
  status: string;
  brainLabel: string;
  statusLabel: string;
  onClick?: () => void;
}

const STATUS_DOT: Record<string, string> = {
  running: "bg-green-500",
  stopped: "bg-neutral-500",
  creating: "bg-yellow-500 animate-pulse",
  error: "bg-red-500",
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
      className={`border border-border rounded-lg px-5 py-4 ${
        onClick ? "cursor-pointer hover:bg-surface" : ""
      } transition-colors`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${dot}`} />
          <div>
            <h3 className="text-sm font-medium text-foreground">{name}</h3>
            <p className="text-xs text-muted mt-0.5">{brainLabel}</p>
          </div>
        </div>
        <span className="text-xs text-muted">{statusLabel}</span>
      </div>
    </div>
  );
}
