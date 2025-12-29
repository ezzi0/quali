import { useState } from 'react';
import Layout from '@/components/layout/Layout';
import { MessageCircle, Mail, MapPin, Clock, Loader2, Check } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { z } from 'zod';

const contactSchema = z.object({
  name: z.string().trim().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
  email: z.string().trim().email('Invalid email address').max(255, 'Email must be less than 255 characters'),
  message: z.string().trim().min(1, 'Message is required').max(2000, 'Message must be less than 2000 characters'),
});

export default function Contact() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrors({});
    
    const formData = new FormData(e.currentTarget);
    const data = {
      name: formData.get('name') as string,
      email: formData.get('email') as string,
      message: formData.get('message') as string,
    };

    const result = contactSchema.safeParse(data);
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

    setIsSubmitting(true);

    try {
      const { error } = await supabase.from('leads').insert({
        form_type: 'contact',
        name: data.name,
        email: data.email,
        message: data.message,
      });

      if (error) throw error;

      supabase.functions.invoke('send-lead-notification', {
        body: {
          type: 'contact',
          name: data.name,
          email: data.email,
          message: data.message,
        },
      }).catch(console.error);

      setIsSuccess(true);
      toast({
        title: 'Received',
        description: 'We will respond during coverage hours.',
      });
    } catch (error) {
      console.error('Error submitting contact form:', error);
      toast({
        title: 'Failed to send',
        description: 'Please try again or contact us via WhatsApp.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Layout>
      <section className="pt-32 pb-20">
        <div className="container-wide">
          <div className="max-w-xl mb-12">
            <h1 className="heading-1 mb-4">Contact Abriqot</h1>
            <p className="text-muted-foreground">Reach out and we will route you to the right specialist for your goals.</p>
          </div>
          
          <div className="grid lg:grid-cols-2 gap-12">
            {/* Contact Info */}
            <div className="space-y-6">
              <p className="text-sm text-muted-foreground">A direct line to the right specialist.</p>
              {[
                { icon: MessageCircle, label: 'WhatsApp', value: '+971 XX XXX XXXX', href: 'https://wa.me/971XXXXXXXXX' },
                { icon: Mail, label: 'Email', value: 'hello@abriqot.com', href: 'mailto:hello@abriqot.com' },
                { icon: MapPin, label: 'Location', value: 'Dubai, UAE' },
                { icon: Clock, label: 'Response target', value: 'Same day during coverage hours' },
              ].map((item) => (
                <div key={item.label} className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <item.icon className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">{item.label}</p>
                    {item.href ? (
                      <a href={item.href} className="font-medium text-foreground hover:text-primary transition-colors">{item.value}</a>
                    ) : (
                      <p className="font-medium text-foreground">{item.value}</p>
                    )}
                  </div>
                </div>
              ))}

              <div className="mt-8 aspect-[4/3] rounded-2xl overflow-hidden">
                <img 
                  src="https://images.unsplash.com/photo-1582407947304-fd86f028f716?w=600&h=450&fit=crop"
                  alt="Dubai cityscape"
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
            
            {/* Contact Form */}
            <div className="bg-card border border-border rounded-2xl p-6 md:p-8">
              {isSuccess ? (
                <div className="text-center py-8">
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                    <Check className="w-8 h-8 text-primary" />
                  </div>
                  <h2 className="text-xl font-semibold text-foreground mb-2">Received</h2>
                  <p className="text-muted-foreground">We will respond during coverage hours.</p>
                </div>
              ) : (
                <>
                  <h2 className="text-xl font-semibold text-foreground mb-6">Send a message</h2>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                      <input 
                        type="text" 
                        name="name"
                        placeholder="Full name" 
                        className={`form-input ${errors.name ? 'border-destructive' : ''}`}
                        disabled={isSubmitting}
                      />
                      {errors.name && <p className="text-destructive text-sm mt-1">{errors.name}</p>}
                    </div>
                    <div>
                      <input 
                        type="email" 
                        name="email"
                        placeholder="Email address" 
                        className={`form-input ${errors.email ? 'border-destructive' : ''}`}
                        disabled={isSubmitting}
                      />
                      {errors.email && <p className="text-destructive text-sm mt-1">{errors.email}</p>}
                    </div>
                    <div>
                      <textarea 
                        name="message"
                        placeholder="How can we help" 
                        rows={4} 
                        className={`form-input ${errors.message ? 'border-destructive' : ''}`}
                        disabled={isSubmitting}
                      />
                      {errors.message && <p className="text-destructive text-sm mt-1">{errors.message}</p>}
                    </div>
                    <button 
                      type="submit" 
                      className="btn-primary w-full"
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Sending...
                        </>
                      ) : (
                        'Send message'
                      )}
                    </button>
                  </form>
                </>
              )}
            </div>
          </div>
        </div>
      </section>
    </Layout>
  );
}