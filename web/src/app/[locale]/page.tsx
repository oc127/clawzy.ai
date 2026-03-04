"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import LanguageSwitcher from "@/components/LanguageSwitcher";

export default function LandingPage() {
  const t = useTranslations("landing");

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-6 max-w-6xl mx-auto">
        <div className="text-xl font-bold flex items-center gap-2">
          🦞 Clawzy
        </div>
        <div className="flex items-center gap-4">
          <LanguageSwitcher />
          <Link
            href="/login"
            className="px-5 py-2 text-sm text-gray-300 hover:text-white transition"
          >
            {t("login")}
          </Link>
          <Link
            href="/register"
            className="px-5 py-2 text-sm bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition"
          >
            {t("freeRegister")}
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <main className="max-w-4xl mx-auto px-8 pt-20 pb-32 text-center">
        <div className="text-7xl mb-6">🦞</div>
        <h1 className="text-5xl font-bold leading-tight mb-6">
          {t("heroTitle")}
          <br />
          <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            {t("heroHighlight")}
          </span>
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
          {t("heroDesc")}
        </p>
        <Link
          href="/register"
          className="inline-block px-8 py-4 bg-blue-600 hover:bg-blue-700 text-lg font-semibold rounded-xl transition"
        >
          {t("cta")}
        </Link>
        <p className="text-sm text-gray-600 mt-4">{t("ctaSubtext")}</p>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 text-left">
          <FeatureCard
            icon="⚡"
            title={t("feature1Title")}
            desc={t("feature1Desc")}
          />
          <FeatureCard
            icon="🧠"
            title={t("feature2Title")}
            desc={t("feature2Desc")}
          />
          <FeatureCard
            icon="🔒"
            title={t("feature3Title")}
            desc={t("feature3Desc")}
          />
        </div>

        {/* Pricing preview */}
        <div className="mt-24">
          <h2 className="text-3xl font-bold mb-8">{t("pricingTitle")}</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
      <footer className="border-t border-gray-800 py-8 text-center text-sm text-gray-600">
        Clawzy.ai — OpenClaw as a Service
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  desc,
}: {
  icon: string;
  title: string;
  desc: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>
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
      className={`rounded-xl p-6 ${
        highlight
          ? "bg-blue-600/10 border-2 border-blue-500"
          : "bg-gray-900 border border-gray-800"
      }`}
    >
      <h3 className="text-lg font-bold text-white">{name}</h3>
      <p className="text-3xl font-bold text-white mt-2">{price}</p>
      <ul className="mt-4 space-y-2">
        {features.map((f) => (
          <li key={f} className="text-sm text-gray-400">
            {f}
          </li>
        ))}
      </ul>
    </div>
  );
}
