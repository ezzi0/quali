'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

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

export default function LeadDetailPage({ params }: { params: { id: string } }) {
  const leadId = params.id
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
      setError('Unable to load lead details. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        Loading...
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#ef4444' }}>
        {error}
      </div>
    )
  }

  if (!lead) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        Lead not found
      </div>
    )
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
          gap: '1rem',
        }}>
          <Link href="/" style={{ color: '#3b82f6', fontWeight: '600' }}>
            ← Back to Leads
          </Link>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '700' }}>
            Lead #{lead.id}
          </h1>
        </div>
      </header>

      <main style={{
        maxWidth: '1400px',
        margin: '2rem auto',
        padding: '0 2rem',
        display: 'grid',
        gridTemplateColumns: '2fr 1fr',
        gap: '1.5rem',
      }}>
        {/* Left Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Contact Info */}
          <div style={{ background: 'white', borderRadius: '8px', padding: '1.5rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '1rem' }}>
              Contact Information
            </h2>
            {lead.contact ? (
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                <div><strong>Name:</strong> {lead.contact.name || '—'}</div>
                <div><strong>Email:</strong> {lead.contact.email || '—'}</div>
                <div><strong>Phone:</strong> {lead.contact.phone || '—'}</div>
              </div>
            ) : (
              <div style={{ color: '#6b7280' }}>No contact information</div>
            )}
          </div>

          {/* Profile */}
          {lead.profile && (
            <div style={{ background: 'white', borderRadius: '8px', padding: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '1rem' }}>
                Requirements
              </h2>
              <div style={{ display: 'grid', gap: '0.5rem' }}>
                <div><strong>Location:</strong> {lead.profile.city || '—'}</div>
                {lead.profile.areas && lead.profile.areas.length > 0 && (
                  <div><strong>Areas:</strong> {lead.profile.areas.join(', ')}</div>
                )}
                <div><strong>Type:</strong> {lead.profile.property_type || '—'}</div>
                <div><strong>Bedrooms:</strong> {lead.profile.beds || '—'}</div>
                <div>
                  <strong>Budget:</strong>{' '}
                  {lead.profile.budget_min && lead.profile.budget_max
                    ? `${lead.profile.budget_min.toLocaleString()} - ${lead.profile.budget_max.toLocaleString()} ${lead.profile.currency}`
                    : '—'}
                </div>
                <div><strong>Move-in:</strong> {lead.profile.move_in_date || '—'}</div>
              </div>
            </div>
          )}

          {/* Timeline */}
          <div style={{ background: 'white', borderRadius: '8px', padding: '1.5rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '1rem' }}>
              Timeline
            </h2>
            {lead.timeline.length === 0 ? (
              <div style={{ color: '#6b7280' }}>No activity yet</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {lead.timeline.map((activity) => (
                  <div
                    key={activity.id}
                    style={{
                      padding: '0.75rem',
                      background: '#f9fafb',
                      borderRadius: '6px',
                      borderLeft: '3px solid #3b82f6',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span style={{ fontWeight: '600', textTransform: 'capitalize' }}>
                        {activity.type.replace('_', ' ')}
                      </span>
                      <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                        {new Date(activity.created_at).toLocaleString()}
                      </span>
                    </div>
                    <pre style={{ fontSize: '0.875rem', color: '#374151', whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(activity.payload, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Qualification */}
          {lead.qualification && (
            <div style={{ background: 'white', borderRadius: '8px', padding: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '1rem' }}>
                Qualification
              </h2>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                marginBottom: '1rem',
              }}>
                <div style={{
                  fontSize: '2.5rem',
                  fontWeight: '700',
                  color: lead.qualification.qualified ? '#10b981' : '#ef4444',
                }}>
                  {lead.qualification.score}
                </div>
                <div>
                  <div style={{
                    fontWeight: '600',
                    color: lead.qualification.qualified ? '#10b981' : '#ef4444',
                  }}>
                    {lead.qualification.qualified ? 'Qualified' : 'Not Qualified'}
                  </div>
                  <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                    {new Date(lead.qualification.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <strong>Reasons:</strong>
                <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                  {lead.qualification.reasons.map((reason, i) => (
                    <li key={i} style={{ marginBottom: '0.25rem' }}>{reason}</li>
                  ))}
                </ul>
              </div>

              {lead.qualification.missing_info.length > 0 && (
                <div style={{ marginBottom: '1rem' }}>
                  <strong>Missing Info:</strong>
                  <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                    {lead.qualification.missing_info.map((info, i) => (
                      <li key={i} style={{ marginBottom: '0.25rem', color: '#ef4444' }}>{info}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={{
                marginTop: '1rem',
                padding: '0.75rem',
                background: '#eff6ff',
                borderRadius: '6px',
                fontWeight: '600',
                color: '#3b82f6',
              }}>
                Next: {lead.qualification.suggested_next_step.replace('_', ' ')}
              </div>
            </div>
          )}

          {/* Tasks */}
          <div style={{ background: 'white', borderRadius: '8px', padding: '1.5rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '1rem' }}>
              Tasks
            </h2>
            {lead.tasks.length === 0 ? (
              <div style={{ color: '#6b7280' }}>No tasks yet</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {lead.tasks.map((task) => (
                  <div
                    key={task.id}
                    style={{
                      padding: '0.75rem',
                      border: '1px solid #e5e7eb',
                      borderRadius: '6px',
                    }}
                  >
                    <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                      {task.title}
                    </div>
                    <div style={{
                      fontSize: '0.875rem',
                      color: '#6b7280',
                      display: 'flex',
                      justifyContent: 'space-between',
                    }}>
                      <span style={{ textTransform: 'capitalize' }}>{task.status.replace('_', ' ')}</span>
                      {task.due_at && (
                        <span>Due: {new Date(task.due_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
