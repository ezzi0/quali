import { Link } from 'react-router-dom';
import { ArrowRight, CreditCard, Calendar, FileText } from 'lucide-react';

const paths = [
  {
    icon: CreditCard,
    title: 'Match by Payment Plan',
    description: 'Find options that fit your down payment and installment preferences.',
    href: '/match?path=payment',
    color: 'bg-accent/10 text-accent',
  },
  {
    icon: Calendar,
    title: 'Match by Handover Year',
    description: 'Choose based on when you want to take ownership or exit.',
    href: '/match?path=handover',
    color: 'bg-accent/10 text-accent',
  },
  {
    icon: FileText,
    title: 'Get Deal Memo Pack',
    description: 'Download our investor toolkit with checklists and sample analysis.',
    href: '/deal-memos',
    color: 'bg-accent/10 text-accent',
  },
];

export default function InvestorPathGrid() {
  return (
    <div className="grid md:grid-cols-3 gap-6">
      {paths.map((path) => (
        <Link 
          key={path.title}
          to={path.href}
          className="card-premium p-6 group"
        >
          <div className={`w-12 h-12 rounded-xl ${path.color} flex items-center justify-center mb-4`}>
            <path.icon className="w-6 h-6" />
          </div>
          <h3 className="font-semibold text-lg text-foreground mb-2">{path.title}</h3>
          <p className="text-muted-foreground text-sm mb-4">{path.description}</p>
          <span className="inline-flex items-center gap-2 text-accent text-sm font-medium group-hover:gap-3 transition-all">
            Get started <ArrowRight className="w-4 h-4" />
          </span>
        </Link>
      ))}
    </div>
  );
}
