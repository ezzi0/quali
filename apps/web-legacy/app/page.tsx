'use client'
/* eslint-disable */

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { Layout } from './components/Layout'
import { Section } from './components/Section'
import { Badge } from './components/Badge'

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

const fallbackLeads: Lead[] = [
  {
    id: 101,
    source: 'web',
    persona: 'buyer',
    status: 'qualified',
    created_at: new Date().toISOString(),
    contact: { name: 'Alex Chen', email: 'alex@example.com', phone: '+971501234567' },
  },
  {
    id: 102,
    source: 'lead_ad',
    persona: 'renter',
    status: 'new',
    created_at: new Date().toISOString(),
    contact: { name: 'Fatima Noor', email: 'fatima@example.com', phone: '+971509998888' },
  },
  {
    id: 103,
    source: 'whatsapp',
    persona: 'buyer',
    status: 'viewing',
    created_at: new Date().toISOString(),
    contact: { name: 'Samir Patel', email: 'samir@example.com', phone: '+971555678901' },
  },
]

export default function LeadsInbox() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('')
  const [search, setSearch] = useState<string>('')

  useEffect(() => {
    fetchLeads()
  }, [filter])

  const fetchLeads = async () => {
    try {
      setLoading(true)
      const url = filter ? `${API_BASE}/leads?status=${filter}` : `${API_BASE}/leads`
      const response = await fetch(url)
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

  const filtered = useMemo(() => {
    const term = search.toLowerCase()
    return leads.filter((lead) => {
      if (!term) return true
      const contact = `${lead.contact?.name || ''} ${lead.contact?.email || ''} ${lead.contact?.phone || ''}`.toLowerCase()
      return contact.includes(term) || lead.status.toLowerCase().includes(term)
    })
  }, [leads, search])

  const counts = useMemo(() => {
    const bucket: Record<string, number> = {}
    leads.forEach((l) => {
      bucket[l.status] = (bucket[l.status] || 0) + 1
    })
    return bucket
  }, [leads])

  const statusList = ['new', 'contacted', 'qualified', 'viewing', 'offer', 'won', 'lost', 'nurture']

  return (
    <Layout title="AI Leads Inbox">
      <Section
        title="Lead Filters"
        actions={
          <div className="pill-row">
            <button className="btn secondary" onClick={() => setFilter('')}>
              All
            </button>
            {statusList.map((s) => (
              <button
                key={s}
                className="btn secondary"
                style={{
                  borderColor: filter === s ? statusColors[s] : 'var(--border)',
                  color: filter === s ? statusColors[s] : 'var(--text)',
                  background: filter === s ? `${statusColors[s]}22` : 'transparent',
                }}
                onClick={() => setFilter(s)}
              >
                {s}
              </button>
            ))}
          </div>
        }
      >
        <div className="input-row">
          <input
            className="input"
            placeholder="Search name, email, phone or status"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </Section>

      <Section title="Pipeline Snapshot">
        <div className="grid">
          {statusList.map((s) => (
            <div key={s} className="card stat">
              <div>
                <div className="stat__value">{counts[s] || 0}</div>
                <div style={{ color: 'var(--muted)', textTransform: 'capitalize' }}>{s}</div>
              </div>
              <Badge text={s} color={statusColors[s]} />
            </div>
          ))}
        </div>
      </Section>

      <Section title="Leads">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--muted)' }}>Loading leads…</div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--muted)' }}>No leads found</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Contact</th>
                <th>Source</th>
                <th>Persona</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((lead) => (
                <tr key={lead.id}>
                  <td>
                    <Link href={`/lead/${lead.id}`} style={{ color: 'var(--accent)', fontWeight: 700 }}>
                      #{lead.id}
                    </Link>
                  </td>
                  <td>
                    {lead.contact ? (
                      <div>
                        <div>{lead.contact.name || 'Unknown'}</div>
                        <div style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>
                          {lead.contact.email || lead.contact.phone || '—'}
                        </div>
                      </div>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td style={{ textTransform: 'capitalize' }}>{lead.source.replace('_', ' ')}</td>
                  <td style={{ textTransform: 'capitalize' }}>{lead.persona || '—'}</td>
                  <td>
                    <Badge text={lead.status} color={statusColors[lead.status] || '#94a3b8'} />
                  </td>
                  <td style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>
                    {new Date(lead.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>
    </Layout>
  )
}
