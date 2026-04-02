'use client'

import { useEffect, useState } from 'react'
import { listAgents, createAgent } from '@/lib/api'
import type { Agent } from '@/lib/types'
import { AgentCard } from '@/components/agent-card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'

export default function DashboardPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newModel, setNewModel] = useState('gpt-4o-mini')
  const [newPrompt, setNewPrompt] = useState('')
  const [creating, setCreating] = useState(false)

  const fetchAgents = async () => {
    try {
      const data = await listAgents()
      setAgents(data)
    } catch (err) {
      console.error('Failed to fetch agents:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAgents()
  }, [])

  const handleCreate = async () => {
    if (!newName.trim()) return
    setCreating(true)
    try {
      await createAgent(newName, newModel, newPrompt || undefined)
      setShowCreate(false)
      setNewName('')
      setNewPrompt('')
      await fetchAgents()
    } catch (err) {
      console.error('Failed to create agent:', err)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">My Agents</h1>
          <p className="text-sm text-neutral-500 mt-1">
            AIエージェントを作成して会話を始めましょう
          </p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? 'Cancel' : '+ 新規作成'}
        </Button>
      </div>

      {/* Create form */}
      {showCreate && (
        <Card className="mb-6 p-6">
          <h2 className="text-lg font-semibold text-neutral-100 mb-4">新しいAgentを作成</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-neutral-400 mb-1.5">Agent Name</label>
              <Input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="My Assistant"
                autoFocus
              />
            </div>
            <div>
              <label className="block text-sm text-neutral-400 mb-1.5">Model</label>
              <select
                value={newModel}
                onChange={(e) => setNewModel(e.target.value)}
                className="flex h-10 w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
              >
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="claude-sonnet">Claude Sonnet</option>
                <option value="claude-haiku">Claude Haiku</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-neutral-400 mb-1.5">System Prompt (optional)</label>
              <textarea
                value={newPrompt}
                onChange={(e) => setNewPrompt(e.target.value)}
                placeholder="You are a helpful assistant..."
                rows={3}
                className="flex w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand resize-none"
              />
            </div>
            <Button onClick={handleCreate} disabled={creating || !newName.trim()}>
              {creating ? '作成中...' : '作成する'}
            </Button>
          </div>
        </Card>
      )}

      {/* Agent list */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-2 border-brand border-t-transparent rounded-full animate-spin" />
        </div>
      ) : agents.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-16 h-16 rounded-2xl bg-neutral-800 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-neutral-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 8V4H8" />
              <rect width="16" height="12" x="4" y="8" rx="2" />
              <path d="m9 15 3-3 3 3" />
            </svg>
          </div>
          <p className="text-neutral-500 mb-4">まだAgentがありません</p>
          <Button onClick={() => setShowCreate(true)}>最初のAgentを作成</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}
    </div>
  )
}
