"use client";

import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Button } from "@/components/ui/button";
import { useLanguage } from "@/context/language-context";
import { ArrowRight, Shield, Zap, Sparkles, Star, Check } from "lucide-react";

const MODELS = ["DeepSeek", "Qwen", "Claude", "GPT-4", "Gemini", "Llama"];

const FEATURE_EMOJIS = ["🤖", "⚡", "💳"];
const FEATURE_GRADIENTS = [
  "from-[#ff385c] to-[#ff8c69]",
  "from-[#3b82f6] to-[#8b5cf6]",
  "from-[#10b981] to-[#34d399]",
];

const TRUST_GRADIENTS = [
  "from-[#f59e0b] to-[#fbbf24]",
  "from-[#3b82f6] to-[#8b5cf6]",
  "from-[#10b981] to-[#34d399]",
];

const PLANS = [
  { name: "Free", price: "0", credits: "500", agents: 1, highlight: false },
  { name: "Starter", price: "9", credits: "5,000", agents: 3, highlight: false },
  { name: "Pro", price: "29", credits: "20,000", agents: 10, highlight: true },
  { name: "Team", price: "99", credits: "100,000", agents: 50, highlight: false },
];

export default function Home() {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* ── HERO ── */}
      <section className="relative overflow-hidden bg-white">
        <div className="pointer-events-none absolute -top-40 -right-40 h-[600px] w-[600px] rounded-full bg-[#ff385c]/8 blur-3xl" />
        <div className="pointer-events-none absolute top-20 -left-40 h-[500px] w-[500px] rounded-full bg-[#ff385c]/5 blur-3xl" />

        <div className="relative mx-auto max-w-6xl px-6 pt-20 pb-16">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            {/* Left copy */}
            <div>
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#ff385c]/25 bg-[#fff0f2] px-4 py-1.5 text-sm font-semibold text-[#ff385c]">
                <Sparkles className="h-3.5 w-3.5" />
                {t.hero.badge}
              </div>

              <h1 className="mb-5 text-5xl font-black leading-[1.08] tracking-tight text-[#222222] lg:text-6xl">
                {t.hero.title1}
                <br />
                <span className="bg-gradient-to-r from-[#ff385c] to-[#ff8c69] bg-clip-text text-transparent">
                  {t.hero.title2}
                </span>
              </h1>

              <p className="mb-8 text-lg leading-relaxed text-[#717171] max-w-lg">
                {t.hero.desc}
              </p>

              <div className="flex flex-col gap-3 sm:flex-row">
                <Link href="/register">
                  <Button className="h-13 gap-2 rounded-2xl bg-[#ff385c] px-8 text-base font-bold text-white shadow-[0_6px_24px_rgba(255,56,92,0.35)] hover:bg-[#e31c5f] hover:shadow-[0_8px_32px_rgba(255,56,92,0.45)] transition-all">
                    {t.hero.cta}
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/login">
                  <Button variant="outline" className="h-13 rounded-2xl border-[#dddddd] px-8 text-base font-semibold text-[#222222] hover:border-[#b0b0b0] hover:bg-[#f7f7f7]">
                    {t.hero.signin}
                  </Button>
                </Link>
              </div>

              <p className="mt-4 text-sm text-[#b0b0b0]">{t.hero.subtext}</p>
            </div>

            {/* Right visual */}
            <div className="relative hidden lg:block">
              <div className="relative h-[420px]">
                <div className="absolute left-8 top-8 w-72 rounded-3xl border border-[#ebebeb] bg-white p-5 shadow-[0_8px_32px_rgba(0,0,0,0.10)]">
                  <div className="mb-3 flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-[#ff385c] to-[#ff8c69] shadow-md">
                      <span className="text-lg">🤖</span>
                    </div>
                    <div>
                      <p className="font-bold text-[#222222]">{t.hero.agentCard1.name}</p>
                      <div className="flex items-center gap-1">
                        <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        <span className="text-xs text-emerald-600 font-medium">{t.hero.agentCard1.running}</span>
                      </div>
                    </div>
                  </div>
                  <div className="rounded-xl bg-[#f7f7f7] p-3 text-xs text-[#717171]">
                    <p className="mb-1 font-semibold text-[#222222]">Last message</p>
                    <p>{t.hero.agentCard1.lastMsg}</p>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-xs text-[#b0b0b0]">
                    <span>{t.hero.agentCard1.model}</span>
                    <span>{t.hero.agentCard1.credits}</span>
                  </div>
                </div>

                <div className="absolute right-0 top-32 w-64 rounded-3xl border border-[#ebebeb] bg-white p-5 shadow-[0_8px_32px_rgba(0,0,0,0.10)]">
                  <div className="mb-3 flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-[#3b82f6] to-[#8b5cf6] shadow-md">
                      <span className="text-lg">🔬</span>
                    </div>
                    <div>
                      <p className="font-bold text-[#222222]">{t.hero.agentCard2.name}</p>
                      <div className="flex items-center gap-1">
                        <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        <span className="text-xs text-emerald-600 font-medium">{t.hero.agentCard2.running}</span>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    {[t.hero.agentCard2.skill1, t.hero.agentCard2.skill2, t.hero.agentCard2.skill3].map((skill) => (
                      <div key={skill} className="flex items-center gap-2 text-xs text-[#717171]">
                        <Check className="h-3 w-3 text-emerald-500 shrink-0" />
                        {skill}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="absolute bottom-8 left-4 flex flex-wrap gap-2 max-w-xs">
                  {MODELS.map((m, i) => (
                    <span key={m} className="rounded-full border border-[#ebebeb] bg-white px-3 py-1 text-xs font-semibold text-[#717171] shadow-sm" style={{ animationDelay: `${i * 100}ms` }}>
                      {m}
                    </span>
                  ))}
                </div>

                <div className="absolute bottom-16 right-0 rounded-2xl border border-[#ebebeb] bg-white px-4 py-3 shadow-[0_4px_16px_rgba(0,0,0,0.08)]">
                  <p className="text-xs text-[#b0b0b0]">{t.hero.creditBalance}</p>
                  <p className="text-2xl font-black text-[#222222]">4,832</p>
                  <p className="text-xs text-emerald-600 font-semibold">{t.hero.creditBonus}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── MODEL STRIP ── */}
      <section className="border-y border-[#ebebeb] bg-[#fafafa] py-5">
        <div className="mx-auto max-w-4xl px-6">
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <span className="text-sm text-[#b0b0b0] font-medium mr-2">{t.poweredBy}</span>
            {MODELS.map((m) => (
              <span key={m} className="rounded-full bg-white border border-[#ebebeb] px-4 py-1.5 text-sm font-semibold text-[#444444] shadow-sm">
                {m}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section className="mx-auto max-w-5xl px-6 py-24">
        <div className="mb-14 text-center">
          <h2 className="mb-3 text-3xl font-black tracking-tight text-[#222222] sm:text-4xl">
            {t.features.title}
          </h2>
          <p className="text-lg text-[#717171]">{t.features.subtitle}</p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {t.features.items.map((f, i) => (
            <div
              key={i}
              className="group rounded-3xl border border-[#ebebeb] bg-white p-8 shadow-[0_2px_12px_rgba(0,0,0,0.06)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.10)] hover:-translate-y-1 transition-all duration-300"
            >
              <div className={`mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${FEATURE_GRADIENTS[i]} shadow-lg text-2xl`}>
                {FEATURE_EMOJIS[i]}
              </div>
              <h3 className="mb-2 text-lg font-bold text-[#222222]">{f.title}</h3>
              <p className="text-sm leading-relaxed text-[#717171]">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── TRUST ── */}
      <section className="border-y border-[#ebebeb] bg-[#f7f7f7] py-14">
        <div className="mx-auto grid max-w-4xl gap-8 px-6 sm:grid-cols-3">
          {t.trust.map((item, i) => (
            <div key={i} className="flex items-center gap-4">
              <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${TRUST_GRADIENTS[i]} shadow-md`}>
                {i === 0 && <Zap className="h-5 w-5 text-white" />}
                {i === 1 && <Shield className="h-5 w-5 text-white" />}
                {i === 2 && <Sparkles className="h-5 w-5 text-white" />}
              </div>
              <div>
                <p className="font-bold text-[#222222]">{item.title}</p>
                <p className="text-sm text-[#717171]">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── PRICING ── */}
      <section className="mx-auto max-w-5xl px-6 py-24">
        <div className="mb-14 text-center">
          <h2 className="mb-3 text-3xl font-black tracking-tight text-[#222222] sm:text-4xl">{t.pricing.title}</h2>
          <p className="text-lg text-[#717171]">{t.pricing.subtitle}</p>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`flex flex-col rounded-3xl border p-6 transition-all ${
                plan.highlight
                  ? "border-[#ff385c] bg-[#ff385c] text-white shadow-[0_8px_32px_rgba(255,56,92,0.30)] scale-105"
                  : "border-[#ebebeb] bg-white shadow-[0_2px_12px_rgba(0,0,0,0.06)]"
              }`}
            >
              {plan.highlight && (
                <div className="mb-3 rounded-full bg-white/20 px-3 py-0.5 text-xs font-bold w-fit">
                  {t.pricing.mostPopular}
                </div>
              )}
              <h3 className={`font-bold text-lg ${plan.highlight ? "text-white" : "text-[#222222]"}`}>{plan.name}</h3>
              <p className={`mt-1 text-3xl font-black ${plan.highlight ? "text-white" : "text-[#222222]"}`}>
                ${plan.price}<span className={`text-sm font-normal ${plan.highlight ? "text-white/70" : "text-[#717171]"}`}>{t.pricing.perMonth}</span>
              </p>
              <div className={`mt-4 flex-1 space-y-2 text-sm ${plan.highlight ? "text-white/80" : "text-[#717171]"}`}>
                <p className="flex items-center gap-2">
                  <Check className="h-4 w-4 shrink-0" />
                  {plan.credits} {t.pricing.creditsPerMonth}
                </p>
                <p className="flex items-center gap-2">
                  <Check className="h-4 w-4 shrink-0" />
                  {plan.agents} {plan.agents > 1 ? t.pricing.agents : t.pricing.agent}
                </p>
              </div>
              <Link href="/register" className="mt-5 block">
                <Button
                  className={`w-full rounded-xl font-semibold ${
                    plan.highlight
                      ? "bg-white text-[#ff385c] hover:bg-white/90"
                      : "bg-[#ff385c] text-white hover:bg-[#e31c5f]"
                  }`}
                >
                  {t.pricing.getStarted}
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* ── REVIEWS ── */}
      <section className="bg-[#f7f7f7] py-20">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-12 text-center">
            <h2 className="mb-3 text-3xl font-black tracking-tight text-[#222222]">{t.reviews.title}</h2>
            <p className="text-lg text-[#717171]">{t.reviews.subtitle}</p>
          </div>
          <div className="grid gap-5 md:grid-cols-3">
            {t.reviews.items.map((r) => (
              <div key={r.name} className="rounded-3xl border border-[#ebebeb] bg-white p-6 shadow-[0_2px_12px_rgba(0,0,0,0.06)]">
                <div className="mb-3 flex gap-0.5">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star key={i} className="h-4 w-4 fill-[#ff385c] text-[#ff385c]" />
                  ))}
                </div>
                <p className="mb-4 text-sm leading-relaxed text-[#444444]">&ldquo;{r.text}&rdquo;</p>
                <div>
                  <p className="font-bold text-[#222222] text-sm">{r.name}</p>
                  <p className="text-xs text-[#717171]">{r.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="bg-gradient-to-br from-[#ff385c] via-[#ff5a5f] to-[#ff8c69] py-24 text-center">
        <div className="mx-auto max-w-2xl px-6">
          <div className="mb-4 text-5xl">🦞</div>
          <h2 className="text-4xl font-black text-white mb-4">{t.cta.title}</h2>
          <p className="text-xl text-white/80 mb-8">{t.cta.subtitle}</p>
          <Link href="/register">
            <Button className="h-14 gap-2 rounded-2xl bg-white px-10 text-lg font-bold text-[#ff385c] shadow-lg hover:bg-white/90 transition-all">
              {t.cta.button}
              <ArrowRight className="h-5 w-5" />
            </Button>
          </Link>
          <p className="mt-4 text-sm text-white/60">{t.cta.subtext}</p>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-[#ebebeb] bg-white py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 px-6 sm:flex-row sm:justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🦞</span>
            <span className="text-lg font-extrabold text-[#222222]">
              <span className="text-[#ff385c]">Nippon</span>Claw
            </span>
          </div>
          <div className="flex items-center gap-6 text-sm text-[#717171]">
            <Link href="/login" className="hover:text-[#222222] transition-colors">{t.footer.login}</Link>
            <Link href="/register" className="hover:text-[#222222] transition-colors">{t.footer.signup}</Link>
            <span>&copy; {new Date().getFullYear()} NipponClaw. {t.footer.rights}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
