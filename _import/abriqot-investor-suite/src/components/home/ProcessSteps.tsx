import { ListFilter, FileText, UserCheck, Send } from 'lucide-react';

const steps = [
  {
    number: '01',
    icon: ListFilter,
    title: 'Match',
    description: 'Answer 9 quick questions about your budget, payment preferences, and timeline.',
  },
  {
    number: '02',
    icon: FileText,
    title: 'Shortlist',
    description: 'Receive 3–5 curated off-plan options that match your specific criteria.',
  },
  {
    number: '03',
    icon: UserCheck,
    title: 'Deal Memo',
    description: 'Review a one-page analysis with assumptions, risks, and verification checklist.',
  },
  {
    number: '04',
    icon: Send,
    title: 'Execute',
    description: 'Reserve your unit with guidance on documents, payments, and next steps.',
  },
];

export default function ProcessSteps() {
  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
      {steps.map((step, index) => (
        <div key={step.number} className="relative">
          {/* Connector line */}
          {index < steps.length - 1 && (
            <div className="hidden lg:block absolute top-8 left-full w-full h-px bg-border -translate-x-1/2 z-0" />
          )}
          
          <div className="relative z-10">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center">
                <step.icon className="w-7 h-7 text-accent" />
              </div>
              <span className="text-4xl font-bold text-border">{step.number}</span>
            </div>
            <h3 className="font-semibold text-lg text-foreground mb-2">{step.title}</h3>
            <p className="text-muted-foreground text-sm">{step.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
