import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { Loader2, ArrowRight, Mail, KeyRound } from 'lucide-react';
import { z } from 'zod';

const authSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters').optional(),
});

const isCompanyEmail = (email: string) => email.toLowerCase().endsWith('@abriqot.com');

export default function AdminAuth() {
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [emailSent, setEmailSent] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handlePasswordSignIn = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrors({});

    const formData = new FormData(e.currentTarget);
    const data = {
      email: formData.get('email') as string,
      password: formData.get('password') as string,
    };

    const result = authSchema.safeParse(data);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      result.error.errors.forEach((err) => {
        if (err.path[0]) {
          fieldErrors[err.path[0] as string] = err.message;
        }
      });
      setErrors(fieldErrors);
      return;
    }

    if (!isCompanyEmail(data.email)) {
      setErrors({ email: 'Only @abriqot.com accounts are allowed.' });
      return;
    }

    setIsLoading(true);

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email: data.email,
        password: data.password,
      });
      if (error) throw error;
      navigate('/admin');
    } catch (error: any) {
      toast({
        title: 'Authentication failed',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleMagicLink = async () => {
    setErrors({});
    const email = (document.getElementById('magic-email') as HTMLInputElement)?.value || '';
    if (!email) {
      setErrors({ email: 'Email is required for magic link.' });
      return;
    }
    if (!isCompanyEmail(email)) {
      setErrors({ email: 'Only @abriqot.com accounts are allowed.' });
      return;
    }

    setIsLoading(true);
    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: `${window.location.origin}/admin` },
      });
      if (error) throw error;
      setEmailSent(true);
      toast({
        title: 'Magic link sent',
        description: 'Check your inbox to sign in.',
      });
    } catch (error: any) {
      toast({
        title: 'Magic link failed',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async () => {
    const email = (document.getElementById('magic-email') as HTMLInputElement)?.value || '';
    if (!email) {
      setErrors({ email: 'Enter your email to reset password.' });
      return;
    }
    if (!isCompanyEmail(email)) {
      setErrors({ email: 'Only @abriqot.com accounts are allowed.' });
      return;
    }

    setIsLoading(true);
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/admin/reset`,
      });
      if (error) throw error;
      toast({
        title: 'Reset email sent',
        description: 'Follow the link in your inbox to set a new password.',
      });
    } catch (error: any) {
      toast({
        title: 'Reset failed',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-semibold text-foreground">Admin Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Invite-only access for Abriqot team members.
          </p>
        </div>

        <div className="bg-card border border-border rounded-2xl p-8 space-y-6">
          <form onSubmit={handlePasswordSignIn} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Work email</label>
              <input
                type="email"
                name="email"
                className={`form-input ${errors.email ? 'border-destructive' : ''}`}
                disabled={isLoading}
                placeholder="name@abriqot.com"
              />
              {errors.email && <p className="text-destructive text-sm mt-1">{errors.email}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Password</label>
              <input
                type="password"
                name="password"
                className={`form-input ${errors.password ? 'border-destructive' : ''}`}
                disabled={isLoading}
              />
              {errors.password && <p className="text-destructive text-sm mt-1">{errors.password}</p>}
            </div>
            <button type="submit" className="btn-primary w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="border-t border-border pt-6 space-y-3">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Magic link</label>
              <input
                id="magic-email"
                type="email"
                className={`form-input ${errors.email ? 'border-destructive' : ''}`}
                placeholder="name@abriqot.com"
                disabled={isLoading}
              />
            </div>
            <button type="button" className="btn-secondary w-full" onClick={handleMagicLink} disabled={isLoading}>
              {emailSent ? (
                <>
                  <Mail className="w-4 h-4" />
                  Link sent
                </>
              ) : (
                <>
                  <Mail className="w-4 h-4" />
                  Send magic link
                </>
              )}
            </button>
            <button type="button" className="btn-ghost w-full" onClick={handleResetPassword} disabled={isLoading}>
              <KeyRound className="w-4 h-4" />
              Reset password
            </button>
          </div>

          <div className="text-xs text-muted-foreground text-center">
            Access is invite-only. Contact Eli for onboarding.
          </div>
        </div>
      </div>
    </div>
  );
}
