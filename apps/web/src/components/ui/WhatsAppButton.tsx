import { MessageCircle } from 'lucide-react';

export default function WhatsAppButton() {
  const handleClick = () => {
    // Track event
    if (typeof window !== 'undefined' && (window as any).dataLayer) {
      (window as any).dataLayer.push({ event: 'whatsapp_click' });
    }
  };

  return (
    <a
      href="https://wa.me/971XXXXXXXXX?text=Hi%2C%20I%27m%20interested%20in%20Dubai%20off-plan%20investments"
      target="_blank"
      rel="noopener noreferrer"
      onClick={handleClick}
      className="whatsapp-float hidden md:flex items-center justify-center"
      aria-label="Contact us on WhatsApp"
    >
      <MessageCircle className="w-6 h-6" />
    </a>
  );
}
