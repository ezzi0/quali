'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Persona {
  id: number
  name: string
  description: string
  status: string
  sample_size: number
  confidence_score: number
  created_at: string
  rules: {
    budget_range?: [number, number]
    property_types?: string[]
    locations?: string[]
  }
  characteristics: {
    urgency?: string
    price_sensitivity?: string
    decision_speed?: string
  }
  messaging: {
    hooks?: string[]
    tone?: string
  }
}

export default function PersonasPage() {
  const [personas, setPersonas] = useState<Persona[]>([])
  const [loading, setLoading] = useState(true)
  const [discovering, setDiscovering] = useState(false)

  useEffect(() => {
    fetchPersonas()
  }, [])

  const fetchPersonas = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/marketing/personas`)
      const data = await response.json()
      setPersonas(data.personas || [])
    } catch (error) {
      console.error('Failed to fetch personas:', error)
    } finally {
      setLoading(false)
    }
  }

  const discoverPersonas = async () => {
    try {
      setDiscovering(true)
      const response = await fetch(`${API_BASE}/marketing/personas/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          min_cluster_size: 25,
          method: 'hdbscan'
        })
      })
      const data = await response.json()
      
      if (data.personas) {
        alert(`Discovered ${data.count} new personas!`)
        fetchPersonas()
      }
    } catch (error) {
      console.error('Failed to discover personas:', error)
      alert('Failed to discover personas. Check logs.')
    } finally {
      setDiscovering(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: '#6b7280',
      active: '#10b981',
      archived: '#ef4444',
    }
    return colors[status] || '#6b7280'
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-AE', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
    }).format(amount)
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
            <Link href="/chat" style={{ color: '#6b7280' }}>AI Chat</Link>
            <Link href="/marketing/personas" style={{ fontWeight: '600' }}>Marketing</Link>
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
              Marketing Personas
            </h2>
            <p style={{ color: '#6b7280' }}>
              AI-discovered customer segments for targeted campaigns
            </p>
          </div>
          <button
            onClick={discoverPersonas}
            disabled={discovering}
            style={{
              padding: '0.75rem 1.5rem',
              background: discovering ? '#d1d5db' : '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontWeight: '600',
              cursor: discovering ? 'not-allowed' : 'pointer',
            }}
          >
            {discovering ? 'Discovering...' : '🔍 Discover New Personas'}
          </button>
        </div>

        {/* Personas Grid */}
        {loading ? (
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '3rem',
            textAlign: 'center',
            color: '#6b7280',
          }}>
            Loading personas...
          </div>
        ) : personas.length === 0 ? (
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '3rem',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎯</div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem' }}>
              No Personas Yet
            </h3>
            <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
              Click "Discover New Personas" to analyze your lead data and create targeted segments.
            </p>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))',
            gap: '1.5rem',
          }}>
            {personas.map((persona) => (
              <div
                key={persona.id}
                style={{
                  background: 'white',
                  borderRadius: '8px',
                  padding: '1.5rem',
                  border: '1px solid #e5e7eb',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)'
                  e.currentTarget.style.boxShadow = '0 10px 25px rgba(0,0,0,0.1)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              >
                {/* Header */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'start',
                  marginBottom: '1rem',
                }}>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: '600', flex: 1 }}>
                    {persona.name}
                  </h3>
                  <span style={{
                    display: 'inline-block',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '12px',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    background: getStatusColor(persona.status) + '20',
                    color: getStatusColor(persona.status),
                    textTransform: 'capitalize',
                  }}>
                    {persona.status}
                  </span>
                </div>

                {/* Description */}
                <p style={{
                  color: '#6b7280',
                  fontSize: '0.875rem',
                  marginBottom: '1rem',
                  lineHeight: '1.5',
                }}>
                  {persona.description}
                </p>

                {/* Metrics */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, 1fr)',
                  gap: '0.75rem',
                  marginBottom: '1rem',
                  paddingTop: '1rem',
                  borderTop: '1px solid #e5e7eb',
                }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      Sample Size
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: '700' }}>
                      {persona.sample_size}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      Confidence
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: '700' }}>
                      {persona.confidence_score.toFixed(1)}%
                    </div>
                  </div>
                </div>

                {/* Budget Range */}
                {persona.rules.budget_range && (
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      Budget Range
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: '600' }}>
                      {formatCurrency(persona.rules.budget_range[0])} - {formatCurrency(persona.rules.budget_range[1])}
                    </div>
                  </div>
                )}

                {/* Characteristics */}
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                  marginBottom: '1rem',
                }}>
                  {persona.characteristics.urgency && (
                    <span style={{
                      fontSize: '0.75rem',
                      padding: '0.25rem 0.5rem',
                      background: '#f3f4f6',
                      borderRadius: '4px',
                    }}>
                      🏃 {persona.characteristics.urgency} urgency
                    </span>
                  )}
                  {persona.characteristics.price_sensitivity && (
                    <span style={{
                      fontSize: '0.75rem',
                      padding: '0.25rem 0.5rem',
                      background: '#f3f4f6',
                      borderRadius: '4px',
                    }}>
                      💰 {persona.characteristics.price_sensitivity} price sensitivity
                    </span>
                  )}
                </div>

                {/* Hooks */}
                {persona.messaging.hooks && persona.messaging.hooks.length > 0 && (
                  <div style={{
                    paddingTop: '1rem',
                    borderTop: '1px solid #e5e7eb',
                  }}>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.5rem' }}>
                      Messaging Hooks
                    </div>
                    <div style={{ fontSize: '0.875rem', color: '#374151', fontStyle: 'italic' }}>
                      "{persona.messaging.hooks[0]}"
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div style={{
                  display: 'flex',
                  gap: '0.75rem',
                  marginTop: '1rem',
                }}>
                  <Link 
                    href={`/marketing/creatives?persona_id=${persona.id}`}
                    style={{
                      flex: 1,
                      padding: '0.5rem',
                      background: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      textAlign: 'center',
                      textDecoration: 'none',
                    }}
                  >
                    Generate Creatives
                  </Link>
                  <Link
                    href={`/marketing/campaigns?persona_id=${persona.id}`}
                    style={{
                      flex: 1,
                      padding: '0.5rem',
                      background: 'white',
                      color: '#3b82f6',
                      border: '1px solid #3b82f6',
                      borderRadius: '6px',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      textAlign: 'center',
                      textDecoration: 'none',
                    }}
                  >
                    View Campaigns
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

