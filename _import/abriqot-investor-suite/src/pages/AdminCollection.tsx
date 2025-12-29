import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { 
  Plus, Pencil, Trash2, LogOut, ArrowLeft, Save, X, Building2, 
  MapPin, Calendar, CreditCard, TrendingUp, Image as ImageIcon
} from 'lucide-react';
import type { User } from '@supabase/supabase-js';

interface Property {
  id: string;
  slug: string;
  title: string;
  location: string;
  developer: string;
  price_from: number;
  price_display: string;
  handover: string;
  handover_year: number;
  payment_plan: string;
  roi: string | null;
  property_type: string;
  image_url: string;
  description: string | null;
  bedrooms: string | null;
  unit_sizes: string | null;
  amenities: string[] | null;
  highlights: string[] | null;
  is_featured: boolean;
  is_active: boolean;
  created_at: string;
}

const emptyProperty: Omit<Property, 'id' | 'created_at'> = {
  slug: '',
  title: '',
  location: '',
  developer: '',
  price_from: 0,
  price_display: '',
  handover: '',
  handover_year: new Date().getFullYear() + 1,
  payment_plan: '60/40',
  roi: '',
  property_type: 'Apartment',
  image_url: '',
  description: '',
  bedrooms: '',
  unit_sizes: '',
  amenities: [],
  highlights: [],
  is_featured: false,
  is_active: true,
};

const locations = [
  'Dubai Marina',
  'Downtown Dubai',
  'Dubai Creek Harbour',
  'Palm Jumeirah',
  'Business Bay',
  'Jumeirah Village Circle',
  'Dubai Hills',
  'MBR City',
  'Arabian Ranches',
  'Dubai South',
  'Jumeirah Beach Residence',
  'DIFC',
  'Al Barari',
  'The World Islands',
];

const propertyTypes = ['Apartment', 'Villa', 'Townhouse', 'Penthouse', 'Studio'];

const paymentPlans = ['40/60', '50/50', '60/40', '70/30', '80/20', 'Post-handover'];

export default function AdminCollection() {
  const [user, setUser] = useState<User | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [properties, setProperties] = useState<Property[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingProperty, setEditingProperty] = useState<Partial<Property> | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null);
      if (!session?.user) {
        navigate('/admin/auth');
      }
    });

    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      if (!session?.user) {
        navigate('/admin/auth');
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  useEffect(() => {
    if (user) {
      checkAdminRole();
      fetchProperties();
    }
  }, [user]);

  const checkAdminRole = async () => {
    const { data } = await supabase
      .from('user_roles')
      .select('role')
      .eq('user_id', user?.id)
      .eq('role', 'admin')
      .maybeSingle();
    
    setIsAdmin(!!data);
    if (!data) {
      toast({
        title: 'Access Denied',
        description: 'You need admin privileges.',
        variant: 'destructive',
      });
    }
  };

  const fetchProperties = async () => {
    setIsLoading(true);
    const { data, error } = await supabase
      .from('properties')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      toast({
        title: 'Error loading properties',
        description: error.message,
        variant: 'destructive',
      });
    } else {
      setProperties(data || []);
    }
    setIsLoading(false);
  };

  const generateSlug = (title: string) => {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  };

  const handleSave = async () => {
    if (!editingProperty) return;

    // Validate required fields
    if (!editingProperty.title || !editingProperty.location || !editingProperty.developer || 
        !editingProperty.price_from || !editingProperty.price_display || !editingProperty.handover || 
        !editingProperty.handover_year || !editingProperty.payment_plan || !editingProperty.image_url) {
      toast({ title: 'Please fill all required fields', variant: 'destructive' });
      return;
    }

    const propertyData = {
      title: editingProperty.title,
      slug: editingProperty.slug || generateSlug(editingProperty.title),
      location: editingProperty.location,
      developer: editingProperty.developer,
      price_from: editingProperty.price_from,
      price_display: editingProperty.price_display,
      handover: editingProperty.handover,
      handover_year: editingProperty.handover_year,
      payment_plan: editingProperty.payment_plan,
      property_type: editingProperty.property_type || 'Apartment',
      image_url: editingProperty.image_url,
      roi: editingProperty.roi || null,
      description: editingProperty.description || null,
      bedrooms: editingProperty.bedrooms || null,
      unit_sizes: editingProperty.unit_sizes || null,
      amenities: editingProperty.amenities || null,
      highlights: editingProperty.highlights || null,
      is_featured: editingProperty.is_featured ?? false,
      is_active: editingProperty.is_active ?? true,
    };

    if (isCreating) {
      const { data, error } = await supabase
        .from('properties')
        .insert([propertyData])
        .select()
        .single();

      if (error) {
        toast({ title: 'Error creating property', description: error.message, variant: 'destructive' });
      } else {
        setProperties([data, ...properties]);
        toast({ title: 'Property created' });
        setEditingProperty(null);
        setIsCreating(false);
      }
    } else {
      const { error } = await supabase
        .from('properties')
        .update(propertyData)
        .eq('id', editingProperty.id);

      if (error) {
        toast({ title: 'Error updating property', description: error.message, variant: 'destructive' });
      } else {
        setProperties(properties.map(p => p.id === editingProperty.id ? { ...p, ...propertyData } as Property : p));
        toast({ title: 'Property updated' });
        setEditingProperty(null);
      }
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this property?')) return;

    const { error } = await supabase
      .from('properties')
      .delete()
      .eq('id', id);

    if (error) {
      toast({ title: 'Error deleting property', description: error.message, variant: 'destructive' });
    } else {
      setProperties(properties.filter(p => p.id !== id));
      toast({ title: 'Property deleted' });
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate('/admin/auth');
  };

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `AED ${(price / 1000000).toFixed(1)}M`;
    }
    return `AED ${(price / 1000).toFixed(0)}K`;
  };

  if (!isAdmin && user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-foreground mb-4">Access Denied</h1>
          <p className="text-muted-foreground mb-6">You need admin privileges.</p>
          <button onClick={handleLogout} className="btn-primary">
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Header */}
      <header className="bg-background border-b border-border sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <Link to="/admin" className="text-muted-foreground hover:text-foreground">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <h1 className="text-xl font-semibold text-foreground">Collection Manager</h1>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  setEditingProperty(emptyProperty);
                  setIsCreating(true);
                }}
                className="btn-primary"
              >
                <Plus className="w-4 h-4" />
                Add Property
              </button>
              <button onClick={handleLogout} className="p-2 text-muted-foreground hover:text-foreground">
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-2xl font-semibold text-foreground">{properties.length}</p>
            <p className="text-sm text-muted-foreground">Total Properties</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-2xl font-semibold text-foreground">{properties.filter(p => p.is_active).length}</p>
            <p className="text-sm text-muted-foreground">Active</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-2xl font-semibold text-foreground">{properties.filter(p => p.is_featured).length}</p>
            <p className="text-sm text-muted-foreground">Featured</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-2xl font-semibold text-foreground">{new Set(properties.map(p => p.location)).size}</p>
            <p className="text-sm text-muted-foreground">Locations</p>
          </div>
        </div>

        {/* Properties Grid */}
        {isLoading ? (
          <div className="text-center py-12 text-muted-foreground">Loading...</div>
        ) : properties.length === 0 ? (
          <div className="text-center py-12">
            <Building2 className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">No properties yet</h3>
            <p className="text-muted-foreground mb-4">Add your first property to the collection.</p>
            <button
              onClick={() => {
                setEditingProperty(emptyProperty);
                setIsCreating(true);
              }}
              className="btn-primary"
            >
              <Plus className="w-4 h-4" />
              Add Property
            </button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {properties.map((property) => (
              <div
                key={property.id}
                className={`bg-card border border-border rounded-xl overflow-hidden ${!property.is_active ? 'opacity-60' : ''}`}
              >
                <div className="aspect-video bg-muted relative">
                  {property.image_url ? (
                    <img src={property.image_url} alt={property.title} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <ImageIcon className="w-8 h-8 text-muted-foreground" />
                    </div>
                  )}
                  {property.is_featured && (
                    <span className="absolute top-2 left-2 px-2 py-1 bg-primary text-primary-foreground text-xs font-medium rounded">
                      Featured
                    </span>
                  )}
                  {!property.is_active && (
                    <span className="absolute top-2 right-2 px-2 py-1 bg-muted text-muted-foreground text-xs font-medium rounded">
                      Inactive
                    </span>
                  )}
                </div>
                <div className="p-4">
                  <h3 className="font-semibold text-foreground mb-1 truncate">{property.title}</h3>
                  <div className="flex items-center gap-1 text-sm text-muted-foreground mb-2">
                    <MapPin className="w-3 h-3" />
                    {property.location}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                    <span>{property.price_display}</span>
                    <span>{property.handover}</span>
                    <span>{property.payment_plan}</span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setEditingProperty(property);
                        setIsCreating(false);
                      }}
                      className="flex-1 btn-outline text-sm py-2"
                    >
                      <Pencil className="w-3 h-3" />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(property.id)}
                      className="p-2 text-destructive hover:bg-destructive/10 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Edit Modal */}
      {editingProperty && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-background rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-background border-b border-border p-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-foreground">
                {isCreating ? 'Add Property' : 'Edit Property'}
              </h2>
              <button
                onClick={() => {
                  setEditingProperty(null);
                  setIsCreating(false);
                }}
                className="p-2 text-muted-foreground hover:text-foreground"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div className="space-y-4">
                <h3 className="font-medium text-foreground flex items-center gap-2">
                  <Building2 className="w-4 h-4" />
                  Basic Information
                </h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Title *</label>
                    <input
                      type="text"
                      value={editingProperty.title || ''}
                      onChange={(e) => setEditingProperty({ ...editingProperty, title: e.target.value })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                      placeholder="Marina Vista Tower"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Slug</label>
                    <input
                      type="text"
                      value={editingProperty.slug || ''}
                      onChange={(e) => setEditingProperty({ ...editingProperty, slug: e.target.value })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                      placeholder="marina-vista-tower"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Auto-generated if left empty</p>
                  </div>
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Location *</label>
                    <select
                      value={editingProperty.location || ''}
                      onChange={(e) => setEditingProperty({ ...editingProperty, location: e.target.value })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                    >
                      <option value="">Select location</option>
                      {locations.map(loc => (
                        <option key={loc} value={loc}>{loc}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Developer *</label>
                    <input
                      type="text"
                      value={editingProperty.developer || ''}
                      onChange={(e) => setEditingProperty({ ...editingProperty, developer: e.target.value })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                      placeholder="Emaar Properties"
                    />
                  </div>
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Property Type *</label>
                    <select
                      value={editingProperty.property_type || 'Apartment'}
                      onChange={(e) => setEditingProperty({ ...editingProperty, property_type: e.target.value })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                    >
                      {propertyTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Image URL *</label>
                    <input
                      type="url"
                      value={editingProperty.image_url || ''}
                      onChange={(e) => setEditingProperty({ ...editingProperty, image_url: e.target.value })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                      placeholder="https://..."
                    />
                  </div>
                </div>
              </div>

              {/* Pricing */}
              <div className="space-y-4">
                <h3 className="font-medium text-foreground flex items-center gap-2">
                  <CreditCard className="w-4 h-4" />
                  Pricing & Payment
                </h3>
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Price From (AED) *</label>
                    <input
                      type="number"
                      value={editingProperty.price_from || ''}
                      onChange={(e) => {
                        const val = parseInt(e.target.value) || 0;
                        setEditingProperty({ 
                          ...editingProperty, 
                          price_from: val,
                          price_display: formatPrice(val)
                        });
                      }}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                      placeholder="1200000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Price Display *</label>
                    <input
                      type="text"
                      value={editingProperty.price_display || ''}
                      onChange={(e) => setEditingProperty({ ...editingProperty, price_display: e.target.value })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                      placeholder="AED 1.2M"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Payment Plan *</label>
                    <select
                      value={editingProperty.payment_plan || '60/40'}
                      onChange={(e) => setEditingProperty({ ...editingProperty, payment_plan: e.target.value })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                    >
                      {paymentPlans.map(plan => (
                        <option key={plan} value={plan}>{plan}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Timeline */}
              <div className="space-y-4">
                <h3 className="font-medium text-foreground flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  Timeline & ROI
                </h3>
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Handover *</label>
                    <input
                      type="text"
                      value={editingProperty.handover || ''}
                      onChange={(e) => setEditingProperty({ ...editingProperty, handover: e.target.value })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                      placeholder="Q4 2026"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Handover Year *</label>
                    <input
                      type="number"
                      value={editingProperty.handover_year || ''}
                      onChange={(e) => setEditingProperty({ ...editingProperty, handover_year: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                      placeholder="2026"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">ROI</label>
                    <input
                      type="text"
                      value={editingProperty.roi || ''}
                      onChange={(e) => setEditingProperty({ ...editingProperty, roi: e.target.value })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                      placeholder="7-9%"
                    />
                  </div>
                </div>
              </div>

              {/* Details */}
              <div className="space-y-4">
                <h3 className="font-medium text-foreground flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Additional Details
                </h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Bedrooms</label>
                    <input
                      type="text"
                      value={editingProperty.bedrooms || ''}
                      onChange={(e) => setEditingProperty({ ...editingProperty, bedrooms: e.target.value })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                      placeholder="Studio, 1BR, 2BR, 3BR"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">Unit Sizes</label>
                    <input
                      type="text"
                      value={editingProperty.unit_sizes || ''}
                      onChange={(e) => setEditingProperty({ ...editingProperty, unit_sizes: e.target.value })}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground"
                      placeholder="500-2000 sqft"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">Description</label>
                  <textarea
                    value={editingProperty.description || ''}
                    onChange={(e) => setEditingProperty({ ...editingProperty, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground resize-none"
                    placeholder="Brief description of the property..."
                  />
                </div>
              </div>

              {/* Settings */}
              <div className="space-y-4">
                <h3 className="font-medium text-foreground">Settings</h3>
                <div className="flex gap-6">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={editingProperty.is_active ?? true}
                      onChange={(e) => setEditingProperty({ ...editingProperty, is_active: e.target.checked })}
                      className="rounded border-border"
                    />
                    <span className="text-sm text-foreground">Active (visible in collection)</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={editingProperty.is_featured ?? false}
                      onChange={(e) => setEditingProperty({ ...editingProperty, is_featured: e.target.checked })}
                      className="rounded border-border"
                    />
                    <span className="text-sm text-foreground">Featured</span>
                  </label>
                </div>
              </div>
            </div>

            <div className="sticky bottom-0 bg-background border-t border-border p-4 flex justify-end gap-3">
              <button
                onClick={() => {
                  setEditingProperty(null);
                  setIsCreating(false);
                }}
                className="btn-outline"
              >
                Cancel
              </button>
              <button onClick={handleSave} className="btn-primary">
                <Save className="w-4 h-4" />
                {isCreating ? 'Create Property' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}