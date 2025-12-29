import { useEffect, useMemo, useState } from 'react';
import { Plus, Pencil, Trash2, Building2, MapPin, Calendar, CreditCard, TrendingUp, Search, Filter, X } from 'lucide-react';
import AdminLayout from '@/components/admin/AdminLayout';
import { api } from '@/lib/api';
import { getUnitImage } from '@/lib/images';
import { useToast } from '@/hooks/use-toast';

interface Unit {
  id: number;
  title: string;
  slug: string | null;
  developer: string | null;
  image_url: string | null;
  price: number;
  currency: string;
  price_display: string | null;
  payment_plan: string | null;
  area_m2: number | null;
  beds: number | null;
  baths: number | null;
  bedrooms_label: string | null;
  unit_sizes: string | null;
  location: string;
  city: string | null;
  area: string | null;
  property_type: string;
  status: string;
  features: string[];
  description: string | null;
  handover: string | null;
  handover_year: number | null;
  roi: string | null;
  active: boolean;
  featured: boolean;
  created_at: string;
}

const emptyUnit: Omit<Unit, 'id' | 'created_at'> = {
  title: '',
  slug: '',
  developer: '',
  image_url: '',
  price: 0,
  currency: 'AED',
  price_display: '',
  payment_plan: '',
  area_m2: null,
  beds: null,
  baths: null,
  bedrooms_label: '',
  unit_sizes: '',
  location: '',
  city: '',
  area: '',
  property_type: 'apartment',
  status: 'available',
  features: [],
  description: '',
  handover: '',
  handover_year: new Date().getFullYear() + 1,
  roi: '',
  active: true,
  featured: false,
};

const propertyTypes = ['apartment', 'villa', 'townhouse', 'penthouse', 'studio'];
const statusOptions = ['available', 'reserved', 'sold', 'rented'];
const paymentPlans = ['40/60', '50/50', '60/40', '70/30', '80/20', 'Post-handover'];

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 200);
}

function formatPrice(price: number, currency = 'AED') {
  if (!price) return '';
  if (price >= 1000000) {
    return `${currency} ${(price / 1000000).toFixed(1)}M`;
  }
  if (price >= 1000) {
    return `${currency} ${(price / 1000).toFixed(0)}K`;
  }
  return `${currency} ${price.toLocaleString()}`;
}

export default function AdminCollection() {
  const [units, setUnits] = useState<Unit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingUnit, setEditingUnit] = useState<Partial<Unit> | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [featuredFilter, setFeaturedFilter] = useState<'all' | 'featured' | 'standard'>('all');
  const { toast } = useToast();

  useEffect(() => {
    fetchUnits();
  }, [searchQuery, statusFilter, activeFilter, featuredFilter]);

  const fetchUnits = async () => {
    setIsLoading(true);
    try {
      const data = await api.inventory.listAdmin({
        q: searchQuery || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        active: activeFilter === 'all' ? undefined : activeFilter === 'active',
        featured: featuredFilter === 'all' ? undefined : featuredFilter === 'featured',
        limit: 200,
      });
      setUnits(data.units || []);
    } catch (error: any) {
      toast({
        title: 'Failed to load inventory',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editingUnit) return;

    if (!editingUnit.title || !editingUnit.location || !editingUnit.price || !editingUnit.property_type) {
      toast({ title: 'Missing required fields', description: 'Title, location, price, and type are required.', variant: 'destructive' });
      return;
    }

    const payload = {
      title: editingUnit.title,
      slug: editingUnit.slug || slugify(editingUnit.title),
      developer: editingUnit.developer || null,
      image_url: editingUnit.image_url || null,
      price: Number(editingUnit.price) || 0,
      currency: editingUnit.currency || 'AED',
      price_display: editingUnit.price_display || formatPrice(Number(editingUnit.price), editingUnit.currency || 'AED'),
      payment_plan: editingUnit.payment_plan || null,
      area_m2: editingUnit.area_m2 || null,
      beds: editingUnit.beds || null,
      baths: editingUnit.baths || null,
      bedrooms_label: editingUnit.bedrooms_label || null,
      unit_sizes: editingUnit.unit_sizes || null,
      location: editingUnit.location,
      city: editingUnit.city || null,
      area: editingUnit.area || null,
      property_type: editingUnit.property_type || 'apartment',
      status: editingUnit.status || 'available',
      features: editingUnit.features || [],
      description: editingUnit.description || null,
      handover: editingUnit.handover || null,
      handover_year: editingUnit.handover_year || null,
      roi: editingUnit.roi || null,
      active: editingUnit.active ?? true,
      featured: editingUnit.featured ?? false,
    };

    try {
      if (isCreating) {
        await api.inventory.create(payload);
        toast({ title: 'Property created' });
      } else if (editingUnit.id) {
        await api.inventory.update(editingUnit.id, payload);
        toast({ title: 'Property updated' });
      }
      setEditingUnit(null);
      setIsCreating(false);
      fetchUnits();
    } catch (error: any) {
      toast({ title: 'Save failed', description: error.message, variant: 'destructive' });
    }
  };

  const handleImageUpload = async (file: File) => {
    if (!editingUnit) return;
    setIsUploading(true);
    try {
      const data = await api.media.upload(file);
      setEditingUnit({ ...editingUnit, image_url: data.url });
      toast({ title: 'Image uploaded' });
    } catch (error: any) {
      toast({ title: 'Image upload failed', description: error.message, variant: 'destructive' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (unitId: number) => {
    if (!confirm('Delete this property?')) return;
    try {
      await api.inventory.remove(unitId);
      setUnits((prev) => prev.filter((unit) => unit.id !== unitId));
      toast({ title: 'Property removed' });
    } catch (error: any) {
      toast({ title: 'Delete failed', description: error.message, variant: 'destructive' });
    }
  };

  const stats = useMemo(() => {
    return {
      total: units.length,
      active: units.filter((unit) => unit.active).length,
      featured: units.filter((unit) => unit.featured).length,
      locations: new Set(units.map((unit) => unit.location)).size,
    };
  }, [units]);

  return (
    <AdminLayout title="Manage the live and draft inventory">
      <div className="space-y-8">
        <section className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold text-foreground">Collection manager</h2>
            <p className="text-sm text-muted-foreground">Keep the public collection curated and accurate.</p>
          </div>
          <button
            onClick={() => {
              setEditingUnit(emptyUnit);
              setIsCreating(true);
            }}
            className="btn-primary"
          >
            <Plus className="w-4 h-4" />
            Add Property
          </button>
        </section>

        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Properties', value: stats.total },
            { label: 'Active', value: stats.active },
            { label: 'Featured', value: stats.featured },
            { label: 'Locations', value: stats.locations },
          ].map((item) => (
            <div key={item.label} className="bg-card border border-border rounded-2xl p-5">
              <p className="text-2xl font-semibold text-foreground">{item.value}</p>
              <p className="text-sm text-muted-foreground">{item.label}</p>
            </div>
          ))}
        </section>

        <section className="bg-card border border-border rounded-2xl p-5">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative">
              <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search by title, developer, location"
                className="pl-9 pr-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              className="px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
            >
              <option value="all">All statuses</option>
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
            <select
              value={activeFilter}
              onChange={(event) => setActiveFilter(event.target.value as 'all' | 'active' | 'inactive')}
              className="px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
            >
              <option value="all">All visibility</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            <select
              value={featuredFilter}
              onChange={(event) => setFeaturedFilter(event.target.value as 'all' | 'featured' | 'standard')}
              className="px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
            >
              <option value="all">All featured</option>
              <option value="featured">Featured</option>
              <option value="standard">Standard</option>
            </select>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Filter className="w-4 h-4" />
              {units.length} results
            </div>
          </div>
        </section>

        {isLoading ? (
          <div className="text-center text-muted-foreground py-16">Loading inventory...</div>
        ) : units.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">No properties match those filters.</div>
        ) : (
          <section className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {units.map((unit) => (
              <div key={unit.id} className={`bg-card border border-border rounded-2xl overflow-hidden ${!unit.active ? 'opacity-70' : ''}`}>
                <div className="relative aspect-[4/3] bg-muted">
                  {getUnitImage(unit) ? (
                    <img src={getUnitImage(unit)} alt={unit.title} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-muted-foreground text-sm">
                      Image pending
                    </div>
                  )}
                  {unit.featured && (
                    <span className="absolute top-3 left-3 px-2 py-1 rounded-full text-xs bg-primary text-primary-foreground">Featured</span>
                  )}
                  {!unit.active && (
                    <span className="absolute top-3 right-3 px-2 py-1 rounded-full text-xs bg-muted text-muted-foreground">Inactive</span>
                  )}
                </div>
                <div className="p-4 space-y-3">
                  <div>
                    <h3 className="text-lg font-semibold text-foreground truncate">{unit.title}</h3>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <MapPin className="w-4 h-4" />
                      {unit.location}
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>{unit.price_display || formatPrice(unit.price, unit.currency)}</span>
                    <span>{unit.payment_plan || 'Plan TBD'}</span>
                  </div>
                  <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <span className="px-2 py-1 rounded-full bg-muted/40">{unit.handover || 'TBD'}</span>
                    {unit.roi && <span className="px-2 py-1 rounded-full bg-primary/10 text-primary">ROI {unit.roi}</span>}
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{unit.developer || 'Developer'}</span>
                    <span className="text-xs uppercase tracking-wide text-muted-foreground">{unit.status}</span>
                  </div>
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => {
                        setEditingUnit(unit);
                        setIsCreating(false);
                      }}
                      className="flex-1 btn-outline text-sm py-2"
                    >
                      <Pencil className="w-3 h-3" />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(unit.id)}
                      className="p-2 rounded-lg text-rose-400 hover:bg-rose-500/10"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </section>
        )}
      </div>

      {editingUnit && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-background border border-border rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border sticky top-0 bg-background">
              <div>
                <h3 className="text-lg font-semibold text-foreground">{isCreating ? 'Add Property' : 'Edit Property'}</h3>
                <p className="text-sm text-muted-foreground">All fields map directly to the public collection.</p>
              </div>
              <button
                onClick={() => {
                  setEditingUnit(null);
                  setIsCreating(false);
                }}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              <section className="space-y-4">
                <h4 className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <Building2 className="w-4 h-4" />
                  Basic information
                </h4>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Title *</label>
                    <input
                      value={editingUnit.title || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, title: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="Marina Vista Tower"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Slug</label>
                    <input
                      value={editingUnit.slug || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, slug: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="marina-vista-tower"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Auto-generated if left empty.</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Location *</label>
                    <input
                      value={editingUnit.location || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, location: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="Dubai Marina"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">City</label>
                    <input
                      value={editingUnit.city || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, city: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="Dubai"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Developer</label>
                    <input
                      value={editingUnit.developer || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, developer: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="Emaar Properties"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Area</label>
                    <input
                      value={editingUnit.area || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, area: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="Dubai Marina"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Property type *</label>
                    <select
                      value={editingUnit.property_type || 'apartment'}
                      onChange={(event) => setEditingUnit({ ...editingUnit, property_type: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                    >
                      {propertyTypes.map((type) => (
                        <option key={type} value={type}>
                          {type}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Image</label>
                    <div className="mt-2 space-y-2">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(event) => {
                          const file = event.target.files?.[0];
                          if (file) {
                            handleImageUpload(file);
                          }
                        }}
                        className="w-full text-sm text-muted-foreground"
                        disabled={isUploading}
                      />
                      {isUploading && (
                        <p className="text-xs text-muted-foreground">Uploading image...</p>
                      )}
                      <input
                        value={editingUnit.image_url || ''}
                        onChange={(event) => setEditingUnit({ ...editingUnit, image_url: event.target.value })}
                        className="w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                        placeholder="Paste image URL"
                      />
                      {editingUnit.image_url && (
                        <img
                          src={getUnitImage({
                            image_url: editingUnit.image_url,
                            property_type: editingUnit.property_type || 'apartment',
                          })}
                          alt={editingUnit.title || 'Preview'}
                          className="h-24 w-full rounded-lg object-cover"
                        />
                      )}
                    </div>
                  </div>
                </div>
              </section>

              <section className="space-y-4">
                <h4 className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <CreditCard className="w-4 h-4" />
                  Pricing and payment
                </h4>
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Price from (AED) *</label>
                    <input
                      type="number"
                      value={editingUnit.price || ''}
                      onChange={(event) => {
                        const value = Number(event.target.value) || 0;
                        setEditingUnit({
                          ...editingUnit,
                          price: value,
                          price_display: formatPrice(value, editingUnit.currency || 'AED'),
                        });
                      }}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="1200000"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Price display</label>
                    <input
                      value={editingUnit.price_display || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, price_display: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="AED 1.2M"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Payment plan</label>
                    <select
                      value={editingUnit.payment_plan || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, payment_plan: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                    >
                      <option value="">Select plan</option>
                      {paymentPlans.map((plan) => (
                        <option key={plan} value={plan}>
                          {plan}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </section>

              <section className="space-y-4">
                <h4 className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <Calendar className="w-4 h-4" />
                  Timeline and ROI
                </h4>
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Handover</label>
                    <input
                      value={editingUnit.handover || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, handover: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="Q4 2026"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Handover year</label>
                    <input
                      type="number"
                      value={editingUnit.handover_year || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, handover_year: Number(event.target.value) || null })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="2026"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">ROI</label>
                    <input
                      value={editingUnit.roi || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, roi: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="7-9%"
                    />
                  </div>
                </div>
              </section>

              <section className="space-y-4">
                <h4 className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <TrendingUp className="w-4 h-4" />
                  Additional details
                </h4>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Bedrooms label</label>
                    <input
                      value={editingUnit.bedrooms_label || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, bedrooms_label: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="Studio, 1BR, 2BR"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Unit sizes</label>
                    <input
                      value={editingUnit.unit_sizes || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, unit_sizes: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                      placeholder="500-2000 sqft"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Beds</label>
                    <input
                      type="number"
                      value={editingUnit.beds || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, beds: Number(event.target.value) || null })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Baths</label>
                    <input
                      type="number"
                      value={editingUnit.baths || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, baths: Number(event.target.value) || null })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Area (m2)</label>
                    <input
                      type="number"
                      value={editingUnit.area_m2 || ''}
                      onChange={(event) => setEditingUnit({ ...editingUnit, area_m2: Number(event.target.value) || null })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Status</label>
                    <select
                      value={editingUnit.status || 'available'}
                      onChange={(event) => setEditingUnit({ ...editingUnit, status: event.target.value })}
                      className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                    >
                      {statusOptions.map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Highlights (comma-separated)</label>
                  <input
                    value={(editingUnit.features || []).join(', ')}
                    onChange={(event) =>
                      setEditingUnit({
                        ...editingUnit,
                        features: event.target.value
                          .split(',')
                          .map((item) => item.trim())
                          .filter(Boolean),
                      })
                    }
                    className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                    placeholder="Prime location, Premium amenities"
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Description</label>
                  <textarea
                    value={editingUnit.description || ''}
                    onChange={(event) => setEditingUnit({ ...editingUnit, description: event.target.value })}
                    rows={3}
                    className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                    placeholder="Brief description of the property"
                  />
                </div>
              </section>

              <section className="space-y-4">
                <h4 className="text-sm font-semibold text-foreground">Settings</h4>
                <div className="flex flex-wrap gap-6 text-sm text-foreground">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={editingUnit.active ?? true}
                      onChange={(event) => setEditingUnit({ ...editingUnit, active: event.target.checked })}
                      className="rounded border-border"
                    />
                    Active (visible in collection)
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={editingUnit.featured ?? false}
                      onChange={(event) => setEditingUnit({ ...editingUnit, featured: event.target.checked })}
                      className="rounded border-border"
                    />
                    Featured
                  </label>
                </div>
              </section>
            </div>

            <div className="sticky bottom-0 bg-background border-t border-border p-4 flex justify-end gap-3">
              <button
                onClick={() => {
                  setEditingUnit(null);
                  setIsCreating(false);
                }}
                className="btn-outline"
              >
                Cancel
              </button>
              <button onClick={handleSave} className="btn-primary">
                {isCreating ? 'Create Property' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
