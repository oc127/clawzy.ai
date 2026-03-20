"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { ModelInfo } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Cpu, Plus, AlertCircle, RefreshCw, Sparkles, Zap } from "lucide-react";

function Skeleton({ className }: { className?: string }) {
  return <div className={`skeleton-shimmer rounded-2xl ${className ?? ""}`} />;
}

const TIER_CONFIG: Record<string, { label: string; bg: string; text: string; gradient: string }> = {
  premium: { label: "Premium", bg: "bg-amber-100", text: "text-amber-700", gradient: "icon-gradient-orange" },
  standard: { label: "Standard", bg: "bg-blue-100", text: "text-blue-700", gradient: "icon-gradient-blue" },
  free: { label: "Free", bg: "bg-emerald-100", text: "text-emerald-700", gradient: "icon-gradient-green" },
};

export default function ModelsPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = () => {
    setLoading(true);
    setError("");
    apiGet<ModelInfo[]>("/models")
      .then(setModels)
      .catch((err) => setError(err.message || "Failed to load models"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div><Skeleton className="mb-1 h-7 w-24" /><Skeleton className="h-4 w-48" /></div>
          <Skeleton className="h-10 w-36" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => <Skeleton key={i} className="h-40" />)}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 rounded-2xl border border-[#ebebeb] bg-white" role="alert">
        <AlertCircle className="h-8 w-8 text-[#ff385c]" />
        <p className="text-sm text-[#717171]">{error}</p>
        <Button variant="outline" size="sm" onClick={fetchData} className="border-[#dddddd]">
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-[#222222]">Models</h1>
          <p className="mt-0.5 text-[#717171]">Available AI models for your agents.</p>
        </div>
        <Link href="/agents">
          <Button className="gap-2 bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl font-semibold shadow-sm">
            <Plus className="h-4 w-4" />
            Create Agent
          </Button>
        </Link>
      </div>

      {/* Stats bar */}
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { icon: <Cpu className="h-5 w-5 text-white" />, label: "Total Models", value: models.length, gradient: "icon-gradient-blue" },
          { icon: <Sparkles className="h-5 w-5 text-white" />, label: "Premium Models", value: models.filter((m) => m.tier === "premium").length, gradient: "icon-gradient-orange" },
          { icon: <Zap className="h-5 w-5 text-white" />, label: "Standard Models", value: models.filter((m) => m.tier !== "premium").length, gradient: "icon-gradient-green" },
        ].map((s) => (
          <div key={s.label} className="flex items-center gap-4 rounded-2xl border border-[#ebebeb] bg-white p-5 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
            <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl shadow-sm ${s.gradient}`}>
              {s.icon}
            </div>
            <div>
              <p className="text-sm text-[#717171]">{s.label}</p>
              <p className="text-2xl font-extrabold text-[#222222]">{s.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Model grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {models.map((model) => {
          const tier = TIER_CONFIG[model.tier] ?? TIER_CONFIG.standard;
          return (
            <div
              key={model.id}
              className="flex flex-col rounded-2xl border border-[#ebebeb] bg-white p-5 shadow-[0_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.10)] hover:-translate-y-0.5 transition-all duration-200"
            >
              <div className="flex items-start gap-3">
                <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl shadow-sm ${tier.gradient}`}>
                  <Cpu className="h-5 w-5 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-bold text-[#222222] truncate">{model.name}</h3>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    <span className="rounded-full bg-[#f7f7f7] border border-[#ebebeb] px-2.5 py-0.5 text-xs font-medium text-[#717171]">
                      {model.provider}
                    </span>
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${tier.bg} ${tier.text}`}>
                      {tier.label}
                    </span>
                  </div>
                </div>
              </div>
              <p className="mt-3 text-sm text-[#717171] leading-relaxed flex-1">{model.description}</p>
              <div className="mt-4 flex justify-between rounded-xl bg-[#f7f7f7] px-4 py-2.5 text-xs text-[#717171]">
                <span>{model.credits_per_1k_input} cr / 1K in</span>
                <span className="text-[#dddddd]">·</span>
                <span>{model.credits_per_1k_output} cr / 1K out</span>
              </div>
            </div>
          );
        })}
      </div>

      {models.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#dddddd] bg-white py-16 text-center">
          <Cpu className="mb-3 h-10 w-10 text-[#b0b0b0]" />
          <p className="text-[#717171]">No models available yet.</p>
        </div>
      )}
    </div>
  );
}
