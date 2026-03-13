"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import type { Agent, ModelInfo } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Bot, Plus, Trash2, MessageSquare, Play, Square } from "lucide-react";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [modelName, setModelName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const fetchAgents = () => {
    apiGet<Agent[]>("/agents")
      .then(setAgents)
      .catch(() => {});
  };

  useEffect(() => {
    Promise.all([
      apiGet<Agent[]>("/agents"),
      apiGet<ModelInfo[]>("/models"),
    ])
      .then(([a, m]) => {
        setAgents(a);
        setModels(m);
        if (m.length > 0) setModelName(m[0].id);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    setError("");
    try {
      await apiPost("/agents", { name: name.trim(), model_name: modelName });
      setName("");
      setShowCreate(false);
      fetchAgents();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create agent");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await apiDelete(`/agents/${id}`);
      fetchAgents();
    } catch {
      // ignore
    }
  };

  const handleToggle = async (agent: Agent) => {
    const action = agent.status === "running" ? "stop" : "start";
    try {
      await apiPost(`/agents/${agent.id}/${action}`);
      fetchAgents();
    } catch {
      // ignore
    }
  };

  if (loading) {
    return <p className="text-muted-foreground">Loading agents...</p>;
  }

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="mb-1 text-2xl font-bold">Agents</h1>
          <p className="text-muted-foreground">
            Create and manage your AI agents.
          </p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Agent
        </Button>
      </div>

      {showCreate && (
        <Card className="mb-8">
          <h2 className="mb-4 text-lg font-semibold">New Agent</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm text-muted-foreground">
                Agent Name
              </label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Assistant"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-muted-foreground">
                Model
              </label>
              <Select
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
              >
                {models.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.provider})
                  </option>
                ))}
              </Select>
            </div>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <div className="flex gap-2">
              <Button type="submit" disabled={creating}>
                {creating ? "Creating..." : "Create"}
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setShowCreate(false)}
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}

      {agents.length === 0 ? (
        <Card className="py-12 text-center">
          <Bot className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
          <h2 className="mb-2 text-lg font-semibold">No agents yet</h2>
          <p className="mb-4 text-sm text-muted-foreground">
            Create your first AI agent to get started.
          </p>
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create Agent
          </Button>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <Card key={agent.id} className="flex flex-col justify-between">
              <div>
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="font-semibold">{agent.name}</h3>
                  <span
                    className={`rounded px-2 py-0.5 text-xs ${
                      agent.status === "running"
                        ? "bg-green-500/20 text-green-400"
                        : "bg-yellow-500/20 text-yellow-400"
                    }`}
                  >
                    {agent.status}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  {agent.model_name}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Created {new Date(agent.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="mt-4 flex gap-2">
                <Link href={`/agents/${agent.id}`} className="flex-1">
                  <Button variant="outline" size="sm" className="w-full">
                    <MessageSquare className="mr-2 h-4 w-4" />
                    Chat
                  </Button>
                </Link>
                {(agent.status === "running" || agent.status === "stopped") && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggle(agent)}
                    className={
                      agent.status === "running"
                        ? "text-yellow-400 hover:text-yellow-300"
                        : "text-green-400 hover:text-green-300"
                    }
                  >
                    {agent.status === "running" ? (
                      <Square className="h-4 w-4" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(agent.id)}
                  className="text-red-400 hover:text-red-300"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
