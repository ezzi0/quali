import { Link } from 'react-router-dom';
import Layout from '@/components/layout/Layout';
import { Target, Users, Shield, ArrowRight

 } from 'lucide-react';

export default function About() {
  return (
    <Layout>
      {/* Hero */}
      <section className="pt-32 pb-16 bg-background">
        <div className="container-wide">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="text-primary text-sm font-medium mb-4">About</p>
              <h1 className="heading-1 text-foreground mb-6">About Abriqot</h1>
              <p className="body-large text-muted-foreground mb-8">
                Abriqot is a Dubai real estate brokerage specializing in off plan apartments and villas for international buyers, with select ready and resale opportunities when the fit is right.
              </p>
              <Link to="/match" className="btn-primary inline-flex items-center gap-2">
                Request a Private Shortlist
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="aspect-[4/3] rounded-2xl overflow-hidden">
              <img 
                src="https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&h=600&fit=crop"
                alt="Dubai skyline"
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Chosen with Intent */}
      <section className="py-20 bg-muted/30">
        <div className="container-wide">
          <div className="max-w-2xl">
            <h2 className="text-2xl font-semibold text-foreground mb-6">Chosen with intent</h2>
            <p className="text-muted-foreground">
              Dubai offers extraordinary opportunities. Our role is to keep selection refined and execution clean so clients can move with confidence.
            </p>
          </div>
        </div>
      </section>

      {/* What Sets Us Apart */}
      <section className="py-20">
        <div className="container-wide">
          <h2 className="text-2xl font-semibold text-foreground mb-12 text-center">What sets us apart</h2>
          <div className="grid md:grid-cols-4 gap-8">
            {[
              { icon: Target, title: 'Focused new development expertise', desc: 'We specialize exclusively in Dubai off plan properties for investment buyers.' },
              { icon: Users, title: 'International execution by design', desc: 'Built for remote transactions with buyers outside the UAE.' },
              { icon: Shield, title: 'Refined shortlist, not a catalogue', desc: 'A focused selection aligned to your criteria, not an inventory dump.' },
              { icon: Shield, title: 'Concierge coordination', desc: 'From brief to reservation with a dedicated specialist.' },
            ].map((item) => (
              <div key={item.title} className="bg-card border border-border rounded-2xl p-6">
                <item.icon className="w-10 h-10 text-primary mb-4" />
                <h3 className="font-semibold text-foreground mb-2">{item.title}</h3>
                <p className="text-muted-foreground text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-muted/30 border-t border-border">
        <div className="container-narrow text-center">
          <h2 className="text-2xl font-semibold text-foreground mb-4">Dubai, curated for global buyers</h2>
          <p className="text-muted-foreground mb-8">
            Tell us your investment goals and we will match you with relevant opportunities.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/team" className="btn-outline">
              Meet the Team
            </Link>
            <Link to="/match" className="btn-primary inline-flex items-center gap-2">
              Request a Private Shortlist
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
}