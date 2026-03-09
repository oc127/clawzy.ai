"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getToolCatalog,
  getAgentTools,
  installTool as apiInstallTool,
  uninstallTool as apiUninstallTool,
  type ToolInfo,
  type CategoryInfo,
} from "@/lib/api";

export function useToolCatalog() {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const fetchCatalog = useCallback(async (cat?: string | null, q?: string) => {
    setLoading(true);
    try {
      const data = await getToolCatalog(cat || undefined, q || undefined);
      setTools(data.tools);
      setCategories(data.categories);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load tools");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCatalog(category, search);
  }, [category, search, fetchCatalog]);

  return { tools, categories, loading, error, category, setCategory, search, setSearch };
}

export function useAgentTools(agentId: string | null) {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!agentId) return;
    setLoading(true);
    try {
      const data = await getAgentTools(agentId);
      setTools(data.tools);
    } catch {
      // Silently fail — agent might not exist yet
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const installTool = useCallback(
    async (toolId: string) => {
      if (!agentId) return null;
      const result = await apiInstallTool(agentId, toolId);
      await refresh();
      return result;
    },
    [agentId, refresh]
  );

  const uninstallTool = useCallback(
    async (toolId: string) => {
      if (!agentId) return null;
      const result = await apiUninstallTool(agentId, toolId);
      await refresh();
      return result;
    },
    [agentId, refresh]
  );

  return { tools, loading, installTool, uninstallTool, refresh };
}
