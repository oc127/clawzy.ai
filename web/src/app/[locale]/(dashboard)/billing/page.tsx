"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { getCredits, getPlans, createCheckoutSession, createPortalSession, type CreditsInfo } from "@/lib/api";

interface Plan {
  id: string;
  name: string;
  price_monthly: number;
  credits_included: number;
  max_agents: number;
}

const PLAN_PRICE_IDS: Record<string, string> = {
  starter: process.env.NEXT_PUBLIC_STRIPE_PRICE_STARTER || "price_starter_monthly",
  pro: process.env.NEXT_PUBLIC_STRIPE_PRICE_PRO || "price_pro_monthly",
  business: process.env.NEXT_PUBLIC_STRIPE_PRICE_BUSINESS || "price_business_monthly",
};

export default function BillingPage() {
  const t = useTranslations("billing");
  const [credits, setCredits] = useState<CreditsInfo | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [upgrading, setUpgrading] = useState<string | null>(null);

  const planNames: Record<string, string> = {
    free: t("planFree"),
    starter: t("planStarter"),
    pro: t("planPro"),
    business: t("planBusiness"),
  };

  useEffect(() => {
    getCredits().then(setCredits);
    getPlans().then(setPlans);
  }, []);

  async function handleUpgrade(planId: string) {
    const priceId = PLAN_PRICE_IDS[planId];
    if (!priceId) return;

    setUpgrading(planId);
    try {
      const { url } = await createCheckoutSession(priceId);
      window.location.href = url;
    } catch (e: any) {
      alert(e.message || t("checkoutFailed"));
      setUpgrading(null);
    }
  }

  return (
    <div className="p-10 max-w-3xl">
      <h1 className="text-xl font-semibold text-foreground tracking-tight mb-8">{t("title")}</h1>

      {credits && (
        <div className="border border-border rounded-lg p-6 mb-8">
          <div className="flex items-baseline justify-between">
            <div>
              <p className="text-xs text-muted uppercase tracking-wide">{t("currentEnergy")}</p>
              <p className="text-3xl font-semibold text-foreground mt-1">{credits.balance}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-muted uppercase tracking-wide">{t("usedThisMonth")}</p>
              <p className="text-xl font-medium text-muted mt-1">{credits.used_this_period}</p>
            </div>
          </div>
          <div className="mt-5 pt-4 border-t border-border flex items-center justify-between">
            <p className="text-sm text-muted">
              {t("currentPlan")} <span className="text-foreground font-medium">{planNames[credits.plan] || credits.plan}</span>
            </p>
            {credits.plan !== "free" && (
              <button
                onClick={async () => {
                  try {
                    const { url } = await createPortalSession();
                    window.location.href = url;
                  } catch {
                    alert(t("portalFailed"));
                  }
                }}
                className="text-xs text-accent hover:text-accent-hover transition-colors"
              >
                {t("manageSubscription")}
              </button>
            )}
          </div>
        </div>
      )}

      <h2 className="text-sm font-medium text-foreground mb-4">{t("choosePlan")}</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {plans.map((plan) => {
          const isCurrent = credits?.plan === plan.id;
          const isUpgrading = upgrading === plan.id;

          return (
            <div
              key={plan.id}
              className={`border rounded-lg p-5 ${
                isCurrent ? "border-accent/40 bg-accent/5" : "border-border"
              }`}
            >
              <h3 className="text-sm font-medium text-foreground">
                {planNames[plan.id] || plan.name}
              </h3>
              <p className="text-2xl font-semibold text-foreground mt-2">
                ${plan.price_monthly}
                <span className="text-xs text-muted font-normal ml-1">{t("perMonth")}</span>
              </p>
              <ul className="mt-3 space-y-1 text-xs text-muted">
                <li>{t("creditsPerMonth", { count: plan.credits_included.toLocaleString() })}</li>
                <li>{t("maxLobsters", { count: plan.max_agents })}</li>
              </ul>
              {isCurrent ? (
                <div className="mt-4 py-1.5 text-center text-xs text-accent border border-accent/30 rounded-md">
                  {t("currentPlanBadge")}
                </div>
              ) : plan.price_monthly === 0 ? (
                <div className="mt-4 py-1.5 text-center text-xs text-muted border border-border rounded-md">
                  {t("freePlan")}
                </div>
              ) : (
                <button
                  onClick={() => handleUpgrade(plan.id)}
                  disabled={isUpgrading}
                  className="mt-4 w-full py-1.5 bg-accent hover:bg-accent-hover disabled:opacity-40 text-white text-xs font-medium rounded-md transition-colors"
                >
                  {isUpgrading ? t("redirecting") : t("upgrade")}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
