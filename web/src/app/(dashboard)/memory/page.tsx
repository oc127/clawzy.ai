"use client";

import { useEffect, useState } from "react";
import { getMemories, deleteMemory } from "@/lib/api";
import type { Memory } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Brain, Trash2, AlertCircle, RefreshCw } from "lucide-react";

function Skeleton({ className }: { className?: string }) {
  return <div className={`skeleton-shimmer rounded-2xl ${className ?? ""}`} />;
}

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = () => {
    setLoading(true);
    setError("");
    getMemories()
      .then(setMemories)
      .catch((err) => setError(err.message || "Failed to load memories"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
      toast.success("Memory deleted");
    } catch {
      toast.error("Failed to delete memory");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div><Skeleton className="mb-1 h-7 w-24" /><Skeleton className="h-4 w-48" /></div>
        <div className="space-y-3">{[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-16" />)}</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a]" role="alert">
        <AlertCircle className="h-8 w-8 text-[#ff385c]" />
        <p className="text-sm text-[#717171] dark:text-[#a0a0a0]">{error}</p>
        <Button variant="outline" size="sm" onClick={fetchData} className="border-[#dddddd] dark:border-[#444]">
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-[#222222] dark:text-white">Memory</h1>
        <p className="mt-0.5 text-[#717171] dark:text-[#a0a0a0]">
          Facts your agents remember across conversations.
        </p>
      </div>

      {memories.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#dddddd] dark:border-[#444] bg-white dark:bg-[#1a1a1a] py-16 text-center">
          <Brain className="mb-3 h-10 w-10 text-[#b0b0b0] dark:text-[#666]" />
          <p className="text-[#717171] dark:text-[#a0a0a0]">No memories yet. Chat with your agents to build memory.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {memories.map((mem) => (
            <div
              key={mem.id}
              className="flex items-center justify-between rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-4 shadow-[0_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.10)] transition-all"
            >
              <div className="flex items-start gap-3 flex-1 min-w-0">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl icon-gradient-purple shadow-sm mt-0.5">
                  <Brain className="h-4 w-4 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-[#222222] dark:text-white">{mem.fact}</p>
                  <p className="mt-1 text-xs text-[#b0b0b0] dark:text-[#666]">
                    {new Date(mem.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDelete(mem.id)}
                className="shrink-0 text-[#b0b0b0] dark:text-[#666] hover:text-[#ff385c] hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
