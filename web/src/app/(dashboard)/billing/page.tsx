"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import type { Credits, CreditTransaction, Plan } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Coins, TrendingUp, Crown, AlertCircle, RefreshCw, ChevronLeft, ChevronRight, Check } from "lucide-react";

const PAGE_SIZE = 10;

function Skeleton({ className }: { className?: string }) {
  return <div className={`skeleton-shimmer rounded-2xl ${className ?? ""}`} />;
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
      .then(([c, t, p]) => { setCredits(c); setTransactions(t); setPlans(p); })
      .catch((err) => setFetchError(err.message || "Failed to load billing info"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

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

  if (loading) {
    return (
      <div className="space-y-6">
        <div><Skeleton className="mb-1 h-7 w-24" /><Skeleton className="h-4 w-48" /></div>
        <div className="grid gap-4 md:grid-cols-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}</div>
        <div className="grid gap-4 md:grid-cols-4">{[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-52" />)}</div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 rounded-2xl border border-[#ebebeb] bg-white" role="alert">
        <AlertCircle className="h-8 w-8 text-[#ff385c]" />
        <p className="text-sm text-[#717171]">{fetchError}</p>
        <Button variant="outline" size="sm" onClick={fetchData} className="border-[#dddddd]">
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold text-[#222222]">Billing</h1>
        <p className="mt-0.5 text-[#717171]">Manage your credits and subscription.</p>
      </div>

      {/* Credits overview */}
      {credits && (
        <div className="grid gap-4 md:grid-cols-3">
          {[
            { icon: <Coins className="h-5 w-5 text-white" />, gradient: "icon-gradient-red", label: "Credit Balance", value: credits.balance },
            { icon: <TrendingUp className="h-5 w-5 text-white" />, gradient: "icon-gradient-blue", label: "Used This Period", value: credits.used_this_period },
            { icon: <Crown className="h-5 w-5 text-white" />, gradient: "icon-gradient-orange", label: "Current Plan", value: <span className="capitalize">{credits.plan}</span> },
          ].map((s) => (
            <div key={s.label} className="flex items-center gap-4 rounded-2xl border border-[#ebebeb] bg-white p-5 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
              <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl shadow-md ${s.gradient}`}>
                {s.icon}
              </div>
              <div>
                <p className="text-sm text-[#717171]">{s.label}</p>
                <p className="text-2xl font-extrabold text-[#222222]">{s.value}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Plans */}
      {plans.length > 0 && (
        <div>
          <h2 className="mb-4 text-lg font-bold text-[#222222]">Plans</h2>
          <div className="grid gap-4 md:grid-cols-4">
            {plans.map((plan) => {
              const isCurrent = credits?.plan === plan.id;
              const isPro = plan.price_monthly > 0;
              return (
                <div
                  key={plan.id}
                  className={`flex flex-col rounded-2xl border p-5 transition-all ${
                    isCurrent
                      ? "border-[#ff385c] bg-[#fff8f8] shadow-[0_4px_16px_rgba(255,56,92,0.15)]"
                      : "border-[#ebebeb] bg-white shadow-[0_2px_8px_rgba(0,0,0,0.06)]"
                  }`}
                >
                  {isCurrent && (
                    <div className="mb-3 inline-flex items-center gap-1 rounded-full bg-[#ff385c] px-2.5 py-0.5 text-xs font-semibold text-white w-fit">
                      <Check className="h-3 w-3" />
                      Current
                    </div>
                  )}
                  <h3 className="font-bold text-[#222222]">{plan.name}</h3>
                  <p className="mt-1 text-3xl font-extrabold text-[#222222]">
                    ${plan.price_monthly}
                    <span className="text-sm font-normal text-[#717171]">/mo</span>
                  </p>
                  <div className="mt-3 flex-1 space-y-1.5 text-sm text-[#717171]">
                    <p className="flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#ff385c] shrink-0" />
                      {plan.credits_included.toLocaleString()} credits
                    </p>
                    <p className="flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#ff385c] shrink-0" />
                      {plan.max_agents} agent{plan.max_agents !== 1 ? "s" : ""}
                    </p>
                  </div>
                  <div className="mt-4">
                    {isCurrent ? (
                      <Button variant="outline" size="sm" disabled className="w-full border-[#dddddd] rounded-xl">
                        Current Plan
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        className={`w-full rounded-xl font-semibold ${
                          isPro
                            ? "bg-[#ff385c] hover:bg-[#e31c5f] text-white shadow-sm"
                            : "bg-[#f7f7f7] text-[#222222] hover:bg-[#ebebeb] border border-[#dddddd]"
                        }`}
                        loading={subscribing === plan.id}
                        disabled={subscribing !== null}
                        onClick={() => handleSubscribe(plan.id)}
                      >
                        {plan.price_monthly === 0 ? "Downgrade" : "Upgrade"}
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Transaction history */}
      <div>
        <h2 className="mb-4 text-lg font-bold text-[#222222]">Transaction History</h2>
        {transactions.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#dddddd] bg-white py-12 text-center">
            <Coins className="mb-2 h-8 w-8 text-[#b0b0b0]" />
            <p className="text-sm text-[#717171]">No transactions yet.</p>
          </div>
        ) : (
          <>
            <div className="rounded-2xl border border-[#ebebeb] bg-white shadow-[0_2px_8px_rgba(0,0,0,0.06)] overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#ebebeb] text-left text-[#717171] bg-[#f7f7f7]">
                    <th className="px-5 py-3 font-semibold">Date</th>
                    <th className="px-5 py-3 font-semibold">Reason</th>
                    <th className="px-5 py-3 font-semibold hidden md:table-cell">Model</th>
                    <th className="px-5 py-3 text-right font-semibold">Amount</th>
                    <th className="px-5 py-3 text-right font-semibold hidden sm:table-cell">Balance</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedTx.map((tx) => (
                    <tr key={tx.id} className="border-b border-[#ebebeb] last:border-0 hover:bg-[#f7f7f7] transition-colors">
                      <td className="px-5 py-3 text-[#717171]">
                        {new Date(tx.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-5 py-3 text-[#222222] capitalize">{tx.reason.replace("_", " ")}</td>
                      <td className="px-5 py-3 text-[#717171] hidden md:table-cell">
                        {tx.model_name ?? "—"}
                      </td>
                      <td className={`px-5 py-3 text-right font-semibold ${tx.amount >= 0 ? "text-emerald-600" : "text-[#ff385c]"}`}>
                        {tx.amount >= 0 ? "+" : ""}{tx.amount}
                      </td>
                      <td className="px-5 py-3 text-right text-[#717171] hidden sm:table-cell">{tx.balance_after}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {totalPages > 1 && (
              <div className="mt-4 flex items-center justify-center gap-3">
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                  aria-label="Previous page"
                  className="rounded-xl border border-[#ebebeb] hover:bg-[#f7f7f7]"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-[#717171] font-medium">{page + 1} / {totalPages}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
                  aria-label="Next page"
                  className="rounded-xl border border-[#ebebeb] hover:bg-[#f7f7f7]"
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
