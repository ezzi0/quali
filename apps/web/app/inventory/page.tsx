'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Unit {
  unit_id: number
  title: string
  price: number
  currency: string
  area_m2: number
  beds: number
  location: string
  property_type: string
  features: string[]
}

export default function InventoryPage() {
  const [units, setUnits] = useState<Unit[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    city: 'Dubai',
    property_type: '',
    min_beds: '',
    max_beds: '',
  })

  useEffect(() => {
    fetchInventory()
  }, [])

  const fetchInventory = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filters.city) params.append('city', filters.city)
      if (filters.property_type) params.append('property_type', filters.property_type)
      if (filters.min_beds) params.append('min_beds', filters.min_beds)
      if (filters.max_beds) params.append('max_beds', filters.max_beds)
      
      const response = await fetch(`${API_BASE}/inventory/search?${params}`)
      if (!response.ok) {
        throw new Error(`Inventory request failed with ${response.status}`)
      }
      const data = await response.json()
      setUnits(data.units || [])
    } catch (error) {
      console.error('Failed to fetch inventory:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatPrice = (price: number, currency: string) => {
    return `${currency} ${price.toLocaleString()}`
  }

  const getPropertyTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      apartment: '#3b82f6',
      villa: '#10b981',
      townhouse: '#8b5cf6',
      penthouse: '#f59e0b',
      studio: '#06b6d4',
    }
    return colors[type] || '#6b7280'
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
            <Link href="/inventory" style={{ fontWeight: '600' }}>Inventory</Link>
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
        <h2 style={{ fontSize: '1.875rem', fontWeight: '700', marginBottom: '1.5rem' }}>
          Property Inventory
        </h2>

        {/* Filters */}
        <div style={{
          background: 'white',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '1.5rem',
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
          }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                City
              </label>
              <select
                value={filters.city}
                onChange={(e) => setFilters({ ...filters, city: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                }}
              >
                <option value="Dubai">Dubai</option>
                <option value="Abu Dhabi">Abu Dhabi</option>
                <option value="Sharjah">Sharjah</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                Property Type
              </label>
              <select
                value={filters.property_type}
                onChange={(e) => setFilters({ ...filters, property_type: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                }}
              >
                <option value="">All Types</option>
                <option value="apartment">Apartment</option>
                <option value="villa">Villa</option>
                <option value="townhouse">Townhouse</option>
                <option value="penthouse">Penthouse</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                Min Bedrooms
              </label>
              <input
                type="number"
                value={filters.min_beds}
                onChange={(e) => setFilters({ ...filters, min_beds: e.target.value })}
                placeholder="Any"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                Max Bedrooms
              </label>
              <input
                type="number"
                value={filters.max_beds}
                onChange={(e) => setFilters({ ...filters, max_beds: e.target.value })}
                placeholder="Any"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                }}
              />
            </div>
          </div>

          <button
            onClick={fetchInventory}
            style={{
              marginTop: '1rem',
              padding: '0.75rem 2rem',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            Search
          </button>
        </div>

        {/* Units Grid */}
        {loading ? (
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '3rem',
            textAlign: 'center',
            color: '#6b7280',
          }}>
            Loading inventory...
          </div>
        ) : units.length === 0 ? (
          <div style={{
            background: 'white',
            borderRadius: '8px',
            padding: '3rem',
            textAlign: 'center',
            color: '#6b7280',
          }}>
            No properties found. Try adjusting your filters.
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
            gap: '1.5rem',
          }}>
            {units.map((unit) => (
              <div
                key={unit.unit_id}
                style={{
                  background: 'white',
                  borderRadius: '8px',
                  overflow: 'hidden',
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
                <div style={{
                  padding: '1.5rem',
                }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'start',
                    marginBottom: '0.75rem',
                  }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      background: getPropertyTypeColor(unit.property_type) + '20',
                      color: getPropertyTypeColor(unit.property_type),
                      textTransform: 'capitalize',
                    }}>
                      {unit.property_type}
                    </span>
                    <span style={{
                      fontSize: '0.875rem',
                      color: '#6b7280',
                      fontWeight: '500',
                    }}>
                      {unit.beds} BD
                    </span>
                  </div>

                  <h3 style={{
                    fontSize: '1.125rem',
                    fontWeight: '600',
                    marginBottom: '0.5rem',
                    lineHeight: '1.4',
                  }}>
                    {unit.title}
                  </h3>

                  <p style={{
                    color: '#6b7280',
                    fontSize: '0.875rem',
                    marginBottom: '1rem',
                  }}>
                    📍 {unit.location}
                  </p>

                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    paddingTop: '1rem',
                    borderTop: '1px solid #e5e7eb',
                  }}>
                    <div>
                      <div style={{
                        fontSize: '1.5rem',
                        fontWeight: '700',
                        color: '#1f2937',
                      }}>
                        {formatPrice(unit.price, unit.currency)}
                      </div>
                      <div style={{
                        fontSize: '0.75rem',
                        color: '#6b7280',
                      }}>
                        {unit.area_m2} m²
                      </div>
                    </div>

                    <button
                      style={{
                        padding: '0.5rem 1rem',
                        background: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                      }}
                    >
                      View Details
                    </button>
                  </div>

                  {unit.features && unit.features.length > 0 && (
                    <div style={{
                      marginTop: '1rem',
                      paddingTop: '1rem',
                      borderTop: '1px solid #e5e7eb',
                    }}>
                      <div style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '0.5rem',
                      }}>
                        {unit.features.slice(0, 3).map((feature, idx) => (
                          <span
                            key={idx}
                            style={{
                              fontSize: '0.75rem',
                              color: '#6b7280',
                              background: '#f3f4f6',
                              padding: '0.25rem 0.5rem',
                              borderRadius: '4px',
                            }}
                          >
                            {feature.replace(/_/g, ' ')}
                          </span>
                        ))}
                        {unit.features.length > 3 && (
                          <span style={{
                            fontSize: '0.75rem',
                            color: '#6b7280',
                          }}>
                            +{unit.features.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
