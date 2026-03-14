"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getSkillBySlug, getSkills, apiGet, installSkill } from "@/lib/api";
import type { Skill, SkillBrief, Agent } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  Download,
  Star,
  User,
  Tag,
  ExternalLink,
  Check,
  ChevronDown,
  Globe,
  Calculator,
  Code,
  Database,
  Sparkles,
  MessageSquare,
  Monitor,
  Zap,
} from "lucide-react";

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  search: Globe,
  productivity: Calculator,
  development: Code,
  data: Database,
  ai: Sparkles,
  communication: MessageSquare,
  browser: Monitor,
};

export default function SkillDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [skill, setSkill] = useState<Skill | null>(null);
  const [related, setRelated] = useState<SkillBrief[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAgentPicker, setShowAgentPicker] = useState(false);
  const [installing, setInstalling] = useState<string | null>(null);
  const [installed, setInstalled] = useState<Set<string>>(new Set());
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    getSkillBySlug(slug)
      .then((s) => {
        setSkill(s);
        // Fetch related skills from same category
        getSkills({ category: s.category, limit: 5 })
          .then((r) => setRelated(r.filter((rs) => rs.slug !== slug)))
          .catch(() => {});
      })
      .catch(() => setError("Skill not found"))
      .finally(() => setLoading(false));

    // Fetch user's agents for install picker
    apiGet<Agent[]>("/agents")
      .then(setAgents)
      .catch(() => {});
  }, [slug]);

  const handleInstall = async (agentId: string) => {
    if (!skill) return;
    setInstalling(agentId);
    try {
      await installSkill(agentId, skill.id);
      setInstalled((prev) => new Set(prev).add(agentId));
    } catch (err: unknown) {
      const detail = err instanceof Error ? err.message : "Failed to install skill";
      setError(detail);
    } finally {
      setInstalling(null);
    }
  };

  if (loading) {
    return <p className="text-muted-foreground">Loading skill...</p>;
  }

  if (!skill) {
    return (
      <div>
        <p className="text-red-400">{error || "Skill not found"}</p>
        <Link href="/clawhub" className="mt-4 inline-block text-sm text-primary hover:underline">
          Back to ClawHub
        </Link>
      </div>
    );
  }

  const Icon = CATEGORY_ICONS[skill.category] || Zap;

  return (
    <div className="mx-auto max-w-4xl">
      {/* Back button */}
      <Link
        href="/clawhub"
        className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to ClawHub
      </Link>

      {/* Header card */}
      <Card className="mb-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Icon className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold">{skill.name}</h1>
                {skill.is_featured && (
                  <span className="flex items-center gap-1 rounded-full bg-yellow-500/10 px-2 py-0.5 text-xs text-yellow-400">
                    <Star className="h-3 w-3" /> Featured
                  </span>
                )}
              </div>
              <p className="mt-1 text-muted-foreground">{skill.summary}</p>

              <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Download className="h-4 w-4" />
                  {skill.install_count.toLocaleString()} installs
                </span>
                {skill.author && (
                  <span className="flex items-center gap-1">
                    <User className="h-4 w-4" />
                    {skill.author}
                  </span>
                )}
                {skill.version && (
                  <span className="flex items-center gap-1">
                    <Tag className="h-4 w-4" />
                    v{skill.version}
                  </span>
                )}
                <span className="rounded bg-accent px-2 py-0.5 text-xs capitalize">
                  {skill.category}
                </span>
              </div>

              {skill.tags && skill.tags.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {skill.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded bg-accent px-2 py-0.5 text-xs text-muted-foreground"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Install button */}
          <div className="relative shrink-0">
            <Button
              onClick={() => setShowAgentPicker(!showAgentPicker)}
              className="gap-2"
            >
              <Download className="h-4 w-4" />
              Install to Agent
              <ChevronDown className="h-3 w-3" />
            </Button>

            {/* Agent picker dropdown */}
            {showAgentPicker && (
              <div className="absolute right-0 top-full z-10 mt-2 w-64 rounded-lg border border-border bg-card shadow-xl">
                <div className="p-2">
                  <p className="px-2 py-1 text-xs font-medium text-muted-foreground">
                    Select an agent
                  </p>
                  {agents.length === 0 ? (
                    <p className="px-2 py-3 text-sm text-muted-foreground">
                      No agents yet.{" "}
                      <Link href="/agents" className="text-primary hover:underline">
                        Create one
                      </Link>
                    </p>
                  ) : (
                    agents.map((agent) => (
                      <button
                        key={agent.id}
                        onClick={() => handleInstall(agent.id)}
                        disabled={installing === agent.id || installed.has(agent.id)}
                        className="flex w-full items-center justify-between rounded-md px-2 py-2 text-sm transition-colors hover:bg-accent disabled:opacity-50"
                      >
                        <span>{agent.name}</span>
                        {installed.has(agent.id) ? (
                          <Check className="h-4 w-4 text-green-400" />
                        ) : installing === agent.id ? (
                          <span className="text-xs text-muted-foreground">Installing...</span>
                        ) : (
                          <Download className="h-3.5 w-3.5 text-muted-foreground" />
                        )}
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>

      {error && (
        <div className="mb-6 rounded-md bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Description (Markdown-like rendering) */}
      <Card className="mb-6">
        <div className="prose prose-invert max-w-none">
          <MarkdownContent content={skill.description} />
        </div>
      </Card>

      {/* ClawHub link */}
      {skill.clawhub_url && (
        <a
          href={skill.clawhub_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mb-6 inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          View on ClawHub <ExternalLink className="h-3 w-3" />
        </a>
      )}

      {/* Related skills */}
      {related.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-4 text-lg font-semibold">Related Skills</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {related.slice(0, 4).map((rs) => {
              const RIcon = CATEGORY_ICONS[rs.category] || Zap;
              return (
                <Link key={rs.id} href={`/clawhub/${rs.slug}`}>
                  <div className="flex items-center gap-3 rounded-lg border border-border p-3 transition-colors hover:border-primary/30 hover:bg-accent/50 cursor-pointer">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <RIcon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium">{rs.name}</p>
                      <p className="text-xs text-muted-foreground line-clamp-1">
                        {rs.summary}
                      </p>
                    </div>
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Download className="h-3 w-3" />
                      {rs.install_count >= 1000
                        ? `${(rs.install_count / 1000).toFixed(1)}K`
                        : rs.install_count}
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}

/**
 * Simple Markdown-like renderer for skill descriptions.
 * Handles headers, bold, lists, and code blocks.
 */
function MarkdownContent({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeLines: string[] = [];
  let key = 0;

  for (const line of lines) {
    if (line.startsWith("```")) {
      if (inCodeBlock) {
        elements.push(
          <pre key={key++} className="my-3 rounded-lg bg-background p-3 text-sm overflow-x-auto">
            <code>{codeLines.join("\n")}</code>
          </pre>
        );
        codeLines = [];
      }
      inCodeBlock = !inCodeBlock;
      continue;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      continue;
    }

    if (line.startsWith("### ")) {
      elements.push(
        <h3 key={key++} className="mt-4 mb-2 text-base font-semibold">
          {line.slice(4)}
        </h3>
      );
    } else if (line.startsWith("## ")) {
      elements.push(
        <h2 key={key++} className="mt-5 mb-2 text-lg font-bold">
          {line.slice(3)}
        </h2>
      );
    } else if (line.startsWith("- ")) {
      elements.push(
        <li key={key++} className="ml-4 text-sm text-muted-foreground list-disc">
          {renderInline(line.slice(2))}
        </li>
      );
    } else if (line.trim() === "") {
      elements.push(<div key={key++} className="h-2" />);
    } else {
      elements.push(
        <p key={key++} className="text-sm text-muted-foreground">
          {renderInline(line)}
        </p>
      );
    }
  }

  return <>{elements}</>;
}

function renderInline(text: string): React.ReactNode {
  // Handle **bold** and `code`
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="text-foreground">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="rounded bg-background px-1.5 py-0.5 text-xs">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}
