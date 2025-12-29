import { Clock, Shield, MessageCircle, CheckCircle } from 'lucide-react';

const trustItems = [
  {
    icon: Clock,
    label: 'Response within 4 hours',
    sublabel: 'During business hours',
  },
  {
    icon: Shield,
    label: 'Verified projects only',
    sublabel: 'We check permits',
  },
  {
    icon: MessageCircle,
    label: 'WhatsApp-first',
    sublabel: 'Your preferred channel',
  },
  {
    icon: CheckCircle,
    label: 'Transparent fees',
    sublabel: 'No hidden charges',
  },
];

export default function TrustBar() {
  return (
    <div className="flex flex-wrap justify-center gap-6 md:gap-12">
      {trustItems.map((item) => (
        <div key={item.label} className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
            <item.icon className="w-5 h-5 text-accent" />
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">{item.label}</p>
            <p className="text-xs text-muted-foreground">{item.sublabel}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
