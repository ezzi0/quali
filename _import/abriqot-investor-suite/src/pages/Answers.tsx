import { Link } from 'react-router-dom';
import { ArrowRight, Search } from 'lucide-react';
import Layout from '@/components/layout/Layout';

const answerCategories = [
  {
    category: 'Getting Started',
    answers: [
      { slug: 'what-is-off-plan', question: 'What is off-plan property?' },
      { slug: 'minimum-investment', question: 'What is the minimum investment amount?' },
    ],
  },
  {
    category: 'Payment & Financing',
    answers: [
      { slug: 'payment-plan-options', question: 'What payment plan options are available?' },
      { slug: 'can-i-get-mortgage', question: 'Can I get a mortgage for off-plan property?' },
    ],
  },
  {
    category: 'Legal & Process',
    answers: [
      { slug: 'buying-as-foreigner', question: 'Can foreigners buy property in Dubai?' },
      { slug: 'what-is-escrow', question: 'What is an escrow account?' },
    ],
  },
  {
    category: 'Returns & Risk',
    answers: [
      { slug: 'expected-returns', question: 'What returns can I expect?' },
      { slug: 'what-are-risks', question: 'What are the risks of off-plan investment?' },
    ],
  },
];

export default function Answers() {
  return (
    <Layout>
      {/* Hero */}
      <section className="pt-32 pb-16 bg-background">
        <div className="container-wide">
          <div className="max-w-2xl">
            <p className="text-primary text-sm font-medium mb-4">Answers</p>
            <h1 className="heading-1 text-foreground mb-6">
              Quick answers, clean next steps
            </h1>
            <p className="body-large text-muted-foreground mb-8">
              The essentials, in plain language. If you want a curated shortlist, start with the brief.
            </p>
            
            {/* Search */}
            <div className="relative mb-8">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search answers..."
                className="w-full pl-12 pr-4 py-3 border border-border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>

            <Link to="/match" className="btn-primary">
              Request a Private Shortlist
            </Link>
          </div>
        </div>
      </section>

      {/* Answers by Category */}
      <section className="section-padding">
        <div className="container-wide">
          <div className="grid md:grid-cols-2 gap-12">
            {answerCategories.map((category) => (
              <div key={category.category}>
                <h2 className="font-semibold text-foreground text-lg mb-4">{category.category}</h2>
                <div className="space-y-2">
                  {category.answers.map((answer) => (
                    <Link
                      key={answer.slug}
                      to={`/answers/${answer.slug}`}
                      className="block p-4 bg-card border border-border rounded-xl hover:border-primary/50 transition-colors"
                    >
                      <span className="text-foreground">{answer.question}</span>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="section-padding bg-card border-t border-border">
        <div className="container-narrow text-center">
          <h2 className="heading-3 mb-4">Fast clarity. Real next steps.</h2>
          <p className="text-muted-foreground mb-8">
            Get in touch and we will help you directly.
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