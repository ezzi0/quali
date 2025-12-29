'use client'
/* eslint-disable */

import { useEffect, useMemo, useState } from 'react'
import { Layout } from '../components/Layout'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

type Unit = {
  id: number
  title: string
  slug?: string
  developer?: string
  image_url?: string
  price: number
  currency: string
  price_display?: string
  payment_plan?: string
  area_m2?: number | null
  beds?: number | null
  baths?: number | null
  bedrooms_label?: string | null
  unit_sizes?: string | null
  location: string
  city?: string | null
  area?: string | null
  property_type: string
  status: string
  active: boolean
  featured: boolean
  handover?: string | null
  handover_year?: number | null
  roi?: string | null
  features?: string[]
  description?: string | null
}

type UnitForm = {
  title: string
  slug: string
  developer: string
  image_url: string
  price: string
  currency: string
  price_display: string
  payment_plan: string
  area_m2: string
  beds: string
  baths: string
  bedrooms_label: string
  unit_sizes: string
  location: string
  city: string
  area: string
  property_type: string
  status: string
  features: string
  description: string
  handover: string
  handover_year: string
  roi: string
  active: boolean
  featured: boolean
}

const fallbackUnits: Unit[] = [
  {
    id: 901,
    title: 'Marina Vista Tower',
    slug: 'marina-vista-tower',
    developer: 'Emaar Properties',
    image_url: 'https://images.unsplash.com/photo-1501183638710-841dd1904471?auto=format&fit=crop&w=1200&q=80',
    price: 1200000,
    currency: 'AED',
    price_display: 'AED 1.2M',
    payment_plan: '60/40',
    area_m2: 120,
    beds: 3,
    baths: 3,
    bedrooms_label: 'Studio, 1BR, 2BR, 3BR',
    unit_sizes: '500-2000 sqft',
    location: 'Dubai Marina',
    city: 'Dubai',
    area: 'Dubai Marina',
    property_type: 'apartment',
    status: 'available',
    active: true,
    featured: true,
    handover: 'Q4 2026',
    handover_year: 2026,
    roi: '7-9%',
    features: ['Sea view', 'Private beach', 'Sky lounge', 'Concierge'],
    description: 'Iconic waterfront tower with panoramic marina views and resort-style amenities.',
  },
  {
    id: 902,
    title: 'Marina Heights',
    slug: 'marina-heights',
    developer: 'Select Group',
    image_url: 'https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=1200&q=80',
    price: 950000,
    currency: 'AED',
    price_display: 'AED 950K',
    payment_plan: '70/30',
    area_m2: 95,
    beds: 2,
    baths: 2,
    bedrooms_label: '1BR, 2BR, 3BR',
    unit_sizes: '620-1600 sqft',
    location: 'Dubai Marina',
    city: 'Dubai',
    area: 'Dubai Marina',
    property_type: 'apartment',
    status: 'available',
    active: true,
    featured: false,
    handover: 'Q2 2025',
    handover_year: 2025,
    roi: '8-10%',
    features: ['Infinity pool', 'Co-working lounge', 'Marina walk access'],
    description: 'Modern high-rise with curated lifestyle amenities and flexible payment terms.',
  },
  {
    id: 903,
    title: 'Marina Edge Residences',
    slug: 'marina-edge-residences',
    developer: 'Damac Properties',
    image_url: 'https://images.unsplash.com/photo-1448630360428-65456885c650?auto=format&fit=crop&w=1200&q=80',
    price: 1800000,
    currency: 'AED',
    price_display: 'AED 1.8M',
    payment_plan: '60/40',
    area_m2: 140,
    beds: 3,
    baths: 3,
    bedrooms_label: '2BR, 3BR, 4BR',
    unit_sizes: '950-2200 sqft',
    location: 'Dubai Marina',
    city: 'Dubai',
    area: 'Dubai Marina',
    property_type: 'apartment',
    status: 'available',
    active: true,
    featured: false,
    handover: 'Q1 2027',
    handover_year: 2027,
    roi: '6-8%',
    features: ['Sky deck', 'Kids club', 'Valet', 'Fitness studio'],
    description: 'Elegant residences with generous layouts and curated interiors.',
  },
  {
    id: 904,
    title: 'Palm Crest Villas',
    slug: 'palm-crest-villas',
    developer: 'Nakheel',
    image_url: 'https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&w=1200&q=80',
    price: 6500000,
    currency: 'AED',
    price_display: 'AED 6.5M',
    payment_plan: '80/20',
    area_m2: 380,
    beds: 5,
    baths: 5,
    bedrooms_label: '4BR, 5BR',
    unit_sizes: '4,000-6,500 sqft',
    location: 'Palm Jumeirah',
    city: 'Dubai',
    area: 'Palm Jumeirah',
    property_type: 'villa',
    status: 'available',
    active: true,
    featured: true,
    handover: 'Q3 2025',
    handover_year: 2025,
    roi: '5-7%',
    features: ['Private beach', 'Garden', 'Smart home', 'Infinity pool'],
    description: 'Seafront villas with private beach access and bespoke interior upgrades.',
  },
  {
    id: 905,
    title: 'Business Bay Lofts',
    slug: 'business-bay-lofts',
    developer: 'Omniyat',
    image_url: 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80',
    price: 980000,
    currency: 'AED',
    price_display: 'AED 980K',
    payment_plan: '65/35',
    area_m2: 88,
    beds: 2,
    baths: 2,
    bedrooms_label: 'Studio, 1BR, 2BR',
    unit_sizes: '540-1,400 sqft',
    location: 'Business Bay',
    city: 'Dubai',
    area: 'Business Bay',
    property_type: 'apartment',
    status: 'available',
    active: true,
    featured: false,
    handover: 'Q4 2025',
    handover_year: 2025,
    roi: '7-9%',
    features: ['Canal view', 'Retail podium', 'Co-working', 'Gym'],
    description: 'Lifestyle-centric lofts in the heart of the business district.',
  },
  {
    id: 906,
    title: 'Jumeirah Bay Estates',
    slug: 'jumeirah-bay-estates',
    developer: 'Meraas',
    image_url: 'https://images.unsplash.com/photo-1502005229762-cf1b2da7c5d6?auto=format&fit=crop&w=1200&q=80',
    price: 9800000,
    currency: 'AED',
    price_display: 'AED 9.8M',
    payment_plan: '50/50',
    area_m2: 520,
    beds: 6,
    baths: 7,
    bedrooms_label: '5BR, 6BR',
    unit_sizes: '6,500-9,000 sqft',
    location: 'Jumeirah Bay Island',
    city: 'Dubai',
    area: 'Jumeirah Bay Island',
    property_type: 'villa',
    status: 'available',
    active: true,
    featured: true,
    handover: 'Q2 2026',
    handover_year: 2026,
    roi: '6-8%',
    features: ['Private marina', 'Beach club access', 'Signature spa'],
    description: 'Exclusive island villas with curated waterfront amenities.',
  },
]

const fallbackImages: Record<string, string> = {
  apartment: 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80',
  villa: 'https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&w=1200&q=80',
  townhouse: 'https://images.unsplash.com/photo-1501183638710-841dd1904471?auto=format&fit=crop&w=1200&q=80',
  studio: 'https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=1200&q=80',
  default: 'https://images.unsplash.com/photo-1448630360428-65456885c650?auto=format&fit=crop&w=1200&q=80',
}

const emptyForm: UnitForm = {
  title: '',
  slug: '',
  developer: '',
  image_url: '',
  price: '',
  currency: 'AED',
  price_display: '',
  payment_plan: '',
  area_m2: '',
  beds: '',
  baths: '',
  bedrooms_label: '',
  unit_sizes: '',
  location: '',
  city: '',
  area: '',
  property_type: 'apartment',
  status: 'available',
  features: '',
  description: '',
  handover: '',
  handover_year: '',
  roi: '',
  active: true,
  featured: false,
}

const slugify = (value: string) => {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)+/g, '')
}

const formatPriceDisplay = (price: number, currency: string) => {
  if (!price || Number.isNaN(price)) return ''
  if (price >= 1000000) return `${currency} ${(price / 1000000).toFixed(1)}M`
  if (price >= 1000) return `${currency} ${(price / 1000).toFixed(0)}K`
  return `${currency} ${price.toLocaleString()}`
}

export default function InventoryPage() {
  const [units, setUnits] = useState<Unit[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    city: 'Dubai',
    area: '',
    property_type: '',
    status: '',
    active: 'true',
    featured: '',
    min_price: '',
    max_price: '',
  })
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Unit | null>(null)
  const [form, setForm] = useState<UnitForm>(emptyForm)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [slugTouched, setSlugTouched] = useState(false)
  const [priceDisplayTouched, setPriceDisplayTouched] = useState(false)

  useEffect(() => {
    fetchInventory()
  }, [])

  useEffect(() => {
    if (modalOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [modalOpen])

  const fetchInventory = async () => {
    setLoading(true)
    setNotice(null)
    try {
      const params = new URLSearchParams()
      if (filters.city) params.append('city', filters.city)
      if (filters.area) params.append('area', filters.area)
      if (filters.property_type) params.append('property_type', filters.property_type)
      if (filters.status) params.append('status', filters.status)
      if (filters.min_price) params.append('min_price', filters.min_price)
      if (filters.max_price) params.append('max_price', filters.max_price)
      if (filters.active !== 'all') params.append('active', filters.active === 'true' ? 'true' : 'false')
      if (filters.featured !== '') params.append('featured', filters.featured === 'true' ? 'true' : 'false')

      const response = await fetch(`${API_BASE}/inventory/search?${params}`)
      if (!response.ok) {
        throw new Error(`Inventory request failed with ${response.status}`)
      }
      const data = await response.json()
      const rows = (data.units || []) as Unit[]
      if (rows.length) {
        setUnits(rows)
      } else {
        setUnits(fallbackUnits)
        setNotice('No live inventory found. Showing local demo data.')
      }
    } catch (err) {
      console.error('Failed to fetch inventory:', err)
      setUnits(fallbackUnits)
      setNotice('Inventory API unavailable. Showing local demo data.')
    } finally {
      setLoading(false)
    }
  }

  const filteredUnits = useMemo(() => {
    const term = search.toLowerCase().trim()
    if (!term) return units
    return units.filter((unit) => {
      const haystack = `${unit.title} ${unit.location} ${unit.area || ''} ${unit.property_type} ${unit.developer || ''}`
        .toLowerCase()
      return haystack.includes(term)
    })
  }, [units, search])

  const stats = useMemo(() => {
    const locations = new Set<string>()
    units.forEach((u) => {
      if (u.area) locations.add(u.area)
      else if (u.location) locations.add(u.location)
    })

    return {
      total: units.length,
      active: units.filter((u) => u.active).length,
      featured: units.filter((u) => u.featured).length,
      locations: locations.size,
    }
  }, [units])

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setSlugTouched(false)
    setPriceDisplayTouched(false)
    setError(null)
    setModalOpen(true)
  }

  const openEdit = (unit: Unit) => {
    setEditing(unit)
    setForm({
      title: unit.title || '',
      slug: unit.slug || '',
      developer: unit.developer || '',
      image_url: unit.image_url || '',
      price: unit.price ? String(unit.price) : '',
      currency: unit.currency || 'AED',
      price_display: unit.price_display || '',
      payment_plan: unit.payment_plan || '',
      area_m2: unit.area_m2 ? String(unit.area_m2) : '',
      beds: unit.beds ? String(unit.beds) : '',
      baths: unit.baths ? String(unit.baths) : '',
      bedrooms_label: unit.bedrooms_label || '',
      unit_sizes: unit.unit_sizes || '',
      location: unit.location || '',
      city: unit.city || '',
      area: unit.area || '',
      property_type: unit.property_type || 'apartment',
      status: unit.status || 'available',
      features: unit.features ? unit.features.join(', ') : '',
      description: unit.description || '',
      handover: unit.handover || '',
      handover_year: unit.handover_year ? String(unit.handover_year) : '',
      roi: unit.roi || '',
      active: unit.active,
      featured: unit.featured,
    })
    setSlugTouched(true)
    setPriceDisplayTouched(true)
    setError(null)
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setEditing(null)
    setError(null)
  }

  const handleSave = async () => {
    setError(null)
    const parsedPrice = Number(form.price)
    if (!form.title.trim() || !form.location.trim() || !form.property_type.trim()) {
      setError('Title, location, and property type are required.')
      return
    }
    if (!parsedPrice || Number.isNaN(parsedPrice)) {
      setError('Price must be a valid number.')
      return
    }

    const payload = {
      title: form.title.trim(),
      slug: form.slug.trim() || undefined,
      developer: form.developer.trim() || undefined,
      image_url: form.image_url.trim() || undefined,
      price: parsedPrice,
      currency: form.currency || 'AED',
      price_display: form.price_display.trim() || undefined,
      payment_plan: form.payment_plan.trim() || undefined,
      area_m2: form.area_m2 ? Number(form.area_m2) : undefined,
      beds: form.beds ? Number(form.beds) : undefined,
      baths: form.baths ? Number(form.baths) : undefined,
      bedrooms_label: form.bedrooms_label.trim() || undefined,
      unit_sizes: form.unit_sizes.trim() || undefined,
      location: form.location.trim(),
      city: form.city.trim() || undefined,
      area: form.area.trim() || undefined,
      property_type: form.property_type.trim(),
      status: form.status || 'available',
      features: form.features
        ? form.features.split(',').map((item) => item.trim()).filter(Boolean)
        : [],
      description: form.description.trim() || undefined,
      handover: form.handover.trim() || undefined,
      handover_year: form.handover_year ? Number(form.handover_year) : undefined,
      roi: form.roi.trim() || undefined,
      active: form.active,
      featured: form.featured,
    }

    try {
      if (editing) {
        const response = await fetch(`${API_BASE}/inventory/${editing.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (!response.ok) {
          throw new Error(`Update failed with ${response.status}`)
        }
        setUnits((prev) => prev.map((unit) => (unit.id === editing.id ? { ...unit, ...payload } as Unit : unit)))
      } else {
        const response = await fetch(`${API_BASE}/inventory`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (!response.ok) {
          throw new Error(`Create failed with ${response.status}`)
        }
        const data = await response.json()
        const newUnit: Unit = {
          id: data.id || Math.floor(Date.now() / 1000),
          ...payload,
          price_display: payload.price_display || formatPriceDisplay(payload.price, payload.currency),
        } as Unit
        setUnits((prev) => [newUnit, ...prev])
      }
      closeModal()
    } catch (err) {
      console.error('Failed to save unit:', err)
      setNotice('Inventory API unavailable. Saved locally for now.')
      if (editing) {
        setUnits((prev) => prev.map((unit) => (unit.id === editing.id ? { ...unit, ...payload } as Unit : unit)))
      } else {
        const tempId = -Math.floor(Date.now() / 1000)
        const newUnit: Unit = {
          id: tempId,
          ...payload,
          price_display: payload.price_display || formatPriceDisplay(payload.price, payload.currency),
        } as Unit
        setUnits((prev) => [newUnit, ...prev])
      }
      closeModal()
    }
  }

  const handleDelete = async (unit: Unit) => {
    const confirmed = window.confirm(`Delete ${unit.title}?`)
    if (!confirmed) return

    try {
      const response = await fetch(`${API_BASE}/inventory/${unit.id}`, { method: 'DELETE' })
      if (!response.ok) {
        throw new Error(`Delete failed with ${response.status}`)
      }
      setUnits((prev) => prev.filter((item) => item.id !== unit.id))
    } catch (err) {
      console.error('Failed to delete unit:', err)
      setNotice('Inventory API unavailable. Deleted locally for now.')
      setUnits((prev) => prev.filter((item) => item.id !== unit.id))
    }
  }

  return (
    <Layout title="Inventory Manager">
      <div className="hero">
        <div>
          <div className="hero__title">Collection Manager</div>
          <div className="hero__subtitle">Curate launch-ready properties and keep the shortlist fresh.</div>
        </div>
        <div className="toolbar">
          <button className="btn" onClick={openCreate}>+ Add Property</button>
          <button className="btn secondary" onClick={fetchInventory}>Refresh</button>
        </div>
      </div>

      {notice && <div className="notice">{notice}</div>}

      <div className="panel">
        <div className="panel__header">
          <h2>Filters</h2>
          <div className="panel__actions">
            <button className="btn secondary" onClick={() => {
              setFilters({
                city: 'Dubai',
                area: '',
                property_type: '',
                status: '',
                active: 'true',
                featured: '',
                min_price: '',
                max_price: '',
              })
              setSearch('')
            }}>Reset</button>
            <button className="btn" onClick={fetchInventory}>Apply</button>
          </div>
        </div>
        <div className="panel__body">
          <div className="input-row">
            <input
              className="input"
              placeholder="Search title, location, developer"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <input
              className="input"
              placeholder="City"
              value={filters.city}
              onChange={(e) => setFilters({ ...filters, city: e.target.value })}
            />
            <input
              className="input"
              placeholder="Area"
              value={filters.area}
              onChange={(e) => setFilters({ ...filters, area: e.target.value })}
            />
            <select
              className="input"
              value={filters.property_type}
              onChange={(e) => setFilters({ ...filters, property_type: e.target.value })}
            >
              <option value="">Any type</option>
              <option value="apartment">Apartment</option>
              <option value="villa">Villa</option>
              <option value="townhouse">Townhouse</option>
              <option value="studio">Studio</option>
            </select>
            <select
              className="input"
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            >
              <option value="">Any status</option>
              <option value="available">Available</option>
              <option value="reserved">Reserved</option>
              <option value="sold">Sold</option>
              <option value="rented">Rented</option>
            </select>
            <select
              className="input"
              value={filters.active}
              onChange={(e) => setFilters({ ...filters, active: e.target.value })}
            >
              <option value="all">All activity</option>
              <option value="true">Active only</option>
              <option value="false">Inactive only</option>
            </select>
            <select
              className="input"
              value={filters.featured}
              onChange={(e) => setFilters({ ...filters, featured: e.target.value })}
            >
              <option value="">Any featured</option>
              <option value="true">Featured</option>
              <option value="false">Not featured</option>
            </select>
            <input
              className="input"
              placeholder="Min price"
              type="number"
              value={filters.min_price}
              onChange={(e) => setFilters({ ...filters, min_price: e.target.value })}
            />
            <input
              className="input"
              placeholder="Max price"
              type="number"
              value={filters.max_price}
              onChange={(e) => setFilters({ ...filters, max_price: e.target.value })}
            />
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel__header">
          <h2>Portfolio Overview</h2>
        </div>
        <div className="grid">
          <div className="card stat">
            <div>
              <div className="stat__value">{stats.total}</div>
              <div style={{ color: 'var(--muted)' }}>Total properties</div>
            </div>
            <span className="pill">Portfolio</span>
          </div>
          <div className="card stat">
            <div>
              <div className="stat__value">{stats.active}</div>
              <div style={{ color: 'var(--muted)' }}>Active</div>
            </div>
            <span className="pill">Live</span>
          </div>
          <div className="card stat">
            <div>
              <div className="stat__value">{stats.featured}</div>
              <div style={{ color: 'var(--muted)' }}>Featured</div>
            </div>
            <span className="pill">Highlight</span>
          </div>
          <div className="card stat">
            <div>
              <div className="stat__value">{stats.locations}</div>
              <div style={{ color: 'var(--muted)' }}>Locations</div>
            </div>
            <span className="pill">Coverage</span>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel__header">
          <h2>Properties</h2>
          <div className="panel__actions">
            <span className="pill">{filteredUnits.length} results</span>
          </div>
        </div>
        <div className="panel__body">
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--muted)' }}>Loading inventory...</div>
          ) : filteredUnits.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--muted)' }}>No properties found.</div>
          ) : (
            <div className="inventory-grid">
              {filteredUnits.map((unit) => {
                const imageUrl = unit.image_url || fallbackImages[unit.property_type] || fallbackImages.default
                return (
                  <div key={unit.id} className="property-card">
                    <div
                      className="property-card__media"
                      style={{ backgroundImage: `url(${imageUrl})` }}
                    >
                      {unit.featured && <span className="property-card__tag">Featured</span>}
                    </div>
                    <div className="property-card__body">
                      <div className="property-card__title">{unit.title}</div>
                      <div className="property-card__meta">
                        <span>{unit.location}</span>
                        <span>{unit.developer || 'Private developer'}</span>
                      </div>
                      {(unit.beds || unit.area_m2 || unit.unit_sizes || unit.bedrooms_label) && (
                        <div className="property-card__meta">
                          <span>{unit.beds ? `${unit.beds} beds` : (unit.bedrooms_label || 'Flexible bedrooms')}</span>
                          <span>{unit.unit_sizes || (unit.area_m2 ? `${unit.area_m2} m2` : 'Size on request')}</span>
                        </div>
                      )}
                      <div className="property-card__price">
                        {unit.price_display || `${unit.currency} ${unit.price.toLocaleString()}`}
                      </div>
                      <div className="pill-row">
                        <span className="pill">{unit.property_type}</span>
                        <span className="pill">{unit.status}</span>
                        {!unit.active && <span className="pill">Inactive</span>}
                        {unit.handover && <span className="pill">Handover {unit.handover}</span>}
                        {unit.payment_plan && <span className="pill">{unit.payment_plan} plan</span>}
                        {unit.roi && <span className="pill warn">ROI {unit.roi}</span>}
                      </div>
                      {unit.features && unit.features.length > 0 && (
                        <div className="pill-row">
                          {unit.features.slice(0, 4).map((feature, index) => (
                            <span key={index} className="pill">{feature}</span>
                          ))}
                        </div>
                      )}
                      <div className="property-card__actions">
                        <button className="btn secondary" onClick={() => openEdit(unit)}>Edit</button>
                        <button className="btn ghost" onClick={() => handleDelete(unit)}>Delete</button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {modalOpen && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal">
            <div className="modal__header">
              <div className="modal__title">{editing ? 'Edit Property' : 'Add Property'}</div>
              <button className="btn ghost" onClick={closeModal}>Close</button>
            </div>
            <div className="modal__body">
              {error && <div className="notice">{error}</div>}
              <div className="form-section">
                <div className="form-section__title">Basic Information</div>
                <div className="form-grid">
                  <div className="field">
                    <label>Title *</label>
                    <input
                      className="input"
                      value={form.title}
                      onChange={(e) => {
                        const value = e.target.value
                        setForm((prev) => ({ ...prev, title: value, slug: slugTouched ? prev.slug : slugify(value) }))
                      }}
                    />
                  </div>
                  <div className="field">
                    <label>Slug</label>
                    <input
                      className="input"
                      value={form.slug}
                      onChange={(e) => {
                        setSlugTouched(true)
                        setForm((prev) => ({ ...prev, slug: e.target.value }))
                      }}
                      placeholder="auto-generated if empty"
                    />
                  </div>
                  <div className="field">
                    <label>Location *</label>
                    <input
                      className="input"
                      value={form.location}
                      onChange={(e) => setForm((prev) => ({ ...prev, location: e.target.value }))}
                    />
                  </div>
                  <div className="field">
                    <label>Developer</label>
                    <input
                      className="input"
                      value={form.developer}
                      onChange={(e) => setForm((prev) => ({ ...prev, developer: e.target.value }))}
                    />
                  </div>
                  <div className="field">
                    <label>City</label>
                    <input
                      className="input"
                      value={form.city}
                      onChange={(e) => setForm((prev) => ({ ...prev, city: e.target.value }))}
                    />
                  </div>
                  <div className="field">
                    <label>Area</label>
                    <input
                      className="input"
                      value={form.area}
                      onChange={(e) => setForm((prev) => ({ ...prev, area: e.target.value }))}
                    />
                  </div>
                  <div className="field">
                    <label>Property Type *</label>
                    <select
                      className="input"
                      value={form.property_type}
                      onChange={(e) => setForm((prev) => ({ ...prev, property_type: e.target.value }))}
                    >
                      <option value="apartment">Apartment</option>
                      <option value="villa">Villa</option>
                      <option value="townhouse">Townhouse</option>
                      <option value="studio">Studio</option>
                    </select>
                  </div>
                  <div className="field">
                    <label>Image URL</label>
                    <input
                      className="input"
                      value={form.image_url}
                      onChange={(e) => setForm((prev) => ({ ...prev, image_url: e.target.value }))}
                      placeholder="https://..."
                    />
                  </div>
                </div>
              </div>

              <div className="form-section">
                <div className="form-section__title">Pricing & Payment</div>
                <div className="form-grid">
                  <div className="field">
                    <label>Price From *</label>
                    <input
                      className="input"
                      type="number"
                      value={form.price}
                      onChange={(e) => {
                        const value = e.target.value
                        setForm((prev) => ({
                          ...prev,
                          price: value,
                          price_display: priceDisplayTouched
                            ? prev.price_display
                            : formatPriceDisplay(Number(value), prev.currency),
                        }))
                      }}
                    />
                  </div>
                  <div className="field">
                    <label>Currency</label>
                    <select
                      className="input"
                      value={form.currency}
                      onChange={(e) => {
                        const currency = e.target.value
                        setForm((prev) => ({
                          ...prev,
                          currency,
                          price_display: priceDisplayTouched
                            ? prev.price_display
                            : formatPriceDisplay(Number(prev.price), currency),
                        }))
                      }}
                    >
                      <option value="AED">AED</option>
                      <option value="USD">USD</option>
                      <option value="SAR">SAR</option>
                    </select>
                  </div>
                  <div className="field">
                    <label>Price Display</label>
                    <input
                      className="input"
                      value={form.price_display}
                      onChange={(e) => {
                        setPriceDisplayTouched(true)
                        setForm((prev) => ({ ...prev, price_display: e.target.value }))
                      }}
                    />
                  </div>
                  <div className="field">
                    <label>Payment Plan</label>
                    <input
                      className="input"
                      value={form.payment_plan}
                      onChange={(e) => setForm((prev) => ({ ...prev, payment_plan: e.target.value }))}
                      placeholder="60/40"
                    />
                  </div>
                </div>
              </div>

              <div className="form-section">
                <div className="form-section__title">Timeline & ROI</div>
                <div className="form-grid">
                  <div className="field">
                    <label>Handover</label>
                    <input
                      className="input"
                      value={form.handover}
                      onChange={(e) => setForm((prev) => ({ ...prev, handover: e.target.value }))}
                      placeholder="Q4 2026"
                    />
                  </div>
                  <div className="field">
                    <label>Handover Year</label>
                    <input
                      className="input"
                      type="number"
                      value={form.handover_year}
                      onChange={(e) => setForm((prev) => ({ ...prev, handover_year: e.target.value }))}
                      placeholder="2026"
                    />
                  </div>
                  <div className="field">
                    <label>ROI</label>
                    <input
                      className="input"
                      value={form.roi}
                      onChange={(e) => setForm((prev) => ({ ...prev, roi: e.target.value }))}
                      placeholder="7-9%"
                    />
                  </div>
                  <div className="field">
                    <label>Status</label>
                    <select
                      className="input"
                      value={form.status}
                      onChange={(e) => setForm((prev) => ({ ...prev, status: e.target.value }))}
                    >
                      <option value="available">Available</option>
                      <option value="reserved">Reserved</option>
                      <option value="sold">Sold</option>
                      <option value="rented">Rented</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="form-section">
                <div className="form-section__title">Additional Details</div>
                <div className="form-grid">
                  <div className="field">
                    <label>Bedrooms</label>
                    <input
                      className="input"
                      value={form.bedrooms_label}
                      onChange={(e) => setForm((prev) => ({ ...prev, bedrooms_label: e.target.value }))}
                      placeholder="Studio, 1BR, 2BR"
                    />
                  </div>
                  <div className="field">
                    <label>Unit Sizes</label>
                    <input
                      className="input"
                      value={form.unit_sizes}
                      onChange={(e) => setForm((prev) => ({ ...prev, unit_sizes: e.target.value }))}
                      placeholder="500-2000 sqft"
                    />
                  </div>
                  <div className="field">
                    <label>Beds</label>
                    <input
                      className="input"
                      type="number"
                      value={form.beds}
                      onChange={(e) => setForm((prev) => ({ ...prev, beds: e.target.value }))}
                    />
                  </div>
                  <div className="field">
                    <label>Baths</label>
                    <input
                      className="input"
                      type="number"
                      value={form.baths}
                      onChange={(e) => setForm((prev) => ({ ...prev, baths: e.target.value }))}
                    />
                  </div>
                  <div className="field">
                    <label>Size (m2)</label>
                    <input
                      className="input"
                      type="number"
                      value={form.area_m2}
                      onChange={(e) => setForm((prev) => ({ ...prev, area_m2: e.target.value }))}
                    />
                  </div>
                  <div className="field">
                    <label>Highlights (comma separated)</label>
                    <input
                      className="input"
                      value={form.features}
                      onChange={(e) => setForm((prev) => ({ ...prev, features: e.target.value }))}
                      placeholder="Sea view, Concierge, Private pool"
                    />
                  </div>
                </div>
                <div className="field">
                  <label>Description</label>
                  <textarea
                    className="textarea"
                    value={form.description}
                    onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
                  />
                </div>
              </div>

              <div className="form-section">
                <div className="form-section__title">Settings</div>
                <div className="checkbox-row">
                  <label>
                    <input
                      type="checkbox"
                      checked={form.active}
                      onChange={(e) => setForm((prev) => ({ ...prev, active: e.target.checked }))}
                    />
                    Active (visible in collection)
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={form.featured}
                      onChange={(e) => setForm((prev) => ({ ...prev, featured: e.target.checked }))}
                    />
                    Featured
                  </label>
                </div>
              </div>
            </div>
            <div className="modal__footer">
              <button className="btn secondary" onClick={closeModal}>Cancel</button>
              <button className="btn" onClick={handleSave}>{editing ? 'Update Property' : 'Create Property'}</button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
