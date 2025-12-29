import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface FAQItem {
  question: string;
  answer: string;
}

interface FAQBlockProps {
  items: FAQItem[];
  title?: string;
}

export default function FAQBlock({ items, title = 'Frequently Asked Questions' }: FAQBlockProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      {title && <h3 className="heading-4 mb-6">{title}</h3>}
      <div className="space-y-2">
        {items.map((item, index) => (
          <div key={index} className="faq-item">
            <button
              className="w-full flex items-center justify-between py-4 text-left"
              onClick={() => setOpenIndex(openIndex === index ? null : index)}
              aria-expanded={openIndex === index}
            >
              <span className="font-medium text-foreground pr-4">{item.question}</span>
              <ChevronDown 
                className={`w-5 h-5 text-muted-foreground flex-shrink-0 transition-transform ${
                  openIndex === index ? 'rotate-180' : ''
                }`} 
              />
            </button>
            {openIndex === index && (
              <div className="pb-4 text-muted-foreground animate-fade-in">
                {item.answer}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
