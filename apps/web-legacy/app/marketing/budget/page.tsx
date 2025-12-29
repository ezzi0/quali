'use client'
/* eslint-disable */

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Layout } from '../../components/Layout'
import { Section } from '../../components/Section'
import { Badge } from '../../components/Badge'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Campaign {
  id: number
  name: string
}

interface BudgetRecommendation {
  ad_set_id: number
  name: string
  current_budget: number
  recommended_budget: number
  change_amount: number
  change_pct: number
  rationale: string
  confidence: number
}

const fallbackRecs: BudgetRecommendation[] = [
  {
    ad_set_id: 1,
    name: 'High Intent - Marina',
    current_budget: 800,
    recommended_budget: 1040,
    change_amount: 240,
    change_pct: 0.3,
    rationale: 'Higher CVR with stable CPA',
    confidence: 0.78,
  },
]

function BudgetContent() {
  const searchParams = useSearchParams()
  const campaignIdParam = searchParams.get('campaign_id')

  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [selectedCampaignId, setSelectedCampaignId] = useState<number | null>(
    campaignIdParam ? parseInt(campaignIdParam) : null
  )
  const [recommendations, setRecommendations] = useState<BudgetRecommendation[]>([])
  const [loading, setLoading] = useState(false)
  const [optimizing, setOptimizing] = useState(false)
  const [applying, setApplying] = useState(false)

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const fetchCampaigns = async () => {
    try {
      const response = await fetch(`${API_BASE}/marketing/campaigns`)
      const data = await response.json()
      setCampaigns(data.campaigns || [])
    } catch (error) {
      console.error('Failed to fetch campaigns:', error)
      setCampaigns([{ id: 10, name: 'Marina High Intent Q4' }])
    }
  }

  const optimizeBudget = async () => {
    if (!selectedCampaignId) {
      alert('Please select a campaign first')
      return
    }

    try {
      setOptimizing(true)
      setLoading(true)
      const response = await fetch(`${API_BASE}/marketing/budget/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_id: selectedCampaignId,
          lookback_days: 7,
          volatility_cap: 0.2,
          auto_apply: false,
        }),
      })
      const data = await response.json()

      if (data.recommendations) {
        setRecommendations(data.recommendations.length ? data.recommendations : fallbackRecs)
      }
    } catch (error) {
      console.error('Failed to optimize budget:', error)
      setRecommendations(fallbackRecs)
    } finally {
      setOptimizing(false)
      setLoading(false)
    }
  }

  const applyRecommendations = async () => {
    if (!selectedCampaignId || recommendations.length === 0) return
    if (!confirm(`Apply ${recommendations.length} budget changes?`)) return

    try {
      setApplying(true)
      const response = await fetch(`${API_BASE}/marketing/budget/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_id: selectedCampaignId,
          lookback_days: 7,
          volatility_cap: 0.2,
          auto_apply: true,
        }),
      })
      const data = await response.json()

      if (data.applied > 0) {
        alert(`Successfully applied ${data.applied} budget changes!`)
        setRecommendations([])
      }
    } catch (error) {
      console.error('Failed to apply recommendations:', error)
      alert('Apply failed. Check logs.')
    } finally {
      setApplying(false)
    }
  }

  return (
    <Layout title="Budget Optimizer">
      <Section title="Campaign Selection" actions={
        <button className="btn" onClick={optimizeBudget} disabled={optimizing}>
          {optimizing ? 'Optimizing…' : 'Optimize'}
        </button>
      }>
        <div className="input-row">
          <select
            className="input"
            value={selectedCampaignId || ''}
            onChange={(e) => setSelectedCampaignId(Number(e.target.value))}
          >
            <option value="">Select campaign</option>
            {campaigns.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <button className="btn secondary" onClick={applyRecommendations} disabled={applying || recommendations.length === 0}>
            {applying ? 'Applying…' : 'Apply Changes'}
          </button>
        </div>
      </Section>

      <Section title="Recommendations">
        {loading ? (
          <div style={{ color: 'var(--muted)' }}>Running optimizer…</div>
        ) : recommendations.length === 0 ? (
          <div style={{ color: 'var(--muted)' }}>No recommendations yet</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Ad Set</th>
                <th>Current</th>
                <th>Recommended</th>
                <th>Change</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {recommendations.map((r) => (
                <tr key={r.ad_set_id}>
                  <td>{r.name}</td>
                  <td>{r.current_budget.toLocaleString()} AED</td>
                  <td>{r.recommended_budget.toLocaleString()} AED</td>
                  <td>{(r.change_pct * 100).toFixed(1)}%</td>
                  <td><Badge text={`${Math.round(r.confidence * 100)}%`} color="#6ee7ff" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>
    </Layout>
  )
}

export default function BudgetOptimizerPage() {
  return (
    <Suspense fallback={<div style={{ padding: '2rem' }}>Loading…</div>}>
      <BudgetContent />
    </Suspense>
  )
}
