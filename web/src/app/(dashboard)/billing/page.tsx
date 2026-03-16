"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import type { Credits, CreditTransaction, Plan } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { Coins, TrendingUp, Crown, AlertCircle, RefreshCw, ChevronLeft, ChevronRight } from "lucide-react";

const PAGE_SIZE = 10;

function BillingSkeleton() {
  return (
    <div>
      <Skeleton className="mb-1 h-8 w-24" />
      <Skeleton className="mb-8 h-5 w-56" />
      <div className="mb-8 grid gap-6 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
      <Skeleton className="mb-4 h-6 w-20" />
      <div className="mb-8 grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-48 w-full" />
        ))}
      </div>
      <Skeleton className="mb-4 h-6 w-40" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

export default function BillingPage() {
  const [credits, setCredits] = useState<Credits | null>(null);
  const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState("");
  const [subscribing, setSubscribing] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const fetchData = () => {
    setLoading(true);
    setFetchError("");
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
      .catch((err) => setFetchError(err.message || "Failed to load billing info"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubscribe = async (planId: string) => {
    setSubscribing(planId);
    try {
      await apiPost("/billing/subscribe", { plan: planId });
      await fetchData();
      toast.success("Subscription updated");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to switch plan");
    } finally {
      setSubscribing(null);
    }
  };

  const totalPages = Math.max(1, Math.ceil(transactions.length / PAGE_SIZE));
  const paginatedTx = transactions.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  if (loading) return <BillingSkeleton />;

  if (fetchError) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3" role="alert">
        <AlertCircle className="h-8 w-8 text-destructive" />
        <p className="text-sm text-muted-foreground">{fetchError}</p>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">Billing</h1>
      <p className="mb-8 text-muted-foreground">
        Manage your credits and subscription.
      </p>

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
                        loading={subscribing === plan.id}
                        disabled={subscribing !== null}
                        onClick={() => handleSubscribe(plan.id)}
                      >
                        {plan.price_monthly === 0 ? "Downgrade" : "Upgrade"}
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
          <>
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
                  {paginatedTx.map((tx) => (
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
            {totalPages > 1 && (
              <div className="mt-4 flex items-center justify-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                  aria-label="Previous page"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-muted-foreground">
                  {page + 1} / {totalPages}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
                  aria-label="Next page"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
