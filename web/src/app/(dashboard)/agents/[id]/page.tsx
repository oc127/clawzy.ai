"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";
import type { Agent, Conversation, Message } from "@/lib/types";
import { useChat } from "@/hooks/use-chat";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/cn";
import { Bot, Send, Plus, MessageSquare, Play, Square, PanelLeftOpen, PanelLeftClose } from "lucide-react";

export default function AgentDetailPage() {
  const params = useParams();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [showSidebar, setShowSidebar] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, setMessages, isStreaming, error, sendMessage } = useChat({
    agentId,
    conversationId: activeConvId,
    onConversationCreated: (id) => {
      setActiveConvId(id);
      fetchConversations();
    },
  });

  const fetchConversations = () => {
    apiGet<Conversation[]>(`/agents/${agentId}/conversations`)
      .then(setConversations)
      .catch(() => {});
  };

  useEffect(() => {
    Promise.all([
      apiGet<Agent>(`/agents/${agentId}`),
      apiGet<Conversation[]>(`/agents/${agentId}/conversations`),
    ])
      .then(([a, c]) => {
        setAgent(a);
        setConversations(c);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [agentId]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadConversation = async (convId: string) => {
    setActiveConvId(convId);
    setShowSidebar(false);
    try {
      const history = await apiGet<Message[]>(
        `/conversations/${convId}/messages`,
      );
      setMessages(
        history.map((m) => ({
          role: m.role as "user" | "assistant",
          content: m.content,
        })),
      );
    } catch {
      // ignore
    }
  };

  const handleNewConversation = () => {
    setActiveConvId(null);
    setMessages([]);
    setShowSidebar(false);
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input.trim());
    setInput("");
  };

  if (loading) {
    return <p className="text-muted-foreground">Loading agent...</p>;
  }

  if (!agent) {
    return <p className="text-red-400">Agent not found.</p>;
  }

  return (
    <div className="flex h-[calc(100vh-5rem)] md:h-[calc(100vh-4rem)] gap-4">
      {/* Mobile sidebar toggle */}
      <button
        className="fixed bottom-20 right-4 z-20 flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg md:hidden"
        onClick={() => setShowSidebar(!showSidebar)}
      >
        {showSidebar ? (
          <PanelLeftClose className="h-5 w-5" />
        ) : (
          <PanelLeftOpen className="h-5 w-5" />
        )}
      </button>

      {/* Left sidebar: agent info + conversations */}
      <div
        className={cn(
          "w-64 shrink-0 flex-col gap-4",
          showSidebar
            ? "fixed inset-y-0 left-0 z-30 flex bg-background p-4 pt-18 shadow-xl md:relative md:p-0 md:pt-0 md:shadow-none"
            : "hidden md:flex"
        )}
      >
        <Card>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h2 className="font-semibold">{agent.name}</h2>
              <p className="text-xs text-muted-foreground">
                {agent.model_name}
              </p>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2">
            <span
              className={`rounded px-2 py-0.5 text-xs ${
                agent.status === "running"
                  ? "bg-green-500/20 text-green-400"
                  : "bg-yellow-500/20 text-yellow-400"
              }`}
            >
              {agent.status}
            </span>
            {(agent.status === "running" || agent.status === "stopped") && (
              <Button
                variant="ghost"
                size="sm"
                onClick={async () => {
                  const action = agent.status === "running" ? "stop" : "start";
                  try {
                    const updated = await apiPost<Agent>(`/agents/${agentId}/${action}`);
                    setAgent(updated);
                  } catch {
                    // ignore
                  }
                }}
                className={
                  agent.status === "running"
                    ? "h-7 text-yellow-400 hover:text-yellow-300"
                    : "h-7 text-green-400 hover:text-green-300"
                }
              >
                {agent.status === "running" ? (
                  <Square className="h-3 w-3" />
                ) : (
                  <Play className="h-3 w-3" />
                )}
              </Button>
            )}
          </div>
        </Card>

        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Conversations</h3>
          <Button variant="ghost" size="sm" onClick={handleNewConversation}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 space-y-1 overflow-y-auto">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => loadConversation(conv.id)}
              className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors ${
                activeConvId === conv.id
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              }`}
            >
              <MessageSquare className="h-3 w-3 shrink-0" />
              <span className="truncate">{conv.title}</span>
            </button>
          ))}
          {conversations.length === 0 && (
            <p className="px-3 text-xs text-muted-foreground">
              No conversations yet. Send a message to start.
            </p>
          )}
        </div>
      </div>

      {/* Overlay for mobile sidebar */}
      {showSidebar && (
        <div
          className="fixed inset-0 z-20 bg-black/50 md:hidden"
          onClick={() => setShowSidebar(false)}
        />
      )}

      {/* Right: chat area */}
      <div className="flex flex-1 flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto rounded-lg border border-border bg-card p-4">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <Bot className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                <p className="text-muted-foreground">
                  Send a message to start chatting with {agent.name}.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[90%] md:max-w-[75%] rounded-lg px-4 py-2 text-sm ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-accent text-accent-foreground"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <p className="mt-2 text-sm text-red-400">{error}</p>
        )}

        {/* Input */}
        <form onSubmit={handleSend} className="mt-4 flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            disabled={isStreaming}
            className="flex-1"
          />
          <Button type="submit" disabled={isStreaming || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
