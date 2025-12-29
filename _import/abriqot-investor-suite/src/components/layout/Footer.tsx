import { Link } from 'react-router-dom';
import { MessageCircle, Mail, MapPin } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';

const footerLinks = {
  explore: [
    { name: 'Collection', href: '/investments' },
    { name: 'Launch List', href: '/launch-list' },
    { name: 'Deal Memo Pack', href: '/deal-memos' },
    { name: 'How It Works', href: '/how-it-works' },
  ],
  company: [
    { name: 'About', href: '/about' },
    { name: 'Contact', href: '/contact' },
    { name: 'Compliance', href: '/compliance' },
  ],
};

export default function Footer() {
  return (
    <footer className="border-t border-border bg-card">
      <div className="container-wide py-16">
        <div className="grid md:grid-cols-4 gap-12">
          {/* Brand */}
          <div className="md:col-span-2">
            <Link to="/" className="text-2xl font-semibold text-foreground tracking-tight">
              abriqot
            </Link>
            <p className="mt-4 text-muted-foreground text-sm max-w-sm leading-relaxed">
              Dubai real estate brokerage specializing in off plan opportunities for international buyers.
            </p>
            <div className="mt-6 space-y-2">
              <a 
                href="https://wa.me/971XXXXXXXXX" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <MessageCircle className="w-4 h-4" />
                <span>WhatsApp</span>
              </a>
              <a 
                href="mailto:hello@abriqot.com"
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <Mail className="w-4 h-4" />
                <span>hello@abriqot.com</span>
              </a>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <MapPin className="w-4 h-4" />
                <span>Dubai, UAE</span>
              </div>
            </div>
          </div>

          {/* Explore */}
          <div>
            <h4 className="font-medium text-foreground mb-4 text-sm">Explore</h4>
            <ul className="space-y-2">
              {footerLinks.explore.map((link) => (
                <li key={link.name}>
                  <Link 
                    to={link.href} 
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-medium text-foreground mb-4 text-sm">Company</h4>
            <ul className="space-y-2">
              {footerLinks.company.map((link) => (
                <li key={link.name}>
                  <Link 
                    to={link.href} 
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom */}
      <div className="border-t border-border">
        <div className="container-wide py-6 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} Abriqot. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <Link to="/privacy" className="hover:text-foreground transition-colors">Privacy</Link>
              <span>·</span>
              <Link to="/terms" className="hover:text-foreground transition-colors">Terms</Link>
              <span>·</span>
              <Link to="/disclaimer" className="hover:text-foreground transition-colors">Disclaimer</Link>
            </div>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </footer>
  );
}