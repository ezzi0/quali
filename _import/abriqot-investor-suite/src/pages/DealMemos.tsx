import { useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '@/components/layout/Layout';
import DefinitionBox from '@/components/shared/DefinitionBox';
import FAQBlock from '@/components/shared/FAQBlock';
import UpdatedBlock from '@/components/shared/UpdatedBlock';
import { FileText, CheckCircle, Download, Eye } from 'lucide-react';

const packContents = [
  'Sample deal memo',
  'Payment plan comparison sheet',
  'Developer and documentation checklist',
  'Remote buying steps',
  'Questions to ask before reservation',
];

const faqItems = [
  {
    question: 'Is this free?',
    answer: 'Yes. The Deal Memo Pack is complimentary and sent directly to your email.',
  },
  {
    question: 'Can I get a deal memo for a specific property?',
    answer: 'Yes. Complete the private brief and we will create personalized investment briefs for your shortlisted options.',
  },
];

export default function DealMemos() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    country: '',
    whatsapp: '',
  });
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    // Track event
    if (typeof window !== 'undefined' && (window as any).dataLayer) {
      (window as any).dataLayer.push({ event: 'dealmemo_submit' });
    }

    // Simulate form submission
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    console.log('Deal memo form submission:', formData);
    setIsSubmitted(true);
    setIsLoading(false);
  };

  if (isSubmitted) {
    return (
      <Layout>
        <section className="section-padding min-h-[80vh] flex items-center">
          <div className="container-narrow text-center">
            <div className="w-20 h-20 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-10 h-10 text-accent" />
            </div>
            <h1 className="heading-2 mb-4">Sent</h1>
            <p className="body-large text-muted-foreground mb-8">
              Check your inbox. If you do not see it, check promotions or spam folders.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/match" className="btn-primary">
                Request a Private Shortlist
              </Link>
              <Link to="/investments" className="btn-secondary">
                Explore the Collection
              </Link>
            </div>
          </div>
        </section>
      </Layout>
    );
  }

  return (
    <Layout>
      {/* Hero */}
      <section className="section-padding bg-gradient-hero">
        <div className="container-wide">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <FileText className="w-5 h-5 text-accent" />
                <span className="text-accent font-medium">Complimentary Download</span>
              </div>
              <h1 className="heading-1 text-foreground mb-6">
                The Abriqot Deal Memo Pack
              </h1>
              <p className="body-large text-muted-foreground mb-8">
                A practical toolkit that shows how we evaluate opportunities and what we verify before clients move forward.
              </p>
            </div>
            
            {/* Form */}
            <div className="card-premium p-8">
              <h2 className="heading-4 mb-6">Send me the pack</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="form-label">Full name</label>
                  <input
                    type="text"
                    required
                    placeholder="Full name"
                    className="form-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="form-label">Email address</label>
                  <input
                    type="email"
                    required
                    placeholder="Email address"
                    className="form-input"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>
                <div>
                  <label className="form-label">Country</label>
                  <input
                    type="text"
                    required
                    placeholder="Select country"
                    className="form-input"
                    value={formData.country}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                  />
                </div>
                <div>
                  <label className="form-label">WhatsApp (optional)</label>
                  <input
                    type="tel"
                    placeholder="+[country code]"
                    className="form-input"
                    value={formData.whatsapp}
                    onChange={(e) => setFormData({ ...formData, whatsapp: e.target.value })}
                  />
                </div>
                <button 
                  type="submit" 
                  className="btn-primary w-full flex items-center justify-center gap-2"
                  disabled={isLoading}
                >
                  {isLoading ? 'Sending...' : (
                    <>
                      <Download className="w-4 h-4" />
                      Send me the pack
                    </>
                  )}
                </button>
              </form>
              <p className="text-xs text-muted-foreground mt-4 text-center">
                By submitting, you agree to our <Link to="/privacy" className="underline">privacy policy</Link>.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Definition Box */}
      <section className="container-wide -mt-8 relative z-20 mb-16">
        <DefinitionBox>
          <p className="text-foreground">
            <strong>See how we think before you speak to anyone.</strong> The Deal Memo Pack gives you the tools to evaluate any Dubai off plan opportunity—whether you work with us or not. <Link to="/match" className="text-accent hover:underline">Want personalized analysis? Request a private shortlist →</Link>
          </p>
        </DefinitionBox>
      </section>

      {/* What's Inside */}
      <section className="section-padding">
        <div className="container-wide">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="heading-3 mb-6">What's inside</h2>
              <ul className="space-y-4">
                {packContents.map((item) => (
                  <li key={item} className="flex items-start gap-4">
                    <CheckCircle className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
                    <span className="text-foreground">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            {/* Preview */}
            <div className="card-premium p-6">
              <div className="flex items-center gap-3 mb-4">
                <Eye className="w-5 h-5 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Preview</span>
              </div>
              <div className="bg-secondary/50 rounded-xl p-6 space-y-4">
                <div className="h-4 bg-foreground/10 rounded w-3/4" />
                <div className="h-3 bg-foreground/5 rounded w-full" />
                <div className="h-3 bg-foreground/5 rounded w-5/6" />
                <div className="grid grid-cols-2 gap-4 pt-4">
                  <div className="bg-foreground/5 rounded-lg p-4">
                    <div className="h-2 bg-foreground/10 rounded w-1/2 mb-2" />
                    <div className="h-4 bg-accent/20 rounded w-3/4" />
                  </div>
                  <div className="bg-foreground/5 rounded-lg p-4">
                    <div className="h-2 bg-foreground/10 rounded w-1/2 mb-2" />
                    <div className="h-4 bg-accent/20 rounded w-3/4" />
                  </div>
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-4 text-center">
                Sample deal memo structure (content blurred)
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="section-padding bg-gradient-subtle">
        <div className="container-narrow">
          <div className="text-center">
            <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
              <strong>Disclaimer:</strong> The Deal Memo Pack provides general guidance and templates for educational purposes. It does not constitute financial, legal, or investment advice. Real estate investing involves risk, and returns are not guaranteed. Always conduct your own due diligence and consult qualified professionals before making investment decisions.
            </p>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="section-padding">
        <div className="container-narrow">
          <FAQBlock items={faqItems} />
        </div>
      </section>

      {/* Updated */}
      <div className="container-wide pb-12">
        <UpdatedBlock date="December 2024" />
      </div>
    </Layout>
  );
}