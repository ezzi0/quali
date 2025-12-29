'use client'
/* eslint-disable */

import { useEffect, useMemo, useState } from 'react'
import { Layout } from '../../components/Layout'
import { Section } from '../../components/Section'
import { Badge } from '../../components/Badge'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Campaign {
  id: number
  name: string
  platform: string
  objective: string
  status: string
  budget_total?: number
  budget_daily?: number
  spend_total?: number
  created_at: string
}

const fallbackCampaigns: Campaign[] = [
  {
    id: 10,
    name: 'Marina High Intent Q4',
    platform: 'meta',
    objective: 'lead_generation',
    status: 'active',
    budget_total: 50000,
    budget_daily: 1200,
    spend_total: 18400,
    created_at: new Date().toISOString(),
  },
  {
    id: 11,
    name: 'First-Time Buyers',
    platform: 'google',
    objective: 'traffic',
    status: 'paused',
    budget_total: 30000,
    budget_daily: 900,
    spend_total: 12300,
    created_at: new Date().toISOString(),
  },
]

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const fetchCampaigns = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/marketing/campaigns`)
      if (!response.ok) throw new Error('Failed to fetch campaigns')
      const data = await response.json()
      const rows = (data.campaigns || []) as Campaign[]
      setCampaigns(rows.length ? rows : fallbackCampaigns)
    } catch (error) {
      console.error(error)
      setCampaigns(fallbackCampaigns)
    } finally {
      setLoading(false)
    }
  }

  const filtered = useMemo(() => {
    if (filter === 'all') return campaigns
    return campaigns.filter((c) => c.platform === filter)
  }, [campaigns, filter])

  return (
    <Layout title="Marketing Campaigns">
      <Section title="Filters" actions={
        <div className="pill-row">
          {['all', 'meta', 'google', 'tiktok'].map((p) => (
            <button key={p} className="btn secondary" onClick={() => setFilter(p)}>
              {p}
            </button>
          ))}
        </div>
      }>
        <div style={{ color: 'var(--muted)' }}>Track spend, status, and objectives across platforms.</div>
      </Section>

      <Section title="Campaigns">
        {loading ? (
          <div style={{ color: 'var(--muted)' }}>Loading campaigns…</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Platform</th>
                <th>Status</th>
                <th>Budget Daily</th>
                <th>Spend</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td style={{ textTransform: 'capitalize' }}>{c.platform}</td>
                  <td><Badge text={c.status} color={c.status === 'active' ? '#4ade80' : '#94a3b8'} /></td>
                  <td>{c.budget_daily ? `${c.budget_daily.toLocaleString()} AED` : '—'}</td>
                  <td>{c.spend_total ? `${c.spend_total.toLocaleString()} AED` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>
    </Layout>
  )
}
