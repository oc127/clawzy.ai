"use client";

import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Button } from "@/components/ui/button";
import { LottieIcon } from "@/components/lottie-icon";
import { Bot, Cpu, Coins, ArrowRight, Shield, Zap, Sparkles, Star } from "lucide-react";

const FEATURES = [
  {
    title: "Custom AI Agents",
    desc: "Create personal AI agents that run 24/7 with persistent memory and isolated environments.",
    lottie: "https://lottie.host/5e0cbc8b-b08a-4d99-be0c-2b95dbdae2c9/JNxCjVLTqH.json",
    fallbackIcon: <Bot className="h-7 w-7 text-white" />,
    gradient: "icon-gradient-red",
  },
  {
    title: "Multiple AI Models",
    desc: "Choose from DeepSeek, Qwen, Claude, GPT and more. Switch models mid-conversation.",
    lottie: "https://lottie.host/2f382b74-7b5e-4e80-a5ff-fcc7f90a7b2e/TmBBzP3mU3.json",
    fallbackIcon: <Cpu className="h-7 w-7 text-white" />,
    gradient: "icon-gradient-blue",
  },
  {
    title: "Pay-as-you-go",
    desc: "Start with 500 free credits. No monthly commitment — top up when you need more.",
    lottie: "https://lottie.host/0dc8d71e-0ded-4f78-8a70-8cb5d20b8c90/YHtD1nzaE0.json",
    fallbackIcon: <Coins className="h-7 w-7 text-white" />,
    gradient: "icon-gradient-green",
  },
];

const TRUST_ITEMS = [
  {
    icon: <Zap className="h-5 w-5 text-white" />,
    gradient: "icon-gradient-orange",
    title: "Lightning Fast",
    desc: "Sub-second response streaming",
  },
  {
    icon: <Shield className="h-5 w-5 text-white" />,
    gradient: "icon-gradient-blue",
    title: "Secure & Isolated",
    desc: "Each agent runs in its own container",
  },
  {
    icon: <Sparkles className="h-5 w-5 text-white" />,
    gradient: "icon-gradient-purple",
    title: "Always Improving",
    desc: "New models added regularly",
  },
];

const REVIEWS = [
  {
    name: "Yuki T.",
    role: "Software Engineer",
    text: "NipponClaw is amazing — I run 3 agents 24/7 for coding, research, and writing. Best AI platform I've tried.",
    stars: 5,
  },
  {
    name: "Haruto M.",
    role: "Product Manager",
    text: "The pay-as-you-go model is perfect. I use DeepSeek and Qwen depending on the task, switching is seamless.",
    stars: 5,
  },
  {
    name: "Aoi S.",
    role: "Freelancer",
    text: "Finally a platform that gives me access to multiple cutting-edge models. The Japanese support is great too!",
    stars: 5,
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero */}
      <section className="relative overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#fff8f8] to-white pointer-events-none" />
        <div className="absolute -top-24 -right-32 h-[500px] w-[500px] rounded-full bg-[#ff385c]/5 blur-3xl pointer-events-none" />
        <div className="absolute top-24 -left-32 h-[400px] w-[400px] rounded-full bg-[#ff385c]/5 blur-3xl pointer-events-none" />

        <div className="relative mx-auto flex max-w-4xl flex-col items-center px-6 pb-28 pt-24 text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#ff385c]/20 bg-[#ff385c]/5 px-4 py-1.5 text-sm font-medium text-[#ff385c]">
            <Sparkles className="h-3.5 w-3.5" />
            AI Agent Platform — Now Available in Japan
          </div>

          <h1 className="mb-6 text-5xl font-extrabold leading-[1.1] tracking-tight text-[#222222] sm:text-6xl lg:text-7xl">
            Your AI Agent,{" "}
            <span className="gradient-text">Any Brain.</span>
          </h1>

          <p className="mb-10 max-w-2xl text-lg leading-relaxed text-[#717171]">
            Create custom AI agents powered by the world&apos;s best language models.
            DeepSeek, Qwen, Claude, GPT — all in one place.
            Pay only for what you use.
          </p>

          <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
            <Link href="/register">
              <Button
                size="lg"
                className="gap-2 bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-2xl font-bold text-base shadow-[0_4px_16px_rgba(255,56,92,0.35)] hover:shadow-[0_6px_24px_rgba(255,56,92,0.45)] transition-all"
              >
                Get Started Free
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/login">
              <Button
                variant="outline"
                size="lg"
                className="rounded-2xl border-[#dddddd] text-[#222222] hover:border-[#b0b0b0] hover:bg-[#f7f7f7] font-semibold text-base"
              >
                Sign In
              </Button>
            </Link>
          </div>

          <p className="mt-5 text-sm text-[#717171]">
            500 free credits on sign up · No credit card required
          </p>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-5xl px-6 pb-24">
        <div className="mb-14 text-center">
          <h2 className="mb-3 text-3xl font-bold tracking-tight text-[#222222]">
            Everything you need
          </h2>
          <p className="text-[#717171] text-lg">
            A complete platform for building and running AI agents.
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="group flex flex-col items-center p-8 text-center rounded-3xl border border-[#ebebeb] bg-white shadow-[0_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0_8px_32px_rgba(0,0,0,0.10)] hover:-translate-y-1 transition-all duration-200"
            >
              <div className={`mb-5 flex h-16 w-16 items-center justify-center rounded-2xl ${f.gradient} shadow-lg`}>
                <LottieIcon
                  src={f.lottie}
                  className="w-10 h-10"
                  fallback={f.fallbackIcon}
                />
              </div>
              <h3 className="mb-2 text-lg font-bold text-[#222222]">{f.title}</h3>
              <p className="text-sm leading-relaxed text-[#717171]">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Trust bar */}
      <section className="border-y border-[#ebebeb] bg-[#f7f7f7] py-16">
        <div className="mx-auto grid max-w-4xl gap-8 px-6 sm:grid-cols-3">
          {TRUST_ITEMS.map((item) => (
            <div key={item.title} className="flex items-center gap-4">
              <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${item.gradient} shadow-md`}>
                {item.icon}
              </div>
              <div>
                <p className="font-bold text-[#222222]">{item.title}</p>
                <p className="text-sm text-[#717171]">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Reviews */}
      <section className="mx-auto max-w-5xl px-6 py-24">
        <div className="mb-12 text-center">
          <h2 className="mb-3 text-3xl font-bold tracking-tight text-[#222222]">
            Loved by creators
          </h2>
          <p className="text-[#717171] text-lg">See what our users are saying.</p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {REVIEWS.map((r) => (
            <div
              key={r.name}
              className="rounded-3xl border border-[#ebebeb] bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.06)]"
            >
              <div className="mb-3 flex gap-0.5">
                {Array.from({ length: r.stars }).map((_, i) => (
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
      </section>

      {/* CTA */}
      <section className="bg-gradient-to-br from-[#ff385c] to-[#ff8c69] py-20 text-center">
        <div className="mx-auto max-w-2xl px-6">
          <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
            Ready to get started?
          </h2>
          <p className="mt-3 text-lg text-white/80">
            Create your first AI agent in under a minute.
          </p>
          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Link href="/register">
              <Button
                size="lg"
                className="gap-2 bg-white text-[#ff385c] hover:bg-white/90 rounded-2xl font-bold text-base shadow-lg"
              >
                Create Free Account
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
          <p className="mt-4 text-sm text-white/70">No credit card required</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#ebebeb] bg-white py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 px-6 sm:flex-row sm:justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-extrabold text-[#222222]">NipponClaw</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-[#717171]">
            <Link href="/login" className="hover:text-[#222222] transition-colors">Log in</Link>
            <Link href="/register" className="hover:text-[#222222] transition-colors">Sign up</Link>
            <span>&copy; {new Date().getFullYear()} NipponClaw. All rights reserved.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
