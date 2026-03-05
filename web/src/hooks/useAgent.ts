"use client";

import { useEffect, useState, useCallback } from "react";
import {
  listAgents,
  createAgent as apiCreateAgent,
  deleteAgent as apiDeleteAgent,
  startAgent as apiStartAgent,
  stopAgent as apiStopAgent,
  type Agent,
} from "@/lib/api";

export function useAgents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listAgents()
      .then(setAgents)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const createAgent = useCallback(async (name: string, modelName: string) => {
    const agent = await apiCreateAgent(name, modelName);
    setAgents((prev) => [agent, ...prev]);
    return agent;
  }, []);

  const deleteAgent = useCallback(async (id: string) => {
    await apiDeleteAgent(id);
    setAgents((prev) => prev.filter((a) => a.id !== id));
  }, []);

  const startAgent = useCallback(async (id: string) => {
    const updated = await apiStartAgent(id);
    setAgents((prev) => prev.map((a) => (a.id === id ? updated : a)));
    return updated;
  }, []);

  const stopAgent = useCallback(async (id: string) => {
    const updated = await apiStopAgent(id);
    setAgents((prev) => prev.map((a) => (a.id === id ? updated : a)));
    return updated;
  }, []);

  return { agents, loading, createAgent, deleteAgent, startAgent, stopAgent };
}
