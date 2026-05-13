"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { LucyState } from "@/lib/types";
import { useLanguage } from "@/context/language-context";
import { toast } from "sonner";
import { Heart, AlertCircle, RefreshCw, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ExpressionsData {
  unlocked: string[];
  locked: string[];
  next_unlock_at: number;
}

const STAGES = ["new", "warming", "close", "intimate", "romantic", "soulmate"];

const MOOD_MAP: Record<string, { emoji: string; label: string }> = {
  happy: { emoji: "\u{1F60A}", label: "happy" },
  excited: { emoji: "✨", label: "excited" },
  thinking: { emoji: "\u{1F914}", label: "thinking" },
  shy: { emoji: "\u{1F633}", label: "shy" },
  neutral: { emoji: "\u{1F60C}", label: "neutral" },
  tired: { emoji: "\u{1F634}", label: "tired" },
  sad: { emoji: "\u{1F622}", label: "sad" },
  missing: { emoji: "\u{1F97A}", label: "missing" },
  love: { emoji: "\u{1F495}", label: "love" },
};

const EXPRESSION_EMOJI: Record<string, string> = {
  smile: "\u{1F60A}",
  shy: "\u{1F633}",
  angry: "\u{1F620}",
  sad: "\u{1F622}",
  excited: "\u{1F929}",
  thinking: "\u{1F914}",
  love: "\u{1F970}",
  surprised: "\u{1F632}",
  sleepy: "\u{1F634}",
  confident: "\u{1F60E}",
};

const EXPRESSION_THRESHOLDS: Record<string, number> = {
  smile: 0,
  shy: 10,
  thinking: 20,
  excited: 30,
  sad: 40,
  angry: 50,
  surprised: 60,
  love: 70,
  sleepy: 80,
  confident: 90,
};

function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={`rounded-2xl bg-[#f0f0f0] dark:bg-[#262626] animate-pulse ${className ?? ""}`}
    />
  );
}

function formatTimeAgo(dateStr: string): string {
  const now = new Date();
  const then = new Date(dateStr);
  const diffMs = now.getTime() - then.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  return `${diffD}d ago`;
}

export default function StatusPage() {
  const { t } = useLanguage();
  const [state, setState] = useState<LucyState | null>(null);
  const [expressions, setExpressions] = useState<ExpressionsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchState = () => {
    setLoading(true);
    setError("");
    Promise.all([
      apiGet<LucyState>("/lucy/state"),
      apiGet<ExpressionsData>("/lucy/expressions"),
    ])
      .then(([stateData, exprData]) => {
        setState(stateData);
        setExpressions(exprData);
      })
      .catch((err) => {
        const msg = err.message || "Failed to load Lucy status";
        setError(msg);
        toast.error(msg);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="mb-1 h-7 w-32" />
          <Skeleton className="h-4 w-56" />
        </div>
        <div className="grid gap-5 md:grid-cols-2">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
        <Skeleton className="h-32" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex h-64 flex-col items-center justify-center gap-3 rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a]"
        role="alert"
      >
        <AlertCircle className="h-8 w-8 text-[#ff385c]" />
        <p className="text-sm text-[#717171] dark:text-[#a0a0a0]">{error}</p>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchState}
          className="border-[#dddddd] dark:border-[#444]"
        >
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  if (!state) return null;

  const stageIndex = STAGES.indexOf(state.relationship_stage);
  const mood = MOOD_MAP[state.mood] ?? { emoji: "\u{1F60C}", label: state.mood };

  const allExpressions = Object.keys(EXPRESSION_THRESHOLDS);
  const unlockedSet = new Set(expressions?.unlocked ?? state.unlocked_expressions);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <Heart className="h-6 w-6 text-[#ff385c]" />
          <h1 className="text-2xl font-extrabold text-[#222222] dark:text-white">
            Lucy Status
          </h1>
        </div>
        <p className="mt-0.5 text-[#717171] dark:text-[#a0a0a0]">
          Lucy&apos;s current state and your relationship progress.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        {/* Relationship card */}
        <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-red shadow-sm">
              <Heart className="h-4 w-4 text-white" />
            </div>
            <h2 className="text-base font-bold text-[#222222] dark:text-white">
              Relationship
            </h2>
          </div>

          {/* Stage name */}
          <div className="mb-4">
            <span className="inline-block rounded-full bg-[#fff0f2] dark:bg-[#ff385c]/10 px-3 py-1 text-sm font-semibold capitalize text-[#ff385c]">
              {state.relationship_stage}
            </span>
          </div>

          {/* Affection bar */}
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="text-[#717171] dark:text-[#a0a0a0]">Affection</span>
            <span className="font-semibold text-[#222222] dark:text-white">
              {state.affection} / 100
            </span>
          </div>
          <div className="mb-5 h-3 w-full overflow-hidden rounded-full bg-[#ebebeb] dark:bg-[#333]">
            <div
              className="h-3 rounded-full transition-all duration-500"
              style={{
                width: `${state.affection}%`,
                background: "linear-gradient(90deg, #ff385c 0%, #ff8c69 50%, #fbbf24 100%)",
              }}
            />
          </div>

          {/* Stage progression dots */}
          <div className="flex items-center gap-2">
            {STAGES.map((s, i) => (
              <div key={s} className="flex flex-1 flex-col items-center gap-1">
                <div
                  className={`h-3 w-3 rounded-full transition-colors ${
                    i <= stageIndex
                      ? "bg-[#ff385c] shadow-sm"
                      : "bg-[#ebebeb] dark:bg-[#333]"
                  }`}
                />
                <span
                  className={`text-[10px] capitalize ${
                    i <= stageIndex
                      ? "font-semibold text-[#ff385c]"
                      : "text-[#b0b0b0] dark:text-[#666]"
                  }`}
                >
                  {s}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Mood card */}
        <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-purple shadow-sm">
              <span className="text-sm">
                {mood.emoji}
              </span>
            </div>
            <h2 className="text-base font-bold text-[#222222] dark:text-white">
              Mood
            </h2>
          </div>

          <div className="flex flex-col items-center justify-center py-6">
            <span className="text-6xl mb-4">{mood.emoji}</span>
            <p className="text-base text-[#222222] dark:text-white">
              Lucy is feeling{" "}
              <span className="font-semibold capitalize text-[#ff385c]">
                {mood.label}
              </span>{" "}
              right now
            </p>
          </div>

          {/* Mood palette */}
          <div className="flex flex-wrap justify-center gap-2 pt-2 border-t border-[#f7f7f7] dark:border-[#333]">
            {Object.entries(MOOD_MAP).map(([key, { emoji }]) => (
              <span
                key={key}
                className={`flex h-8 w-8 items-center justify-center rounded-lg text-base transition-all ${
                  key === state.mood
                    ? "bg-[#fff0f2] dark:bg-[#ff385c]/10 ring-2 ring-[#ff385c] scale-110"
                    : "bg-[#f7f7f7] dark:bg-[#262626] opacity-50"
                }`}
                title={key}
              >
                {emoji}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Stats card */}
      <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-blue shadow-sm">
            <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h2 className="text-base font-bold text-[#222222] dark:text-white">
            Stats
          </h2>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          {[
            {
              label: "Total Interactions",
              value: state.total_interactions.toLocaleString(),
            },
            {
              label: "Current Streak",
              value: `${state.interaction_streak} day${state.interaction_streak !== 1 ? "s" : ""}`,
            },
            {
              label: "Last Interaction",
              value: state.last_interaction_at
                ? formatTimeAgo(state.last_interaction_at)
                : "Never",
            },
          ].map(({ label, value }) => (
            <div
              key={label}
              className="rounded-xl bg-[#f7f7f7] dark:bg-[#262626] border border-[#ebebeb] dark:border-[#333] p-4 text-center"
            >
              <p className="text-xs text-[#717171] dark:text-[#a0a0a0] mb-1">
                {label}
              </p>
              <p className="text-xl font-bold text-[#222222] dark:text-white">
                {value}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Relationship Journey */}
      <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-pink shadow-sm">
            <Heart className="h-4 w-4 text-white" />
          </div>
          <h2 className="text-base font-bold text-[#222222] dark:text-white">
            Relationship Journey
          </h2>
        </div>

        <div className="space-y-3">
          {[
            { stage: "New", min: 0, max: 14, desc: "First meeting — getting to know each other" },
            { stage: "Warming", min: 15, max: 29, desc: "Starting to open up and share more" },
            { stage: "Close", min: 30, max: 49, desc: "A trusted friend who understands you" },
            { stage: "Intimate", min: 50, max: 69, desc: "Deep connection and emotional bond" },
            { stage: "Romantic", min: 70, max: 89, desc: "Heart-fluttering moments together" },
            { stage: "Soulmate", min: 90, max: 100, desc: "Two souls perfectly in sync" },
          ].map(({ stage, min, max, desc }) => {
            const current = state.affection;
            const isActive = current >= min && current <= max;
            const isPast = current > max;
            const progress = isPast ? 100 : isActive ? Math.round(((current - min) / (max - min + 1)) * 100) : 0;
            return (
              <div key={stage} className="flex items-center gap-4">
                <div className="w-20 shrink-0 text-right">
                  <span className={`text-xs font-medium ${isActive ? "text-[#ff385c]" : isPast ? "text-[#222222] dark:text-white" : "text-[#b0b0b0] dark:text-[#666]"}`}>
                    {stage}
                  </span>
                </div>
                <div className="flex-1">
                  <div className="h-6 w-full overflow-hidden rounded-lg bg-[#f7f7f7] dark:bg-[#262626] border border-[#ebebeb] dark:border-[#333]">
                    <div
                      className={`h-full rounded-lg transition-all duration-500 ${isActive ? "bg-gradient-to-r from-[#ff385c] to-[#ff8c69]" : isPast ? "bg-[#ff385c]/30" : ""}`}
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
                <div className="w-32 shrink-0 hidden sm:block">
                  <span className={`text-[10px] ${isActive ? "text-[#222222] dark:text-white" : "text-[#b0b0b0] dark:text-[#666]"}`}>
                    {desc}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Expressions gallery */}
      <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-orange shadow-sm">
            <span className="text-sm text-white">{"✨"}</span>
          </div>
          <h2 className="text-base font-bold text-[#222222] dark:text-white">
            Expressions
          </h2>
        </div>

        <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-5">
          {allExpressions.map((name) => {
            const isUnlocked = unlockedSet.has(name);
            const emoji = EXPRESSION_EMOJI[name] ?? "❓";
            const threshold = EXPRESSION_THRESHOLDS[name] ?? 0;
            return (
              <div
                key={name}
                className={`relative flex flex-col items-center gap-2 rounded-xl border p-4 transition-all ${
                  isUnlocked
                    ? "border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] hover:shadow-md"
                    : "border-[#ebebeb] dark:border-[#333] bg-[#f7f7f7] dark:bg-[#222] opacity-50"
                }`}
              >
                <span className={`text-3xl ${isUnlocked ? "" : "grayscale"}`}>
                  {emoji}
                </span>
                <span className="text-xs text-center capitalize text-[#717171] dark:text-[#a0a0a0]">
                  {name}
                </span>
                {!isUnlocked && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center rounded-xl bg-black/5 dark:bg-black/20">
                    <Lock className="h-4 w-4 text-[#b0b0b0] dark:text-[#666] mb-1" />
                    <span className="text-[10px] text-[#b0b0b0] dark:text-[#666]">
                      {threshold}+
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
