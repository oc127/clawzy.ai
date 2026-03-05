interface CreditsBadgeProps {
  balance: number;
  label?: string;
}

export default function CreditsBadge({ balance, label = "Energy" }: CreditsBadgeProps) {
  return (
    <span className="text-xs text-muted">
      {balance} {label}
    </span>
  );
}
