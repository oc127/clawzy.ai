'use client'

import Link from 'next/link'
import type { Agent } from '@/lib/types'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface AgentCardProps {
  agent: Agent
}

export function AgentCard({ agent }: AgentCardProps) {
  const statusVariant = agent.status === 'running' ? 'success' : agent.status === 'error' ? 'error' : 'default'

  return (
    <Link href={`/dashboard/chat/${agent.id}`}>
      <Card className="hover:border-neutral-700 transition-colors cursor-pointer group">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-brand/10 flex items-center justify-center text-brand font-bold text-sm group-hover:bg-brand/20 transition-colors">
              {agent.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h3 className="font-semibold text-neutral-100 group-hover:text-white transition-colors">
                {agent.name}
              </h3>
              <p className="text-xs text-neutral-500 mt-0.5">{agent.model_name}</p>
            </div>
          </div>
          <Badge variant={statusVariant}>{agent.status}</Badge>
        </div>
        {agent.system_prompt && (
          <p className="mt-3 text-xs text-neutral-500 line-clamp-2">
            {agent.system_prompt}
          </p>
        )}
      </Card>
    </Link>
  )
}
