import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { api } from '@/lib/api';

export type AdminProfile = {
  email: string;
  role: 'admin' | 'agent';
  is_super_admin: boolean;
};

export function useAdminSession() {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<AdminProfile | null>(null);

  useEffect(() => {
    let mounted = true;

    const hydrate = async () => {
      const { data } = await supabase.auth.getSession();
      const session = data.session;
      if (!session) {
        if (mounted) {
          setProfile(null);
          setLoading(false);
        }
        return;
      }

      const email = session.user?.email || '';
      if (!email.endsWith('@abriqot.com')) {
        await supabase.auth.signOut();
        if (mounted) {
          setProfile(null);
          setLoading(false);
        }
        return;
      }

      try {
        const me = await api.auth.me();
        if (mounted) {
          setProfile(me as AdminProfile);
          setLoading(false);
        }
      } catch (error) {
        await supabase.auth.signOut();
        if (mounted) {
          setProfile(null);
          setLoading(false);
        }
      }
    };

    hydrate();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(() => {
      hydrate();
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  return { loading, profile };
}
