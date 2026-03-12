'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { getToken, clearTokens, isLoggedIn } from '@/lib/auth';
import { getProfile, getAgents, createAgent, type Agent, type UserProfile } from '@/lib/api';

const MODELS = [
  { value: 'deepseek-chat', label: 'DeepSeek Chat' },
  { value: 'deepseek-reasoner', label: 'DeepSeek Reasoner' },
  { value: 'qwen-turbo', label: 'Qwen Turbo' },
  { value: 'qwen-plus', label: 'Qwen Plus' },
  { value: 'qwen-max', label: 'Qwen Max' },
];

export default function DashboardPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newModel, setNewModel] = useState('deepseek-chat');
  const [creating, setCreating] = useState(false);

  const loadData = useCallback(async () => {
    const token = getToken();
    if (!token) {
      router.replace('/login');
      return;
    }
    try {
      const [p, a] = await Promise.all([getProfile(token), getAgents(token)]);
      setProfile(p);
      setAgents(a);
    } catch {
      clearTokens();
      router.replace('/login');
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace('/login');
      return;
    }
    loadData();
  }, [router, loadData]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const token = getToken();
    if (!token || !newName.trim()) return;
    setCreating(true);
    try {
      await createAgent(token, newName.trim(), newModel);
      setNewName('');
      setShowCreate(false);
      loadData();
    } catch {
      // ignore
    } finally {
      setCreating(false);
    }
  }

  function handleLogout() {
    clearTokens();
    router.replace('/login');
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-pulse text-gray-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Clawzy.ai</h1>
          <div className="flex items-center gap-4">
            {profile && (
              <div className="text-sm text-gray-600">
                <span className="font-medium">{profile.name}</span>
                <span className="ml-3 px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                  {profile.credit_balance} credits
                </span>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">My Agents</h2>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition"
          >
            + New Agent
          </button>
        </div>

        {/* Create form */}
        {showCreate && (
          <form onSubmit={handleCreate} className="mb-6 p-4 bg-white rounded-xl border border-gray-200">
            <div className="flex gap-3">
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Agent name"
                required
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500"
              />
              <select
                value={newModel}
                onChange={(e) => setNewModel(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500"
              >
                {MODELS.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
              <button
                type="submit"
                disabled={creating}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
              >
                {creating ? 'Creating...' : 'Create'}
              </button>
            </div>
          </form>
        )}

        {/* Agent list */}
        {agents.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
            <p className="text-gray-400 mb-2">No agents yet</p>
            <p className="text-sm text-gray-400">Create your first AI agent to get started</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {agents.map((agent) => (
              <div
                key={agent.id}
                onClick={() => router.push(`/chat?agent=${agent.id}`)}
                className="p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md cursor-pointer transition"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900">{agent.name}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    agent.status === 'running'
                      ? 'bg-green-50 text-green-700'
                      : 'bg-gray-100 text-gray-500'
                  }`}>
                    {agent.status}
                  </span>
                </div>
                <p className="text-sm text-gray-500">{agent.model_name}</p>
                <p className="text-xs text-gray-400 mt-2">
                  Created {new Date(agent.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
