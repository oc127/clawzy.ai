'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { getAgent, listConversations, getConversationMessages, createChatWebSocket } from '@/lib/api'
import type { Agent, Conversation, Message, WSResponse } from '@/lib/types'
import { MessageBubble } from '@/components/chat/message-bubble'
import { ChatInput } from '@/components/chat/chat-input'
import { TypingIndicator } from '@/components/chat/typing-indicator'
import { Button } from '@/components/ui/button'

export default function ChatPage() {
  const params = useParams()
  const router = useRouter()
  const agentId = params.agentId as string

  const [agent, setAgent] = useState<Agent | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConvId, setActiveConvId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [streamingContent, setStreamingContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [loading, setLoading] = useState(true)

  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent, scrollToBottom])

  // Load agent and conversations
  useEffect(() => {
    const load = async () => {
      try {
        const [agentData, convData] = await Promise.all([
          getAgent(agentId),
          listConversations(agentId),
        ])
        setAgent(agentData)
        setConversations(convData)
        if (convData.length > 0) {
          setActiveConvId(convData[0].id)
        }
      } catch (err) {
        console.error('Failed to load agent:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [agentId])

  // Load messages when conversation changes
  useEffect(() => {
    if (!activeConvId) return
    const load = async () => {
      try {
        const msgs = await getConversationMessages(activeConvId)
        setMessages(msgs)
      } catch (err) {
        console.error('Failed to load messages:', err)
      }
    }
    load()
  }, [activeConvId])

  // WebSocket connection
  useEffect(() => {
    const ws = createChatWebSocket(agentId)
    if (!ws) return

    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const data: WSResponse = JSON.parse(event.data)

        switch (data.type) {
          case 'stream':
            setIsStreaming(true)
            setStreamingContent((prev) => prev + (data.content || ''))
            break

          case 'done':
            setIsStreaming(false)
            const finalContent = data.content || ''
            setStreamingContent('')
            setMessages((prev) => [
              ...prev,
              {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: finalContent || streamingContent,
                created_at: new Date().toISOString(),
                conversation_id: data.conversation_id || activeConvId || '',
              },
            ])
            // Set conversation if new
            if (data.conversation_id && !activeConvId) {
              setActiveConvId(data.conversation_id)
            }
            break

          case 'error':
            setIsStreaming(false)
            setStreamingContent('')
            console.error('Chat error:', data.message)
            break
        }
      } catch (err) {
        console.error('Failed to parse WS message:', err)
      }
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
    }

    wsRef.current = ws

    return () => {
      ws.close()
      wsRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentId])

  const handleSend = (content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected')
      return
    }

    // Add user message to local state immediately
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
      conversation_id: activeConvId || '',
    }
    setMessages((prev) => [...prev, userMsg])

    // Send via WebSocket
    wsRef.current.send(
      JSON.stringify({
        type: 'message',
        content,
        conversation_id: activeConvId || undefined,
      }),
    )
  }

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Conversation sidebar */}
      <div className="hidden lg:flex lg:w-64 flex-col border-r border-neutral-800 bg-surface-300">
        <div className="p-4 border-b border-neutral-800">
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => {
              setActiveConvId(null)
              setMessages([])
            }}
          >
            + New Chat
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-1">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => setActiveConvId(conv.id)}
              className={`w-full text-left rounded-lg px-3 py-2 text-sm transition-colors truncate ${
                conv.id === activeConvId
                  ? 'bg-brand/10 text-brand'
                  : 'text-neutral-400 hover:bg-neutral-800'
              }`}
            >
              {conv.title || 'Untitled'}
            </button>
          ))}
          {conversations.length === 0 && (
            <p className="text-xs text-neutral-600 text-center py-4">No conversations yet</p>
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Chat header */}
        <div className="flex items-center gap-3 px-6 py-3 border-b border-neutral-800">
          <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')}>
            <BackIcon className="w-4 h-4" />
          </Button>
          {agent && (
            <div>
              <h2 className="font-semibold text-neutral-100">{agent.name}</h2>
              <p className="text-xs text-neutral-500">{agent.model_name}</p>
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-4 space-y-4">
          {messages.length === 0 && !isStreaming && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-2xl bg-brand/10 flex items-center justify-center mb-4">
                <span className="text-2xl font-bold text-brand">
                  {agent?.name.charAt(0).toUpperCase() || 'A'}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-neutral-200 mb-1">
                {agent?.name || 'Agent'}
              </h3>
              <p className="text-sm text-neutral-500 max-w-sm">
                メッセージを送信して会話を始めましょう
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* Streaming message */}
          {isStreaming && streamingContent && (
            <MessageBubble
              message={{ role: 'assistant', content: streamingContent }}
              isStreaming
            />
          )}

          {/* Typing indicator (before any streaming content arrives) */}
          {isStreaming && !streamingContent && <TypingIndicator />}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <ChatInput
          onSend={handleSend}
          disabled={isStreaming}
          placeholder="メッセージを入力..."
        />
      </div>
    </div>
  )
}

function BackIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 19-7-7 7-7" />
      <path d="M19 12H5" />
    </svg>
  )
}
