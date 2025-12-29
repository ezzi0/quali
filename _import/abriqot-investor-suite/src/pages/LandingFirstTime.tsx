import { Link } from 'react-router-dom';
import Layout from '@/components/layout/Layout';
import { Helmet } from 'react-helmet-async';
import { BookOpen, Users, CheckCircle, ArrowRight, Shield, FileText } from 'lucide-react';

export default function LandingFirstTime() {
  return (
    <Layout>
      <Helmet>
        <title>First-Time Dubai Property Buyer Guide | Abriqot</title>
        <meta name="description" content="New to Dubai real estate? A refined process for first-time international buyers. Educational resources, personal guidance, and vetted opportunities." />
      </Helmet>

      {/* Hero */}
      <section className="pt-32 pb-20 bg-background">
        <div className="container-wide">
          <div className="max-w-3xl">
            <span className="text-primary text-sm font-medium tracking-wide uppercase">
              For First-Time Buyers
            </span>
            <h1 className="mt-4 text-4xl md:text-5xl lg:text-6xl font-semibold text-foreground tracking-tight leading-tight">
              Your first Dubai property, done with clarity
            </h1>
            <p className="mt-6 text-xl text-muted-foreground leading-relaxed">
              Buying off-plan in Dubai does not have to be complicated. We guide international buyers through every step, from selection to handover.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4">
              <Link to="/match" className="btn-primary text-center">
                Request a Private Shortlist
              </Link>
              <Link to="/guides" className="btn-secondary text-center">
                Read Our Guides
              </Link>
            </div>
            <p className="mt-4 text-sm text-muted-foreground">A clearer way to decide.</p>
          </div>
        </div>
      </section>

      {/* How We Support */}
      <section className="py-20 bg-muted/30">
        <div className="container-wide">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-semibold text-foreground mb-3">How we support first-time buyers</h2>
            <p className="text-muted-foreground">Everything you need to move forward with confidence.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-8 bg-background rounded-lg border border-border">
              <BookOpen className="w-10 h-10 text-primary mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Educational resources</h3>
              <p className="text-muted-foreground text-sm">
                Plain-language guides covering payment plans, legal requirements, and what to expect at each stage.
              </p>
            </div>
            <div className="p-8 bg-background rounded-lg border border-border">
              <Users className="w-10 h-10 text-primary mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Personal guidance</h3>
              <p className="text-muted-foreground text-sm">
                A dedicated specialist who speaks your language and understands international buyer considerations.
              </p>
            </div>
            <div className="p-8 bg-background rounded-lg border border-border">
              <CheckCircle className="w-10 h-10 text-primary mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Vetted opportunities</h3>
              <p className="text-muted-foreground text-sm">
                We only present projects from developers with delivery discipline and proper escrow arrangements.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* What you get */}
      <section className="py-20 bg-background">
        <div className="container-wide">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-semibold text-foreground mb-8 text-center">What you receive</h2>
            <div className="space-y-6">
              <div className="flex items-start gap-4 p-6 bg-card border border-border rounded-xl">
                <Shield className="w-6 h-6 text-primary flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium text-foreground mb-1">A refined shortlist</h3>
                  <p className="text-sm text-muted-foreground">A focused selection aligned to your criteria, delivered with context and clarity.</p>
                </div>
              </div>
              <div className="flex items-start gap-4 p-6 bg-card border border-border rounded-xl">
                <FileText className="w-6 h-6 text-primary flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium text-foreground mb-1">A clear investment brief</h3>
                  <p className="text-sm text-muted-foreground">Key considerations, payment plan snapshot, timeline notes, and what to verify before you proceed.</p>
                </div>
              </div>
              <div className="flex items-start gap-4 p-6 bg-card border border-border rounded-xl">
                <Users className="w-6 h-6 text-primary flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium text-foreground mb-1">Concierge execution</h3>
                  <p className="text-sm text-muted-foreground">A dedicated specialist and a remote-ready process from brief to reservation.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-muted/30">
        <div className="container-wide text-center">
          <h2 className="text-3xl font-semibold text-foreground mb-4">Ready to explore?</h2>
          <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
            Tell us about yourself and we will recommend the best starting point for your Dubai investment.
          </p>
          <Link to="/match" className="btn-primary inline-flex items-center gap-2">
            Request a Private Shortlist <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </Layout>
  );
}