"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { listModels, type ModelInfo } from "@/lib/api";

const TIER_COLORS: Record<string, string> = {
  budget: "text-green-400 border-green-400/30",
  standard: "text-blue-400 border-blue-400/30",
  premium: "text-purple-400 border-purple-400/30",
};

export default function ModelsPage() {
  const t = useTranslations("models");
  const tc = useTranslations("common");
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listModels()
      .then((data) => setModels(Array.isArray(data) ? data : []))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load models"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-10 text-sm text-muted">{tc("loading")}</div>;
  }

  return (
    <div className="p-10 max-w-3xl">
      <h1 className="text-xl font-semibold text-foreground tracking-tight mb-2">
        {t("title")}
      </h1>
      <p className="text-sm text-muted mb-8">{t("description")}</p>

      {error && (
        <div className="mb-4 px-4 py-2.5 bg-red-500/10 border border-red-500/20 rounded-lg">
          <span className="text-xs text-red-400">{error}</span>
        </div>
      )}

      {models.length === 0 && !error ? (
        <p className="text-sm text-muted">{t("noModels")}</p>
      ) : (
        <div className="space-y-3">
          {models.map((model) => {
            const tierColor = TIER_COLORS[model.tier] || TIER_COLORS.standard;
            return (
              <div
                key={model.id}
                className="border border-border rounded-lg px-5 py-4"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-medium text-foreground">
                        {model.name}
                      </h3>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 border rounded-full ${tierColor}`}
                      >
                        {model.tier}
                      </span>
                    </div>
                    <p className="text-xs text-muted mt-1">{model.provider}</p>
                    {model.description && (
                      <p className="text-xs text-muted mt-1.5">{model.description}</p>
                    )}
                  </div>
                  <div className="text-right text-xs text-muted whitespace-nowrap">
                    <p>
                      {t("inputCost", { cost: model.credits_per_1k_input })}
                    </p>
                    <p className="mt-0.5">
                      {t("outputCost", { cost: model.credits_per_1k_output })}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
