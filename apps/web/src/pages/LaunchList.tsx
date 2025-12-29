import { useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '@/components/layout/Layout';
import DefinitionBox from '@/components/shared/DefinitionBox';
import FAQBlock from '@/components/shared/FAQBlock';
import UpdatedBlock from '@/components/shared/UpdatedBlock';
import { Bell, CheckCircle } from 'lucide-react';
import { api } from '@/lib/api';

const faqItems = [
  {
    question: 'How often will I receive updates?',
    answer: 'Weekly digest or launch only alerts - you choose your preference.',
  },
  {
    question: 'Can I unsubscribe?',
    answer: 'Yes, anytime. One click in any email.',
  },
  {
    question: 'What kind of launches do you cover?',
    answer: 'Off plan projects from established developers that match investor criteria - not every launch on the market.',
  },
];

export default function LaunchList() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    budgetBand: '',
    downPaymentComfort: '',
    handoverWindow: '',
    alertType: '',
    countryTimezone: '',
  });
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await api.leads.createPublic({
        form_type: 'launch_list',
        name: formData.name || null,
        email: formData.email,
        message: `Launch list preferences: ${formData.budgetBand}, ${formData.handoverWindow}, ${formData.alertType}`,
        raw_payload: formData,
      });

      if (typeof window !== 'undefined' && (window as any).dataLayer) {
        (window as any).dataLayer.push({ event: 'launchlist_submit' });
      }

      setIsSubmitted(true);
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <Layout>
        <section className="section-padding min-h-[80vh] flex items-center">
          <div className="container-narrow text-center">
            <div className="w-20 h-20 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-10 h-10 text-accent" />
            </div>
            <h1 className="heading-2 mb-4">You are in</h1>
            <p className="body-large text-muted-foreground mb-8">
              Updates aligned to your criteria are on the way.
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
      <section className="section-padding bg-gradient-hero">
        <div className="container-wide">
          <div className="max-w-3xl mx-auto text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Bell className="w-5 h-5 text-accent" />
              <span className="text-accent font-medium">Early Visibility</span>
            </div>
            <h1 className="heading-1 text-foreground mb-6">Join the Launch List</h1>
            <p className="body-large text-muted-foreground mb-8">
              Early alerts for launches and opportunities that match your profile. Weekly digest or launch only alerts, you choose.
            </p>
          </div>
        </div>
      </section>

      <section className="container-wide -mt-8 relative z-20 mb-16">
        <DefinitionBox>
          <p className="text-foreground">
            <strong>Timing is a strategy.</strong> The Launch List is for buyers who want early visibility on opportunities aligned to their criteria. <Link to="/match" className="text-accent hover:underline">Want immediate matching? Request a private shortlist -&gt;</Link>
          </p>
        </DefinitionBox>
      </section>

      <section className="section-padding">
        <div className="container-narrow">
          <div className="card-premium p-8 max-w-2xl mx-auto">
            <h2 className="heading-4 mb-6">Tell us what you are looking for</h2>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="form-label">Name</label>
                <input
                  type="text"
                  required
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              <div>
                <label className="form-label">Email</label>
                <input
                  type="email"
                  required
                  className="form-input"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
              <div>
                <label className="form-label">Budget band</label>
                <select
                  required
                  className="form-input"
                  value={formData.budgetBand}
                  onChange={(e) => setFormData({ ...formData, budgetBand: e.target.value })}
                >
                  <option value="">Select a range</option>
                  <option value="under-1m">Under AED 1M</option>
                  <option value="1m-1.5m">AED 1M to 1.5M</option>
                  <option value="1.5m-2.5m">AED 1.5M to 2.5M</option>
                  <option value="2.5m-5m">AED 2.5M to 5M</option>
                  <option value="5m-plus">AED 5M+</option>
                </select>
              </div>

              <div>
                <label className="form-label">Down payment comfort</label>
                <select
                  required
                  className="form-input"
                  value={formData.downPaymentComfort}
                  onChange={(e) => setFormData({ ...formData, downPaymentComfort: e.target.value })}
                >
                  <option value="">Choose one</option>
                  <option value="10-15">10 to 15 percent</option>
                  <option value="20">20 percent</option>
                  <option value="30-plus">30 percent+</option>
                  <option value="flexible">Flexible</option>
                </select>
              </div>

              <div>
                <label className="form-label">Handover window</label>
                <select
                  required
                  className="form-input"
                  value={formData.handoverWindow}
                  onChange={(e) => setFormData({ ...formData, handoverWindow: e.target.value })}
                >
                  <option value="">Choose one</option>
                  <option value="2026-2027">2026 to 2027</option>
                  <option value="2028">2028</option>
                  <option value="2029-plus">2029+</option>
                  <option value="flexible">Flexible</option>
                </select>
              </div>

              <div>
                <label className="form-label">Alert preference</label>
                <select
                  required
                  className="form-input"
                  value={formData.alertType}
                  onChange={(e) => setFormData({ ...formData, alertType: e.target.value })}
                >
                  <option value="">Choose one</option>
                  <option value="weekly">Weekly digest</option>
                  <option value="launch-only">Launch only alerts</option>
                </select>
              </div>

              <div>
                <label className="form-label">Country / timezone</label>
                <input
                  type="text"
                  required
                  placeholder="Type here"
                  className="form-input"
                  value={formData.countryTimezone}
                  onChange={(e) => setFormData({ ...formData, countryTimezone: e.target.value })}
                />
              </div>

              <button type="submit" className="btn-primary w-full" disabled={isLoading}>
                {isLoading ? 'Joining...' : 'Join the Launch List'}
              </button>
            </form>

            <p className="text-xs text-muted-foreground mt-4 text-center">Private. Curated. On your terms.</p>
          </div>
        </div>
      </section>

      <section className="section-padding bg-gradient-subtle">
        <div className="container-narrow">
          <FAQBlock items={faqItems} />
        </div>
      </section>

      <div className="container-wide pb-12">
        <UpdatedBlock date="December 2024" />
      </div>
    </Layout>
  );
}
