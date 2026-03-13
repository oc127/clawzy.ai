"use client";

import { useAuth } from "@/context/auth-context";
import { Card } from "@/components/ui/card";
import { Coins, Bot, Cpu } from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">
        Welcome back, {user.name}
      </h1>
      <p className="mb-8 text-muted-foreground">
        Here&apos;s an overview of your account.
      </p>

      <div className="grid gap-6 md:grid-cols-3">
        <Card>
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

        <Card>
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Active Agents</p>
              <p className="text-2xl font-bold">0</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Available Models</p>
              <p className="text-2xl font-bold">5</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
