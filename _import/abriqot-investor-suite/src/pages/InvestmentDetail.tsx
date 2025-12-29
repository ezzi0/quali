import { useParams, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { ArrowLeft, MapPin, CheckCircle } from 'lucide-react';
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
  description: string | null;
  bedrooms: string | null;
  unit_sizes: string | null;
  amenities: string[] | null;
  highlights: string[] | null;
}

const defaultHighlights = [
  'Prime location',
  'Premium amenities',
  'Flexible payment plan',
  'Quality construction',
  'Modern design',
  'Developer track record',
];

export default function InvestmentDetail() {
  const { id } = useParams();
  const [property, setProperty] = useState<Property | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchProperty();
    }
  }, [id]);

  const fetchProperty = async () => {
    setIsLoading(true);
    const { data, error } = await supabase
      .from('properties')
      .select('*')
      .eq('slug', id)
      .eq('is_active', true)
      .maybeSingle();

    if (!error && data) {
      setProperty(data);
    }
    setIsLoading(false);
  };

  if (isLoading) {
    return (
      <Layout>
        <section className="pt-32 pb-16">
          <div className="container-wide text-center text-muted-foreground">
            Loading...
          </div>
        </section>
      </Layout>
    );
  }

  if (!property) {
    return (
      <Layout>
        <section className="pt-32 pb-16">
          <div className="container-wide text-center">
            <h1 className="heading-2 text-foreground mb-4">Property not found</h1>
            <p className="text-muted-foreground mb-8">This property may no longer be available.</p>
            <Link to="/investments" className="btn-primary">
              Back to Collection
            </Link>
          </div>
        </section>
      </Layout>
    );
  }

  const highlights = property.highlights?.length ? property.highlights : defaultHighlights;

  return (
    <Layout>
      {/* Hero */}
      <section className="pt-24 pb-8 bg-background">
        <div className="container-wide">
          <Link to="/investments" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Collection
          </Link>
          
          <div className="aspect-[2/1] rounded-2xl overflow-hidden mb-8 bg-muted">
            <img
              src={property.image_url}
              alt={property.title}
              className="w-full h-full object-cover"
            />
          </div>
        </div>
      </section>

      {/* Details */}
      <section className="pb-16">
        <div className="container-wide">
          <div className="grid lg:grid-cols-3 gap-12">
            {/* Main Content */}
            <div className="lg:col-span-2">
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <MapPin className="w-4 h-4" />
                {property.location}
              </div>
              <h1 className="heading-2 text-foreground mb-2">{property.title}</h1>
              <p className="text-muted-foreground mb-8">by {property.developer}</p>

              {property.description && (
                <div className="prose prose-lg max-w-none mb-12">
                  <p className="text-muted-foreground">{property.description}</p>
                </div>
              )}

              {/* Why It Fits */}
              <div className="mb-12">
                <h2 className="heading-4 mb-6">Why it fits</h2>
                <div className="grid sm:grid-cols-2 gap-4">
                  {highlights.map((highlight) => (
                    <div key={highlight} className="flex items-center gap-3">
                      <CheckCircle className="w-5 h-5 text-primary flex-shrink-0" />
                      <span className="text-foreground">{highlight}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* What to verify */}
              <div className="p-6 bg-muted/50 border border-border rounded-xl">
                <h3 className="font-semibold text-foreground mb-4">What to verify</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li>• RERA registration and escrow account details</li>
                  <li>• Developer track record and delivery history</li>
                  <li>• Payment plan schedule and terms</li>
                  <li>• Unit specifications and floor plans</li>
                  <li>• Service charge estimates</li>
                </ul>
              </div>
            </div>

            {/* Sidebar */}
            <div className="lg:col-span-1">
              <div className="sticky top-32 bg-card border border-border rounded-2xl p-6">
                <h3 className="font-semibold text-foreground mb-4">At a glance</h3>
                <div className="space-y-4 mb-6">
                  <div className="flex justify-between items-center py-3 border-b border-border">
                    <span className="text-muted-foreground">Starting from</span>
                    <span className="font-semibold text-foreground">{property.price_display}</span>
                  </div>
                  <div className="flex justify-between items-center py-3 border-b border-border">
                    <span className="text-muted-foreground">Handover</span>
                    <span className="font-medium text-foreground">{property.handover}</span>
                  </div>
                  <div className="flex justify-between items-center py-3 border-b border-border">
                    <span className="text-muted-foreground">Payment plan</span>
                    <span className="font-medium text-foreground">{property.payment_plan}</span>
                  </div>
                  <div className="flex justify-between items-center py-3 border-b border-border">
                    <span className="text-muted-foreground">Property type</span>
                    <span className="font-medium text-foreground">{property.property_type}</span>
                  </div>
                  {property.roi && (
                    <div className="flex justify-between items-center py-3">
                      <span className="text-muted-foreground">Projected ROI</span>
                      <span className="font-medium text-primary">{property.roi}</span>
                    </div>
                  )}
                </div>

                <Link to="/match" className="btn-primary w-full justify-center mb-3">
                  Request a Private Shortlist
                </Link>
                <Link to="/match" className="btn-outline w-full justify-center">
                  Request an Investment Brief
                </Link>

                <p className="text-xs text-muted-foreground/70 mt-4 text-center">
                  Information is general guidance, not financial advice.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </Layout>
  );
}