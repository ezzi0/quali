'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'

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

export default function BudgetOptimizerPage() {
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
          volatility_cap: 0.20,
          auto_apply: false
        })
      })
      const data = await response.json()
      
      if (data.recommendations) {
        setRecommendations(data.recommendations)
        if (data.count === 0) {
          alert('No budget changes recommended at this time.')
        }
      }
    } catch (error) {
      console.error('Failed to optimize budget:', error)
      alert('Failed to optimize budget. Check logs.')
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
          volatility_cap: 0.20,
          auto_apply: true
        })
      })
      const data = await response.json()
      
      if (data.applied > 0) {
        alert(`Successfully applied ${data.applied} budget changes!`)
        setRecommendations([])
      }
    } catch (error) {
      console.error('Failed to apply recommendations:', error)
      alert('Failed to apply recommendations. Check logs.')
    } finally {
      setApplying(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-AE', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 2,
    }).format(amount)
  }

  const getChangeColor = (changePct: number) => {
    if (changePct > 0) return '#10b981'
    if (changePct < 0) return '#ef4444'
    return '#6b7280'
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb' }}>
      {/* Header */}
      <header style={{
        background: 'white',
        borderBottom: '1px solid #e5e7eb',
        padding: '1rem 2rem',
      }}>
        <div style={{
          maxWidth: '1400px',
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '700' }}>
            Real Estate AI CRM
          </h1>
          <nav style={{ display: 'flex', gap: '1.5rem' }}>
            <Link href="/" style={{ color: '#6b7280' }}>Leads</Link>
            <Link href="/marketing/personas" style={{ color: '#6b7280' }}>Personas</Link>
            <Link href="/marketing/campaigns" style={{ color: '#6b7280' }}>Campaigns</Link>
            <Link href="/marketing/budget" style={{ fontWeight: '600' }}>Budget Optimizer</Link>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main style={{
        maxWidth: '1400px',
        margin: '2rem auto',
        padding: '0 2rem',
      }}>
        {/* Page Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '2rem',
        }}>
          <div>
            <h2 style={{ fontSize: '1.875rem', fontWeight: '700', marginBottom: '0.5rem' }}>
              Budget Optimizer
            </h2>
            <p style={{ color: '#6b7280' }}>
              AI-powered budget allocation using Thompson Sampling
            </p>
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <select
              value={selectedCampaignId || ''}
              onChange={(e) => setSelectedCampaignId(e.target.value ? parseInt(e.target.value) : null)}
              style={{
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '0.875rem',
                minWidth: '250px',
              }}
            >
              <option value="">Select Campaign...</option>
              {campaigns.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <button
              onClick={optimizeBudget}
              disabled={optimizing || !selectedCampaignId}
              style={{
                padding: '0.75rem 1.5rem',
                background: (optimizing || !selectedCampaignId) ? '#d1d5db' : '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontWeight: '600',
                cursor: (optimizing || !selectedCampaignId) ? 'not-allowed' : 'pointer',
              }}
            >
              {optimizing ? 'Optimizing...' : '🎯 Optimize Budget'}
            </button>
          </div>
        </div>

        {/* Info Box */}
        <div style={{
          background: '#dbeafe',
          border: '1px solid #3b82f6',
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '2rem',
        }}>
          <div style={{ fontSize: '0.875rem', color: '#1e40af' }}>
            <strong>How it works:</strong> The optimizer uses Thompson Sampling (Bayesian bandit algorithm) 
            to allocate budget based on performance. It analyzes the last 7 days of data and recommends 
            changes with built-in safety constraints (max 20% daily change, floors & ceilings).
          </div>
        </div>

        {/* Recommendations */}
        {loading ? (
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '3rem',
            textAlign: 'center',
            color: '#6b7280',
          }}>
            Analyzing campaign performance...
          </div>
        ) : recommendations.length === 0 ? (
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '3rem',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💡</div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem' }}>
              No Recommendations Yet
            </h3>
            <p style={{ color: '#6b7280' }}>
              Select a campaign and click "Optimize Budget" to get AI-powered recommendations.
            </p>
          </div>
        ) : (
          <>
            {/* Summary */}
            <div style={{
              background: 'white',
              borderRadius: '8px',
              padding: '1.5rem',
              marginBottom: '1.5rem',
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <div>
                  <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                    Budget Changes Recommended
                  </div>
                  <div style={{ fontSize: '2rem', fontWeight: '700' }}>
                    {recommendations.length} Ad Sets
                  </div>
                </div>
                <button
                  onClick={applyRecommendations}
                  disabled={applying}
                  style={{
                    padding: '0.75rem 1.5rem',
                    background: applying ? '#d1d5db' : '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontWeight: '600',
                    cursor: applying ? 'not-allowed' : 'pointer',
                  }}
                >
                  {applying ? 'Applying...' : '✓ Apply All Changes'}
                </button>
              </div>
            </div>

            {/* Recommendations List */}
            <div style={{ background: 'white', borderRadius: '8px', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
                    <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                      AD SET
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'right', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                      CURRENT
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'center', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                      CHANGE
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'right', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                      RECOMMENDED
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                      RATIONALE
                    </th>
                    <th style={{ padding: '1rem', textAlign: 'center', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                      CONFIDENCE
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {recommendations.map((rec) => (
                    <tr key={rec.ad_set_id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ fontWeight: '600' }}>{rec.name}</div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                          ID: {rec.ad_set_id}
                        </div>
                      </td>
                      <td style={{ padding: '1rem', textAlign: 'right', fontWeight: '600' }}>
                        {formatCurrency(rec.current_budget)}
                      </td>
                      <td style={{ padding: '1rem', textAlign: 'center' }}>
                        <div style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          padding: '0.25rem 0.75rem',
                          borderRadius: '12px',
                          fontSize: '0.875rem',
                          fontWeight: '600',
                          background: getChangeColor(rec.change_pct) + '20',
                          color: getChangeColor(rec.change_pct),
                        }}>
                          {rec.change_pct > 0 ? '↑' : '↓'} {Math.abs(rec.change_pct * 100).toFixed(0)}%
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                          {rec.change_amount > 0 ? '+' : ''}{formatCurrency(rec.change_amount)}
                        </div>
                      </td>
                      <td style={{ padding: '1rem', textAlign: 'right' }}>
                        <div style={{ fontWeight: '700', fontSize: '1.125rem' }}>
                          {formatCurrency(rec.recommended_budget)}
                        </div>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ fontSize: '0.875rem', lineHeight: '1.5' }}>
                          {rec.rationale}
                        </div>
                      </td>
                      <td style={{ padding: '1rem', textAlign: 'center' }}>
                        <div style={{
                          display: 'inline-block',
                          width: '60px',
                          height: '60px',
                          borderRadius: '50%',
                          border: '4px solid #e5e7eb',
                          borderTopColor: rec.confidence > 0.8 ? '#10b981' : rec.confidence > 0.6 ? '#f59e0b' : '#6b7280',
                          position: 'relative',
                        }}>
                          <div style={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            fontSize: '0.875rem',
                            fontWeight: '700',
                          }}>
                            {(rec.confidence * 100).toFixed(0)}%
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

