"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChatMarkdown } from "@/components/chat-markdown";
import { FileText, Code, X, Download, ChevronRight } from "lucide-react";

export interface Artifact {
  id: string;
  name: string;
  type: "markdown" | "code" | "text";
  content: string;
  language?: string;
}

export function ArtifactsPanel({
  artifacts,
  onClose,
}: {
  artifacts: Artifact[];
  onClose: () => void;
}) {
  const [selected, setSelected] = useState<string | null>(
    artifacts.length > 0 ? artifacts[0].id : null
  );
  const active = artifacts.find((a) => a.id === selected);

  const handleDownload = (artifact: Artifact) => {
    const ext = artifact.type === "code" ? (artifact.language || "txt") : artifact.type === "markdown" ? "md" : "txt";
    const blob = new Blob([artifact.content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${artifact.name}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (artifacts.length === 0) return null;

  return (
    <div className="w-80 shrink-0 flex flex-col rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] shadow-[0_2px_8px_rgba(0,0,0,0.06)] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#ebebeb] dark:border-[#333] px-4 py-3">
        <h3 className="text-sm font-bold text-[#222222] dark:text-white flex items-center gap-2">
          <FileText className="h-4 w-4" />
          Artifacts
          <span className="rounded-full bg-[#f7f7f7] dark:bg-[#262626] px-2 py-0.5 text-xs text-[#717171] dark:text-[#a0a0a0]">
            {artifacts.length}
          </span>
        </h3>
        <Button variant="ghost" size="sm" onClick={onClose} className="h-7 w-7 p-0 rounded-lg text-[#717171] dark:text-[#a0a0a0] hover:bg-[#f7f7f7] dark:hover:bg-[#262626]">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* File list */}
      <div className="border-b border-[#ebebeb] dark:border-[#333] max-h-32 overflow-y-auto">
        {artifacts.map((a) => (
          <button
            key={a.id}
            onClick={() => setSelected(a.id)}
            className={`flex w-full items-center gap-2 px-4 py-2 text-sm transition-colors ${
              selected === a.id
                ? "bg-[#fff0f2] dark:bg-[#ff385c]/10 text-[#ff385c]"
                : "text-[#717171] dark:text-[#a0a0a0] hover:bg-[#f7f7f7] dark:hover:bg-[#262626]"
            }`}
          >
            {a.type === "code" ? <Code className="h-3.5 w-3.5 shrink-0" /> : <FileText className="h-3.5 w-3.5 shrink-0" />}
            <span className="truncate">{a.name}</span>
            <ChevronRight className="h-3 w-3 shrink-0 ml-auto" />
          </button>
        ))}
      </div>

      {/* Content view */}
      <div className="flex-1 overflow-y-auto p-4">
        {active ? (
          <>
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-semibold text-[#717171] dark:text-[#a0a0a0] uppercase">{active.type}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDownload(active)}
                className="h-7 text-xs text-[#717171] dark:text-[#a0a0a0] hover:bg-[#f7f7f7] dark:hover:bg-[#262626] rounded-lg"
              >
                <Download className="h-3 w-3 mr-1" />
                Download
              </Button>
            </div>
            {active.type === "markdown" ? (
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ChatMarkdown content={active.content} />
              </div>
            ) : (
              <pre className="whitespace-pre-wrap text-xs font-mono bg-[#f7f7f7] dark:bg-[#262626] rounded-xl p-3 text-[#222222] dark:text-white border border-[#ebebeb] dark:border-[#333]">
                {active.content}
              </pre>
            )}
          </>
        ) : (
          <p className="text-center text-sm text-[#b0b0b0] dark:text-[#666]">Select an artifact to preview</p>
        )}
      </div>
    </div>
  );
}
