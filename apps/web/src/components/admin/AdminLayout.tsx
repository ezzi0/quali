import { ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useAdminSession } from '@/hooks/use-admin-session';

export default function AdminLayout({ children, title }: { children: ReactNode; title?: string }) {
  const { loading, profile } = useAdminSession();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate('/admin/auth');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-muted/30 flex items-center justify-center">
        <div className="text-muted-foreground">Loading admin console...</div>
      </div>
    );
  }

  if (!profile) {
    navigate('/admin/auth');
    return null;
  }

  const navLinks = [
    { to: '/admin', label: 'Leads' },
    { to: '/admin/collection', label: 'Collection' },
    { to: '/admin/marketing', label: 'Marketing' },
    { to: '/admin/chat', label: 'Qualification' },
    ...(profile?.is_super_admin ? [{ to: '/admin/users', label: 'Users' }] : []),
  ];

  return (
    <div className="dark">
      <div className="min-h-screen bg-muted/30">
      <header className="bg-background border-b border-border sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 py-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-xl font-semibold text-foreground">Abriqot Admin</h1>
              {title && <p className="text-sm text-muted-foreground">{title}</p>}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`px-3 py-2 text-sm rounded-lg transition-colors ${
                    location.pathname === link.to
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
              <span className="text-xs text-muted-foreground hidden md:block">{profile.email}</span>
              <button onClick={handleLogout} className="p-2 text-muted-foreground hover:text-foreground transition-colors">
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      </div>
    </div>
  );
}
