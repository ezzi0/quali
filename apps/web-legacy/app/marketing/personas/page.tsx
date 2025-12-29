'use client'
/* eslint-disable */

import { useEffect, useState } from 'react'
import { Layout } from '../../components/Layout'
import { Section } from '../../components/Section'
import { Badge } from '../../components/Badge'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Persona {
  id: number
  name: string
  description: string
  status: string
  sample_size: number
  confidence_score: number
  created_at: string
}

const fallbackPersonas: Persona[] = [
  {
    id: 1,
    name: 'Luxury Waterfront Seekers',
    description: 'High-income buyers prioritizing waterfront living and amenities.',
    status: 'active',
    sample_size: 124,
    confidence_score: 0.87,
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    name: 'First-Time Buyers',
    description: 'Budget-conscious buyers seeking starter apartments near transit.',
    status: 'active',
    sample_size: 310,
    confidence_score: 0.79,
    created_at: new Date().toISOString(),
  },
]

export default function PersonasPage() {
  const [personas, setPersonas] = useState<Persona[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  useEffect(() => {
    fetchPersonas()
  }, [])

  const fetchPersonas = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/marketing/personas`)
      if (!response.ok) throw new Error('Failed to fetch personas')
      const data = await response.json()
      const rows = (data.personas || []) as Persona[]
      setPersonas(rows.length ? rows : fallbackPersonas)
    } catch (error) {
      console.error(error)
      setPersonas(fallbackPersonas)
    } finally {
      setLoading(false)
    }
  }

  const discoverPersonas = async () => {
    try {
      setRunning(true)
      const response = await fetch(`${API_BASE}/marketing/personas/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ min_cluster_size: 25, method: 'hdbscan' }),
      })
      if (!response.ok) throw new Error('Failed to discover personas')
      await fetchPersonas()
    } catch (error) {
      console.error(error)
      alert('Discovery failed. Showing sample personas.')
      setPersonas(fallbackPersonas)
    } finally {
      setRunning(false)
    }
  }

  return (
    <Layout title="Marketing Personas">
      <Section title="Persona Discovery" actions={
        <button className="btn" onClick={discoverPersonas} disabled={running}>
          {running ? 'Discovering…' : 'Discover Personas'}
        </button>
      }>
        <div style={{ color: 'var(--muted)' }}>
          AI clusters qualified leads into segments with messaging guidance.
        </div>
      </Section>

      <Section title="Personas">
        {loading ? (
          <div style={{ color: 'var(--muted)' }}>Loading personas…</div>
        ) : (
          <div className="grid">
            {personas.map((persona) => (
              <div key={persona.id} className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <div style={{ fontWeight: 700 }}>{persona.name}</div>
                  <Badge text={persona.status} color={persona.status === 'active' ? '#4ade80' : '#94a3b8'} />
                </div>
                <div style={{ color: 'var(--muted)', marginBottom: '0.5rem' }}>{persona.description}</div>
                <div className="pill-row">
                  <span className="pill">Sample size {persona.sample_size}</span>
                  <span className="pill">Confidence {Math.round(persona.confidence_score * 100)}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>
    </Layout>
  )
}
