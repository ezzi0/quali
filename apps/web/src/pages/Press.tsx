import { Link } from 'react-router-dom';
import { ArrowRight, ExternalLink } from 'lucide-react';
import Layout from '@/components/layout/Layout';

const pressItems = [
  {
    title: 'Dubai Off-Plan Market Sees Record International Investment',
    publication: 'Gulf News',
    date: 'December 2024',
    excerpt: 'International buyers continue to drive demand in Dubai\'s off-plan sector...',
    link: '#',
  },
  {
    title: 'How Technology is Transforming Dubai Real Estate',
    publication: 'Arabian Business',
    date: 'November 2024',
    excerpt: 'Digital platforms are making it easier than ever for international investors...',
    link: '#',
  },
];

export default function Press() {
  return (
    <Layout>
      {/* Hero */}
      <section className="pt-32 pb-16 bg-background">
        <div className="container-wide">
          <div className="max-w-2xl">
            <h1 className="heading-1 text-foreground mb-6">
              Press and media
            </h1>
            <p className="body-large text-muted-foreground">
              Updates and coverage related to Abriqot and Dubai real estate.
            </p>
          </div>
        </div>
      </section>

      {/* Press Items */}
      <section className="section-padding">
        <div className="container-wide">
          <p className="text-sm text-muted-foreground mb-8">Updates and coverage, in one place.</p>
          {pressItems.length > 0 ? (
            <div className="space-y-6">
              {pressItems.map((item) => (
                <a
                  key={item.title}
                  href={item.link}
                  className="block p-6 bg-card border border-border rounded-2xl hover:border-primary/50 transition-colors"
                >
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-primary font-medium text-sm">{item.publication}</span>
                        <span className="text-muted-foreground text-sm">{item.date}</span>
                      </div>
                      <h3 className="font-semibold text-foreground text-lg mb-2">{item.title}</h3>
                      <p className="text-muted-foreground text-sm">{item.excerpt}</p>
                    </div>
                    <ExternalLink className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <p className="text-muted-foreground">No public mentions yet. For media inquiries, contact us below.</p>
            </div>
          )}
        </div>
      </section>

      {/* Media Contact */}
      <section className="section-padding bg-card border-t border-border">
        <div className="container-narrow text-center">
          <h2 className="heading-3 mb-4">Media inquiries</h2>
          <p className="text-muted-foreground mb-8">
            For press inquiries, please contact our media team.
          </p>
          <Link to="/contact" className="btn-primary inline-flex items-center gap-2">
            Contact Us
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </Layout>
  );
}