"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getSkillBySlug,
  getSkillRecommendations,
  getSkillReviews,
  getMyReview,
  createReview,
  updateReview,
  deleteReview,
  apiGet,
  installSkill,
} from "@/lib/api";
import type { Skill, SkillBrief, SkillReview, Agent } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { CATEGORY_ICONS } from "@/lib/skill-icons";
import { toast } from "sonner";
import {
  ArrowLeft,
  Download,
  Star,
  User,
  Tag,
  ExternalLink,
  Check,
  ChevronDown,
  Zap,
  MessageSquare,
  Trash2,
  Edit3,
} from "lucide-react";

export default function SkillDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [skill, setSkill] = useState<Skill | null>(null);
  const [recommended, setRecommended] = useState<SkillBrief[]>([]);
  const [reviews, setReviews] = useState<SkillReview[]>([]);
  const [myReview, setMyReview] = useState<SkillReview | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAgentPicker, setShowAgentPicker] = useState(false);
  const [installing, setInstalling] = useState<string | null>(null);
  const [installed, setInstalled] = useState<Set<string>>(new Set());
  const [error, setError] = useState("");

  // Review form
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewTitle, setReviewTitle] = useState("");
  const [reviewContent, setReviewContent] = useState("");
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [editingReview, setEditingReview] = useState(false);

  useEffect(() => {
    setLoading(true);
    getSkillBySlug(slug)
      .then((s) => {
        setSkill(s);
        // Fetch recommendations instead of basic related
        getSkillRecommendations(slug, 6)
          .then(setRecommended)
          .catch(() => {});
        // Fetch reviews
        getSkillReviews(slug)
          .then(setReviews)
          .catch(() => {});
        // Check for my review
        getMyReview(slug)
          .then(setMyReview)
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
      toast.success(`Installed ${skill.name}`);
    } catch (err: unknown) {
      const detail = err instanceof Error ? err.message : "Failed to install skill";
      toast.error(detail);
    } finally {
      setInstalling(null);
    }
  };

  const handleSubmitReview = async () => {
    setReviewSubmitting(true);
    try {
      if (editingReview && myReview) {
        const updated = await updateReview(slug, {
          rating: reviewRating,
          title: reviewTitle || undefined,
          content: reviewContent || undefined,
        });
        setMyReview(updated);
        setReviews((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
        toast.success("Review updated");
      } else {
        const created = await createReview(slug, {
          rating: reviewRating,
          title: reviewTitle || undefined,
          content: reviewContent || undefined,
        });
        setMyReview(created);
        setReviews((prev) => [created, ...prev]);
        toast.success("Review submitted");
      }
      setShowReviewForm(false);
      setEditingReview(false);
      // Refresh skill to get updated rating
      getSkillBySlug(slug).then(setSkill).catch(() => {});
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to submit review");
    } finally {
      setReviewSubmitting(false);
    }
  };

  const handleDeleteReview = async () => {
    try {
      await deleteReview(slug);
      setReviews((prev) => prev.filter((r) => r.id !== myReview?.id));
      setMyReview(null);
      toast.success("Review deleted");
      getSkillBySlug(slug).then(setSkill).catch(() => {});
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to delete review");
    }
  };

  const startEditReview = () => {
    if (!myReview) return;
    setReviewRating(myReview.rating);
    setReviewTitle(myReview.title || "");
    setReviewContent(myReview.content || "");
    setEditingReview(true);
    setShowReviewForm(true);
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl space-y-6">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
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
                {skill.review_count > 0 && (
                  <span className="flex items-center gap-1 text-yellow-400">
                    <Star className="h-4 w-4 fill-current" />
                    {skill.avg_rating.toFixed(1)}
                    <span className="text-muted-foreground">({skill.review_count} reviews)</span>
                  </span>
                )}
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
                    <Link
                      key={tag}
                      href={`/clawhub?tag=${encodeURIComponent(tag)}`}
                      className="rounded bg-accent px-2 py-0.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {tag}
                    </Link>
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

      {/* Description */}
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

      {/* Reviews Section */}
      <section className="mt-8 mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">
              Reviews {skill.review_count > 0 && `(${skill.review_count})`}
            </h2>
          </div>
          {!myReview && !showReviewForm && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setShowReviewForm(true);
                setEditingReview(false);
                setReviewRating(5);
                setReviewTitle("");
                setReviewContent("");
              }}
            >
              Write a Review
            </Button>
          )}
        </div>

        {/* Review form */}
        {showReviewForm && (
          <Card className="mb-6">
            <h3 className="font-medium mb-3">
              {editingReview ? "Edit Your Review" : "Write a Review"}
            </h3>
            <div className="space-y-3">
              {/* Star selector */}
              <div>
                <label className="mb-1 block text-sm text-muted-foreground">Rating</label>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setReviewRating(star)}
                      className="transition-colors"
                    >
                      <Star
                        className={`h-6 w-6 ${
                          star <= reviewRating
                            ? "text-yellow-400 fill-current"
                            : "text-muted-foreground"
                        }`}
                      />
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm text-muted-foreground">
                  Title (optional)
                </label>
                <Input
                  value={reviewTitle}
                  onChange={(e) => setReviewTitle(e.target.value)}
                  placeholder="Summarize your experience"
                  maxLength={200}
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-muted-foreground">
                  Review (optional)
                </label>
                <Textarea
                  value={reviewContent}
                  onChange={(e) => setReviewContent(e.target.value)}
                  placeholder="Share your experience with this skill..."
                  rows={3}
                  maxLength={2000}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleSubmitReview}
                  disabled={reviewSubmitting}
                  size="sm"
                >
                  {reviewSubmitting
                    ? "Submitting..."
                    : editingReview
                      ? "Update Review"
                      : "Submit Review"}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setShowReviewForm(false);
                    setEditingReview(false);
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* My review highlight */}
        {myReview && !showReviewForm && (
          <Card className="mb-4 border-primary/30">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium">Your Review</span>
                  <div className="flex">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`h-3.5 w-3.5 ${
                          star <= myReview.rating
                            ? "text-yellow-400 fill-current"
                            : "text-muted-foreground"
                        }`}
                      />
                    ))}
                  </div>
                </div>
                {myReview.title && (
                  <p className="text-sm font-medium">{myReview.title}</p>
                )}
                {myReview.content && (
                  <p className="mt-1 text-sm text-muted-foreground">{myReview.content}</p>
                )}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={startEditReview}
                  className="rounded p-1 text-muted-foreground hover:text-foreground"
                  title="Edit review"
                >
                  <Edit3 className="h-4 w-4" />
                </button>
                <button
                  onClick={handleDeleteReview}
                  className="rounded p-1 text-muted-foreground hover:text-red-400"
                  title="Delete review"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </Card>
        )}

        {/* Other reviews */}
        {reviews.filter((r) => r.id !== myReview?.id).length > 0 ? (
          <div className="space-y-3">
            {reviews
              .filter((r) => r.id !== myReview?.id)
              .map((review) => (
                <div
                  key={review.id}
                  className="rounded-lg border border-border p-4"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium">
                      {review.user.name || "Anonymous"}
                    </span>
                    <div className="flex">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <Star
                          key={star}
                          className={`h-3 w-3 ${
                            star <= review.rating
                              ? "text-yellow-400 fill-current"
                              : "text-muted-foreground"
                          }`}
                        />
                      ))}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {new Date(review.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {review.title && (
                    <p className="text-sm font-medium">{review.title}</p>
                  )}
                  {review.content && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {review.content}
                    </p>
                  )}
                </div>
              ))}
          </div>
        ) : (
          !myReview && (
            <p className="text-sm text-muted-foreground">
              No reviews yet. Be the first to review this skill!
            </p>
          )
        )}
      </section>

      {/* Recommended skills */}
      {recommended.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-4 text-lg font-semibold">Recommended Skills</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {recommended.slice(0, 6).map((rs) => {
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
                    <div className="flex flex-col items-end gap-1">
                      {rs.review_count > 0 && (
                        <span className="flex items-center gap-0.5 text-xs text-yellow-400">
                          <Star className="h-3 w-3 fill-current" />
                          {rs.avg_rating.toFixed(1)}
                        </span>
                      )}
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Download className="h-3 w-3" />
                        {rs.install_count >= 1000
                          ? `${(rs.install_count / 1000).toFixed(1)}K`
                          : rs.install_count}
                      </span>
                    </div>
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
