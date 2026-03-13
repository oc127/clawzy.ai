"use client";

import Link from "next/link";
import { Navbar } from "@/components/navbar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Bot, Cpu, Coins } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      {/* Hero */}
      <section className="mx-auto flex max-w-4xl flex-col items-center px-4 pb-20 pt-24 text-center">
        <div className="mb-4 inline-flex rounded-full border border-border bg-card px-4 py-1.5 text-sm text-muted-foreground">
          AI Agent Platform
        </div>
        <h1 className="mb-6 text-5xl font-bold leading-tight tracking-tight sm:text-6xl">
          Your AI Lobster,{" "}
          <span className="text-primary">Any Brain.</span>
        </h1>
        <p className="mb-10 max-w-2xl text-lg text-muted-foreground">
          Create custom AI agents powered by the world&apos;s best language
          models. DeepSeek, Qwen, and more — all in one place. Pay only for
          what you use.
        </p>
        <div className="flex gap-4">
          <Link href="/register">
            <Button size="lg">Get Started Free</Button>
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
        <div className="grid gap-6 md:grid-cols-3">
          <Card className="flex flex-col items-center p-8 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Bot className="h-6 w-6" />
            </div>
            <h3 className="mb-2 text-lg font-semibold">Custom Agents</h3>
            <p className="text-sm text-muted-foreground">
              Create personal AI agents that run 24/7. Each agent gets its own
              isolated environment with persistent memory.
            </p>
          </Card>

          <Card className="flex flex-col items-center p-8 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Cpu className="h-6 w-6" />
            </div>
            <h3 className="mb-2 text-lg font-semibold">Multiple AI Models</h3>
            <p className="text-sm text-muted-foreground">
              Choose from DeepSeek, Qwen, and more. Switch models mid-conversation
              to find the best fit for your task.
            </p>
          </Card>

          <Card className="flex flex-col items-center p-8 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Coins className="h-6 w-6" />
            </div>
            <h3 className="mb-2 text-lg font-semibold">Pay-as-you-go</h3>
            <p className="text-sm text-muted-foreground">
              Start with 500 free credits. No monthly commitment — top up when
              you need more, or subscribe for better rates.
            </p>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 text-center text-sm text-muted-foreground">
        &copy; {new Date().getFullYear()} Clawzy.ai. All rights reserved.
      </footer>
    </div>
  );
}
