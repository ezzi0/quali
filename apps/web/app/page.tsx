'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

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

export default function LeadsInbox() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('')

  useEffect(() => {
    fetchLeads()
  }, [filter])

  const fetchLeads = async () => {
    try {
      setLoading(true)
      const url = filter 
        ? `${API_BASE}/leads?status=${filter}`
        : `${API_BASE}/leads`
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error(`Leads request failed with ${response.status}`)
      }
      const data = await response.json()
      setLeads(data.leads || [])
    } catch (error) {
      console.error('Failed to fetch leads:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      new: '#3b82f6',
      contacted: '#8b5cf6',
      qualified: '#10b981',
      viewing: '#f59e0b',
      offer: '#ef4444',
      won: '#22c55e',
      lost: '#6b7280',
      nurture: '#06b6d4',
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
            <Link href="/" style={{ fontWeight: '600' }}>Leads</Link>
            <Link href="/chat" style={{ color: '#6b7280' }}>AI Chat</Link>
            <Link href="/inventory" style={{ color: '#6b7280' }}>Inventory</Link>
            <Link href="/marketing/personas" style={{ color: '#6b7280' }}>Marketing</Link>
            <Link href="/pipeline" style={{ color: '#6b7280' }}>Pipeline</Link>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main style={{
        maxWidth: '1400px',
        margin: '2rem auto',
        padding: '0 2rem',
      }}>
        {/* Filters */}
        <div style={{
          background: 'white',
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '1rem',
          display: 'flex',
          gap: '0.5rem',
          flexWrap: 'wrap',
        }}>
          <button
            onClick={() => setFilter('')}
            style={{
              padding: '0.5rem 1rem',
              border: filter === '' ? '2px solid #3b82f6' : '1px solid #d1d5db',
              borderRadius: '6px',
              background: filter === '' ? '#eff6ff' : 'white',
              fontWeight: filter === '' ? '600' : '400',
            }}
          >
            All
          </button>
          {['new', 'qualified', 'viewing', 'won'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              style={{
                padding: '0.5rem 1rem',
                border: filter === status ? '2px solid #3b82f6' : '1px solid #d1d5db',
                borderRadius: '6px',
                background: filter === status ? '#eff6ff' : 'white',
                fontWeight: filter === status ? '600' : '400',
                textTransform: 'capitalize',
              }}
            >
              {status}
            </button>
          ))}
        </div>

        {/* Leads Table */}
        <div style={{
          background: 'white',
          borderRadius: '8px',
          overflow: 'hidden',
        }}>
          {loading ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: '#6b7280' }}>
              Loading leads...
            </div>
          ) : leads.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: '#6b7280' }}>
              No leads found
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                <tr>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: '600' }}>ID</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: '600' }}>Contact</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: '600' }}>Source</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: '600' }}>Persona</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: '600' }}>Status</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: '600' }}>Created</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((lead) => (
                  <tr
                    key={lead.id}
                    style={{
                      borderBottom: '1px solid #e5e7eb',
                      transition: 'background 0.2s',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = '#f9fafb'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
                  >
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <Link
                        href={`/lead/${lead.id}`}
                        style={{ color: '#3b82f6', fontWeight: '600' }}
                      >
                        #{lead.id}
                      </Link>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {lead.contact ? (
                        <div>
                          <div>{lead.contact.name || 'Unknown'}</div>
                          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                            {lead.contact.email || lead.contact.phone || '—'}
                          </div>
                        </div>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', textTransform: 'capitalize' }}>
                      {lead.source.replace('_', ' ')}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', textTransform: 'capitalize' }}>
                      {lead.persona || '—'}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '0.25rem 0.75rem',
                        borderRadius: '12px',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        background: getStatusColor(lead.status) + '20',
                        color: getStatusColor(lead.status),
                        textTransform: 'capitalize',
                      }}>
                        {lead.status}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: '#6b7280', fontSize: '0.875rem' }}>
                      {new Date(lead.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  )
}
