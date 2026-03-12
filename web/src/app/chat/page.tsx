'use client';

import { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { getToken, isLoggedIn } from '@/lib/auth';
import ReactMarkdown from 'react-markdown';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

function ChatContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const agentId = searchParams.get('agent');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [credits, setCredits] = useState<number | null>(null);
  const [connStatus, setConnStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamBuf = useRef('');

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (!isLoggedIn() || !agentId) {
      router.replace('/dashboard');
      return;
    }

    const token = getToken();
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/chat/${agentId}?token=${token}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnStatus('connecting'); // still waiting for 'ready' from backend
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'ready') {
        setConnStatus('connected');
      } else if (data.type === 'stream') {
        streamBuf.current += data.content;
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, content: streamBuf.current };
          } else {
            updated.push({ role: 'assistant', content: streamBuf.current });
          }
          return updated;
        });
      } else if (data.type === 'done') {
        setStreaming(false);
        streamBuf.current = '';
        if (data.usage?.balance !== undefined) {
          setCredits(data.usage.balance);
        }
      } else if (data.type === 'error') {
        setStreaming(false);
        streamBuf.current = '';
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `Error: ${data.message || 'Something went wrong'}` },
        ]);
      }
    };

    ws.onerror = () => {
      setStreaming(false);
      setConnStatus('disconnected');
    };

    ws.onclose = () => {
      setStreaming(false);
      setConnStatus('disconnected');
    };

    return () => {
      ws.close();
    };
  }, [agentId, router]);

  function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || streaming || !wsRef.current || connStatus !== 'connected') return;

    const content = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content }]);
    setStreaming(true);
    streamBuf.current = '';

    wsRef.current.send(JSON.stringify({
      type: 'message',
      content,
    }));
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push('/dashboard')}
            className="text-gray-500 hover:text-gray-700 text-sm"
          >
            &larr; Back
          </button>
          <h1 className="font-semibold text-gray-900">Chat</h1>
          <span className={`ml-2 w-2 h-2 rounded-full inline-block ${
            connStatus === 'connected' ? 'bg-green-500' :
            connStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'
          }`} />
        </div>
        {credits !== null && (
          <span className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded-full font-medium">
            {credits} credits
          </span>
        )}
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-20 text-gray-400">
              <p className="text-lg mb-1">Start a conversation</p>
              <p className="text-sm">Type a message below to begin</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] px-4 py-3 rounded-2xl ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-800'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 px-4 py-3 flex-shrink-0">
        <form onSubmit={sendMessage} className="max-w-3xl mx-auto flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              connStatus === 'connecting' ? 'Connecting to AI agent...' :
              connStatus === 'disconnected' ? 'Disconnected. Refresh to reconnect.' :
              streaming ? 'AI is thinking...' : 'Type your message...'
            }
            disabled={streaming || connStatus !== 'connected'}
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 transition"
          />
          <button
            type="submit"
            disabled={streaming || !input.trim() || connStatus !== 'connected'}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-pulse text-gray-400">Loading chat...</div>
      </div>
    }>
      <ChatContent />
    </Suspense>
  );
}
