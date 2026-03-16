"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { submitSkill, getMySubmissions, getSkillCategories } from "@/lib/api";
import type { SkillSubmission } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  ArrowLeft,
  Upload,
  Clock,
  CheckCircle,
  XCircle,
  Package,
} from "lucide-react";

export default function SubmitSkillPage() {
  const [categories, setCategories] = useState<string[]>([]);
  const [submissions, setSubmissions] = useState<SkillSubmission[]>([]);
  const [loading, setLoading] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [summary, setSummary] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [version, setVersion] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");

  useEffect(() => {
    getSkillCategories()
      .then(setCategories)
      .catch(() => {});
    getMySubmissions()
      .then(setSubmissions)
      .catch(() => {});
  }, []);

  // Auto-generate slug from name
  useEffect(() => {
    if (name && !slug) {
      setSlug(
        name
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "")
      );
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [name]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !slug || !summary || !description || !category) {
      toast.error("Please fill in all required fields");
      return;
    }

    setLoading(true);
    try {
      const tags = tagsInput
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);

      const submission = await submitSkill({
        name,
        slug,
        summary,
        description,
        category,
        tags: tags.length > 0 ? tags : undefined,
        version: version || undefined,
        source_url: sourceUrl || undefined,
      });
      setSubmissions((prev) => [submission, ...prev]);
      toast.success("Skill submitted for review!");
      // Reset form
      setName("");
      setSlug("");
      setSummary("");
      setDescription("");
      setCategory("");
      setTagsInput("");
      setVersion("");
      setSourceUrl("");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to submit skill");
    } finally {
      setLoading(false);
    }
  };

  const statusIcon = (status: string) => {
    if (status === "approved") return <CheckCircle className="h-4 w-4 text-green-400" />;
    if (status === "rejected") return <XCircle className="h-4 w-4 text-red-400" />;
    return <Clock className="h-4 w-4 text-yellow-400" />;
  };

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        href="/clawhub"
        className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to ClawHub
      </Link>

      <div className="flex items-center gap-3 mb-1">
        <Upload className="h-7 w-7 text-primary" />
        <h1 className="text-2xl font-bold">Submit a Skill</h1>
      </div>
      <p className="mb-8 text-muted-foreground">
        Share your skill with the community. Submissions are reviewed before publishing.
      </p>

      {/* Submission Form */}
      <Card className="mb-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium">
                Name <span className="text-red-400">*</span>
              </label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Web Scraper Pro"
                maxLength={200}
                required
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">
                Slug <span className="text-red-400">*</span>
              </label>
              <Input
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="e.g. web-scraper-pro"
                maxLength={100}
                pattern="^[a-z0-9][a-z0-9-]*[a-z0-9]$"
                required
              />
              <p className="mt-0.5 text-xs text-muted-foreground">
                Lowercase letters, numbers, and hyphens only
              </p>
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">
              Category <span className="text-red-400">*</span>
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
              required
            >
              <option value="">Select a category</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">
              Summary <span className="text-red-400">*</span>
            </label>
            <Input
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder="A brief one-line description of what your skill does"
              maxLength={500}
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">
              Description <span className="text-red-400">*</span>
            </label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detailed description of your skill. Supports Markdown formatting."
              rows={8}
              maxLength={10000}
              required
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium">Tags</label>
              <Input
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                placeholder="comma, separated, tags"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Version</label>
              <Input
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="e.g. 1.0.0"
                maxLength={50}
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Source URL</label>
            <Input
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder="e.g. https://github.com/user/my-skill"
              maxLength={500}
            />
          </div>

          <Button type="submit" disabled={loading} className="gap-2">
            <Upload className="h-4 w-4" />
            {loading ? "Submitting..." : "Submit for Review"}
          </Button>
        </form>
      </Card>

      {/* My Submissions */}
      {submissions.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold">My Submissions</h2>
          <div className="space-y-3">
            {submissions.map((sub) => (
              <div
                key={sub.id}
                className="flex items-center justify-between rounded-lg border border-border p-4"
              >
                <div className="flex items-center gap-3">
                  <Package className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">{sub.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {sub.category} &middot; Submitted{" "}
                      {new Date(sub.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {statusIcon(sub.status)}
                  <span className="text-sm capitalize text-muted-foreground">
                    {sub.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
