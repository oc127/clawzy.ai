"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { apiGet } from "@/lib/api";
import type { Agent, ModelInfo } from "@/lib/types";
import { Card } from "@/components/ui/card";
import {
  Coins,
  Bot,
  Cpu,
  Plus,
  ArrowRight,
  CreditCard,
  Settings,
} from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();
  const [agentCount, setAgentCount] = useState(0);
  const [modelCount, setModelCount] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<Agent[]>("/agents")
      .then((a) => setAgentCount(a.length))
      .catch((err) => setError(err.message || "Failed to load data"));
    apiGet<ModelInfo[]>("/models")
      .then((m) => setModelCount(m.length))
      .catch((err) => setError(err.message || "Failed to load data"));
  }, []);

  if (!user) return null;

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">
        Welcome back, {user.name}
      </h1>
      <p className="mb-8 text-muted-foreground">
        Here&apos;s an overview of your account.
      </p>

      {error && (
        <div className="mb-6 rounded-md bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Stat cards with links */}
      <div className="mb-8 grid gap-6 md:grid-cols-3">
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

        <Link href="/agents">
          <Card className="cursor-pointer transition-colors hover:border-primary">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Active Agents</p>
                <p className="text-2xl font-bold">{agentCount}</p>
              </div>
            </div>
          </Card>
        </Link>

        <Link href="/models">
          <Card className="cursor-pointer transition-colors hover:border-primary">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
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
                Update your profile
              </p>
            </div>
            <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground" />
          </Card>
        </Link>
      </div>
    </div>
  );
}
