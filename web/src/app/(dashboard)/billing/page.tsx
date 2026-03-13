"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import type { Credits, CreditTransaction, Plan } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Coins, TrendingUp, Crown } from "lucide-react";

export default function BillingPage() {
  const [credits, setCredits] = useState<Credits | null>(null);
  const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [subscribing, setSubscribing] = useState<string | null>(null);

  const fetchData = () => {
    return Promise.all([
      apiGet<Credits>("/billing/credits"),
      apiGet<CreditTransaction[]>("/billing/credits/transactions"),
      apiGet<Plan[]>("/billing/plans"),
    ])
      .then(([c, t, p]) => {
        setCredits(c);
        setTransactions(t);
        setPlans(p);
      })
      .catch((err) => setError(err.message || "Failed to load billing info"));
  };

  useEffect(() => {
    fetchData().finally(() => setLoading(false));
  }, []);

  const handleSubscribe = async (planId: string) => {
    setSubscribing(planId);
    setError("");
    try {
      await apiPost("/billing/subscribe", { plan: planId });
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to switch plan");
    } finally {
      setSubscribing(null);
    }
  };

  if (loading) {
    return <p className="text-muted-foreground">Loading billing info...</p>;
  }

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">Billing</h1>
      <p className="mb-8 text-muted-foreground">
        Manage your credits and subscription.
      </p>

      {error && (
        <div className="mb-6 rounded-md bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Credits overview */}
      {credits && (
        <div className="mb-8 grid gap-6 md:grid-cols-3">
          <Card>
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Coins className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Credit Balance</p>
                <p className="text-2xl font-bold">{credits.balance}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <TrendingUp className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Used This Period</p>
                <p className="text-2xl font-bold">{credits.used_this_period}</p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Crown className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Current Plan</p>
                <p className="text-2xl font-bold capitalize">{credits.plan}</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Plans */}
      {plans.length > 0 && (
        <div className="mb-8">
          <h2 className="mb-4 text-lg font-semibold">Plans</h2>
          <div className="grid gap-4 md:grid-cols-4">
            {plans.map((plan) => {
              const isCurrent = credits?.plan === plan.id;
              return (
                <Card
                  key={plan.id}
                  className={isCurrent ? "border-primary" : ""}
                >
                  <h3 className="font-semibold">{plan.name}</h3>
                  <p className="mt-1 text-2xl font-bold">
                    ${plan.price_monthly}
                    <span className="text-sm font-normal text-muted-foreground">
                      /mo
                    </span>
                  </p>
                  <div className="mt-3 space-y-1 text-sm text-muted-foreground">
                    <p>{plan.credits_included.toLocaleString()} credits</p>
                    <p>
                      {plan.max_agents} agent{plan.max_agents !== 1 ? "s" : ""}
                    </p>
                  </div>
                  <div className="mt-4">
                    {isCurrent ? (
                      <Button variant="outline" size="sm" disabled className="w-full">
                        Current Plan
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        className="w-full"
                        disabled={subscribing !== null}
                        onClick={() => handleSubscribe(plan.id)}
                      >
                        {subscribing === plan.id
                          ? "Switching..."
                          : plan.price_monthly === 0
                            ? "Downgrade"
                            : "Upgrade"}
                      </Button>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Transaction history */}
      <div>
        <h2 className="mb-4 text-lg font-semibold">Transaction History</h2>
        {transactions.length === 0 ? (
          <p className="text-sm text-muted-foreground">No transactions yet.</p>
        ) : (
          <Card className="overflow-hidden p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Reason</th>
                  <th className="px-4 py-3">Model</th>
                  <th className="px-4 py-3 text-right">Amount</th>
                  <th className="px-4 py-3 text-right">Balance</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr
                    key={tx.id}
                    className="border-b border-border last:border-0"
                  >
                    <td className="px-4 py-3">
                      {new Date(tx.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">{tx.reason}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {tx.model_name ?? "\u2014"}
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-medium ${
                        tx.amount >= 0 ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {tx.amount >= 0 ? "+" : ""}
                      {tx.amount}
                    </td>
                    <td className="px-4 py-3 text-right">{tx.balance_after}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </div>
    </div>
  );
}
