"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { ModelInfo } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Cpu, Plus } from "lucide-react";

export default function ModelsPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<ModelInfo[]>("/models")
      .then(setModels)
      .catch((err) => setError(err.message || "Failed to load models"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-muted-foreground">Loading models...</p>;
  }

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="mb-1 text-2xl font-bold">Models</h1>
          <p className="text-muted-foreground">
            Available AI models for your agents.
          </p>
        </div>
        <Link href="/agents">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Agent
          </Button>
        </Link>
      </div>

      {error && (
        <div className="mb-6 rounded-md bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {models.map((model) => (
          <Card key={model.id}>
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Cpu className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold">{model.name}</h3>
                <div className="mt-1 flex gap-2">
                  <span className="rounded bg-accent px-2 py-0.5 text-xs">
                    {model.provider}
                  </span>
                  <span
                    className={`rounded px-2 py-0.5 text-xs ${
                      model.tier === "premium"
                        ? "bg-yellow-500/20 text-yellow-400"
                        : "bg-green-500/20 text-green-400"
                    }`}
                  >
                    {model.tier}
                  </span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  {model.description}
                </p>
                <div className="mt-3 text-xs text-muted-foreground">
                  <p>{model.credits_per_1k_input} credits / 1K input</p>
                  <p>{model.credits_per_1k_output} credits / 1K output</p>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {models.length === 0 && (
        <p className="text-center text-muted-foreground">
          No models available.
        </p>
      )}
    </div>
  );
}
