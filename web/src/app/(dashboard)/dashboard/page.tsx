"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { apiGet } from "@/lib/api";
import type { Agent, ModelInfo, CreditTransaction } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
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

interface DailyUsage {
  date: string;
  credits: number;
}

interface TodayUsage {
  used_today: number;
  daily_limit: number | null;
}

function DashboardSkeleton() {
  return (
    <div>
      <Skeleton className="mb-1 h-8 w-64" />
      <Skeleton className="mb-8 h-5 w-48" />
      <div className="mb-8 grid gap-6 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
      <Skeleton className="mb-4 h-64 w-full" />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    </div>
  );
}

function UsageChart({ data }: { data: DailyUsage[] }) {
  const maxCredits = Math.max(...data.map((d) => d.credits), 1);

  return (
    <div className="flex h-40 items-end gap-2">
      {data.map((day) => {
        const height = Math.max((day.credits / maxCredits) * 100, 2);
        const label = new Date(day.date + "T00:00:00").toLocaleDateString(undefined, {
          weekday: "short",
        });
        return (
          <div key={day.date} className="flex flex-1 flex-col items-center gap-1">
            <span className="text-[10px] text-muted-foreground">
              {day.credits > 0 ? day.credits : ""}
            </span>
            <div
              className="w-full rounded-t-md bg-primary/80 transition-all hover:bg-primary"
              style={{ height: `${height}%` }}
              title={`${day.date}: ${day.credits} credits`}
            />
            <span className="text-[10px] text-muted-foreground">{label}</span>
          </div>
        );
      })}
    </div>
  );
}

function RecentActivity({ transactions }: { transactions: CreditTransaction[] }) {
  if (transactions.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-muted-foreground">
        No recent activity
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {transactions.map((tx) => (
        <div key={tx.id} className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div
              className={`h-2 w-2 rounded-full ${
                tx.amount > 0 ? "bg-green-400" : "bg-red-400"
              }`}
            />
            <span className="text-muted-foreground capitalize">
              {tx.reason.replaceAll("_", " ")}
            </span>
            {tx.model_name && (
              <span className="rounded bg-muted px-1.5 py-0.5 text-xs">
                {tx.model_name}
              </span>
            )}
          </div>
          <span className={tx.amount > 0 ? "text-green-400" : "text-red-400"}>
            {tx.amount > 0 ? "+" : ""}
            {tx.amount}
          </span>
        </div>
      ))}
    </div>
  );
}

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
    Promise.allSettled([
      apiGet<Agent[]>("/agents"),
      apiGet<ModelInfo[]>("/models"),
      apiGet<TodayUsage>("/billing/credits/today"),
      apiGet<DailyUsage[]>("/billing/credits/usage-chart"),
      apiGet<CreditTransaction[]>("/billing/credits/transactions?limit=5"),
    ])
      .then(([a, m, today, chart, tx]) => {
        if (a.status === "fulfilled") setAgents(a.value);
        if (m.status === "fulfilled") setModelCount(m.value.length);
        if (today.status === "fulfilled") setTodayUsage(today.value);
        if (chart.status === "fulfilled") setChartData(chart.value);
        if (tx.status === "fulfilled") setRecentTx(tx.value);
        // Only show error if all failed
        const allFailed = [a, m, today, chart, tx].every((r) => r.status === "rejected");
        if (allFailed) setError("Failed to load data");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (!user) return null;

  if (loading) return <DashboardSkeleton />;

  if (error) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3" role="alert">
        <AlertCircle className="h-8 w-8 text-destructive" />
        <p className="text-sm text-muted-foreground">{error}</p>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  const runningAgents = agents.filter((a) => a.status === "running").length;

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">
        Welcome back, {user.name}
      </h1>
      <p className="mb-8 text-muted-foreground">
        Here&apos;s an overview of your account.
      </p>

      {/* Stat cards */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link href="/billing">
          <Card className="cursor-pointer transition-colors hover:border-primary">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Coins className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Credit Balance</p>
                <p className="text-2xl font-bold">{user.credit_balance}</p>
              </div>
            </div>
          </Card>
        </Link>

        <Card>
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-yellow-500/10 text-yellow-400">
              <Zap className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Used Today</p>
              <div className="flex items-baseline gap-1">
                <p className="text-2xl font-bold">{todayUsage.used_today}</p>
                {todayUsage.daily_limit && (
                  <span className="text-sm text-muted-foreground">
                    / {todayUsage.daily_limit}
                  </span>
                )}
              </div>
            </div>
          </div>
          {todayUsage.daily_limit && (
            <div className="mt-2">
              <div className="h-1.5 w-full rounded-full bg-muted">
                <div
                  className={`h-1.5 rounded-full transition-all ${
                    todayUsage.used_today >= todayUsage.daily_limit
                      ? "bg-red-500"
                      : todayUsage.used_today >= todayUsage.daily_limit * 0.8
                        ? "bg-yellow-500"
                        : "bg-primary"
                  }`}
                  style={{
                    width: `${Math.min(
                      (todayUsage.used_today / todayUsage.daily_limit) * 100,
                      100
                    )}%`,
                  }}
                />
              </div>
            </div>
          )}
        </Card>

        <Link href="/agents">
          <Card className="cursor-pointer transition-colors hover:border-primary">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10 text-green-400">
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Agents</p>
                <div className="flex items-baseline gap-1">
                  <p className="text-2xl font-bold">{runningAgents}</p>
                  <span className="text-sm text-muted-foreground">
                    / {agents.length} running
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </Link>

        <Link href="/models">
          <Card className="cursor-pointer transition-colors hover:border-primary">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400">
                <Cpu className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Available Models</p>
                <p className="text-2xl font-bold">{modelCount}</p>
              </div>
            </div>
          </Card>
        </Link>
      </div>

      {/* Chart + Recent Activity */}
      <div className="mb-8 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Usage (Last 7 Days)</h2>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </div>
          <UsageChart data={chartData} />
        </Card>

        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent Activity</h2>
            <Link href="/billing" className="text-xs text-primary hover:underline">
              View all
            </Link>
          </div>
          <RecentActivity transactions={recentTx} />
        </Card>
      </div>

      {/* Quick actions */}
      <h2 className="mb-4 text-lg font-semibold">Quick Actions</h2>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Link href="/agents">
          <Card className="flex cursor-pointer items-center gap-3 transition-colors hover:border-primary">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-green-500/10 text-green-400">
              <Plus className="h-5 w-5" />
            </div>
            <div>
              <p className="font-medium">Create Agent</p>
              <p className="text-xs text-muted-foreground">
                Build a new AI assistant
              </p>
            </div>
            <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
          </Card>
        </Link>

        <Link href="/models">
          <Card className="flex cursor-pointer items-center gap-3 transition-colors hover:border-primary">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <p className="font-medium">Browse Models</p>
              <p className="text-xs text-muted-foreground">
                View available AI models
              </p>
            </div>
            <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
          </Card>
        </Link>

        <Link href="/billing">
          <Card className="flex cursor-pointer items-center gap-3 transition-colors hover:border-primary">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-yellow-500/10 text-yellow-400">
              <CreditCard className="h-5 w-5" />
            </div>
            <div>
              <p className="font-medium">Billing & Plans</p>
              <p className="text-xs text-muted-foreground">
                Manage credits & subscription
              </p>
            </div>
            <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
          </Card>
        </Link>

        <Link href="/settings">
          <Card className="flex cursor-pointer items-center gap-3 transition-colors hover:border-primary">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-purple-500/10 text-purple-400">
              <Settings className="h-5 w-5" />
            </div>
            <div>
              <p className="font-medium">Settings</p>
              <p className="text-xs text-muted-foreground">
                Budget limits & profile
              </p>
            </div>
            <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
          </Card>
        </Link>
      </div>
    </div>
  );
}
