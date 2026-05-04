"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { getSkills, getTrendingSkills, getSkillCategories, getSkillTags } from "@/lib/api";
import type { SkillBrief } from "@/lib/types";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import { CATEGORY_ICONS } from "@/lib/skill-icons";
import { toast } from "sonner";
import {
  Search,
  TrendingUp,
  Download,
  Star,
  Zap,
  Package,
  AlertCircle,
  RefreshCw,
  ShieldCheck,
  ShieldAlert,
  Plus,
  X,
} from "lucide-react";

const SORT_OPTIONS = [
  { value: "install_count", label: "Most Popular" },
  { value: "rating", label: "Top Rated" },
  { value: "newest", label: "Newest" },
  { value: "featured", label: "Featured" },
];

function SkeletonEl({ className }: { className?: string }) {
  return <div className={`skeleton-shimmer rounded-2xl ${className ?? ""}`} />;
}

function ClawHubSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div><SkeletonEl className="mb-1 h-7 w-40" /><SkeletonEl className="h-4 w-64" /></div>
        <SkeletonEl className="h-10 w-32" />
      </div>
      <SkeletonEl className="h-11 w-full" />
      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => <SkeletonEl key={i} className="h-44" />)}
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map((i) => <SkeletonEl key={i} className="h-32" />)}
      </div>
    </div>
  );
}

function StarRating({ rating, count }: { rating: number; count: number }) {
  if (count === 0) return null;
  return (
    <span className="flex items-center gap-1 text-xs text-amber-500">
      <Star className="h-3 w-3 fill-current" />
      {rating.toFixed(1)}
      <span className="text-[#b0b0b0] dark:text-[#666]">({count})</span>
    </span>
  );
}

export default function ClawHubPage() {
  const [trending, setTrending] = useState<SkillBrief[]>([]);
  const [skills, setSkills] = useState<SkillBrief[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("install_count");
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState("");
  const [showTagFilter, setShowTagFilter] = useState(false);

  const fetchData = () => {
    setLoading(true);
    setFetchError("");
    Promise.all([
      getTrendingSkills(10),
      getSkills(),
      getSkillCategories(),
      getSkillTags(),
    ])
      .then(([t, s, c, tags]) => {
        setTrending(t);
        setSkills(s);
        setCategories(c);
        setAllTags(tags);
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
      tag: activeTag || undefined,
    })
      .then(setSkills)
      .catch(() => toast.error("Failed to load skills"));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeCategory, searchQuery, sortBy, activeTag]);

  if (loading) return <ClawHubSkeleton />;

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
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl icon-gradient-purple shadow-sm">
              <Package className="h-4 w-4 text-white" />
            </div>
            <h1 className="text-2xl font-extrabold text-[#222222] dark:text-white">ClawHub</h1>
          </div>
          <p className="text-[#717171] dark:text-[#a0a0a0] ml-12">
            Discover and install skills to supercharge your agents.
          </p>
        </div>
        <Link href="/clawhub/submit">
          <Button variant="outline" className="gap-2 border-[#dddddd] dark:border-[#444] text-[#222222] dark:text-white hover:bg-[#f7f7f7] dark:hover:bg-[#262626] rounded-xl font-semibold">
            <Plus className="h-4 w-4" />
            Submit Skill
          </Button>
        </Link>
      </div>

      {/* Search bar */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#b0b0b0] dark:text-[#666]" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search skills..."
          className="pl-11 h-12 rounded-2xl border-[#dddddd] dark:border-[#444] text-base"
        />
      </div>

      {/* Tag filter */}
      {allTags.length > 0 && (
        <div>
          <button
            onClick={() => setShowTagFilter(!showTagFilter)}
            className="mb-2 flex items-center gap-1 text-sm text-[#717171] dark:text-[#a0a0a0] hover:text-[#222222] dark:hover:text-white font-medium transition-colors"
          >
            Filter by tag {showTagFilter ? "▾" : "▸"}
            {activeTag && (
              <span className="ml-2 flex items-center gap-1 rounded-full bg-[#fff0f2] dark:bg-[#ff385c]/10 border border-[#ff385c]/20 px-2 py-0.5 text-xs text-[#ff385c]">
                {activeTag}
                <X className="h-3 w-3 cursor-pointer" onClick={(e) => { e.stopPropagation(); setActiveTag(null); }} />
              </span>
            )}
          </button>
          {showTagFilter && (
            <div className="flex flex-wrap gap-1.5">
              {allTags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => setActiveTag(activeTag === tag ? null : tag)}
                  className={cn(
                    "rounded-full px-3 py-1 text-xs font-medium transition-colors border",
                    activeTag === tag
                      ? "bg-[#ff385c] text-white border-[#ff385c]"
                      : "bg-white dark:bg-[#1a1a1a] border-[#ebebeb] dark:border-[#333] text-[#717171] dark:text-[#a0a0a0] hover:text-[#222222] dark:hover:text-white hover:border-[#dddddd] dark:hover:border-[#444]"
                  )}
                >
                  {tag}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Trending Skills */}
      {!searchQuery && !activeCategory && !activeTag && (
        <section>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-5 w-5 text-[#ff385c]" />
            <h2 className="text-lg font-bold text-[#222222] dark:text-white">Trending Skills</h2>
          </div>

          <div className="grid gap-4 md:grid-cols-3 mb-4">
            {trending.slice(0, 3).map((skill, i) => (
              <Link key={skill.id} href={`/clawhub/${skill.slug}`}>
                <div className="flex flex-col rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-5 shadow-[0_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.10)] hover:-translate-y-0.5 transition-all duration-200 cursor-pointer h-full">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full icon-gradient-red text-sm font-bold text-white shadow-sm">
                      {i + 1}
                    </span>
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl icon-gradient-purple shadow-sm">
                      <SkillIcon category={skill.category} className="h-4 w-4 text-white" />
                    </div>
                  </div>
                  <h3 className="font-bold text-[#222222] dark:text-white mb-1 flex items-center gap-1.5">
                    {skill.name}
                    <SecurityBadge status={skill.security_status} />
                  </h3>
                  <p className="text-sm text-[#717171] dark:text-[#a0a0a0] line-clamp-2 mb-3 flex-1">{skill.summary}</p>
                  <div className="flex items-center gap-3 text-xs text-[#717171] dark:text-[#a0a0a0]">
                    <span className="flex items-center gap-1"><Download className="h-3 w-3" />{formatCount(skill.install_count)}</span>
                    <StarRating rating={skill.avg_rating} count={skill.review_count} />
                    <span className="rounded-full bg-[#f7f7f7] dark:bg-[#262626] border border-[#ebebeb] dark:border-[#333] px-2 py-0.5 capitalize">{skill.category}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {trending.length > 3 && (
            <div className="grid gap-2 md:grid-cols-2">
              {trending.slice(3).map((skill, i) => (
                <Link key={skill.id} href={`/clawhub/${skill.slug}`}>
                  <div className="flex items-center gap-3 rounded-xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-3 hover:border-[#dddddd] dark:hover:border-[#444] hover:bg-[#f7f7f7] dark:hover:bg-[#262626] transition-colors cursor-pointer">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#f7f7f7] dark:bg-[#262626] text-xs font-semibold text-[#717171] dark:text-[#a0a0a0]">{i + 4}</span>
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg icon-gradient-purple shadow-sm">
                      <SkillIcon category={skill.category} className="h-3.5 w-3.5 text-white" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <span className="text-sm font-semibold text-[#222222] dark:text-white">{skill.name}</span>
                    </div>
                    <StarRating rating={skill.avg_rating} count={skill.review_count} />
                    <span className="flex items-center gap-1 text-xs text-[#b0b0b0] dark:text-[#666]">
                      <Download className="h-3 w-3" />{formatCount(skill.install_count)}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Category tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {["All", ...categories].map((cat) => {
          const isAll = cat === "All";
          const isActive = isAll ? !activeCategory : activeCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(isAll ? null : cat)}
              className={cn(
                "shrink-0 rounded-full px-4 py-1.5 text-sm font-medium capitalize transition-all border",
                isActive
                  ? "bg-[#ff385c] text-white border-[#ff385c] shadow-sm"
                  : "bg-white dark:bg-[#1a1a1a] border-[#ebebeb] dark:border-[#333] text-[#717171] dark:text-[#a0a0a0] hover:text-[#222222] dark:hover:text-white hover:border-[#dddddd] dark:hover:border-[#444]"
              )}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Sort bar */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-[#717171] dark:text-[#a0a0a0] font-medium">Sort:</span>
        {SORT_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setSortBy(opt.value)}
            className={cn(
              "text-sm font-medium transition-colors",
              sortBy === opt.value ? "text-[#ff385c]" : "text-[#b0b0b0] dark:text-[#666] hover:text-[#717171] dark:hover:text-[#a0a0a0]"
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
            <div className="flex flex-col rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-5 shadow-[0_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.10)] hover:-translate-y-0.5 transition-all duration-200 cursor-pointer h-full">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl icon-gradient-purple shadow-sm">
                  <SkillIcon category={skill.category} className="h-5 w-5 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <h3 className="font-bold text-[#222222] dark:text-white">{skill.name}</h3>
                    {skill.is_featured && <Star className="h-3.5 w-3.5 text-amber-500 fill-current" />}
                    <SecurityBadge status={skill.security_status} />
                  </div>
                  <p className="mt-1 text-sm text-[#717171] dark:text-[#a0a0a0] line-clamp-2">{skill.summary}</p>
                  <div className="mt-3 flex items-center gap-2 flex-wrap text-xs text-[#b0b0b0] dark:text-[#666]">
                    <span className="flex items-center gap-1"><Download className="h-3 w-3" />{formatCount(skill.install_count)}</span>
                    <StarRating rating={skill.avg_rating} count={skill.review_count} />
                    <span className="rounded-full bg-[#f7f7f7] dark:bg-[#262626] border border-[#ebebeb] dark:border-[#333] px-2 py-0.5 capitalize text-[#717171] dark:text-[#a0a0a0]">{skill.category}</span>
                    {skill.tags?.slice(0, 2).map((tag) => (
                      <span key={tag} className="rounded-full bg-[#f7f7f7] dark:bg-[#262626] border border-[#ebebeb] dark:border-[#333] px-2 py-0.5 text-[#717171] dark:text-[#a0a0a0]">{tag}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {skills.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#dddddd] dark:border-[#444] bg-white dark:bg-[#1a1a1a] py-16 text-center">
          <Package className="mx-auto mb-3 h-10 w-10 text-[#b0b0b0] dark:text-[#666]" />
          <p className="text-[#717171] dark:text-[#a0a0a0]">No skills found. Try a different search or category.</p>
        </div>
      )}
    </div>
  );
}

function SkillIcon({ category, className }: { category: string; className?: string }) {
  const Icon = (CATEGORY_ICONS as Record<string, React.ComponentType<{ className?: string }>>)[category] || Zap;
  return <Icon className={className} />;
}

function formatCount(n: number): string {
  if (n >= 10000) return `${(n / 1000).toFixed(0)}K`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return String(n);
}

function SecurityBadge({ status }: { status: string }) {
  if (status === "verified") {
    return (
      <span className="flex items-center gap-0.5 text-emerald-500" title="Security verified">
        <ShieldCheck className="h-3 w-3" />
      </span>
    );
  }
  if (status === "warning") {
    return (
      <span className="flex items-center gap-0.5 text-amber-500" title="Security warning — use with caution">
        <ShieldAlert className="h-3 w-3" />
      </span>
    );
  }
  return null;
}
