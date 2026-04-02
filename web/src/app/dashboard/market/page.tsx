'use client'

import { useEffect, useState } from 'react'
import { listTemplates } from '@/lib/api'
import type { MarketTemplate } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function MarketPage() {
  const [templates, setTemplates] = useState<MarketTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const data = await listTemplates()
        setTemplates(data)
      } catch (err) {
        console.error('Failed to load templates:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const filtered = templates.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.description.toLowerCase().includes(search.toLowerCase()) ||
      t.category.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Market</h1>
        <p className="text-sm text-neutral-500 mt-1">
          テンプレートを使ってすぐにAgentを作成できます
        </p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="テンプレートを検索..."
          className="max-w-md"
        />
      </div>

      {/* Templates grid */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-2 border-brand border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-neutral-500">
            {search ? 'テンプレートが見つかりません' : 'テンプレートがありません'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((template) => (
            <Card key={template.id} className="hover:border-neutral-700 transition-colors">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-base">{template.name}</CardTitle>
                  <Badge>{template.category}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="line-clamp-2 mb-3">{template.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-neutral-600">{template.model_name}</span>
                  <Button size="sm">使用する</Button>
                </div>
                {template.tags && template.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-3">
                    {template.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-500"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
