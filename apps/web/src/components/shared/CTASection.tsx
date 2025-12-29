import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

interface CTASectionProps {
  title: string;
  description?: string;
  primaryCTA: { text: string; href: string };
  secondaryCTA?: { text: string; href: string };
}

export default function CTASection({ title, description, primaryCTA, secondaryCTA }: CTASectionProps) {
  return (
    <section className="section-padding bg-gradient-subtle">
      <div className="container-narrow text-center">
        <h2 className="heading-3 mb-4">{title}</h2>
        {description && (
          <p className="body-large text-muted-foreground mb-8 max-w-2xl mx-auto">
            {description}
          </p>
        )}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to={primaryCTA.href} className="btn-primary inline-flex items-center justify-center gap-2">
            {primaryCTA.text}
            <ArrowRight className="w-4 h-4" />
          </Link>
          {secondaryCTA && (
            <Link to={secondaryCTA.href} className="btn-secondary inline-flex items-center justify-center">
              {secondaryCTA.text}
            </Link>
          )}
        </div>
      </div>
    </section>
  );
}
