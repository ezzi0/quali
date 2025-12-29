import { Link } from 'react-router-dom';
import { ArrowRight, Clock } from 'lucide-react';
import Layout from '@/components/layout/Layout';

const guides = [
  {
    slug: 'off-plan-vs-ready',
    title: 'Off-Plan vs Ready Property: Which is Right for You?',
    excerpt: 'Understand the key differences between off-plan and ready properties in Dubai.',
    readTime: '8 min read',
    category: 'Payment plans',
    image: 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=600&h=400&fit=crop',
  },
  {
    slug: 'payment-plans-explained',
    title: 'Dubai Payment Plans Explained',
    excerpt: 'A complete breakdown of developer payment plans, including 60/40, 70/30, and post-handover options.',
    readTime: '6 min read',
    category: 'Payment plans',
    image: 'https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=600&h=400&fit=crop',
  },
  {
    slug: 'golden-visa-property',
    title: 'How to Get a Golden Visa Through Property Investment',
    excerpt: 'Step-by-step guide to obtaining UAE residency through real estate investment.',
    readTime: '10 min read',
    category: 'Remote buying',
    image: 'https://images.unsplash.com/photo-1582407947304-fd86f028f716?w=600&h=400&fit=crop',
  },
  {
    slug: 'due-diligence-checklist',
    title: 'The Complete Due Diligence Checklist',
    excerpt: 'Everything you need to verify before committing to an off-plan purchase.',
    readTime: '12 min read',
    category: 'Developer diligence',
    image: 'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=600&h=400&fit=crop',
  },
  {
    slug: 'rental-yields-dubai',
    title: 'Understanding Rental Yields in Dubai',
    excerpt: 'How to calculate and compare rental yields across different Dubai neighborhoods.',
    readTime: '7 min read',
    category: 'Handover strategy',
    image: 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600&h=400&fit=crop',
  },
  {
    slug: 'buying-remotely',
    title: 'How to Buy Dubai Property Remotely',
    excerpt: 'A practical guide for international buyers on completing purchases without visiting Dubai.',
    readTime: '9 min read',
    category: 'Remote buying',
    image: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600&h=400&fit=crop',
  },
];

export default function Guides() {
  return (
    <Layout>
      {/* Hero */}
      <section className="pt-32 pb-16 bg-background">
        <div className="container-wide">
          <div className="max-w-2xl">
            <p className="text-primary text-sm font-medium mb-4">Guides</p>
            <h1 className="heading-1 text-foreground mb-6">
              Dubai off plan, clearly explained
            </h1>
            <p className="body-large text-muted-foreground mb-8">
              Short, focused guides for international buyers evaluating off plan opportunities in Dubai.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link to="/answers" className="btn-primary">
                Browse Answers
              </Link>
              <Link to="/match" className="btn-outline">
                Request a Private Shortlist
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Guides Grid */}
      <section className="pb-20">
        <div className="container-wide">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {guides.map((guide) => (
              <Link
                key={guide.slug}
                to={`/guides/${guide.slug}`}
                className="group bg-card border border-border rounded-2xl overflow-hidden hover:border-primary/50 transition-colors"
              >
                <div className="aspect-[3/2] overflow-hidden">
                  <img 
                    src={guide.image} 
                    alt={guide.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                </div>
                <div className="p-6">
                  <span className="inline-block px-3 py-1 bg-primary/10 text-primary text-xs font-medium rounded-full mb-3">
                    {guide.category}
                  </span>
                  <h3 className="font-semibold text-foreground text-lg mb-2 group-hover:text-primary transition-colors">
                    {guide.title}
                  </h3>
                  <p className="text-muted-foreground text-sm mb-4 line-clamp-2">
                    {guide.excerpt}
                  </p>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="w-4 h-4" />
                    {guide.readTime}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-muted/30 border-t border-border">
        <div className="container-narrow text-center">
          <h2 className="text-2xl font-semibold text-foreground mb-4">Want a shortlist built around your criteria?</h2>
          <p className="text-muted-foreground mb-8">
            Start with a brief. We will return with a refined selection.
          </p>
          <Link to="/match" className="btn-primary inline-flex items-center gap-2">
            Request a Private Shortlist
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </Layout>
  );
}