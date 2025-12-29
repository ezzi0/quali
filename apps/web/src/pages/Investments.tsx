import { useState, useMemo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, MapPin, Search } from 'lucide-react';
import Layout from '@/components/layout/Layout';
import { api } from '@/lib/api';
import { getUnitImage } from '@/lib/images';

interface Unit {
  id: number;
  slug: string | null;
  title: string;
  location: string;
  developer: string | null;
  price: number;
  currency: string;
  price_display: string | null;
  handover: string | null;
  handover_year: number | null;
  payment_plan: string | null;
  roi: string | null;
  property_type: string;
  image_url: string | null;
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

function formatPrice(price: number, currency: string) {
  if (price >= 1000000) {
    return `${currency} ${(price / 1000000).toFixed(1)}M`;
  }
  if (price >= 1000) {
    return `${currency} ${(price / 1000).toFixed(0)}K`;
  }
  return `${currency} ${price.toLocaleString()}`;
}

export default function Investments() {
  const [properties, setProperties] = useState<Unit[]>([]);
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
    try {
      const data = await api.inventory.searchPublic({ active: true, limit: 200 });
      setProperties(data.units || []);
    } catch (error) {
      setProperties([]);
    } finally {
      setIsLoading(false);
    }
  };

  const developers = useMemo(() => {
    const devs = new Set(properties.map((prop) => prop.developer).filter(Boolean) as string[]);
    return ['All Developers', ...Array.from(devs).sort()];
  }, [properties]);

  const filteredProperties = useMemo(() => {
    return properties.filter((prop) => {
      if (selectedLocation !== 'All Locations' && prop.location !== selectedLocation) {
        return false;
      }

      const priceRange = priceRanges[selectedPriceRange];
      if (prop.price < priceRange.min || prop.price >= priceRange.max) {
        return false;
      }

      if (selectedHandover !== 'All Handover Dates') {
        if (selectedHandover === '2028+') {
          if ((prop.handover_year || 0) < 2028) return false;
        } else {
          if (prop.handover_year !== parseInt(selectedHandover)) return false;
        }
      }

      if (selectedType !== 'All Types') {
        if (prop.property_type.toLowerCase() !== selectedType.toLowerCase()) return false;
      }

      if (selectedDeveloper !== 'All Developers') {
        if (prop.developer !== selectedDeveloper) return false;
      }

      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          prop.title.toLowerCase().includes(query) ||
          prop.location.toLowerCase().includes(query) ||
          (prop.developer || '').toLowerCase().includes(query)
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
      <section className="pt-32 pb-16 bg-background">
        <div className="container-wide">
          <div className="max-w-2xl">
            <p className="text-primary text-sm font-medium mb-4">Collection</p>
            <h1 className="heading-1 text-foreground mb-6">Off plan, curated</h1>
            <p className="body-large text-muted-foreground mb-8">
              A refined view of opportunities across apartments, villas, and select ready and resale options. Availability changes quickly.
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

      <section className="py-6 border-b border-border bg-muted/30">
        <div className="container-wide space-y-4">
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

          <p className="text-sm text-muted-foreground">
            {filteredProperties.length} {filteredProperties.length === 1 ? 'property' : 'properties'} found
          </p>
        </div>
      </section>

      <section className="section-padding">
        <div className="container-wide">
          {isLoading ? (
            <div className="text-center py-12 text-muted-foreground">Loading collection...</div>
          ) : filteredProperties.length === 0 ? (
            <div className="text-center py-16">
              <h3 className="text-lg font-medium text-foreground mb-2">Nothing matches that combination</h3>
              <p className="text-muted-foreground mb-6">Try adjusting one filter or request a private shortlist.</p>
              <Link to="/match" className="btn-primary">
                Request a Private Shortlist
              </Link>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredProperties.map((property) => {
                const image = getUnitImage(property);
                return (
                  <Link
                    key={property.id}
                    to={`/investments/${property.slug || property.id}`}
                    className="group bg-card border border-border rounded-2xl overflow-hidden hover:border-primary/50 transition-colors"
                  >
                    <div className="aspect-[4/3] overflow-hidden bg-muted">
                      {image ? (
                        <img
                          src={image}
                          alt={property.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                          Image pending
                        </div>
                      )}
                    </div>
                  <div className="p-6">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                        {property.title}
                      </h3>
                      <span className="text-sm font-medium text-primary whitespace-nowrap">
                        {property.price_display || formatPrice(property.price, property.currency)}
                      </span>
                    </div>

                    <div className="flex items-center gap-1 text-sm text-muted-foreground mb-4">
                      <MapPin className="w-4 h-4" />
                      {property.location}
                    </div>

                    <div className="flex flex-wrap gap-2 mb-4">
                      <span className="px-2 py-1 bg-muted text-muted-foreground text-xs rounded">
                        {property.handover || 'TBD'}
                      </span>
                      {property.payment_plan && (
                        <span className="px-2 py-1 bg-muted text-muted-foreground text-xs rounded">
                          {property.payment_plan}
                        </span>
                      )}
                      {property.roi && (
                        <span className="px-2 py-1 bg-primary/10 text-primary text-xs rounded">
                          {property.roi} ROI
                        </span>
                      )}
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-border">
                      <span className="text-sm text-muted-foreground">{property.developer || 'Developer'}</span>
                      <span className="text-primary text-sm font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
                        View <ArrowRight className="w-4 h-4" />
                      </span>
                    </div>
                  </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </section>

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
