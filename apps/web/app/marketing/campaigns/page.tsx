'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Campaign {
  id: number
  name: string
  platform: string
  objective: string
  status: string
  budget_total: number | null
  budget_daily: number | null
  spend_total: number
  created_at: string
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPlatform, setSelectedPlatform] = useState<string>('')

  useEffect(() => {
    fetchCampaigns()
  }, [selectedPlatform])

  const fetchCampaigns = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (selectedPlatform) {
        params.append('platform', selectedPlatform)
      }
      
      const response = await fetch(`${API_BASE}/marketing/campaigns?${params}`)
      const data = await response.json()
      setCampaigns(data.campaigns || [])
    } catch (error) {
      console.error('Failed to fetch campaigns:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: '#6b7280',
      scheduled: '#f59e0b',
      active: '#10b981',
      paused: '#f59e0b',
      completed: '#6b7280',
      archived: '#ef4444',
    }
    return colors[status] || '#6b7280'
  }

  const getPlatformIcon = (platform: string) => {
    const icons: Record<string, string> = {
      meta: '📘',
      google: '🔍',
      tiktok: '🎵',
      multi: '🌐',
    }
    return icons[platform] || '📢'
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-AE', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
    }).format(amount)
  }

  const calculateSpendPercentage = (campaign: Campaign) => {
    if (!campaign.budget_total || campaign.budget_total === 0) return 0
    return (campaign.spend_total / campaign.budget_total) * 100
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
            <Link href="/marketing/creatives" style={{ color: '#6b7280' }}>Creatives</Link>
            <Link href="/marketing/campaigns" style={{ fontWeight: '600' }}>Campaigns</Link>
            <Link href="/marketing/budget" style={{ color: '#6b7280' }}>Budget</Link>
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
              Campaigns
            </h2>
            <p style={{ color: '#6b7280' }}>
              Multi-platform marketing campaigns
            </p>
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <select
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(e.target.value)}
              style={{
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '0.875rem',
              }}
            >
              <option value="">All Platforms</option>
              <option value="meta">Meta (Facebook/Instagram)</option>
              <option value="google">Google Ads</option>
              <option value="tiktok">TikTok</option>
            </select>
            <button
              style={{
                padding: '0.75rem 1.5rem',
                background: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontWeight: '600',
                cursor: 'pointer',
              }}
            >
              + Create Campaign
            </button>
          </div>
        </div>

        {/* Campaign Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '1.5rem',
          marginBottom: '2rem',
        }}>
          {[
            { label: 'Active', value: campaigns.filter(c => c.status === 'active').length, color: '#10b981' },
            { label: 'Paused', value: campaigns.filter(c => c.status === 'paused').length, color: '#f59e0b' },
            { label: 'Draft', value: campaigns.filter(c => c.status === 'draft').length, color: '#6b7280' },
            { 
              label: 'Total Spend', 
              value: formatCurrency(campaigns.reduce((sum, c) => sum + c.spend_total, 0)), 
              color: '#3b82f6' 
            },
          ].map((stat, idx) => (
            <div
              key={idx}
              style={{
                background: 'white',
                borderRadius: '8px',
                padding: '1.5rem',
                border: '1px solid #e5e7eb',
              }}
            >
              <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                {stat.label}
              </div>
              <div style={{ fontSize: '2rem', fontWeight: '700', color: stat.color }}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>

        {/* Campaigns List */}
        {loading ? (
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '3rem',
            textAlign: 'center',
            color: '#6b7280',
          }}>
            Loading campaigns...
          </div>
        ) : campaigns.length === 0 ? (
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '3rem',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📢</div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem' }}>
              No Campaigns Yet
            </h3>
            <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
              Create your first campaign to start generating leads.
            </p>
          </div>
        ) : (
          <div style={{ background: 'white', borderRadius: '8px', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
                  <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                    CAMPAIGN
                  </th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                    PLATFORM
                  </th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                    OBJECTIVE
                  </th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                    STATUS
                  </th>
                  <th style={{ padding: '1rem', textAlign: 'right', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                    BUDGET
                  </th>
                  <th style={{ padding: '1rem', textAlign: 'right', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                    SPEND
                  </th>
                  <th style={{ padding: '1rem', textAlign: 'center', fontSize: '0.75rem', fontWeight: '600', color: '#6b7280' }}>
                    ACTIONS
                  </th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((campaign) => (
                  <tr key={campaign.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ fontWeight: '600' }}>{campaign.name}</div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                        Created {new Date(campaign.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span>{getPlatformIcon(campaign.platform)}</span>
                        <span style={{ textTransform: 'capitalize' }}>{campaign.platform}</span>
                      </div>
                    </td>
                    <td style={{ padding: '1rem', fontSize: '0.875rem', textTransform: 'capitalize' }}>
                      {campaign.objective.replace(/_/g, ' ')}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '0.25rem 0.75rem',
                        borderRadius: '12px',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        background: getStatusColor(campaign.status) + '20',
                        color: getStatusColor(campaign.status),
                        textTransform: 'capitalize',
                      }}>
                        {campaign.status}
                      </span>
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      <div style={{ fontWeight: '600' }}>
                        {campaign.budget_daily ? formatCurrency(campaign.budget_daily) + '/day' : '-'}
                      </div>
                      {campaign.budget_total && (
                        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                          {formatCurrency(campaign.budget_total)} total
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      <div style={{ fontWeight: '600' }}>
                        {formatCurrency(campaign.spend_total)}
                      </div>
                      {campaign.budget_total && (
                        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                          {calculateSpendPercentage(campaign).toFixed(0)}% of budget
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'center' }}>
                      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                        <button
                          style={{
                            padding: '0.5rem 0.75rem',
                            background: 'white',
                            color: '#3b82f6',
                            border: '1px solid #3b82f6',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: '600',
                            cursor: 'pointer',
                          }}
                        >
                          View
                        </button>
                        <Link
                          href={`/marketing/budget?campaign_id=${campaign.id}`}
                          style={{
                            padding: '0.5rem 0.75rem',
                            background: '#3b82f6',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: '600',
                            textDecoration: 'none',
                            display: 'inline-block',
                          }}
                        >
                          Optimize
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}

