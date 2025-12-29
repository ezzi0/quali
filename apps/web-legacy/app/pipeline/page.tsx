'use client'
/* eslint-disable */

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { Layout } from '../components/Layout'
import { Section } from '../components/Section'
import { Badge } from '../components/Badge'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Lead {
  id: number
  source: string
  persona: string | null
  status: string
  created_at: string
  contact: {
    name: string | null
    email: string | null
    phone: string | null
  } | null
}

const fallbackLeads: Lead[] = [
  { id: 301, source: 'web', persona: 'buyer', status: 'new', created_at: new Date().toISOString(), contact: { name: 'Lana Ortiz', email: 'lana@example.com', phone: '+971501111111' } },
  { id: 302, source: 'lead_ad', persona: 'renter', status: 'contacted', created_at: new Date().toISOString(), contact: { name: 'Omar Yusuf', email: 'omar@example.com', phone: '+971502222222' } },
  { id: 303, source: 'whatsapp', persona: 'buyer', status: 'qualified', created_at: new Date().toISOString(), contact: { name: 'Nina Park', email: 'nina@example.com', phone: '+971503333333' } },
  { id: 304, source: 'web', persona: 'buyer', status: 'viewing', created_at: new Date().toISOString(), contact: { name: 'Marcus Lee', email: 'marcus@example.com', phone: '+971504444444' } },
  { id: 305, source: 'web', persona: 'buyer', status: 'offer', created_at: new Date().toISOString(), contact: { name: 'Sara Ghali', email: 'sara@example.com', phone: '+971505555555' } },
  { id: 306, source: 'lead_ad', persona: 'buyer', status: 'won', created_at: new Date().toISOString(), contact: { name: 'Victor Cho', email: 'victor@example.com', phone: '+971506666666' } },
]

const statusColors: Record<string, string> = {
  new: '#6ee7ff',
  contacted: '#8b7bff',
  qualified: '#4ade80',
  viewing: '#f59e0b',
  offer: '#fb7185',
  won: '#22c55e',
  lost: '#94a3b8',
  nurture: '#06b6d4',
}

const columns = ['new', 'contacted', 'qualified', 'viewing', 'offer', 'won', 'lost', 'nurture']

export default function PipelinePage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLeads()
  }, [])

  const fetchLeads = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE}/leads`)
      if (!response.ok) {
        throw new Error(`Leads request failed with ${response.status}`)
      }
      const data = await response.json()
      const rows = (data.leads || []) as Lead[]
      setLeads(rows.length ? rows : fallbackLeads)
    } catch (error) {
      console.error('Failed to fetch leads:', error)
      setLeads(fallbackLeads)
    } finally {
      setLoading(false)
    }
  }

  const grouped = useMemo(() => {
    const map: Record<string, Lead[]> = {}
    columns.forEach((c) => (map[c] = []))
    leads.forEach((lead) => {
      const key = lead.status || 'new'
      if (!map[key]) map[key] = []
      map[key].push(lead)
    })
    return map
  }, [leads])

  return (
    <Layout title="Pipeline">
      <Section title="Pipeline Overview" actions={
        <button className="btn secondary" onClick={fetchLeads}>
          Refresh
        </button>
      }>
        {loading ? (
          <div style={{ color: 'var(--muted)' }}>Loading pipeline…</div>
        ) : (
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
            {columns.map((c) => (
              <div key={c} className="card stat">
                <div>
                  <div className="stat__value">{grouped[c]?.length || 0}</div>
                  <div style={{ color: 'var(--muted)', textTransform: 'capitalize' }}>{c}</div>
                </div>
                <Badge text={c} color={statusColors[c] || '#94a3b8'} />
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="Kanban">
        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
          {columns.map((status) => (
            <div key={status} className="card" style={{ minHeight: '240px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <div style={{ fontWeight: 700, textTransform: 'capitalize' }}>{status}</div>
                <Badge text={`${grouped[status]?.length || 0}`} color={statusColors[status]} />
              </div>
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                {(grouped[status] || []).map((lead) => (
                  <div key={lead.id} className="pill" style={{ display: 'grid', gap: '0.25rem' }}>
                    <Link href={`/lead/${lead.id}`} style={{ fontWeight: 700, color: 'var(--accent)' }}>
                      #{lead.id} {lead.contact?.name || 'Unknown'}
                    </Link>
                    <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>{lead.source}</div>
                  </div>
                ))}
                {(grouped[status] || []).length === 0 && (
                  <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>No leads</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </Section>
    </Layout>
  )
}
