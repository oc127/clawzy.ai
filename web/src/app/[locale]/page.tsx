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

      {/* Hero — generous vertical space, clear hierarchy */}
      <main className="max-w-3xl mx-auto px-8">
        <section className="pt-32 pb-40 text-center">
          <h1 className="text-4xl md:text-5xl font-bold leading-tight tracking-tight mb-5">
            {t("heroTitle")}
            <br />
            <span className="bg-gradient-to-r from-accent to-purple-400 bg-clip-text text-transparent">
              {t("heroHighlight")}
            </span>
          </h1>
          <p className="text-lg text-muted max-w-xl mx-auto mb-10 leading-relaxed">
            {t("heroDesc")}
          </p>
          <Link
            href="/register"
            className="inline-block px-7 py-3 bg-accent hover:bg-accent-hover text-white font-medium rounded-lg transition-all duration-300 hover:shadow-[0_0_24px_rgba(79,110,247,0.25)]"
          >
            {t("cta")}
          </Link>
          <p className="text-xs text-muted mt-4">{t("ctaSubtext")}</p>
        </section>

        {/* Divider — subtle gradient line */}
        <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent" />

        {/* Features — tighter to pricing (same decision flow) */}
        <section className="py-24">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-left">
            <FeatureCard title={t("feature1Title")} desc={t("feature1Desc")} />
            <FeatureCard title={t("feature2Title")} desc={t("feature2Desc")} />
            <FeatureCard title={t("feature3Title")} desc={t("feature3Desc")} />
          </div>
        </section>

        {/* Divider */}
        <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent" />

        {/* Pricing — closer to features, part of the same narrative */}
        <section className="py-24 text-center">
          <h2 className="text-2xl font-semibold tracking-tight mb-10">{t("pricingTitle")}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <PriceCard
              name={t("planFree")}
              price={t("priceFree")}
              features={[t("featureFreeCredits"), t("featureFree1Lobster")]}
              ctaLabel={t("getStartedFree")}
              ctaHref="/register"
            />
            <PriceCard
              name={t("planStarter")}
              price={t("priceStarter")}
              features={[t("featureStarterCredits"), t("featureStarter1Lobster"), t("featureStarterAllBrains")]}
              highlight
              badge={t("recommended")}
              ctaLabel={t("choosePlan")}
              ctaHref="/register"
            />
            <PriceCard
              name={t("planPro")}
              price={t("pricePro")}
              features={[t("featureProCredits"), t("featurePro3Lobsters"), t("featureProSupport")]}
              ctaLabel={t("choosePlan")}
              ctaHref="/register"
            />
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-8 text-center text-xs text-muted">
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <span>Clawzy.ai</span>
          <span className="text-border">|</span>
          <Link href="/terms" className="hover:text-foreground transition-colors">{t("footerTerms")}</Link>
          <Link href="/privacy" className="hover:text-foreground transition-colors">{t("footerPrivacy")}</Link>
          <span className="text-border">|</span>
          <a href="https://github.com/openclaw/openclaw" target="_blank" rel="noopener noreferrer" className="hover:text-foreground transition-colors">{t("footerPoweredBy")}</a>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="group border border-border rounded-xl p-6 hover:border-accent/20 hover:bg-surface/40 transition-all duration-300">
      <h3 className="text-sm font-medium text-foreground mb-2.5">{title}</h3>
      <p className="text-sm text-muted leading-relaxed">{desc}</p>
    </div>
  );
}

function PriceCard({
  name,
  price,
  features,
  highlight,
  badge,
  ctaLabel,
  ctaHref,
}: {
  name: string;
  price: string;
  features: string[];
  highlight?: boolean;
  badge?: string;
  ctaLabel: string;
  ctaHref: string;
}) {
  return (
    <div
      className={`relative rounded-xl p-6 text-left transition-all duration-300 ${
        highlight
          ? "border-2 border-accent/50 bg-accent/[0.03] shadow-[0_0_32px_rgba(79,110,247,0.08)]"
          : "border border-border hover:border-accent/20"
      }`}
    >
      {badge && (
        <span className="absolute -top-2.5 left-5 px-2.5 py-0.5 bg-accent text-white text-[10px] font-medium rounded-full tracking-wide">
          {badge}
        </span>
      )}
      <h3 className="text-sm font-medium text-foreground">{name}</h3>
      <p className="text-2xl font-semibold text-foreground mt-2">{price}</p>
      <ul className="mt-4 space-y-2">
        {features.map((f) => (
          <li key={f} className="text-sm text-muted flex items-start gap-2">
            <span className="text-accent/60 mt-0.5">&#8226;</span>
            {f}
          </li>
        ))}
      </ul>
      <Link
        href={ctaHref}
        className={`block mt-6 py-2 text-center text-sm font-medium rounded-lg transition-all duration-200 ${
          highlight
            ? "bg-accent hover:bg-accent-hover text-white hover:shadow-[0_0_16px_rgba(79,110,247,0.2)]"
            : "border border-border text-foreground hover:bg-surface hover:border-accent/30"
        }`}
      >
        {ctaLabel}
      </Link>
    </div>
  );
}
