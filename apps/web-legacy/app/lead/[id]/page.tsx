'use client'
/* eslint-disable */

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { Layout } from '../../components/Layout'
import { Section } from '../../components/Section'
import { Badge } from '../../components/Badge'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface LeadDetail {
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
  profile: {
    city: string | null
    areas: string[] | null
    property_type: string | null
    beds: number | null
    budget_min: number | null
    budget_max: number | null
    currency: string
    move_in_date: string | null
  } | null
  qualification: {
    score: number
    qualified: boolean
    reasons: string[]
    missing_info: string[]
    suggested_next_step: string
    created_at: string
  } | null
  timeline: Array<{
    id: number
    type: string
    payload: any
    created_at: string
  }>
  tasks: Array<{
    id: number
    title: string
    status: string
    due_at: string | null
    created_at: string
  }>
}

const fallbackLead: LeadDetail = {
  id: 101,
  source: 'web',
  persona: 'buyer',
  status: 'qualified',
  created_at: new Date().toISOString(),
  contact: { name: 'Alex Chen', email: 'alex@example.com', phone: '+971501234567' },
  profile: {
    city: 'Dubai',
    areas: ['Dubai Marina', 'JBR'],
    property_type: 'apartment',
    beds: 3,
    budget_min: 1200000,
    budget_max: 1800000,
    currency: 'AED',
    move_in_date: '60 days',
  },
  qualification: {
    score: 82,
    qualified: true,
    reasons: ['Strong property match', 'Budget aligned', 'High intent'],
    missing_info: [],
    suggested_next_step: 'Book a viewing for top 3 units',
    created_at: new Date().toISOString(),
  },
  timeline: [
    {
      id: 1,
      type: 'message',
      payload: { text: 'Interested in 3BR near Marina.' },
      created_at: new Date().toISOString(),
    },
    {
      id: 2,
      type: 'qualification',
      payload: { score: 82, qualified: true },
      created_at: new Date().toISOString(),
    },
  ],
  tasks: [
    {
      id: 1,
      title: 'Schedule viewing',
      status: 'todo',
      due_at: null,
      created_at: new Date().toISOString(),
    },
  ],
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

export default function LeadDetailPage({ params }: any) {
  const leadId = params?.id
  const [lead, setLead] = useState<LeadDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchLead()
  }, [leadId])

  const fetchLead = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`${API_BASE}/leads/${leadId}`)
      if (!response.ok) {
        throw new Error(`Lead request failed with ${response.status}`)
      }
      const data = await response.json()
      setLead(data)
    } catch (error) {
      console.error('Failed to fetch lead:', error)
      setLead(fallbackLead)
      setError('Showing sample lead data (API not available).')
    } finally {
      setLoading(false)
    }
  }

  const aiSummary = useMemo(() => {
    if (!lead) return ''
    const profile = lead.profile
    if (!profile) return 'No profile data available.'
    return `Looking for a ${profile.beds || '?'}BR ${profile.property_type || 'home'} in ${profile.city || 'Dubai'} with a budget up to ${profile.budget_max?.toLocaleString() || 'N/A'} ${profile.currency}.`
  }, [lead])

  return (
    <Layout title={`Lead #${leadId}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link href="/" className="btn secondary">Back to Leads</Link>
        {lead?.status && <Badge text={lead.status} color={statusColors[lead.status] || '#94a3b8'} />}
      </div>

      {loading && <div style={{ padding: '2rem', color: 'var(--muted)' }}>Loading lead…</div>}
      {!loading && error && <div style={{ color: 'var(--warning)' }}>{error}</div>}

      {lead && (
        <>
          <Section title="AI Summary">
            <div style={{ color: 'var(--muted)' }}>{aiSummary}</div>
            {lead.qualification && (
              <div className="pill-row">
                <Badge text={`Score ${lead.qualification.score}`} color={lead.qualification.score >= 65 ? '#4ade80' : '#f59e0b'} />
                <span className="pill">{lead.qualification.suggested_next_step}</span>
              </div>
            )}
          </Section>

          <div className="grid">
            <Section title="Contact">
              {lead.contact ? (
                <div className="panel__body">
                  <div><strong>Name:</strong> {lead.contact.name || '—'}</div>
                  <div><strong>Email:</strong> {lead.contact.email || '—'}</div>
                  <div><strong>Phone:</strong> {lead.contact.phone || '—'}</div>
                </div>
              ) : (
                <div style={{ color: 'var(--muted)' }}>No contact information</div>
              )}
            </Section>
            <Section title="Preferences">
              {lead.profile ? (
                <div className="panel__body">
                  <div><strong>City:</strong> {lead.profile.city || '—'}</div>
                  <div><strong>Areas:</strong> {lead.profile.areas?.join(', ') || '—'}</div>
                  <div><strong>Type:</strong> {lead.profile.property_type || '—'}</div>
                  <div><strong>Beds:</strong> {lead.profile.beds || '—'}</div>
                  <div><strong>Budget:</strong> {lead.profile.budget_min?.toLocaleString()} - {lead.profile.budget_max?.toLocaleString()} {lead.profile.currency}</div>
                  <div><strong>Move-in:</strong> {lead.profile.move_in_date || '—'}</div>
                </div>
              ) : (
                <div style={{ color: 'var(--muted)' }}>No profile data</div>
              )}
            </Section>
          </div>

          <Section title="Timeline">
            {lead.timeline.length === 0 ? (
              <div style={{ color: 'var(--muted)' }}>No activity yet</div>
            ) : (
              <div className="panel__body">
                {lead.timeline.map((activity) => (
                  <div key={activity.id} className="card">
                    <div style={{ fontWeight: 700, textTransform: 'capitalize' }}>{activity.type.replace('_', ' ')}</div>
                    <div style={{ color: 'var(--muted)' }}>{activity.payload?.text || JSON.stringify(activity.payload)}</div>
                  </div>
                ))}
              </div>
            )}
          </Section>

          <Section title="Tasks">
            {lead.tasks.length === 0 ? (
              <div style={{ color: 'var(--muted)' }}>No tasks yet</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Task</th>
                    <th>Status</th>
                    <th>Due</th>
                  </tr>
                </thead>
                <tbody>
                  {lead.tasks.map((task) => (
                    <tr key={task.id}>
                      <td>{task.title}</td>
                      <td><Badge text={task.status} /></td>
                      <td>{task.due_at ? new Date(task.due_at).toLocaleDateString() : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Section>
        </>
      )}
    </Layout>
  )
}
