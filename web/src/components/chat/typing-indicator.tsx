'use client'

export function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="bg-neutral-800 rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-neutral-500 animate-bounce [animation-delay:0ms]" />
        <span className="w-2 h-2 rounded-full bg-neutral-500 animate-bounce [animation-delay:150ms]" />
        <span className="w-2 h-2 rounded-full bg-neutral-500 animate-bounce [animation-delay:300ms]" />
      </div>
    </div>
  )
}
