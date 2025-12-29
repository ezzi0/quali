import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { siteAssets } from '@/data/site-assets';

const desktopNav = [
  { name: 'Collection', href: '/investments' },
  { name: 'Qualification', href: '/qualification' },
  { name: 'How It Works', href: '/how-it-works' },
  { name: 'Launch List', href: '/launch-list' },
];

const mobileNav = [
  { name: 'Collection', href: '/investments' },
  { name: 'Qualification', href: '/qualification' },
  { name: 'How It Works', href: '/how-it-works' },
  { name: 'Launch List', href: '/launch-list' },
  { name: 'Deal Memo Pack', href: '/deal-memos' },
  { name: 'Contact', href: '/contact' },
];

export default function Header() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === '/';

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location]);

  // Auto-detect system theme preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleThemeChange = (e: MediaQueryListEvent | MediaQueryList) => {
      if (e.matches) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    };

    // Set initial theme
    handleThemeChange(mediaQuery);

    // Listen for changes
    mediaQuery.addEventListener('change', handleThemeChange);
    return () => mediaQuery.removeEventListener('change', handleThemeChange);
  }, []);

  // On home page with video, always use light text until scrolled
  const useLight = isHome && !isScrolled;

  return (
    <header 
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled 
          ? 'bg-background/95 backdrop-blur-md border-b border-border' 
          : 'bg-transparent'
      }`}
    >
      <nav className={`container-wide flex items-center justify-between transition-all duration-300 ${
        isScrolled ? 'py-3' : 'py-5 lg:py-6'
      }`}>
        {/* Logo */}
        <Link to="/" className="flex-shrink-0">
          {siteAssets.logo ? (
            <img
              src={siteAssets.logo}
              alt="Abriqot"
              className={`h-7 w-auto transition-all ${
                useLight ? 'brightness-0 invert' : 'dark:brightness-0 dark:invert'
              }`}
            />
          ) : (
            <span className={`text-sm font-semibold tracking-wide ${useLight ? 'text-white' : 'text-foreground'}`}>
              Abriqot
            </span>
          )}
        </Link>

        {/* Desktop Navigation - Center */}
        <div className="hidden lg:flex items-center gap-8">
          {desktopNav.map((item) => (
            <Link 
              key={item.name}
              to={item.href} 
              className={`text-sm font-light tracking-wide transition-colors duration-300 ${
                useLight 
                  ? 'text-white/80 hover:text-white' 
                  : 'text-foreground/70 hover:text-foreground'
              }`}
            >
              {item.name}
            </Link>
          ))}
        </div>

        {/* Desktop CTA */}
        <div className="hidden lg:flex items-center">
          <Link 
            to="/match" 
            className={`px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-300 ${
              useLight 
                ? 'border border-white/30 text-white hover:border-white/50 hover:bg-white/10' 
                : 'btn-primary'
            }`}
          >
            Request a Private Shortlist
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <div className="flex lg:hidden items-center">
          <button 
            className={`p-2 transition-colors ${useLight ? 'text-white' : 'text-foreground'}`}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-background/95 backdrop-blur-md border-t border-border fixed inset-x-0 top-[57px] bottom-0 flex flex-col">
          <div className="container-wide py-6 flex-1 overflow-auto">
            {mobileNav.map((item) => (
              <Link 
                key={item.name} 
                to={item.href} 
                className="block py-4 text-foreground font-medium border-b border-border/50"
              >
                {item.name}
              </Link>
            ))}
          </div>
          {/* Fixed CTA at bottom */}
          <div className="container-wide py-4 border-t border-border bg-background">
            <Link to="/match" className="block w-full btn-primary text-center">
              Request a Private Shortlist
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
