"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import LanguageSwitcher from "@/components/LanguageSwitcher";

export default function LandingPage() {
  const t = useTranslations("landing");

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5 max-w-5xl mx-auto">
        <span className="text-base font-semibold tracking-tight">Clawzy</span>
        <div className="flex items-center gap-5">
          <LanguageSwitcher />
          <Link
            href="/login"
            className="text-sm text-muted hover:text-foreground transition-colors"
          >
            {t("login")}
          </Link>
          <Link
            href="/register"
            className="px-4 py-1.5 text-sm bg-accent hover:bg-accent-hover text-white rounded-md font-medium transition-colors"
          >
            {t("freeRegister")}
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <main className="max-w-3xl mx-auto px-8 pt-28 pb-36 text-center">
        <h1 className="text-4xl md:text-5xl font-bold leading-tight tracking-tight mb-5">
          {t("heroTitle")}
          <br />
          <span className="text-accent">{t("heroHighlight")}</span>
        </h1>
        <p className="text-lg text-muted max-w-xl mx-auto mb-10 leading-relaxed">
          {t("heroDesc")}
        </p>
        <Link
          href="/register"
          className="inline-block px-7 py-3 bg-accent hover:bg-accent-hover text-white font-medium rounded-lg transition-colors"
        >
          {t("cta")}
        </Link>
        <p className="text-xs text-muted mt-4">{t("ctaSubtext")}</p>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-28 text-left">
          <FeatureCard title={t("feature1Title")} desc={t("feature1Desc")} />
          <FeatureCard title={t("feature2Title")} desc={t("feature2Desc")} />
          <FeatureCard title={t("feature3Title")} desc={t("feature3Desc")} />
        </div>

        {/* Pricing */}
        <div className="mt-28">
          <h2 className="text-2xl font-semibold tracking-tight mb-8">{t("pricingTitle")}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <PriceCard
              name={t("planFree")}
              price={t("priceFree")}
              features={[t("featureFreeCredits"), t("featureFree1Lobster")]}
            />
            <PriceCard
              name={t("planStarter")}
              price={t("priceStarter")}
              features={[t("featureStarterCredits"), t("featureStarter1Lobster"), t("featureStarterAllBrains")]}
              highlight
            />
            <PriceCard
              name={t("planPro")}
              price={t("pricePro")}
              features={[t("featureProCredits"), t("featurePro3Lobsters"), t("featureProSupport")]}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-8 text-center text-xs text-muted">
        Clawzy.ai
      </footer>
    </div>
  );
}

function FeatureCard({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="border border-border rounded-lg p-5 hover:border-muted/30 transition-colors">
      <h3 className="text-sm font-medium text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted leading-relaxed">{desc}</p>
    </div>
  );
}

function PriceCard({
  name,
  price,
  features,
  highlight,
}: {
  name: string;
  price: string;
  features: string[];
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-lg p-5 ${
        highlight
          ? "border border-accent/40 bg-accent/5"
          : "border border-border"
      }`}
    >
      <h3 className="text-sm font-medium text-foreground">{name}</h3>
      <p className="text-2xl font-semibold text-foreground mt-2">{price}</p>
      <ul className="mt-4 space-y-1.5">
        {features.map((f) => (
          <li key={f} className="text-sm text-muted">{f}</li>
        ))}
      </ul>
    </div>
  );
}
