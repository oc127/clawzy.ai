"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import type { Agent, ModelInfo } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { toast } from "sonner";
import {
  Bot,
  Plus,
  Trash2,
  MessageSquare,
  Play,
  Square,
  AlertCircle,
  RefreshCw,
  Code,
  FileText,
  Globe,
  Briefcase,
} from "lucide-react";

// --- Agent Templates ---
interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  defaultName: string;
  recommendedModel: string;
  icon: React.ReactNode;
}

const AGENT_TEMPLATES: AgentTemplate[] = [
  {
    id: "blank",
    name: "Blank Agent",
    description: "Start from scratch with a custom configuration",
    defaultName: "",
    recommendedModel: "",
    icon: <Plus className="h-5 w-5" />,
  },
  {
    id: "coder",
    name: "Code Assistant",
    description: "Write, review, and debug code across languages",
    defaultName: "Code Buddy",
    recommendedModel: "deepseek-chat",
    icon: <Code className="h-5 w-5" />,
  },
  {
    id: "writer",
    name: "Writing Assistant",
    description: "Draft, edit, and polish articles and documents",
    defaultName: "Writing Pro",
    recommendedModel: "qwen-max",
    icon: <FileText className="h-5 w-5" />,
  },
  {
    id: "research",
    name: "Research Agent",
    description: "Analyze data, summarize papers, and find insights",
    defaultName: "Research Hub",
    recommendedModel: "deepseek-reasoner",
    icon: <Globe className="h-5 w-5" />,
  },
  {
    id: "business",
    name: "Business Analyst",
    description: "Create reports, analyze metrics, and plan strategies",
    defaultName: "Biz Analyst",
    recommendedModel: "qwen-plus",
    icon: <Briefcase className="h-5 w-5" />,
  },
];

function AgentsSkeleton() {
  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <Skeleton className="mb-1 h-8 w-32" />
          <Skeleton className="h-5 w-56" />
        </div>
        <Skeleton className="h-10 w-36" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-40 w-full" />
        ))}
      </div>
    </div>
  );
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("blank");
  const [name, setName] = useState("");
  const [modelName, setModelName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Agent | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchData = () => {
    setLoading(true);
    setFetchError("");
    Promise.all([
      apiGet<Agent[]>("/agents"),
      apiGet<ModelInfo[]>("/models"),
    ])
      .then(([a, m]) => {
        setAgents(a);
        setModels(m);
        if (m.length > 0 && !modelName) setModelName(m[0].id);
      })
      .catch((err) => setFetchError(err.message || "Failed to load agents"))
      .finally(() => setLoading(false));
  };

  const fetchAgents = () => {
    apiGet<Agent[]>("/agents")
      .then(setAgents)
      .catch(() => {});
  };

  useEffect(() => {
    fetchData();
  }, []);

  const applyTemplate = (templateId: string) => {
    setSelectedTemplate(templateId);
    const template = AGENT_TEMPLATES.find((t) => t.id === templateId);
    if (!template) return;

    if (template.defaultName) {
      setName(template.defaultName);
    }
    if (template.recommendedModel && models.some((m) => m.id === template.recommendedModel)) {
      setModelName(template.recommendedModel);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    setError("");
    try {
      await apiPost("/agents", { name: name.trim(), model_name: modelName });
      setName("");
      setShowCreate(false);
      setSelectedTemplate("blank");
      fetchAgents();
      toast.success("Agent created");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create agent");
      toast.error("Failed to create agent");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await apiDelete(`/agents/${deleteTarget.id}`);
      fetchAgents();
      toast.success("Agent deleted");
    } catch {
      toast.error("Failed to delete agent");
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  };

  const handleToggle = async (agent: Agent) => {
    const action = agent.status === "running" ? "stop" : "start";
    try {
      await apiPost(`/agents/${agent.id}/${action}`);
      fetchAgents();
      toast.success(`Agent ${action === "start" ? "started" : "stopped"}`);
    } catch {
      toast.error(`Failed to ${action} agent`);
    }
  };

  if (loading) return <AgentsSkeleton />;

  if (fetchError) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3" role="alert">
        <AlertCircle className="h-8 w-8 text-destructive" />
        <p className="text-sm text-muted-foreground">{fetchError}</p>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
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

          {/* Template selector */}
          <div className="mb-6">
            <label className="mb-2 block text-sm text-muted-foreground">
              Start from a template
            </label>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
              {AGENT_TEMPLATES.map((template) => (
                <button
                  key={template.id}
                  type="button"
                  onClick={() => applyTemplate(template.id)}
                  className={`flex flex-col items-center gap-1.5 rounded-xl border p-3 text-center transition-all hover:border-primary ${
                    selectedTemplate === template.id
                      ? "border-primary bg-primary/5"
                      : "border-border"
                  }`}
                >
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                      selectedTemplate === template.id
                        ? "bg-primary/20 text-primary"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {template.icon}
                  </div>
                  <span className="text-xs font-medium">{template.name}</span>
                </button>
              ))}
            </div>
            {selectedTemplate !== "blank" && (
              <p className="mt-2 text-xs text-muted-foreground">
                {AGENT_TEMPLATES.find((t) => t.id === selectedTemplate)?.description}
              </p>
            )}
          </div>

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
            {error && (
              <p className="text-sm text-destructive" role="alert">{error}</p>
            )}
            <div className="flex gap-2">
              <Button type="submit" loading={creating}>
                Create
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setShowCreate(false);
                  setSelectedTemplate("blank");
                }}
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
                    aria-label={agent.status === "running" ? "Stop agent" : "Start agent"}
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
                  onClick={() => setDeleteTarget(agent)}
                  aria-label={`Delete ${agent.name}`}
                  className="text-red-400 hover:text-red-300"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Agent"
        message={`Are you sure you want to delete "${deleteTarget?.name}"? All conversations will be lost.`}
        confirmLabel="Delete"
        variant="danger"
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
