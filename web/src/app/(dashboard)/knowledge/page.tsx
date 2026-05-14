"use client";

import { useEffect, useRef, useState } from "react";
import {
  getKnowledgeBases,
  createKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  getKnowledgeDocuments,
  uploadKnowledgeDocument,
  deleteKnowledgeDocument,
  searchKnowledge,
  exportKnowledgeBase,
} from "@/lib/api";
import type {
  KnowledgeBase,
  KnowledgeDocument,
  KnowledgeSearchResult,
} from "@/lib/types";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  BookOpen,
  FileText,
  Upload,
  Search,
  Plus,
  Trash2,
  ArrowLeft,
  ChevronRight,
  AlertCircle,
  RefreshCw,
  Download,
} from "lucide-react";

function Skeleton({ className }: { className?: string }) {
  return <div className={`skeleton-shimmer rounded-2xl ${className ?? ""}`} />;
}

function formatFileSize(bytes: number): string {
  if (bytes >= 1024 * 1024) {
    return (bytes / 1024 / 1024).toFixed(1) + " MB";
  }
  return (bytes / 1024).toFixed(1) + " KB";
}

const statusColors: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700",
  processing: "bg-blue-100 text-blue-700",
  ready: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

const ACCEPTED_FILE_TYPES =
  ".pdf,.md,.txt,.py,.js,.ts,.tsx,.jsx,.json,.yaml,.yml,.toml,.xml,.sql,.sh,.rb,.php,.swift,.kt,.go,.rs,.c,.cpp,.h,.css,.html";

export default function KnowledgePage() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKb, setSelectedKb] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newKbName, setNewKbName] = useState("");
  const [newKbDescription, setNewKbDescription] = useState("");
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<KnowledgeSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchKnowledgeBases = () => {
    setLoading(true);
    setError("");
    getKnowledgeBases()
      .then(setKnowledgeBases)
      .catch((err) => setError(err.message || "Failed to load knowledge bases"))
      .finally(() => setLoading(false));
  };

  const fetchDocuments = (kbId: string) => {
    setLoading(true);
    setError("");
    getKnowledgeDocuments(kbId)
      .then(setDocuments)
      .catch((err) => setError(err.message || "Failed to load documents"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchKnowledgeBases();
  }, []);

  const handleSelectKb = (kb: KnowledgeBase) => {
    setSelectedKb(kb);
    setDocuments([]);
    fetchDocuments(kb.id);
  };

  const handleBack = () => {
    setSelectedKb(null);
    setDocuments([]);
    setError("");
    fetchKnowledgeBases();
  };

  const handleCreateKb = async () => {
    if (!newKbName.trim()) {
      toast.error("Name is required");
      return;
    }
    try {
      const kb = await createKnowledgeBase({
        name: newKbName.trim(),
        description: newKbDescription.trim() || undefined,
      });
      setKnowledgeBases((prev) => [...prev, kb]);
      setNewKbName("");
      setNewKbDescription("");
      setShowCreateDialog(false);
      toast.success("Knowledge base created");
    } catch {
      toast.error("Failed to create knowledge base");
    }
  };

  const handleDeleteKb = async (id: string) => {
    try {
      await deleteKnowledgeBase(id);
      setKnowledgeBases((prev) => prev.filter((kb) => kb.id !== id));
      toast.success("Knowledge base deleted");
    } catch {
      toast.error("Failed to delete knowledge base");
    }
  };

  const handleToggleActive = async (kb: KnowledgeBase) => {
    try {
      const updated = await updateKnowledgeBase(kb.id, { is_active: !kb.is_active });
      setKnowledgeBases((prev) => prev.map((k) => (k.id === kb.id ? updated : k)));
      toast.success(updated.is_active ? "Knowledge base activated" : "Knowledge base deactivated");
    } catch {
      toast.error("Failed to update knowledge base");
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedKb) return;
    setUploading(true);
    try {
      const doc = await uploadKnowledgeDocument(selectedKb.id, file);
      setDocuments((prev) => [...prev, doc]);
      toast.success("Document uploaded");
    } catch {
      toast.error("Failed to upload document");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!selectedKb) return;
    try {
      await deleteKnowledgeDocument(selectedKb.id, docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      toast.success("Document deleted");
    } catch {
      toast.error("Failed to delete document");
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const results = await searchKnowledge(searchQuery.trim());
      setSearchResults(results);
    } catch {
      toast.error("Search failed");
    } finally {
      setSearching(false);
    }
  };

  // --- Loading state ---
  if (loading && !selectedKb && knowledgeBases.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="mb-1 h-7 w-40" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-10 w-full" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-36" />
          ))}
        </div>
      </div>
    );
  }

  // --- Error state ---
  if (error && !selectedKb && knowledgeBases.length === 0) {
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
          onClick={fetchKnowledgeBases}
          className="border-[#dddddd] dark:border-[#444]"
        >
          <RefreshCw className="mr-2 h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  // --- KB Detail View ---
  if (selectedKb) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBack}
            className="text-[#717171] dark:text-[#a0a0a0] hover:text-[#222222] dark:hover:text-white rounded-xl"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-extrabold text-[#222222] dark:text-white">
              {selectedKb.name}
            </h1>
            {selectedKb.description && (
              <p className="mt-0.5 text-[#717171] dark:text-[#a0a0a0]">
                {selectedKb.description}
              </p>
            )}
          </div>
        </div>

        {/* Upload + Export buttons + hidden input */}
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_FILE_TYPES}
            onChange={handleUpload}
            className="hidden"
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="rounded-xl bg-[#222222] text-white hover:bg-[#444] dark:bg-white dark:text-[#222222] dark:hover:bg-[#e0e0e0]"
          >
            <Upload className="mr-2 h-4 w-4" />
            {uploading ? "Uploading..." : "Upload Document"}
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              exportKnowledgeBase(selectedKb.id).catch(() =>
                toast.error("Failed to export knowledge base")
              );
            }}
            className="rounded-xl border-[#ebebeb] dark:border-[#333]"
          >
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>

        {/* Error in detail view */}
        {error && (
          <div
            className="flex h-32 flex-col items-center justify-center gap-3 rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a]"
            role="alert"
          >
            <AlertCircle className="h-6 w-6 text-[#ff385c]" />
            <p className="text-sm text-[#717171] dark:text-[#a0a0a0]">{error}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchDocuments(selectedKb.id)}
              className="border-[#dddddd] dark:border-[#444]"
            >
              <RefreshCw className="mr-2 h-3.5 w-3.5" />
              Retry
            </Button>
          </div>
        )}

        {/* Loading in detail view */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16" />
            ))}
          </div>
        )}

        {/* Documents list */}
        {!loading && !error && documents.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#dddddd] dark:border-[#444] bg-white dark:bg-[#1a1a1a] py-16 text-center">
            <FileText className="mb-3 h-10 w-10 text-[#b0b0b0] dark:text-[#666]" />
            <p className="text-[#717171] dark:text-[#a0a0a0]">
              No documents yet. Upload a file to get started.
            </p>
          </div>
        )}

        {!loading && !error && documents.length > 0 && (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-4 shadow-[0_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.10)] transition-all"
              >
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl icon-gradient-teal shadow-sm mt-0.5">
                    <FileText className="h-4 w-4 text-white" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-[#222222] dark:text-white truncate">
                      {doc.filename}
                    </p>
                    <div className="mt-1 flex flex-wrap items-center gap-2">
                      <span className="inline-block rounded-md bg-[#f5f5f5] dark:bg-[#2a2a2a] px-2 py-0.5 text-xs text-[#717171] dark:text-[#a0a0a0]">
                        {doc.file_type}
                      </span>
                      <span className="text-xs text-[#b0b0b0] dark:text-[#666]">
                        {formatFileSize(doc.file_size)}
                      </span>
                      <span
                        className={`inline-block rounded-md px-2 py-0.5 text-xs font-medium ${statusColors[doc.status] ?? "bg-gray-100 text-gray-700"}`}
                      >
                        {doc.status}
                      </span>
                    </div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteDocument(doc.id)}
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

  // --- Default View (KB list) ---
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-[#222222] dark:text-white">
            Knowledge Base
          </h1>
          <p className="mt-0.5 text-[#717171] dark:text-[#a0a0a0]">
            Manage knowledge bases and documents for your agents.
          </p>
        </div>
        <Button
          onClick={() => setShowCreateDialog((v) => !v)}
          className="rounded-xl bg-[#222222] text-white hover:bg-[#444] dark:bg-white dark:text-[#222222] dark:hover:bg-[#e0e0e0]"
        >
          <Plus className="mr-2 h-4 w-4" />
          New Knowledge Base
        </Button>
      </div>

      {/* Create KB inline form */}
      {showCreateDialog && (
        <div className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-5 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
          <h2 className="mb-3 text-sm font-semibold text-[#222222] dark:text-white">
            Create Knowledge Base
          </h2>
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Name"
              value={newKbName}
              onChange={(e) => setNewKbName(e.target.value)}
              className="w-full rounded-xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] px-3 py-2 text-sm text-[#222222] dark:text-white placeholder:text-[#b0b0b0] dark:placeholder:text-[#666] outline-none focus:border-[#222222] dark:focus:border-white transition-colors"
            />
            <textarea
              placeholder="Description (optional)"
              value={newKbDescription}
              onChange={(e) => setNewKbDescription(e.target.value)}
              rows={2}
              className="w-full rounded-xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] px-3 py-2 text-sm text-[#222222] dark:text-white placeholder:text-[#b0b0b0] dark:placeholder:text-[#666] outline-none focus:border-[#222222] dark:focus:border-white transition-colors resize-none"
            />
            <div className="flex gap-2">
              <Button
                onClick={handleCreateKb}
                className="rounded-xl bg-[#222222] text-white hover:bg-[#444] dark:bg-white dark:text-[#222222] dark:hover:bg-[#e0e0e0]"
              >
                Create
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setShowCreateDialog(false);
                  setNewKbName("");
                  setNewKbDescription("");
                }}
                className="rounded-xl text-[#717171] dark:text-[#a0a0a0]"
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Search bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#b0b0b0] dark:text-[#666]" />
          <input
            type="text"
            placeholder="Search across all knowledge bases..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="w-full rounded-xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] py-2 pl-10 pr-3 text-sm text-[#222222] dark:text-white placeholder:text-[#b0b0b0] dark:placeholder:text-[#666] outline-none focus:border-[#222222] dark:focus:border-white transition-colors"
          />
        </div>
        <Button
          onClick={handleSearch}
          disabled={searching}
          variant="outline"
          className="rounded-xl border-[#ebebeb] dark:border-[#333]"
        >
          {searching ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Search className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Search results */}
      {searchResults.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-[#222222] dark:text-white">
            Search Results
          </h2>
          {searchResults.map((result, idx) => (
            <div
              key={idx}
              className="rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-4 shadow-[0_2px_8px_rgba(0,0,0,0.06)]"
            >
              <p className="text-sm text-[#222222] dark:text-white">
                {result.content.length > 200
                  ? result.content.slice(0, 200) + "..."
                  : result.content}
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-[#b0b0b0] dark:text-[#666]">
                <span className="inline-block rounded-md bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                  {(result.score * 100).toFixed(0)}% match
                </span>
                <span>Document: {result.document}</span>
                <span>KB: {result.knowledge_base}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* KB grid */}
      {knowledgeBases.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#dddddd] dark:border-[#444] bg-white dark:bg-[#1a1a1a] py-16 text-center">
          <BookOpen className="mb-3 h-10 w-10 text-[#b0b0b0] dark:text-[#666]" />
          <p className="text-[#717171] dark:text-[#a0a0a0]">
            No knowledge bases yet. Create one to get started.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {knowledgeBases.map((kb) => (
            <div
              key={kb.id}
              className="group rounded-2xl border border-[#ebebeb] dark:border-[#333] bg-white dark:bg-[#1a1a1a] p-5 shadow-[0_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.10)] transition-all"
            >
              <div className="flex items-start justify-between">
                <div
                  className="flex items-start gap-3 flex-1 min-w-0 cursor-pointer"
                  onClick={() => handleSelectKb(kb)}
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl icon-gradient-teal shadow-sm">
                    <BookOpen className="h-5 w-5 text-white" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-sm font-semibold text-[#222222] dark:text-white truncate">
                      {kb.name}
                    </h3>
                    {kb.description && (
                      <p className="mt-0.5 text-xs text-[#717171] dark:text-[#a0a0a0] line-clamp-2">
                        {kb.description}
                      </p>
                    )}
                  </div>
                </div>
                <ChevronRight
                  className="h-4 w-4 shrink-0 text-[#b0b0b0] dark:text-[#666] opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer mt-1"
                  onClick={() => handleSelectKb(kb)}
                />
              </div>

              <div className="mt-3 flex items-center gap-3 text-xs text-[#b0b0b0] dark:text-[#666]">
                <span>{kb.document_count} document{kb.document_count !== 1 ? "s" : ""}</span>
                <span>&middot;</span>
                <span>{kb.total_chunks} chunk{kb.total_chunks !== 1 ? "s" : ""}</span>
              </div>

              <div className="mt-3 flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleToggleActive(kb)}
                  className={`rounded-xl text-xs font-medium ${
                    kb.is_active
                      ? "text-green-700 bg-green-100 hover:bg-green-200"
                      : "text-[#b0b0b0] dark:text-[#666] bg-[#f5f5f5] dark:bg-[#2a2a2a] hover:bg-[#eee] dark:hover:bg-[#333]"
                  }`}
                >
                  {kb.is_active ? "Active" : "Inactive"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteKb(kb.id)}
                  className="shrink-0 text-[#b0b0b0] dark:text-[#666] hover:text-[#ff385c] hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
