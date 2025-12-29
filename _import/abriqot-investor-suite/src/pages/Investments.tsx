import { useState, useMemo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, MapPin, Search } from 'lucide-react';
import Layout from '@/components/layout/Layout';
import { supabase } from '@/integrations/supabase/client';

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
}

const locations = [
  'All Locations',
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
];

const priceRanges = [
  { label: 'All Price Ranges', min: 0, max: Infinity },
  { label: 'Under AED 1M', min: 0, max: 1000000 },
  { label: 'AED 1M - 2M', min: 1000000, max: 2000000 },
  { label: 'AED 2M - 5M', min: 2000000, max: 5000000 },
  { label: 'Above AED 5M', min: 5000000, max: Infinity },
];

const handoverYears = ['All Handover Dates', '2025', '2026', '2027', '2028+'];

const propertyTypes = ['All Types', 'Apartment', 'Villa', 'Townhouse'];

export default function Investments() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedLocation, setSelectedLocation] = useState('All Locations');
  const [selectedPriceRange, setSelectedPriceRange] = useState(0);
  const [selectedHandover, setSelectedHandover] = useState('All Handover Dates');
  const [selectedType, setSelectedType] = useState('All Types');
  const [selectedDeveloper, setSelectedDeveloper] = useState('All Developers');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchProperties();
  }, []);

  const fetchProperties = async () => {
    setIsLoading(true);
    const { data, error } = await supabase
      .from('properties')
      .select('id, slug, title, location, developer, price_from, price_display, handover, handover_year, payment_plan, roi, property_type, image_url')
      .eq('is_active', true)
      .order('created_at', { ascending: false });

    if (!error && data) {
      setProperties(data);
    }
    setIsLoading(false);
  };

  // Get unique developers from properties
  const developers = useMemo(() => {
    const devs = new Set(properties.map(p => p.developer));
    return ['All Developers', ...Array.from(devs).sort()];
  }, [properties]);

  const filteredProperties = useMemo(() => {
    return properties.filter((prop) => {
      // Location filter
      if (selectedLocation !== 'All Locations' && prop.location !== selectedLocation) {
        return false;
      }

      // Price range filter
      const priceRange = priceRanges[selectedPriceRange];
      if (prop.price_from < priceRange.min || prop.price_from >= priceRange.max) {
        return false;
      }

      // Handover filter
      if (selectedHandover !== 'All Handover Dates') {
        if (selectedHandover === '2028+') {
          if (prop.handover_year < 2028) return false;
        } else {
          if (prop.handover_year !== parseInt(selectedHandover)) return false;
        }
      }

      // Property type filter
      if (selectedType !== 'All Types' && prop.property_type !== selectedType) {
        return false;
      }

      // Developer filter
      if (selectedDeveloper !== 'All Developers' && prop.developer !== selectedDeveloper) {
        return false;
      }

      // Search query
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          prop.title.toLowerCase().includes(query) ||
          prop.location.toLowerCase().includes(query) ||
          prop.developer.toLowerCase().includes(query)
        );
      }

      return true;
    });
  }, [properties, selectedLocation, selectedPriceRange, selectedHandover, selectedType, selectedDeveloper, searchQuery]);

  const clearFilters = () => {
    setSelectedLocation('All Locations');
    setSelectedPriceRange(0);
    setSelectedHandover('All Handover Dates');
    setSelectedType('All Types');
    setSelectedDeveloper('All Developers');
    setSearchQuery('');
  };

  const hasActiveFilters =
    selectedLocation !== 'All Locations' ||
    selectedPriceRange !== 0 ||
    selectedHandover !== 'All Handover Dates' ||
    selectedType !== 'All Types' ||
    selectedDeveloper !== 'All Developers' ||
    searchQuery !== '';

  return (
    <Layout>
      {/* Hero */}
      <section className="pt-32 pb-16 bg-background">
        <div className="container-wide">
          <div className="max-w-2xl">
            <p className="text-primary text-sm font-medium mb-4">Collection</p>
            <h1 className="heading-1 text-foreground mb-6">
              Off plan, curated
            </h1>
            <p className="body-large text-muted-foreground mb-8">
              A refined view of opportunities across apartments, villas, and select ready and resale options. Availability changes quickly. For the most accurate shortlist, start with the brief.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link to="/match" className="btn-primary">
                Request a Private Shortlist
              </Link>
              <Link to="/launch-list" className="btn-outline">
                Join the Launch List
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Filters */}
      <section className="py-6 border-b border-border bg-muted/30">
        <div className="container-wide space-y-4">
          {/* Search */}
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search properties..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          {/* Filter selects */}
          <div className="flex flex-wrap gap-3">
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="px-4 py-2 border border-border rounded-lg bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              {locations.map((loc) => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>

            <select
              value={selectedPriceRange}
              onChange={(e) => setSelectedPriceRange(Number(e.target.value))}
              className="px-4 py-2 border border-border rounded-lg bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              {priceRanges.map((range, idx) => (
                <option key={range.label} value={idx}>{range.label}</option>
              ))}
            </select>

            <select
              value={selectedHandover}
              onChange={(e) => setSelectedHandover(e.target.value)}
              className="px-4 py-2 border border-border rounded-lg bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              {handoverYears.map((year) => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>

            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-4 py-2 border border-border rounded-lg bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              {propertyTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>

            <select
              value={selectedDeveloper}
              onChange={(e) => setSelectedDeveloper(e.target.value)}
              className="px-4 py-2 border border-border rounded-lg bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              {developers.map((dev) => (
                <option key={dev} value={dev}>{dev}</option>
              ))}
            </select>

            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Clear filters
              </button>
            )}
          </div>

          {/* Results count */}
          <p className="text-sm text-muted-foreground">
            {filteredProperties.length} {filteredProperties.length === 1 ? 'property' : 'properties'} found
          </p>
        </div>
      </section>

      {/* Properties Grid */}
      <section className="section-padding">
        <div className="container-wide">
          {isLoading ? (
            <div className="text-center py-12 text-muted-foreground">Loading collection...</div>
          ) : filteredProperties.length === 0 ? (
            <div className="text-center py-16">
              <h3 className="text-lg font-medium text-foreground mb-2">Nothing matches that combination</h3>
              <p className="text-muted-foreground mb-6">Try adjusting one filter or request a private shortlist for more precise options.</p>
              <Link to="/match" className="btn-primary">
                Request a Private Shortlist
              </Link>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredProperties.map((property) => (
                <Link
                  key={property.id}
                  to={`/investments/${property.slug}`}
                  className="group bg-card border border-border rounded-2xl overflow-hidden hover:border-primary/50 transition-colors"
                >
                  <div className="aspect-[4/3] overflow-hidden bg-muted">
                    <img
                      src={property.image_url}
                      alt={property.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  </div>
                  <div className="p-6">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                        {property.title}
                      </h3>
                      <span className="text-sm font-medium text-primary whitespace-nowrap">
                        {property.price_display}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-1 text-sm text-muted-foreground mb-4">
                      <MapPin className="w-4 h-4" />
                      {property.location}
                    </div>

                    <div className="flex flex-wrap gap-2 mb-4">
                      <span className="px-2 py-1 bg-muted text-muted-foreground text-xs rounded">
                        {property.handover}
                      </span>
                      <span className="px-2 py-1 bg-muted text-muted-foreground text-xs rounded">
                        {property.payment_plan}
                      </span>
                      {property.roi && (
                        <span className="px-2 py-1 bg-primary/10 text-primary text-xs rounded">
                          {property.roi} ROI
                        </span>
                      )}
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-border">
                      <span className="text-sm text-muted-foreground">{property.developer}</span>
                      <span className="text-primary text-sm font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
                        View <ArrowRight className="w-4 h-4" />
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* CTA */}
      <section className="section-padding border-t border-border">
        <div className="container-narrow text-center">
          <h2 className="heading-3 mb-4">Looking for something specific?</h2>
          <p className="text-muted-foreground mb-8">
            Tell us your criteria and we will curate a private shortlist tailored to your needs.
          </p>
          <Link to="/match" className="btn-primary">
            Request a Private Shortlist
          </Link>
        </div>
      </section>
    </Layout>
  );
}