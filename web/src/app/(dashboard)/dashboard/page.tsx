"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { apiGet } from "@/lib/api";
import type { Agent, ModelInfo, CreditTransaction } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
  Coins,
  Bot,
  Cpu,
  Plus,
  ArrowRight,
  CreditCard,
  Settings,
  AlertCircle,
  RefreshCw,
  TrendingUp,
  Zap,
} from "lucide-react";

interface DailyUsage { date: string; credits: number; }
interface TodayUsage { used_today: number; daily_limit: number | null; }

function Skeleton({ className }: { className?: string }) {
  return <div className={`skeleton-shimmer rounded-2xl ${className ?? ""}`} />;
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="mb-1 h-8 w-56" />
        <Skeleton className="h-5 w-40" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-28" />)}
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Skeleton className="h-64 lg:col-span-2" />
        <Skeleton className="h-64" />
      </div>
    </div>
  );
}

function StatCard({
  href,
  label,
  value,
  sub,
  icon,
  gradient,
  progress,
}: {
  href?: string;
  label: string;
  value: React.ReactNode;
  sub?: string;
  icon: React.ReactNode;
  gradient: string;
  progress?: { used: number; total: number };
}) {
  const inner = (
    <div className="flex items-start gap-4">
      <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl shadow-md ${gradient}`}>
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm text-[#717171] font-medium">{label}</p>
        <div className="flex items-baseline gap-1.5">
          <p className="text-2xl font-extrabold text-[#222222]">{value}</p>
          {sub && <span className="text-sm text-[#717171]">{sub}</span>}
        </div>
        {progress && (
          <div className="mt-2 h-1.5 w-full rounded-full bg-[#ebebeb]">
            <div
              className={`h-1.5 rounded-full transition-all ${
                progress.used >= progress.total
                  ? "bg-red-500"
                  : progress.used >= progress.total * 0.8
                  ? "bg-yellow-500"
                  : "bg-[#ff385c]"
              }`}
              style={{ width: `${Math.min((progress.used / progress.total) * 100, 100)}%` }}
            />
          </div>
        )}
      </div>
    </div>
  );

  const cardClass =
    "rounded-2xl border border-[#ebebeb] bg-white p-5 shadow-[0_2px_8px_rgba(0,0,0,0.06)] transition-all duration-200";

  if (href) {
    return (
      <Link href={href} className={`${cardClass} block hover:shadow-[0_6px_20px_rgba(0,0,0,0.10)] hover:-translate-y-0.5`}>
        {inner}
      </Link>
    );
  }
  return <div className={cardClass}>{inner}</div>;
}

function UsageChart({ data }: { data: DailyUsage[] }) {
  const max = Math.max(...data.map((d) => d.credits), 1);
  return (
    <div className="flex h-44 items-end gap-2">
      {data.map((day) => {
        const height = Math.max((day.credits / max) * 100, 3);
        const label = new Date(day.date + "T00:00:00").toLocaleDateString(undefined, { weekday: "short" });
        return (
          <div key={day.date} className="flex flex-1 flex-col items-center gap-1">
            {day.credits > 0 && (
              <span className="text-[10px] font-medium text-[#717171]">{day.credits}</span>
            )}
            <div
              className="w-full rounded-t-lg bg-gradient-to-t from-[#ff385c] to-[#ff8c69] transition-all hover:from-[#e31c5f] hover:to-[#ff6b35]"
              style={{ height: `${height}%` }}
              title={`${day.date}: ${day.credits} credits`}
            />
            <span className="text-[10px] text-[#717171]">{label}</span>
          </div>
        );
      })}
    </div>
  );
}

function RecentActivity({ transactions }: { transactions: CreditTransaction[] }) {
  if (transactions.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-[#b0b0b0]">No recent activity</p>
    );
  }
  return (
    <div className="space-y-3">
      {transactions.map((tx) => (
        <div key={tx.id} className="flex items-center justify-between text-sm py-1">
          <div className="flex items-center gap-2.5">
            <div className={`h-2 w-2 rounded-full ${tx.amount > 0 ? "bg-emerald-500" : "bg-[#ff385c]"}`} />
            <span className="text-[#717171] capitalize">{tx.reason.replace("_", " ")}</span>
            {tx.model_name && (
              <span className="rounded-lg bg-[#f7f7f7] border border-[#ebebeb] px-2 py-0.5 text-xs text-[#717171]">
                {tx.model_name}
              </span>
            )}
          </div>
          <span className={`font-semibold ${tx.amount > 0 ? "text-emerald-600" : "text-[#ff385c]"}`}>
            {tx.amount > 0 ? "+" : ""}{tx.amount}
          </span>
        </div>
      ))}
    </div>
  );
}

const QUICK_ACTIONS = [
  { href: "/agents", label: "Create Agent", desc: "Build a new AI assistant", icon: <Plus className="h-5 w-5 text-white" />, gradient: "icon-gradient-red" },
  { href: "/models", label: "Browse Models", desc: "View available AI models", icon: <Cpu className="h-5 w-5 text-white" />, gradient: "icon-gradient-blue" },
  { href: "/billing", label: "Billing & Plans", desc: "Manage credits & subscription", icon: <CreditCard className="h-5 w-5 text-white" />, gradient: "icon-gradient-green" },
  { href: "/settings", label: "Settings", desc: "Budget limits & profile", icon: <Settings className="h-5 w-5 text-white" />, gradient: "icon-gradient-orange" },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [modelCount, setModelCount] = useState(0);
  const [todayUsage, setTodayUsage] = useState<TodayUsage>({ used_today: 0, daily_limit: null });
  const [chartData, setChartData] = useState<DailyUsage[]>([]);
  const [recentTx, setRecentTx] = useState<CreditTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = () => {
    setLoading(true);
    setError("");
    Promise.all([
      apiGet<Agent[]>("/agents"),
      apiGet<ModelInfo[]>("/models"),
      apiGet<TodayUsage>("/billing/credits/today"),
      apiGet<DailyUsage[]>("/billing/credits/usage-chart"),
      apiGet<CreditTransaction[]>("/billing/credits/transactions?limit=5"),
    ])
      .then(([a, m, today, chart, tx]) => {
        setAgents(a);
        setModelCount(m.length);
        setTodayUsage(today);
        setChartData(chart);
        setRecentTx(tx);
      })
      .catch((err) => setError(err.message || "Failed to load data"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  if (!user) return null;
  if (loading) return <DashboardSkeleton />;

  if (error) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 rounded-2xl border border-[#ebebeb] bg-white" role="alert">
        <AlertCircle className="h-8 w-8 text-[#ff385c]" />
        <p className="text-sm text-[#717171]">{error}</p>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchData}
          className="border-[#dddddd] text-[#222222] hover:bg-[#f7f7f7]"
        >
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  const runningAgents = agents.filter((a) => a.status === "running").length;
  const firstName = user.name?.split(" ")[0] ?? user.name ?? "there";

  return (
    <div className="space-y-7">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-[#222222]">
          Good morning, {firstName} 👋
        </h1>
        <p className="mt-1 text-[#717171]">Here&apos;s your account overview.</p>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          href="/billing"
          label="Credit Balance"
          value={user.credit_balance}
          icon={<Coins className="h-5 w-5 text-white" />}
          gradient="icon-gradient-red"
        />
        <StatCard
          label="Used Today"
          value={todayUsage.used_today}
          sub={todayUsage.daily_limit ? `/ ${todayUsage.daily_limit}` : undefined}
          icon={<Zap className="h-5 w-5 text-white" />}
          gradient="icon-gradient-orange"
          progress={todayUsage.daily_limit ? { used: todayUsage.used_today, total: todayUsage.daily_limit } : undefined}
        />
        <StatCard
          href="/agents"
          label="Active Agents"
          value={runningAgents}
          sub={`/ ${agents.length} total`}
          icon={<Bot className="h-5 w-5 text-white" />}
          gradient="icon-gradient-green"
        />
        <StatCard
          href="/models"
          label="Available Models"
          value={modelCount}
          icon={<Cpu className="h-5 w-5 text-white" />}
          gradient="icon-gradient-blue"
        />
      </div>

      {/* Chart + Activity */}
      <div className="grid gap-5 lg:grid-cols-3">
        <div className="rounded-2xl border border-[#ebebeb] bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.06)] lg:col-span-2">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="font-bold text-[#222222]">Credit Usage — Last 7 Days</h2>
            <TrendingUp className="h-4 w-4 text-[#b0b0b0]" />
          </div>
          <UsageChart data={chartData} />
        </div>

        <div className="rounded-2xl border border-[#ebebeb] bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-bold text-[#222222]">Recent Activity</h2>
            <Link href="/billing" className="text-xs font-semibold text-[#ff385c] hover:underline">
              View all
            </Link>
          </div>
          <RecentActivity transactions={recentTx} />
        </div>
      </div>

      {/* Quick actions */}
      <div>
        <h2 className="mb-4 font-bold text-[#222222]">Quick Actions</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {QUICK_ACTIONS.map((action) => (
            <Link key={action.href} href={action.href}>
              <div className="flex items-center gap-3 rounded-2xl border border-[#ebebeb] bg-white p-4 shadow-[0_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.10)] hover:-translate-y-0.5 transition-all duration-200 cursor-pointer">
                <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl shadow-sm ${action.gradient}`}>
                  {action.icon}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-sm text-[#222222]">{action.label}</p>
                  <p className="text-xs text-[#717171] truncate">{action.desc}</p>
                </div>
                <ArrowRight className="h-4 w-4 text-[#b0b0b0] shrink-0" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
