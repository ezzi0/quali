import { ListChecks, Calendar, FileText, Users } from 'lucide-react';

const values = [
  {
    icon: ListChecks,
    title: 'Curated Shortlist',
    description: '3–5 options matched to your specific requirements, not a generic inventory dump.',
  },
  {
    icon: Calendar,
    title: 'Payment Plan Fit',
    description: 'Down payment and installment structure that aligns with your financial comfort.',
  },
  {
    icon: FileText,
    title: 'Deal Memo',
    description: 'Transparent analysis with assumptions, risks, and what to verify before you commit.',
  },
  {
    icon: Users,
    title: 'Specialist Matching',
    description: 'Speak to the right agent the first time—no handoffs, no runaround.',
  },
];

export default function ValueGrid() {
  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {values.map((value) => (
        <div key={value.title} className="card-premium p-6">
          <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4">
            <value.icon className="w-6 h-6 text-accent" />
          </div>
          <h3 className="font-semibold text-foreground mb-2">{value.title}</h3>
          <p className="text-muted-foreground text-sm">{value.description}</p>
        </div>
      ))}
    </div>
  );
}
