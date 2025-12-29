import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle, Calendar, CreditCard, FileText, Users, Target, Shield, Globe, Clock, X } from 'lucide-react';
import Layout from '@/components/layout/Layout';
import officeImage from '@/assets/office-team.jpg';

const features = [
  {
    icon: FileText,
    title: 'A refined shortlist',
    desc: 'A focused selection aligned to your criteria, delivered with context and clarity.'
  },
  {
    icon: CreditCard,
    title: 'A clear investment brief',
    desc: 'Key considerations, payment plan snapshot, timeline notes, and what to verify before you proceed.'
  },
  {
    icon: Calendar,
    title: 'Timing and access',
    desc: 'Launch alerts and early visibility when they match your profile.'
  },
  {
    icon: Users,
    title: 'Concierge execution',
    desc: 'A dedicated specialist and a remote ready process from brief to reservation.'
  }
];

const wePrioritize = [
  'Locations with durable demand',
  'Payment plans that fit real buyers',
  'Developers with delivery discipline',
  'Timing aligned to your strategy',
  'Clear documentation and verification steps'
];

const weAvoid = [
  'Inflated promises',
  'Catalogue style selling',
  'Pressure tactics',
  'Unclear terms'
];

const faq = [
  {
    q: 'Do you only work with off plan properties?',
    a: 'Yes. Off plan is our primary focus. We also present select ready and resale opportunities when the fit is exceptional.'
  },
  {
    q: 'Do you work with buyers outside the UAE?',
    a: 'Yes. Most of our clients are international and our process is built for remote execution.'
  },
  {
    q: 'Do you guarantee returns?',
    a: 'No. We provide structured guidance and transaction support. Investing involves risk and outcomes vary.'
  },
  {
    q: 'How are you compensated?',
    a: 'In most transactions, commission is paid by the developer. If any other fee applies, it is disclosed before you proceed.'
  }
];

const trustStrip = [
  'Dubai based brokerage',
  'International coverage',
  'New launches and rare allocations',
  'Specialist led execution'
];

export default function Index() {
  return (
    <Layout>
      {/* Hero - Cinematic Full Screen */}
      <section className="relative min-h-screen flex flex-col">
        {/* Video Background */}
        <div className="absolute inset-0 z-0 overflow-hidden">
          <video
            autoPlay
            muted
            loop
            playsInline
            className="absolute inset-0 w-full h-full object-cover"
            style={{ minHeight: '100%', minWidth: '100%' }}
          >
            <source src="/videos/dubai-marina.mp4" type="video/mp4" />
          </video>
          <div className="absolute inset-0 bg-black/50 dark:bg-black/60" />
          <div className="absolute inset-0 bg-gradient-to-r from-black/30 to-transparent" />
        </div>

        {/* Content - LEFT aligned, anchored to bottom */}
        <div className="flex-1 flex flex-col justify-end items-start relative z-20">
          <div className="container-wide pb-16 lg:pb-24 pt-32 w-full">
            <div className="max-w-xl">
              {/* Eyebrow */}
              <p className="text-white/70 text-sm font-light tracking-widest uppercase mb-6">
                Dubai Off Plan
              </p>
              
              {/* H1 */}
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-light text-white leading-[1.1] tracking-tight mb-6">
                <span className="block">Curated opportunities.</span>
                <span className="block text-white/80">Chosen with intent.</span>
              </h1>
              
              {/* Subhead */}
              <p className="text-white/70 text-lg font-light leading-relaxed mb-8">
                Off plan apartments and villas, plus select ready opportunities, curated for international buyers.
              </p>
              
              {/* CTAs */}
              <div className="flex flex-col sm:flex-row gap-4 mb-4">
                <Link 
                  to="/match" 
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full bg-white text-black font-medium hover:bg-white/90 transition-all duration-300 group"
                >
                  Request a Private Shortlist
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link 
                  to="/investments" 
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full border border-white/30 text-white font-medium hover:border-white/50 hover:bg-white/5 transition-all duration-300"
                >
                  Explore the Collection
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Strip */}
      <section className="py-6 border-b border-border bg-muted/30">
        <div className="container-wide">
          <div className="flex flex-wrap justify-center gap-8 md:gap-16">
            {trustStrip.map((item) => (
              <div key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                <CheckCircle className="w-4 h-4 text-primary" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Three Entry Paths */}
      <section className="section-padding">
        <div className="container-wide">
          <div className="max-w-xl mb-16">
            <h2 className="heading-2 mb-4">Start where you are</h2>
            <p className="text-muted-foreground">
              Choose a path. We will take it from there.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="group bg-card border border-border rounded-2xl p-8 hover:border-primary/50 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-6 group-hover:bg-primary/20 transition-colors">
                <CreditCard className="w-6 h-6 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground text-xl mb-3">Match by Payment Plan</h3>
              <p className="text-muted-foreground mb-6">
                Share what feels comfortable month to month or quarter to quarter. We shortlist options that fit the schedule, not just the price.
              </p>
              <Link to="/match" className="text-primary font-medium hover:underline">
                Start →
              </Link>
            </div>

            <div className="group bg-card border border-border rounded-2xl p-8 hover:border-primary/50 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-6 group-hover:bg-primary/20 transition-colors">
                <Calendar className="w-6 h-6 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground text-xl mb-3">Match by Handover Year</h3>
              <p className="text-muted-foreground mb-6">
                Align timing with your strategy. We curate based on your handover window first.
              </p>
              <Link to="/match" className="text-primary font-medium hover:underline">
                Start →
              </Link>
            </div>

            <div className="group bg-card border border-border rounded-2xl p-8 hover:border-primary/50 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-6 group-hover:bg-primary/20 transition-colors">
                <FileText className="w-6 h-6 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground text-xl mb-3">The Deal Memo Pack</h3>
              <p className="text-muted-foreground mb-6">
                See how we evaluate opportunities, what we verify, and how decisions get made.
              </p>
              <Link to="/deal-memos" className="text-primary font-medium hover:underline">
                Get the pack →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* A Quieter Way to Buy */}
      <section className="section-padding border-y border-border">
        <div className="container-wide">
          <div className="max-w-xl mb-16">
            <h2 className="heading-2 mb-4">A quieter way to buy in Dubai</h2>
            <p className="text-muted-foreground">
              Fewer options. Better fit. Cleaner execution.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((item) => (
              <div key={item.title} className="group">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                  <item.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-medium text-foreground mb-2">{item.title}</h3>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* The Abriqot Standard */}
      <section className="section-padding">
        <div className="container-wide">
          <div className="max-w-xl mb-16">
            <h2 className="heading-2 mb-4">The Abriqot standard</h2>
            <p className="text-muted-foreground">
              What we prioritize, and what we leave behind.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-12">
            <div className="bg-card border border-border rounded-2xl p-8">
              <h3 className="font-semibold text-foreground mb-6 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-primary" />
                We prioritize
              </h3>
              <ul className="space-y-3">
                {wePrioritize.map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <CheckCircle className="w-4 h-4 text-primary flex-shrink-0 mt-1" />
                    <span className="text-foreground">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-card border border-border rounded-2xl p-8">
              <h3 className="font-semibold text-foreground mb-6 flex items-center gap-2">
                <X className="w-5 h-5 text-muted-foreground" />
                We avoid
              </h3>
              <ul className="space-y-3">
                {weAvoid.map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <X className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-1" />
                    <span className="text-muted-foreground">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* International by Design */}
      <section className="section-padding border-y border-border">
        <div className="container-wide">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="heading-2 mb-6">International by design</h2>
              <p className="text-muted-foreground mb-8">
                Built for buyers outside the UAE.
              </p>
              
              <div className="space-y-4">
                {[
                  'WhatsApp and email coordination',
                  'Time zone scheduling',
                  'Clear document checklist',
                  'One point of contact throughout'
                ].map((item) => (
                  <div key={item} className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-primary flex-shrink-0" />
                    <span className="text-foreground">{item}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="relative">
              <img src={officeImage} alt="Professional office environment" className="rounded-2xl w-full h-auto" />
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="section-padding">
        <div className="container-wide">
          <div className="max-w-xl mb-16">
            <h2 className="heading-2 mb-4">From brief to reservation</h2>
            <p className="text-muted-foreground">
              Four steps. Always on your terms.
            </p>
          </div>
          
          <div className="grid md:grid-cols-4 gap-8">
            {[
              { step: '01', title: 'Private brief', desc: 'Budget, payment plan comfort, timeline, preferences. Just the inputs that matter.' },
              { step: '02', title: 'Curated shortlist', desc: 'A focused selection aligned to your criteria, shared with context.' },
              { step: '03', title: 'Investment brief', desc: 'Key considerations, timeline notes, payment plan snapshot, and what to verify.' },
              { step: '04', title: 'Execution', desc: 'Your specialist coordinates next steps, documentation, and updates.' }
            ].map((item) => (
              <div key={item.step}>
                <span className="text-4xl font-semibold text-primary/30">{item.step}</span>
                <h3 className="font-medium text-foreground mt-3 mb-2">{item.title}</h3>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-12">
            <Link to="/how-it-works" className="text-primary hover:underline text-sm font-medium">
              Learn more about our process →
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="section-padding border-y border-border">
        <div className="container-narrow">
          <h2 className="heading-3 mb-12 text-center">Frequently asked</h2>
          
          <div className="space-y-6">
            {faq.map((item) => (
              <div key={item.q} className="border-b border-border pb-6 last:border-0">
                <h3 className="font-medium text-foreground mb-2">{item.q}</h3>
                <p className="text-muted-foreground text-sm">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="section-padding">
        <div className="container-narrow text-center">
          <h2 className="heading-2 mb-4">Begin with a private brief</h2>
          <p className="text-muted-foreground mb-8 max-w-lg mx-auto">
            Tell us what you are looking for. We will return with a refined shortlist.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/match" className="btn-primary">
              Request a Private Shortlist
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
}