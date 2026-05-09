"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPatch, ApiError } from "@/lib/api";
import { useLanguage } from "@/context/language-context";
import { toast } from "sonner";
import { Sparkles, AlertCircle, RefreshCw, ChevronDown, ChevronUp, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";

interface PersonalityState {
  personality_type: string;
  preferred_model: string;
}

interface SoulFiles {
  soul_md: string;
  persona_md: string;
  taste_md: string;
}

const PERSONALITY_TYPES = [
  {
    id: "少女",
    label: "少女",
    description:
      "Sweet, cheerful, and energetic. Uses cute expressions and is always eager to help. Speaks with warmth and youthful enthusiasm.",
  },
  {
    id: "御姐",
    label: "御姐",
    description:
      "Mature, elegant, and composed. Speaks with confidence and gentle authority. Calm and reassuring presence.",
  },
  {
    id: "custom",
    label: "Custom",
    description:
      "Define your own personality style with a custom prompt. Full creative control over how Lucy behaves and speaks.",
  },
];

const MODEL_OPTIONS = [
  { value: "deepseek-chat", label: "DeepSeek Chat" },
  { value: "qwen-turbo", label: "Qwen Turbo" },
  { value: "claude-sonnet", label: "Claude Sonnet" },
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini" },
];

function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={`rounded-2xl bg-[#f0f0f0] dark:bg-[#262626] animate-pulse ${className ?? ""}`}
    />
  );
}

export default function PersonalityPage() {
  const { t } = useLanguage();
  const [personalityType, setPersonalityType] = useState("少女");
  const [customPrompt, setCustomPrompt] = useState("");
  const [model, setModel] = useState("deepseek-chat");
  const [soul, setSoul] = useState<SoulFiles>({ soul_md: "", persona_md: "", taste_md: "" });
  const [soulOpen, setSoulOpen] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingPersonality, setSavingPersonality] = useState(false);
  const [savingModel, setSavingModel] = useState(false);
  const [savingCustom, setSavingCustom] = useState(false);
  const [savingSoul, setSavingSoul] = useState(false);
  const [loadingSoul, setLoadingSoul] = useState(false);

  const fetchState = () => {
    setLoading(true);
    setError("");
    apiGet<PersonalityState>("/lucy/state")
      .then((data) => {
        setPersonalityType(data.personality_type || "少女");
        setModel(data.preferred_model || "deepseek-chat");
      })
      .catch((err) => {
        const msg = err.message || "Failed to load personality data";
        setError(msg);
        toast.error(msg);
      })
      .finally(() => setLoading(false));
  };

  const fetchSoul = () => {
    setLoadingSoul(true);
    apiGet<SoulFiles>("/lucy/soul")
      .then(setSoul)
      .catch((err) => {
        toast.error(err instanceof ApiError ? err.detail : "Failed to load soul files");
      })
      .finally(() => setLoadingSoul(false));
  };

  useEffect(() => {
    fetchState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (soulOpen) fetchSoul();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [soulOpen]);

  const handleSelectPersonality = async (type: string) => {
    setSavingPersonality(true);
    try {
      await apiPatch("/lucy/personality", {
        personality_type: type,
        ...(type === "custom" ? { custom_personality_prompt: customPrompt } : {}),
      });
      setPersonalityType(type);
      toast.success("Personality updated");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : "Failed to update personality");
    } finally {
      setSavingPersonality(false);
    }
  };

  const handleSaveCustomPrompt = async () => {
    setSavingCustom(true);
    try {
      await apiPatch("/lucy/personality", {
        personality_type: "custom",
        custom_personality_prompt: customPrompt,
      });
      toast.success("Custom personality saved");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : "Failed to save custom personality");
    } finally {
      setSavingCustom(false);
    }
  };

  const handleModelChange = async (newModel: string) => {
    setSavingModel(true);
    try {
      await apiPatch("/lucy/model", { model_name: newModel });
      setModel(newModel);
      toast.success("Model preference updated");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : "Failed to update model");
    } finally {
      setSavingModel(false);
    }
  };

  const handleSaveSoul = async () => {
    setSavingSoul(true);
    try {
      await apiPatch("/lucy/soul", soul);
      toast.success("Soul files saved");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : "Failed to save soul files");
    } finally {
      setSavingSoul(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="mb-1 h-7 w-32" />
          <Skeleton className="h-4 w-56" />
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
        <Skeleton className="h-24" />
        <Skeleton className="h-16" />
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex h-64 flex-col items-center justify-center gap-3 rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a]"
        role="alert"
      >
        <AlertCircle className="h-8 w-8 text-[#ff385c]" />
        <p className="text-sm text-[#717171] dark:text-[#a0a0a0]">{error}</p>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchState}
          className="border-[#dddddd] dark:border-[#444]"
        >
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-[#ff385c]" />
          <h1 className="text-2xl font-extrabold text-[#222222] dark:text-white">
            Personality
          </h1>
        </div>
        <p className="mt-0.5 text-[#717171] dark:text-[#a0a0a0]">
          Choose Lucy&apos;s personality style and configure her behavior.
        </p>
      </div>

      {/* Personality type selector */}
      <div className="grid gap-4 md:grid-cols-3">
        {PERSONALITY_TYPES.map((pt) => {
          const isActive = personalityType === pt.id;
          return (
            <button
              key={pt.id}
              onClick={() => handleSelectPersonality(pt.id)}
              disabled={savingPersonality}
              className={`group rounded-2xl border p-6 text-left transition-all ${
                isActive
                  ? "border-[#ff385c] bg-[#fff0f2] dark:bg-[#ff385c]/10 shadow-[0_2px_8px_rgba(255,56,92,0.15)]"
                  : "border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] shadow-[0_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.10)] hover:border-[#ff385c]/40"
              }`}
            >
              <div className="mb-3 flex items-center justify-between">
                <span className="text-xl font-bold text-[#222222] dark:text-white">
                  {pt.label}
                </span>
                <div
                  className={`h-5 w-5 rounded-full border-2 transition-colors ${
                    isActive
                      ? "border-[#ff385c] bg-[#ff385c]"
                      : "border-[#d0d0d0] dark:border-[#555]"
                  }`}
                >
                  {isActive && (
                    <svg className="h-full w-full text-white" viewBox="0 0 20 20" fill="currentColor">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
              </div>
              <p className="text-sm text-[#717171] dark:text-[#a0a0a0] leading-relaxed">
                {pt.description}
              </p>
            </button>
          );
        })}
      </div>

      {/* Custom personality editor */}
      {personalityType === "custom" && (
        <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-purple shadow-sm">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <h2 className="text-base font-bold text-[#222222] dark:text-white">
              Custom Personality Prompt
            </h2>
          </div>
          <Textarea
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder="Describe how Lucy should behave, speak, and interact with you..."
            className="mb-4 min-h-[120px]"
          />
          <Button
            onClick={handleSaveCustomPrompt}
            loading={savingCustom}
            className="bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl font-semibold shadow-sm"
          >
            <Save className="mr-2 h-4 w-4" />
            Save Prompt
          </Button>
        </div>
      )}

      {/* Model preference */}
      <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] shadow-[0_2px_8px_rgba(0,0,0,0.06)] p-6">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-teal shadow-sm">
            <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 className="text-base font-bold text-[#222222] dark:text-white">
            Model Preference
          </h2>
        </div>
        <p className="mb-4 text-sm text-[#717171] dark:text-[#a0a0a0]">
          Choose which AI model powers Lucy&apos;s responses.
        </p>
        <div className="flex items-center gap-3">
          <Select
            value={model}
            onChange={(e) => handleModelChange(e.target.value)}
            disabled={savingModel}
            className="max-w-xs"
          >
            {MODEL_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
          {savingModel && (
            <svg className="h-4 w-4 animate-spin text-[#ff385c]" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
        </div>
      </div>

      {/* Advanced: Soul files */}
      <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
        <button
          onClick={() => setSoulOpen(!soulOpen)}
          className="flex w-full items-center justify-between p-6 text-left"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl icon-gradient-orange shadow-sm">
              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <div>
              <h2 className="text-base font-bold text-[#222222] dark:text-white">
                Advanced: Soul Files
              </h2>
              <p className="text-xs text-[#b0b0b0] dark:text-[#666]">
                These control Lucy&apos;s core identity. Edit with care.
              </p>
            </div>
          </div>
          {soulOpen ? (
            <ChevronUp className="h-5 w-5 text-[#717171]" />
          ) : (
            <ChevronDown className="h-5 w-5 text-[#717171]" />
          )}
        </button>

        {soulOpen && (
          <div className="border-t border-[#ebebeb] dark:border-[#333] p-6 space-y-5">
            {loadingSoul ? (
              <div className="space-y-4">
                <Skeleton className="h-32" />
                <Skeleton className="h-32" />
                <Skeleton className="h-32" />
              </div>
            ) : (
              <>
                {(
                  [
                    { key: "soul_md" as const, label: "soul.md", desc: "Lucy's core soul and values" },
                    { key: "persona_md" as const, label: "persona.md", desc: "Lucy's persona and speaking style" },
                    { key: "taste_md" as const, label: "taste.md", desc: "Lucy's preferences and tastes" },
                  ] as const
                ).map(({ key, label, desc }) => (
                  <div key={key} className="space-y-2">
                    <div>
                      <label className="block text-sm font-semibold text-[#222222] dark:text-white">
                        {label}
                      </label>
                      <p className="text-xs text-[#b0b0b0] dark:text-[#666]">{desc}</p>
                    </div>
                    <Textarea
                      value={soul[key]}
                      onChange={(e) =>
                        setSoul((prev) => ({ ...prev, [key]: e.target.value }))
                      }
                      className="min-h-[120px] font-mono text-xs"
                      placeholder={`Content of ${label}...`}
                    />
                  </div>
                ))}

                <Button
                  onClick={handleSaveSoul}
                  loading={savingSoul}
                  className="bg-[#ff385c] hover:bg-[#e31c5f] text-white rounded-xl font-semibold shadow-sm"
                >
                  <Save className="mr-2 h-4 w-4" />
                  Save Soul Files
                </Button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
