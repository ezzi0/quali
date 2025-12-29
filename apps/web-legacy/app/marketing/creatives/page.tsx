'use client'
/* eslint-disable */

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Layout } from '../../components/Layout'
import { Section } from '../../components/Section'
import { Badge } from '../../components/Badge'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Creative {
  id: number
  name: string
  format: string
  status: string
  persona_id?: number
  headline?: string
  risk_flags?: Record<string, any>
  created_at?: string
}

interface PersonaOption {
  id: number
  name: string
}

const fallbackCreatives: Creative[] = [
  {
    id: 1,
    name: 'Marina Luxury - Variant A',
    format: 'image',
    status: 'approved',
    headline: 'Wake up to the Marina',
  },
  {
    id: 2,
    name: 'Starter Homes - Variant B',
    format: 'carousel',
    status: 'review',
    headline: 'Your first home, simplified',
  },
]

function CreativesContent() {
  const searchParams = useSearchParams()
  const personaIdParam = searchParams.get('persona_id')

  const [personas, setPersonas] = useState<PersonaOption[]>([])
  const [creatives, setCreatives] = useState<Creative[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [personaId, setPersonaId] = useState<string>(personaIdParam || '')

  useEffect(() => {
    fetchPersonas()
    fetchCreatives()
  }, [])

  const fetchPersonas = async () => {
    try {
      const response = await fetch(`${API_BASE}/marketing/personas`)
      const data = await response.json()
      setPersonas(data.personas || [])
    } catch (error) {
      console.error(error)
      setPersonas([{ id: 1, name: 'Luxury Waterfront Seekers' }])
    }
  }

  const fetchCreatives = async () => {
    try {
      setLoading(true)
      const url = personaId ? `${API_BASE}/marketing/creatives?persona_id=${personaId}` : `${API_BASE}/marketing/creatives`
      const response = await fetch(url)
      const data = await response.json()
      const rows = (data.creatives || []) as Creative[]
      setCreatives(rows.length ? rows : fallbackCreatives)
    } catch (error) {
      console.error(error)
      setCreatives(fallbackCreatives)
    } finally {
      setLoading(false)
    }
  }

  const generateCreatives = async () => {
    if (!personaId) {
      alert('Select a persona to generate creatives.')
      return
    }
    try {
      setGenerating(true)
      const response = await fetch(`${API_BASE}/marketing/creatives/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona_id: Number(personaId),
          format: 'image',
          count: 3,
        }),
      })
      if (!response.ok) throw new Error('Failed to generate')
      await fetchCreatives()
    } catch (error) {
      console.error(error)
      alert('Generation failed. Showing sample creatives.')
      setCreatives(fallbackCreatives)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <Layout title="AI Creatives">
      <Section title="Generate Creatives" actions={
        <button className="btn" onClick={generateCreatives} disabled={generating}>
          {generating ? 'Generating…' : 'Generate'}
        </button>
      }>
        <div className="input-row">
          <select className="input" value={personaId} onChange={(e) => setPersonaId(e.target.value)}>
            <option value="">Select persona</option>
            {personas.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <button className="btn secondary" onClick={fetchCreatives}>Refresh</button>
        </div>
      </Section>

      <Section title="Creatives">
        {loading ? (
          <div style={{ color: 'var(--muted)' }}>Loading creatives…</div>
        ) : (
          <div className="grid">
            {creatives.map((c) => (
              <div key={c.id} className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <div style={{ fontWeight: 700 }}>{c.name}</div>
                  <Badge text={c.status} color={c.status === 'approved' ? '#4ade80' : '#f59e0b'} />
                </div>
                <div style={{ color: 'var(--muted)', marginBottom: '0.5rem' }}>{c.headline || 'Creative headline'}</div>
                <div className="pill-row">
                  <span className="pill">Format {c.format}</span>
                  {c.persona_id && <span className="pill">Persona {c.persona_id}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>
    </Layout>
  )
}

export default function CreativesPage() {
  return (
    <Suspense fallback={<div style={{ padding: '2rem' }}>Loading…</div>}>
      <CreativesContent />
    </Suspense>
  )
}
