import { Link } from 'react-router-dom';
import Layout from '@/components/layout/Layout';
import { ListFilter, FileText, UserCheck, Send, CheckCircle, FileCheck, Globe, Shield, ArrowRight } from 'lucide-react';

const steps = [
  {
    number: '01',
    icon: ListFilter,
    title: '1. Your private brief',
    subtitle: 'Tell us what matters',
    description: 'Budget, payment plan comfort, timeline, preferences. Just the inputs that matter.',
    output: 'A clear profile that guides our shortlist curation.',
  },
  {
    number: '02',
    icon: FileText,
    title: '2. Your curated shortlist',
    subtitle: 'Receive curated options',
    description: 'A focused selection aligned to your criteria, shared with context.',
    whatsIncluded: ['Project overview', 'Payment plan structure', 'Handover timeline', 'Developer background note', 'Key highlights'],
    output: 'A focused list—not an inventory dump.',
  },
  {
    number: '03',
    icon: UserCheck,
    title: '3. Your investment brief',
    subtitle: 'Review before you call',
    description: 'Key considerations, timeline notes, payment plan snapshot, and what to verify before moving forward.',
    whatsInside: ['Key assumptions', 'Risks to consider', 'What to verify independently', 'Questions to ask', 'Next steps if you proceed'],
    output: 'Transparency before any sales conversation.',
  },
  {
    number: '04',
    icon: Send,
    title: '4. Concierge execution',
    subtitle: 'Reserve and coordinate',
    description: 'Your specialist coordinates next steps, documentation, and updates with a remote ready approach.',
    processIncludes: ['Reservation form completion', 'Payment guidance', 'Document checklist', 'Developer liaison', 'Milestone updates'],
    output: 'Smooth execution from abroad.',
  },
];

const remoteBuyingChecklist = [
  'Time zone scheduling',
  'WhatsApp and email coordination',
  'Document checklist and timeline',
  'One point of contact',
];

const faqItems = [
  {
    question: 'How long does the matching process take?',
    answer: "The brief takes about 60 seconds. You'll receive your curated shortlist within 24–48 business hours.",
  },
  {
    question: 'Can I speak to someone before completing the brief?',
    answer: "Yes, but we recommend completing the brief first. It helps us prepare relevant information before the call, making the conversation more productive.",
  },
  {
    question: 'What if none of the shortlisted options interest me?',
    answer: "Let us know what didn't fit, and we'll refine the criteria. Sometimes the first round helps clarify what you actually want.",
  },
  {
    question: 'Can I reserve a unit without visiting Dubai?',
    answer: "Yes. Most of our international clients complete the entire process remotely. We can coordinate everything via WhatsApp, email, and video calls.",
  },
];

export default function HowItWorks() {
  return (
    <Layout>
      {/* Hero */}
      <section className="pt-32 pb-16 bg-background">
        <div className="container-wide">
          <div className="max-w-3xl">
            <p className="text-primary text-sm font-medium mb-4">How It Works</p>
            <h1 className="heading-1 text-foreground mb-6">
              A refined process for global buyers
            </h1>
            <p className="body-large text-muted-foreground mb-8">
              Abriqot is a Dubai real estate brokerage built for international buyers seeking off plan apartments and villas, with select ready opportunities when the fit is right.
            </p>
            <Link to="/match" className="btn-primary inline-flex items-center gap-2">
              Request a Private Shortlist
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Process Overview */}
      <section className="py-12 border-y border-border bg-muted/30">
        <div className="container-wide">
          <h2 className="font-semibold text-foreground mb-2">The Abriqot flow</h2>
          <p className="text-muted-foreground">
            A simple sequence designed to keep decisions clear.
          </p>
        </div>
      </section>

      {/* Detailed Steps */}
      <section className="section-padding">
        <div className="container-wide space-y-12">
          {steps.map((step) => (
            <div key={step.number} className="grid lg:grid-cols-12 gap-8 items-start">
              {/* Step Number & Icon */}
              <div className="lg:col-span-2">
                <div className="flex lg:flex-col items-center lg:items-start gap-4">
                  <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center">
                    <step.icon className="w-7 h-7 text-primary" />
                  </div>
                  <span className="text-4xl font-bold text-border">{step.number}</span>
                </div>
              </div>
              
              {/* Content */}
              <div className="lg:col-span-10">
                <div className="bg-card border border-border rounded-2xl p-8">
                  <h2 className="text-2xl font-semibold text-foreground mb-1">{step.title}</h2>
                  <p className="text-primary text-sm font-medium mb-4">{step.subtitle}</p>
                  <p className="text-muted-foreground mb-6">{step.description}</p>
                  
                  {step.whatsIncluded && (
                    <div className="mb-4">
                      <p className="font-medium text-foreground mb-2">What's included:</p>
                      <ul className="grid sm:grid-cols-2 gap-2">
                        {step.whatsIncluded.map((item) => (
                          <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                            <CheckCircle className="w-4 h-4 text-primary flex-shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {step.whatsInside && (
                    <div className="mb-4">
                      <p className="font-medium text-foreground mb-2">What's inside the investment brief:</p>
                      <ul className="grid sm:grid-cols-2 gap-2">
                        {step.whatsInside.map((item) => (
                          <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                            <CheckCircle className="w-4 h-4 text-primary flex-shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {step.processIncludes && (
                    <div className="mb-4">
                      <p className="font-medium text-foreground mb-2">The process includes:</p>
                      <ul className="grid sm:grid-cols-2 gap-2">
                        {step.processIncludes.map((item) => (
                          <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                            <CheckCircle className="w-4 h-4 text-primary flex-shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  <div className="border-t border-border pt-4 mt-4">
                    <p className="text-sm text-muted-foreground">
                      <strong className="text-foreground">Output:</strong> {step.output}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Remote Ready */}
      <section className="section-padding bg-muted/30">
        <div className="container-wide">
          <div className="grid lg:grid-cols-2 gap-12 items-start">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <Globe className="w-5 h-5 text-primary" />
                <span className="text-primary font-medium text-sm">For International Buyers</span>
              </div>
              <h2 className="text-2xl font-semibold text-foreground mb-4">Built for international execution</h2>
              <p className="text-muted-foreground">
                Everything you need to purchase off plan property in Dubai from abroad.
              </p>
            </div>
            <div className="bg-card border border-border rounded-2xl p-6">
              <ul className="space-y-4">
                {remoteBuyingChecklist.map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <FileCheck className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                    <span className="text-foreground">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="section-padding">
        <div className="container-narrow">
          <h2 className="text-2xl font-semibold text-foreground mb-8 text-center">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {faqItems.map((item) => (
              <div key={item.question} className="bg-card border border-border rounded-xl p-6">
                <h3 className="font-medium text-foreground mb-2">{item.question}</h3>
                <p className="text-muted-foreground text-sm">{item.answer}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="section-padding bg-card border-t border-border">
        <div className="container-narrow text-center">
          <h2 className="text-2xl font-semibold text-foreground mb-4">Start with the brief</h2>
          <p className="text-muted-foreground mb-8">
            Private. Curated. On your terms.
          </p>
          <Link to="/match" className="btn-primary inline-flex items-center justify-center gap-2">
            Request a Private Shortlist
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Updated */}
      <div className="container-wide py-8">
        <p className="text-xs text-muted-foreground">
          Last updated: December 2024
        </p>
      </div>
    </Layout>
  );
}