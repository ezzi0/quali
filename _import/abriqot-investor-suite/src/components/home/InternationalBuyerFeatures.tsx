import { MessageCircle, Clock, FileCheck, UserCircle } from 'lucide-react';

const features = [
  {
    icon: MessageCircle,
    title: 'WhatsApp-First Communication',
    description: 'Your preferred channel. Quick responses, no phone tag.',
  },
  {
    icon: Clock,
    title: 'Timezone-Aware Scheduling',
    description: 'Calls scheduled around your local business hours.',
  },
  {
    icon: FileCheck,
    title: 'Remote Documentation',
    description: 'Complete checklist for purchasing from abroad.',
  },
  {
    icon: UserCircle,
    title: 'Single Point of Contact',
    description: 'One dedicated specialist throughout your journey.',
  },
];

export default function InternationalBuyerFeatures() {
  return (
    <div className="grid sm:grid-cols-2 gap-6">
      {features.map((feature) => (
        <div key={feature.title} className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center flex-shrink-0">
            <feature.icon className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h4 className="font-semibold text-foreground mb-1">{feature.title}</h4>
            <p className="text-muted-foreground text-sm">{feature.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
