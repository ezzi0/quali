'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Creative {
  id: number
  name: string
  format: string
  status: string
  persona_id: number
  headline: string
  primary_text: string
  description: string
  call_to_action: string
  risk_flags: {
    compliance_issues?: string[]
    warnings?: string[]
    toxicity_score?: number
  }
  created_at: string
}

interface Persona {
  id: number
  name: string
}

export default function CreativesPage() {
  const searchParams = useSearchParams()
  const personaIdParam = searchParams.get('persona_id')

  const [creatives, setCreatives] = useState<Creative[]>([])
  const [personas, setPersonas] = useState<Persona[]>([])
  const [selectedPersonaId, setSelectedPersonaId] = useState<number | null>(
    personaIdParam ? parseInt(personaIdParam) : null
  )
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    fetchPersonas()
    fetchCreatives()
  }, [selectedPersonaId])

  const fetchPersonas = async () => {
    try {
      const response = await fetch(`${API_BASE}/marketing/personas`)
      const data = await response.json()
      setPersonas(data.personas || [])
    } catch (error) {
      console.error('Failed to fetch personas:', error)
    }
  }

  const fetchCreatives = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (selectedPersonaId) {
        params.append('persona_id', selectedPersonaId.toString())
      }
      
      const response = await fetch(`${API_BASE}/marketing/creatives?${params}`)
      const data = await response.json()
      setCreatives(data.creatives || [])
    } catch (error) {
      console.error('Failed to fetch creatives:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateCreatives = async () => {
    if (!selectedPersonaId) {
      alert('Please select a persona first')
      return
    }

    try {
      setGenerating(true)
      const response = await fetch(`${API_BASE}/marketing/creatives/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona_id: selectedPersonaId,
          format: 'image',
          count: 3
        })
      })
      const data = await response.json()
      
      if (data.creatives) {
        alert(`Generated ${data.count} new creatives!`)
        fetchCreatives()
      }
    } catch (error) {
      console.error('Failed to generate creatives:', error)
      alert('Failed to generate creatives. Check logs.')
    } finally {
      setGenerating(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: '#6b7280',
      review: '#f59e0b',
      approved: '#10b981',
      rejected: '#ef4444',
      active: '#3b82f6',
      archived: '#6b7280',
    }
    return colors[status] || '#6b7280'
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
            <Link href="/marketing/creatives" style={{ fontWeight: '600' }}>Creatives</Link>
            <Link href="/marketing/campaigns" style={{ color: '#6b7280' }}>Campaigns</Link>
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
              Ad Creatives
            </h2>
            <p style={{ color: '#6b7280' }}>
              AI-generated ad copy with compliance checks
            </p>
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <select
              value={selectedPersonaId || ''}
              onChange={(e) => setSelectedPersonaId(e.target.value ? parseInt(e.target.value) : null)}
              style={{
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '0.875rem',
              }}
            >
              <option value="">All Personas</option>
              {personas.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            <button
              onClick={generateCreatives}
              disabled={generating || !selectedPersonaId}
              style={{
                padding: '0.75rem 1.5rem',
                background: (generating || !selectedPersonaId) ? '#d1d5db' : '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontWeight: '600',
                cursor: (generating || !selectedPersonaId) ? 'not-allowed' : 'pointer',
              }}
            >
              {generating ? 'Generating...' : '✨ Generate Creatives'}
            </button>
          </div>
        </div>

        {/* Creatives List */}
        {loading ? (
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '3rem',
            textAlign: 'center',
            color: '#6b7280',
          }}>
            Loading creatives...
          </div>
        ) : creatives.length === 0 ? (
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '3rem',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎨</div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem' }}>
              No Creatives Yet
            </h3>
            <p style={{ color: '#6b7280', marginBottom: '1.5rem' }}>
              Select a persona and click "Generate Creatives" to create AI-powered ad copy.
            </p>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(450px, 1fr))',
            gap: '1.5rem',
          }}>
            {creatives.map((creative) => (
              <div
                key={creative.id}
                style={{
                  background: 'white',
                  borderRadius: '8px',
                  padding: '1.5rem',
                  border: '1px solid #e5e7eb',
                }}
              >
                {/* Header */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'start',
                  marginBottom: '1rem',
                }}>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '0.25rem' }}>
                      {creative.name}
                    </h3>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                      {creative.format.toUpperCase()}
                    </div>
                  </div>
                  <span style={{
                    display: 'inline-block',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '12px',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    background: getStatusColor(creative.status) + '20',
                    color: getStatusColor(creative.status),
                    textTransform: 'capitalize',
                  }}>
                    {creative.status}
                  </span>
                </div>

                {/* Creative Content */}
                <div style={{
                  background: '#f9fafb',
                  borderRadius: '6px',
                  padding: '1rem',
                  marginBottom: '1rem',
                }}>
                  <div style={{ marginBottom: '0.75rem' }}>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      Headline
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: '600' }}>
                      {creative.headline}
                    </div>
                  </div>

                  <div style={{ marginBottom: '0.75rem' }}>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      Primary Text
                    </div>
                    <div style={{ fontSize: '0.875rem', lineHeight: '1.5' }}>
                      {creative.primary_text}
                    </div>
                  </div>

                  {creative.description && (
                    <div style={{ marginBottom: '0.75rem' }}>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                        Description
                      </div>
                      <div style={{ fontSize: '0.875rem' }}>
                        {creative.description}
                      </div>
                    </div>
                  )}

                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                      Call to Action
                    </div>
                    <div style={{
                      display: 'inline-block',
                      padding: '0.5rem 1rem',
                      background: '#3b82f6',
                      color: 'white',
                      borderRadius: '4px',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                    }}>
                      {creative.call_to_action}
                    </div>
                  </div>
                </div>

                {/* Risk Flags */}
                {(creative.risk_flags.compliance_issues?.length || creative.risk_flags.warnings?.length) ? (
                  <div style={{
                    background: '#fef3c7',
                    border: '1px solid #fbbf24',
                    borderRadius: '6px',
                    padding: '0.75rem',
                    marginBottom: '1rem',
                  }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: '600', color: '#92400e', marginBottom: '0.5rem' }}>
                      ⚠️ Compliance Review Required
                    </div>
                    {creative.risk_flags.compliance_issues?.map((issue, idx) => (
                      <div key={idx} style={{ fontSize: '0.75rem', color: '#92400e', marginBottom: '0.25rem' }}>
                        • {issue}
                      </div>
                    ))}
                    {creative.risk_flags.warnings?.map((warning, idx) => (
                      <div key={idx} style={{ fontSize: '0.75rem', color: '#92400e' }}>
                        • {warning}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{
                    background: '#d1fae5',
                    border: '1px solid #10b981',
                    borderRadius: '6px',
                    padding: '0.75rem',
                    marginBottom: '1rem',
                  }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: '600', color: '#065f46' }}>
                      ✓ Compliance Approved
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div style={{
                  display: 'flex',
                  gap: '0.75rem',
                }}>
                  <button
                    style={{
                      flex: 1,
                      padding: '0.5rem',
                      background: 'white',
                      color: '#3b82f6',
                      border: '1px solid #3b82f6',
                      borderRadius: '6px',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      cursor: 'pointer',
                    }}
                  >
                    Edit
                  </button>
                  <button
                    style={{
                      flex: 1,
                      padding: '0.5rem',
                      background: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      cursor: 'pointer',
                    }}
                  >
                    Use in Campaign
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

