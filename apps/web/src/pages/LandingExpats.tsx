import { Link } from 'react-router-dom';
import Layout from '@/components/layout/Layout';
import { Helmet } from 'react-helmet-async';
import { Home, Globe, Wallet, ArrowRight, Clock, MapPin } from 'lucide-react';

export default function LandingExpats() {
  return (
    <Layout>
      <Helmet>
        <title>Dubai Property for Expats & Relocators | Abriqot</title>
        <meta name="description" content="Relocating to Dubai? Secure an off-plan apartment or villa before you arrive. Concierge execution for expats moving from anywhere in the world." />
      </Helmet>

      {/* Hero */}
      <section className="pt-32 pb-20 bg-background">
        <div className="container-wide">
          <div className="max-w-3xl">
            <span className="text-primary text-sm font-medium tracking-wide uppercase">
              For Expats & Relocators
            </span>
            <h1 className="mt-4 text-4xl md:text-5xl lg:text-6xl font-semibold text-foreground tracking-tight leading-tight">
              Your Dubai address, arranged before you land
            </h1>
            <p className="mt-6 text-xl text-muted-foreground leading-relaxed">
              Relocating to Dubai? Secure an off-plan apartment or villa now for handover when you arrive, or as an investment while you plan the move.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4">
              <Link to="/match" className="btn-primary text-center">
                Request a Private Shortlist
              </Link>
              <Link to="/answers" className="btn-secondary text-center">
                Browse Answers
              </Link>
            </div>
            <p className="mt-4 text-sm text-muted-foreground">Concierge execution for international relocators.</p>
          </div>
        </div>
      </section>

      {/* Why expats choose off-plan */}
      <section className="py-20 bg-muted/30">
        <div className="container-wide">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-semibold text-foreground mb-3">Why expats choose off-plan</h2>
            <p className="text-muted-foreground">Align your property purchase with your relocation timeline.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-8 bg-background rounded-lg border border-border">
              <Wallet className="w-10 h-10 text-primary mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Payment plans that fit</h3>
              <p className="text-muted-foreground text-sm">
                Spread payments over construction. Many plans continue post-handover, aligning with your income timing.
              </p>
            </div>
            <div className="p-8 bg-background rounded-lg border border-border">
              <Home className="w-10 h-10 text-primary mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Brand new on arrival</h3>
              <p className="text-muted-foreground text-sm">
                Time your purchase so your home is ready when you land. No renovations, no waiting.
              </p>
            </div>
            <div className="p-8 bg-background rounded-lg border border-border">
              <Globe className="w-10 h-10 text-primary mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Remote-ready process</h3>
              <p className="text-muted-foreground text-sm">
                Complete the entire purchase from your current country. We coordinate everything locally.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Built for international execution */}
      <section className="py-20 bg-background">
        <div className="container-wide">
          <div className="max-w-3xl mx-auto text-center mb-12">
            <h2 className="text-2xl font-semibold text-foreground mb-3">International by design</h2>
            <p className="text-muted-foreground">Built for buyers outside the UAE.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl mx-auto">
            <div className="flex items-start gap-3 p-4">
              <Clock className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
              <span className="text-sm text-muted-foreground">Time zone scheduling</span>
            </div>
            <div className="flex items-start gap-3 p-4">
              <Globe className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
              <span className="text-sm text-muted-foreground">WhatsApp and email coordination</span>
            </div>
            <div className="flex items-start gap-3 p-4">
              <Home className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
              <span className="text-sm text-muted-foreground">Clear document checklist</span>
            </div>
            <div className="flex items-start gap-3 p-4">
              <MapPin className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
              <span className="text-sm text-muted-foreground">One point of contact throughout</span>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-muted/30">
        <div className="container-wide text-center">
          <h2 className="text-3xl font-semibold text-foreground mb-4">Planning your move?</h2>
          <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
            Share your timeline and preferences. We will match you with properties that align with your relocation.
          </p>
          <Link to="/match" className="btn-primary inline-flex items-center gap-2">
            Request a Private Shortlist <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </Layout>
  );
}