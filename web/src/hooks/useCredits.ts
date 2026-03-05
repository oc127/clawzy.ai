"use client";

import { useEffect, useState } from "react";
import { getCredits, type CreditsInfo } from "@/lib/api";

export function useCredits() {
  const [credits, setCredits] = useState<CreditsInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCredits()
      .then(setCredits)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load credits"))
      .finally(() => setLoading(false));
  }, []);

  function refresh() {
    getCredits()
      .then(setCredits)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to refresh credits"));
  }

  return { credits, loading, error, refresh };
}
