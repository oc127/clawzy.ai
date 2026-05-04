"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import type { Agent, ModelInfo } from "@/lib/types";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
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
  ChevronUp,
} from "lucide-react";

interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  defaultName: string;
  recommendedModel: string;
  icon: React.ReactNode;
  gradient: string;
}

const AGENT_TEMPLATES: AgentTemplate[] = [
  { id: "blank", name: "Blank", description: "Start from scratch", defaultName: "", recommendedModel: "", icon: <Plus className="h-4 w-4 text-white" />, gradient: "icon-gradient-red" },
  { id: "coder", name: "Coder", description: "Write & debug code", defaultName: "Code Buddy", recommendedModel: "deepseek-chat", icon: <Code className="h-4 w-4 text-white" />, gradient: "icon-gradient-blue" },
  { id: "writer", name: "Writer", description: "Draft & edit content", defaultName: "Writing Pro", recommendedModel: "qwen-max", icon: <FileText className="h-4 w-4 text-white" />, gradient: "icon-gradient-purple" },
  { id: "research", name: "Research", description: "Analyze & summarize", defaultName: "Research Hub", recommendedModel: "deepseek-reasoner", icon: <Globe className="h-4 w-4 text-white" />, gradient: "icon-gradient-teal" },
  { id: "business", name: "Business", description: "Reports & metrics", defaultName: "Biz Analyst", recommendedModel: "qwen-plus", icon: <Briefcase className="h-4 w-4 text-white" />, gradient: "icon-gradient-green" },
];

function Skeleton({ className }: { className?: string }) {
  return <div className={`skeleton-shimmer rounded-2xl ${className ?? ""}`} />;
}

function AgentsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="mb-1 h-7 w-24" />
          <Skeleton className="h-4 w-48" />
        </div>
        <Skeleton className="h-10 w-36" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => <Skeleton key={i} className="h-44" />)}
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
  const [selectedTemplate, setSelectedTemplate] = useState("blank");
  const [name, setName] = useState("");
  const [modelName, setModelName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Agent | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchData = () => {
    setLoading(true);
    setFetchError("");
    Promise.all([apiGet<Agent[]>("/agents"), apiGet<ModelInfo[]>("/models")])
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
      .catch(() => toast.error("Failed to refresh agents"));
  };

  useEffect(() => { fetchData(); }, []);

  const applyTemplate = (templateId: string) => {
    setSelectedTemplate(templateId);
    const tpl = AGENT_TEMPLATES.find((t) => t.id === templateId);
    if (!tpl) return;
    if (tpl.defaultName) setName(tpl.defaultName);
    if (tpl.recommendedModel && models.some((m) => m.id === tpl.recommendedModel))
      setModelName(tpl.recommendedModel);
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
      toast.success("Agent created!");
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
      <div className="flex h-64 flex-col items-center justify-center gap-3 rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a]" role="alert">
        <AlertCircle className="h-8 w-8 text-[#ff385c]" />
        <p className="text-sm text-[#717171] dark:text-[#a0a0a0]">{fetchError}</p>
        <Button variant="outline" size="sm" onClick={fetchData} className="border-[#dddddd] dark:border-[#444]">
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
          <h1 className="text-2xl font-extrabold text-[#222222] dark:text-white">Agents</h1>
          <p className="text-[#717171] dark:text-[#a0a0a0] mt-0.5">Create and manage your AI agents.</p>
        </div>
        <Button
          onClick={() => setShowCreate(!showCreate)}
          className="gap-2 bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl font-semibold shadow-sm"
        >
          {showCreate ? (
            <><ChevronUp className="h-4 w-4" /> Cancel</>
          ) : (
            <><Plus className="h-4 w-4" /> Create Agent</>
          )}
        </Button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-6 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
          <h2 className="mb-5 text-lg font-bold text-[#222222] dark:text-white">New Agent</h2>

          {/* Templates */}
          <div className="mb-6">
            <label className="mb-3 block text-sm font-semibold text-[#717171] dark:text-[#a0a0a0]">
              Choose a template
            </label>
            <div className="grid gap-2 grid-cols-2 sm:grid-cols-5">
              {AGENT_TEMPLATES.map((tpl) => (
                <button
                  key={tpl.id}
                  type="button"
                  onClick={() => applyTemplate(tpl.id)}
                  className={`flex flex-col items-center gap-2 rounded-xl border p-3 text-center transition-all hover:border-[#ff385c] ${
                    selectedTemplate === tpl.id
                      ? "border-[#ff385c] bg-[#fff0f2] dark:bg-[#ff385c]/10"
                      : "border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a]"
                  }`}
                >
                  <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${tpl.gradient} shadow-sm`}>
                    {tpl.icon}
                  </div>
                  <span className="text-xs font-semibold text-[#222222] dark:text-white">{tpl.name}</span>
                  <span className="text-[10px] text-[#717171] dark:text-[#a0a0a0] leading-tight">{tpl.description}</span>
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-semibold text-[#222222] dark:text-white">Agent Name</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="My Assistant" />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-semibold text-[#222222] dark:text-white">Model</label>
              <Select value={modelName} onChange={(e) => setModelName(e.target.value)}>
                {models.map((m) => (
                  <option key={m.id} value={m.id}>{m.name} ({m.provider})</option>
                ))}
              </Select>
            </div>
            {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
            <div className="flex gap-2">
              <Button
                type="submit"
                loading={creating}
                className="bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl font-semibold"
              >
                Create
              </Button>
              <Button
                type="button"
                variant="ghost"
                className="text-[#717171] dark:text-[#a0a0a0] hover:bg-[#f7f7f7] dark:hover:bg-[#262626]"
                onClick={() => { setShowCreate(false); setSelectedTemplate("blank"); }}
              >
                Cancel
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* Agent list */}
      {agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#dddddd] dark:border-[#444] bg-white dark:bg-[#1a1a1a] py-20 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#f7f7f7] dark:bg-[#262626]">
            <Bot className="h-8 w-8 text-[#b0b0b0] dark:text-[#666]" />
          </div>
          <h2 className="mb-1 text-lg font-bold text-[#222222] dark:text-white">No agents yet</h2>
          <p className="mb-6 text-sm text-[#717171] dark:text-[#a0a0a0]">Create your first AI agent to get started.</p>
          <Button
            onClick={() => setShowCreate(true)}
            className="gap-2 bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl font-semibold shadow-sm"
          >
            <Plus className="h-4 w-4" />
            Create Agent
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="flex flex-col justify-between rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-5 shadow-[0_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.10)] transition-all duration-200"
            >
              <div>
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl icon-gradient-red shadow-sm">
                      <Bot className="h-5 w-5 text-white" />
                    </div>
                    <h3 className="font-bold text-[#222222] dark:text-white">{agent.name}</h3>
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                      agent.status === "running"
                        ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400"
                        : "bg-[#f7f7f7] dark:bg-[#262626] text-[#717171] dark:text-[#a0a0a0]"
                    }`}
                  >
                    {agent.status}
                  </span>
                </div>
                <p className="text-sm text-[#717171] dark:text-[#a0a0a0]">{agent.model_name}</p>
                <p className="mt-1 text-xs text-[#b0b0b0] dark:text-[#666]">
                  Created {new Date(agent.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="mt-4 flex gap-2">
                <Link href={`/agents/${agent.id}`} className="flex-1">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full border-[#dddddd] dark:border-[#444] text-[#222222] dark:text-white hover:bg-[#f7f7f7] dark:hover:bg-[#262626] rounded-xl font-semibold"
                  >
                    <MessageSquare className="mr-1.5 h-3.5 w-3.5" />
                    Chat
                  </Button>
                </Link>
                {(agent.status === "running" || agent.status === "stopped") && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggle(agent)}
                    aria-label={agent.status === "running" ? "Stop agent" : "Start agent"}
                    className={`rounded-xl ${
                      agent.status === "running"
                        ? "text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20"
                        : "text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
                    }`}
                  >
                    {agent.status === "running" ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setDeleteTarget(agent)}
                  aria-label={`Delete ${agent.name}`}
                  className="rounded-xl text-[#ff385c] hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
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
