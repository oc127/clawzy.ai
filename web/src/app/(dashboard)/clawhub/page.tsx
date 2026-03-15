"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getSkills, getTrendingSkills, getSkillCategories } from "@/lib/api";
import type { SkillBrief } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/cn";
import {
  Search,
  TrendingUp,
  Download,
  Star,
  Globe,
  Calculator,
  Code,
  Database,
  Sparkles,
  MessageSquare,
  Monitor,
  Zap,
  Package,
  AlertCircle,
  RefreshCw,
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

const SORT_OPTIONS = [
  { value: "install_count", label: "Most Popular" },
  { value: "newest", label: "Newest" },
  { value: "featured", label: "Featured" },
];

function ClawHubSkeleton() {
  return (
    <div>
      <div className="mb-8">
        <Skeleton className="mb-1 h-8 w-40" />
        <Skeleton className="h-5 w-64" />
      </div>
      <Skeleton className="mb-8 h-10 w-full" />
      <Skeleton className="mb-4 h-6 w-36" />
      <div className="grid gap-4 md:grid-cols-3 mb-8">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-44 w-full" />
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    </div>
  );
}

export default function ClawHubPage() {
  const [trending, setTrending] = useState<SkillBrief[]>([]);
  const [skills, setSkills] = useState<SkillBrief[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("install_count");
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState("");

  const fetchData = () => {
    setLoading(true);
    setFetchError("");
    Promise.all([
      getTrendingSkills(10),
      getSkills(),
      getSkillCategories(),
    ])
      .then(([t, s, c]) => {
        setTrending(t);
        setSkills(s);
        setCategories(c);
      })
      .catch((err) => setFetchError(err.message || "Failed to load ClawHub"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (loading) return;
    getSkills({
      category: activeCategory || undefined,
      search: searchQuery || undefined,
      sort_by: sortBy,
    })
      .then(setSkills)
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeCategory, searchQuery, sortBy]);

  if (loading) return <ClawHubSkeleton />;

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
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-1">
          <Package className="h-7 w-7 text-primary" />
          <h1 className="text-2xl font-bold">ClawHub</h1>
        </div>
        <p className="text-muted-foreground">
          Discover and install skills to supercharge your agents.
        </p>
      </div>

      {/* Search bar */}
      <div className="relative mb-8">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search skills..."
          className="pl-10"
        />
      </div>

      {/* Trending Skills */}
      {!searchQuery && !activeCategory && (
        <section className="mb-10">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Trending Skills</h2>
          </div>

          {/* Top 3 large cards */}
          <div className="grid gap-4 md:grid-cols-3 mb-4">
            {trending.slice(0, 3).map((skill, i) => (
              <Link key={skill.id} href={`/clawhub/${skill.slug}`}>
                <Card className="relative overflow-hidden transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 cursor-pointer h-full">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-sm font-bold text-primary">
                      {i + 1}
                    </span>
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent">
                      <SkillIcon category={skill.category} className="h-4 w-4 text-foreground" />
                    </div>
                  </div>
                  <h3 className="font-semibold mb-1">{skill.name}</h3>
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                    {skill.summary}
                  </p>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Download className="h-3 w-3" />
                      {formatCount(skill.install_count)}
                    </span>
                    <span className="rounded bg-accent px-1.5 py-0.5">
                      {skill.category}
                    </span>
                    {skill.is_featured && (
                      <span className="flex items-center gap-1 text-yellow-400">
                        <Star className="h-3 w-3" /> Featured
                      </span>
                    )}
                  </div>
                </Card>
              </Link>
            ))}
          </div>

          {/* Remaining trending as compact list */}
          {trending.length > 3 && (
            <div className="grid gap-2 md:grid-cols-2">
              {trending.slice(3).map((skill, i) => (
                <Link key={skill.id} href={`/clawhub/${skill.slug}`}>
                  <div className="flex items-center gap-3 rounded-lg border border-border p-3 transition-colors hover:border-primary/30 hover:bg-accent/50 cursor-pointer">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-medium text-muted-foreground">
                      {i + 4}
                    </span>
                    <SkillIcon category={skill.category} className="h-4 w-4 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      <span className="text-sm font-medium">{skill.name}</span>
                    </div>
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Download className="h-3 w-3" />
                      {formatCount(skill.install_count)}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Category tabs */}
      <div className="mb-6 flex items-center gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => setActiveCategory(null)}
          className={cn(
            "shrink-0 rounded-full px-4 py-1.5 text-sm transition-colors",
            !activeCategory
              ? "bg-primary text-primary-foreground"
              : "bg-accent text-muted-foreground hover:text-foreground"
          )}
        >
          All
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={cn(
              "shrink-0 rounded-full px-4 py-1.5 text-sm capitalize transition-colors",
              activeCategory === cat
                ? "bg-primary text-primary-foreground"
                : "bg-accent text-muted-foreground hover:text-foreground"
            )}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Sort bar */}
      <div className="mb-4 flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Sort by:</span>
        {SORT_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setSortBy(opt.value)}
            className={cn(
              "text-sm transition-colors",
              sortBy === opt.value
                ? "text-primary font-medium"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Skills grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {skills.map((skill) => (
          <Link key={skill.id} href={`/clawhub/${skill.slug}`}>
            <Card className="transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 cursor-pointer h-full">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <SkillIcon category={skill.category} className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{skill.name}</h3>
                    {skill.is_featured && (
                      <Star className="h-3.5 w-3.5 text-yellow-400" />
                    )}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                    {skill.summary}
                  </p>
                  <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Download className="h-3 w-3" />
                      {formatCount(skill.install_count)}
                    </span>
                    <span className="rounded bg-accent px-1.5 py-0.5 capitalize">
                      {skill.category}
                    </span>
                    {skill.tags?.slice(0, 2).map((tag) => (
                      <span key={tag} className="rounded bg-accent px-1.5 py-0.5">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>

      {skills.length === 0 && (
        <div className="mt-12 text-center">
          <Package className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
          <p className="text-muted-foreground">
            No skills found. Try a different search or category.
          </p>
        </div>
      )}
    </div>
  );
}

function SkillIcon({ category, className }: { category: string; className?: string }) {
  const Icon = CATEGORY_ICONS[category] || Zap;
  return <Icon className={className} />;
}

function formatCount(n: number): string {
  if (n >= 10000) return `${(n / 1000).toFixed(0)}K`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return String(n);
}
