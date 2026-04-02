'use client'

import { cn } from '@/lib/cn'
import type { Message } from '@/lib/types'

interface MessageBubbleProps {
  message: Pick<Message, 'role' | 'content'>
  isStreaming?: boolean
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
          isUser
            ? 'bg-brand text-white rounded-br-md'
            : 'bg-neutral-800 text-neutral-200 rounded-bl-md',
          isStreaming && 'animate-pulse',
        )}
      >
        <div className="whitespace-pre-wrap break-words">{message.content}</div>
      </div>
    </div>
  )
}
