import { Link } from 'react-router-dom';
import Layout from '@/components/layout/Layout';
import { Helmet } from 'react-helmet-async';
import { TrendingUp, Shield, Clock, ArrowRight, BarChart3, FileCheck } from 'lucide-react';

export default function LandingInvestors() {
  return (
    <Layout>
      <Helmet>
        <title>Dubai Off-Plan Investment for Global Investors | Abriqot</title>
        <meta name="description" content="Access Dubai's highest-yield off-plan properties. Independent analysis, vetted developers, and personalized matching for serious investors." />
      </Helmet>

      {/* Hero */}
      <section className="pt-32 pb-20 bg-background">
        <div className="container-wide">
          <div className="max-w-3xl">
            <span className="text-primary text-sm font-medium tracking-wide uppercase">
              For Serious Investors
            </span>
            <h1 className="mt-4 text-4xl md:text-5xl lg:text-6xl font-semibold text-foreground tracking-tight leading-tight">
              Dubai off-plan with institutional-grade analysis
            </h1>
            <p className="mt-6 text-xl text-muted-foreground leading-relaxed">
              Skip the sales pitches. Get independent deal memos, developer vetting, and a curated shortlist based on your investment criteria.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4">
              <Link to="/match" className="btn-primary text-center">
                Request a Private Shortlist
              </Link>
              <Link to="/deal-memos" className="btn-secondary text-center">
                Get the Deal Memo Pack
              </Link>
            </div>
            <p className="mt-4 text-sm text-muted-foreground">A shortlist that fits your strategy, not just your budget.</p>
          </div>
        </div>
      </section>

      {/* Value Props */}
      <section className="py-20 bg-muted/30">
        <div className="container-wide">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-semibold text-foreground mb-3">What serious investors receive</h2>
            <p className="text-muted-foreground">Analysis and execution built for portfolio allocation.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-8 bg-background rounded-lg border border-border">
              <TrendingUp className="w-10 h-10 text-primary mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Yield-focused selection</h3>
              <p className="text-muted-foreground text-sm">
                We analyze ROI projections, rental yields, and capital appreciation potential for every project we recommend.
              </p>
            </div>
            <div className="p-8 bg-background rounded-lg border border-border">
              <Shield className="w-10 h-10 text-primary mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Developer due diligence</h3>
              <p className="text-muted-foreground text-sm">
                Track record analysis, delivery history, and escrow compliance verification for every developer.
              </p>
            </div>
            <div className="p-8 bg-background rounded-lg border border-border">
              <Clock className="w-10 h-10 text-primary mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">Time-efficient process</h3>
              <p className="text-muted-foreground text-sm">
                Receive a curated shortlist within 24 hours. No endless browsing or catalogue-style presentations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* What you get */}
      <section className="py-20 bg-background">
        <div className="container-wide">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-semibold text-foreground mb-8 text-center">Investment-grade deliverables</h2>
            <div className="space-y-6">
              <div className="flex items-start gap-4 p-6 bg-card border border-border rounded-xl">
                <BarChart3 className="w-6 h-6 text-primary flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium text-foreground mb-1">Deal memos</h3>
                  <p className="text-sm text-muted-foreground">Structured analysis covering location fundamentals, developer track record, payment plan mechanics, and key risk factors.</p>
                </div>
              </div>
              <div className="flex items-start gap-4 p-6 bg-card border border-border rounded-xl">
                <FileCheck className="w-6 h-6 text-primary flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium text-foreground mb-1">Verification checklist</h3>
                  <p className="text-sm text-muted-foreground">What to confirm before reservation: RERA registration, escrow setup, SPA terms, and documentation requirements.</p>
                </div>
              </div>
              <div className="flex items-start gap-4 p-6 bg-card border border-border rounded-xl">
                <TrendingUp className="w-6 h-6 text-primary flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-medium text-foreground mb-1">Payment plan comparison</h3>
                  <p className="text-sm text-muted-foreground">Side-by-side analysis of payment structures across shortlisted opportunities.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-muted/30">
        <div className="container-wide text-center">
          <h2 className="text-3xl font-semibold text-foreground mb-4">Ready to invest smarter?</h2>
          <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
            Tell us your budget, timeline, and goals. We will match you with opportunities that fit your strategy.
          </p>
          <Link to="/match" className="btn-primary inline-flex items-center gap-2">
            Request a Private Shortlist <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </Layout>
  );
}