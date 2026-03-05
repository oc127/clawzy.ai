"use client";

import { useEffect, useState } from "react";
import { getCredits, type CreditsInfo } from "@/lib/api";

export function useCredits() {
  const [credits, setCredits] = useState<CreditsInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCredits()
      .then(setCredits)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  function refresh() {
    getCredits().then(setCredits).catch(() => {});
  }

  return { credits, loading, refresh };
}
