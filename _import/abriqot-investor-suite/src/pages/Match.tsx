import { useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '@/components/layout/Layout';
import { ArrowLeft, ArrowRight, Check, Calendar, MessageCircle, Loader2 } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface MatchData {
  budget: string;
  downPayment: string;
  installmentPreference: string;
  handoverPreference: string;
  strategy: string;
  riskStyle: string;
  exitPreference: string;
  countryTimezone: string;
  contactPreference: string;
  contactDetails: string;
}

const steps = [
  {
    id: 'budget',
    question: 'What is your budget range?',
    hint: 'Helps us filter to projects within your investment capacity.',
    options: [
      { value: 'under-1m', label: 'Under AED 1M' },
      { value: '1m-1.5m', label: 'AED 1M to 1.5M' },
      { value: '1.5m-2.5m', label: 'AED 1.5M to 2.5M' },
      { value: '2.5m-5m', label: 'AED 2.5M to 5M' },
      { value: '5m-plus', label: 'AED 5M+' },
    ],
  },
  {
    id: 'downPayment',
    question: 'Down payment comfort?',
    hint: 'Payment plan structures vary by developer.',
    options: [
      { value: '10-15', label: '10 to 15 percent' },
      { value: '20', label: '20 percent' },
      { value: '30-plus', label: '30 percent+' },
      { value: 'depends', label: 'Depends on the opportunity' },
    ],
  },
  {
    id: 'installmentPreference',
    question: 'Installment preference?',
    hint: 'Different developers offer different payment schedules.',
    options: [
      { value: 'monthly', label: 'Monthly' },
      { value: 'quarterly', label: 'Quarterly' },
      { value: 'flexible', label: 'Flexible' },
    ],
  },
  {
    id: 'handoverPreference',
    question: 'Handover preference?',
    hint: 'Handover year affects payment structure and exit options.',
    options: [
      { value: '2026-2027', label: '2026 to 2027' },
      { value: '2028', label: '2028' },
      { value: '2029-plus', label: '2029+' },
      { value: 'flexible', label: 'Flexible' },
    ],
  },
  {
    id: 'strategy',
    question: 'Strategy?',
    hint: 'Different projects suit different goals.',
    options: [
      { value: 'capital-growth', label: 'Capital growth' },
      { value: 'rental', label: 'Rental at handover' },
      { value: 'balanced', label: 'Balanced' },
    ],
  },
  {
    id: 'riskStyle',
    question: 'Risk style?',
    hint: 'Helps match developer profiles and project types.',
    options: [
      { value: 'conservative', label: 'Conservative' },
      { value: 'balanced', label: 'Balanced' },
      { value: 'opportunistic', label: 'Opportunistic' },
    ],
  },
  {
    id: 'exitPreference',
    question: 'Exit preference?',
    hint: 'Affects which projects and payment plans are suitable.',
    options: [
      { value: 'hold', label: 'Hold to handover' },
      { value: 'flexible', label: 'Flexible' },
      { value: 'not-sure', label: 'Not sure' },
    ],
  },
  {
    id: 'countryTimezone',
    question: 'Country and time zone?',
    hint: 'Helps us schedule calls at convenient times.',
    type: 'text',
    placeholder: 'Select your country',
  },
  {
    id: 'contactPreference',
    question: 'Preferred contact method?',
    hint: "We'll use your preferred channel.",
    options: [
      { value: 'whatsapp', label: 'WhatsApp' },
      { value: 'email', label: 'Email' },
      { value: 'call', label: 'Call' },
    ],
  },
  {
    id: 'contactDetails',
    question: 'Your contact information',
    hint: "We'll reach out within 24 hours.",
    type: 'text',
    placeholder: '+[country code] or name@email.com',
  },
];

export default function Match() {
  const [currentStep, setCurrentStep] = useState(0);
  const [matchData, setMatchData] = useState<Partial<MatchData>>({});
  const [isComplete, setIsComplete] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleSelect = (value: string) => {
    const stepId = steps[currentStep].id as keyof MatchData;
    setMatchData({ ...matchData, [stepId]: value });
    
    if (currentStep < steps.length - 1) {
      setTimeout(() => setCurrentStep(currentStep + 1), 150);
    } else {
      handleSubmit({ ...matchData, [stepId]: value });
    }
  };

  const handleTextInput = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const value = formData.get('input') as string;
    const stepId = steps[currentStep].id as keyof MatchData;
    
    if (value.trim()) {
      setMatchData({ ...matchData, [stepId]: value });
      if (currentStep < steps.length - 1) {
        setCurrentStep(currentStep + 1);
      } else {
        handleSubmit({ ...matchData, [stepId]: value });
      }
    }
  };

  const handleSubmit = async (data: Partial<MatchData>) => {
    setIsSubmitting(true);
    
    try {
      // Determine if contact details is email or phone
      const contactDetails = data.contactDetails || '';
      const isEmail = contactDetails.includes('@');
      
      const { error } = await supabase.from('leads').insert({
        form_type: 'match',
        budget: data.budget,
        down_payment: data.downPayment,
        installment_preference: data.installmentPreference,
        handover_preference: data.handoverPreference,
        strategy: data.strategy,
        risk_style: data.riskStyle,
        exit_preference: data.exitPreference,
        country_timezone: data.countryTimezone,
        contact_preference: data.contactPreference,
        email: isEmail ? contactDetails : null,
        phone: !isEmail ? contactDetails : null,
      });

      if (error) throw error;

      // Send email notification (fire and forget)
      supabase.functions.invoke('send-lead-notification', {
        body: {
          type: 'match',
          email: isEmail ? contactDetails : null,
          phone: !isEmail ? contactDetails : null,
          budget: data.budget,
          strategy: data.strategy,
          handoverPreference: data.handoverPreference,
          contactPreference: data.contactPreference,
        },
      }).catch(console.error);

      // Track in dataLayer if available
      if (typeof window !== 'undefined' && (window as any).dataLayer) {
        (window as any).dataLayer.push({ event: 'match_complete', matchData: data });
      }
      
      setIsComplete(true);
    } catch (error) {
      console.error('Error submitting match form:', error);
      toast({
        title: 'Submission failed',
        description: 'Please try again or contact us directly.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const goBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const progress = ((currentStep + 1) / steps.length) * 100;
  const step = steps[currentStep];

  // Success state
  if (isComplete) {
    return (
      <Layout>
        <section className="min-h-[80vh] flex items-center py-32">
          <div className="container-narrow text-center">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6">
              <Check className="w-8 h-8 text-primary" />
            </div>
            
            <h1 className="text-3xl font-semibold text-foreground mb-4">Brief received</h1>
            <p className="text-muted-foreground mb-8">
              Your specialist will reach out via {matchData.contactPreference} with a curated shortlist.
            </p>
            
            <div className="bg-card border border-border rounded-2xl p-6 max-w-md mx-auto mb-8">
              <h3 className="font-medium mb-4">Your preferences</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Budget</p>
                  <p className="text-foreground">{matchData.budget}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Handover</p>
                  <p className="text-foreground">{matchData.handoverPreference}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Down payment</p>
                  <p className="text-foreground">{matchData.downPayment}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Strategy</p>
                  <p className="text-foreground">{matchData.strategy}</p>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a 
                href="https://calendly.com/abriqot" 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn-primary inline-flex items-center justify-center gap-2"
              >
                <Calendar className="w-4 h-4" />
                Schedule a Call
              </a>
              <a 
                href="https://wa.me/971XXXXXXXXX"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-outline inline-flex items-center justify-center gap-2"
              >
                <MessageCircle className="w-4 h-4" />
                Message on WhatsApp
              </a>
            </div>

            <p className="text-xs text-muted-foreground mt-12">
              If you want to add context, reply with preferred areas, unit type, or developer preferences.
            </p>
          </div>
        </section>
      </Layout>
    );
  }

  // Wizard
  return (
    <Layout>
      <section className="min-h-[80vh] flex flex-col py-32">
        <div className="container-narrow flex-1">
          {/* Header */}
          <div className="mb-8">
            <p className="text-primary text-sm font-medium mb-2">Private Shortlist</p>
            <h1 className="text-2xl font-semibold text-foreground">Tell us what fits. We will curate the rest.</h1>
            <p className="text-muted-foreground text-sm mt-2">Designed for speed. Built for precision.</p>
          </div>

          {/* Progress */}
          <div className="mb-12">
            <div className="flex justify-between text-sm text-muted-foreground mb-3">
              <span>Step {currentStep + 1} of {steps.length}</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="h-1 bg-muted rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Back */}
          {currentStep > 0 && (
            <button 
              onClick={goBack}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-8 transition-colors text-sm"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
          )}

          {/* Question */}
          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-foreground mb-2">{step.question}</h2>
            <p className="text-muted-foreground text-sm">{step.hint}</p>
          </div>

          {/* Options or Input */}
          {step.type === 'text' ? (
            <form onSubmit={handleTextInput}>
              <input
                type="text"
                name="input"
                placeholder={step.placeholder}
                className="form-input text-lg mb-6"
                autoFocus
                disabled={isSubmitting}
              />
              <button type="submit" className="btn-primary" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Submitting...
                  </>
                ) : currentStep === steps.length - 1 ? (
                  'Request shortlist'
                ) : (
                  <>
                    Continue
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          ) : (
            <div className="grid sm:grid-cols-2 gap-3">
              {step.options?.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleSelect(option.value)}
                  disabled={isSubmitting}
                  className={`text-left p-4 rounded-xl border transition-all ${
                    matchData[step.id as keyof MatchData] === option.value
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <span className="font-medium text-foreground">{option.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="container-narrow mt-16 pt-8 border-t border-border">
          <p className="text-xs text-muted-foreground text-center">
            Private. Curated. On your terms. <Link to="/privacy" className="underline">Privacy policy</Link>
          </p>
        </div>
      </section>
    </Layout>
  );
}