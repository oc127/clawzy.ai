"use client";

import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Logo, LogoIcon } from "@/components/logo";
import { Bot, Cpu, Coins, ArrowRight, Sparkles, Shield, Zap } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      {/* Hero */}
      <section className="mx-auto flex max-w-4xl flex-col items-center px-4 pb-24 pt-28 text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm text-primary">
          <Sparkles className="h-3.5 w-3.5" />
          AI Agent Platform
        </div>
        <h1 className="mb-6 text-5xl font-bold leading-[1.1] tracking-tight sm:text-6xl lg:text-7xl">
          Your AI Lobster,{" "}
          <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Any Brain.
          </span>
        </h1>
        <p className="mb-10 max-w-2xl text-lg leading-relaxed text-muted-foreground">
          Create custom AI agents powered by the world&apos;s best language
          models. DeepSeek, Qwen, Claude, GPT — all in one place. Pay only for
          what you use.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
          <Link href="/register">
            <Button size="lg" className="gap-2">
              Get Started Free
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link href="/login">
            <Button variant="outline" size="lg">
              Sign In
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-5xl px-4 pb-24">
        <div className="mb-12 text-center">
          <h2 className="mb-3 text-3xl font-bold tracking-tight">
            Everything you need
          </h2>
          <p className="text-muted-foreground">
            A complete platform for building and running AI agents.
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          <Card className="group flex flex-col items-center p-8 text-center hover:border-primary/30">
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary transition-transform group-hover:scale-110">
              <Bot className="h-7 w-7" />
            </div>
            <h3 className="mb-2 text-lg font-semibold">Custom Agents</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Create personal AI agents that run 24/7. Each agent gets its own
              isolated environment with persistent memory.
            </p>
          </Card>

          <Card className="group flex flex-col items-center p-8 text-center hover:border-primary/30">
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary/10 text-secondary transition-transform group-hover:scale-110">
              <Cpu className="h-7 w-7" />
            </div>
            <h3 className="mb-2 text-lg font-semibold">Multiple AI Models</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Choose from DeepSeek, Qwen, Claude, GPT, and more. Switch models
              mid-conversation to find the best fit.
            </p>
          </Card>

          <Card className="group flex flex-col items-center p-8 text-center hover:border-primary/30">
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary transition-transform group-hover:scale-110">
              <Coins className="h-7 w-7" />
            </div>
            <h3 className="mb-2 text-lg font-semibold">Pay-as-you-go</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Start with 500 free credits. No monthly commitment — top up when
              you need more, or subscribe for better rates.
            </p>
          </Card>
        </div>
      </section>

      {/* Trust bar */}
      <section className="border-t border-border bg-card/30 py-16">
        <div className="mx-auto grid max-w-4xl gap-8 px-4 md:grid-cols-3">
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Zap className="h-5 w-5" />
            </div>
            <div>
              <p className="font-semibold">Fast & Reliable</p>
              <p className="text-sm text-muted-foreground">Sub-second response streaming</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-secondary/10 text-secondary">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <p className="font-semibold">Secure & Isolated</p>
              <p className="text-sm text-muted-foreground">Each agent runs in its own container</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <p className="font-semibold">Always Improving</p>
              <p className="text-sm text-muted-foreground">New models added regularly</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 text-center">
        <div className="mx-auto max-w-2xl px-4">
          <LogoIcon size={48} />
          <h2 className="mt-6 text-3xl font-bold tracking-tight">
            Ready to get started?
          </h2>
          <p className="mt-3 text-lg text-muted-foreground">
            Create your first AI agent in under a minute.
          </p>
          <div className="mt-8">
            <Link href="/register">
              <Button size="lg" className="gap-2">
                Create Free Account
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4">
          <Logo size="sm" />
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} Clawzy.ai. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
