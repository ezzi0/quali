import { serve } from "https://deno.land/std@0.190.0/http/server.ts";
import { Resend } from "https://esm.sh/resend@2.0.0";

const resend = new Resend(Deno.env.get("RESEND_API_KEY"));

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface LeadNotificationRequest {
  type: 'match' | 'contact';
  name?: string;
  email?: string;
  phone?: string;
  budget?: string;
  strategy?: string;
  handoverPreference?: string;
  contactPreference?: string;
  message?: string;
}

// HTML escape function to prevent XSS attacks
const escapeHtml = (text: string | undefined): string => {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
};

// Simple input validation
const validateInput = (data: LeadNotificationRequest): { valid: boolean; error?: string } => {
  // Type must be 'match' or 'contact'
  if (!data.type || !['match', 'contact'].includes(data.type)) {
    return { valid: false, error: 'Invalid form type' };
  }
  
  // At least one contact method required
  if (!data.email && !data.phone && !data.name) {
    return { valid: false, error: 'At least one contact field is required' };
  }
  
  // Email format validation if provided
  if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    return { valid: false, error: 'Invalid email format' };
  }
  
  // Length limits to prevent abuse
  const maxLengths: Record<string, number> = {
    name: 100,
    email: 255,
    phone: 50,
    budget: 100,
    strategy: 100,
    handoverPreference: 100,
    contactPreference: 100,
    message: 2000,
  };
  
  for (const [field, maxLength] of Object.entries(maxLengths)) {
    const value = data[field as keyof LeadNotificationRequest];
    if (value && typeof value === 'string' && value.length > maxLength) {
      return { valid: false, error: `${field} exceeds maximum length of ${maxLength} characters` };
    }
  }
  
  return { valid: true };
};

const handler = async (req: Request): Promise<Response> => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const data: LeadNotificationRequest = await req.json();
    console.log("Received lead notification request:", { type: data.type, hasEmail: !!data.email });

    // Validate input
    const validation = validateInput(data);
    if (!validation.valid) {
      console.warn("Validation failed:", validation.error);
      return new Response(
        JSON.stringify({ error: validation.error }),
        { status: 400, headers: { "Content-Type": "application/json", ...corsHeaders } }
      );
    }

    const adminEmail = Deno.env.get("ADMIN_EMAIL") || "hello@abriqot.com";
    const isMatchForm = data.type === 'match';

    // Escape all user-provided data before embedding in HTML
    const safeName = escapeHtml(data.name);
    const safeEmail = escapeHtml(data.email);
    const safePhone = escapeHtml(data.phone);
    const safeContactPreference = escapeHtml(data.contactPreference);
    const safeBudget = escapeHtml(data.budget);
    const safeStrategy = escapeHtml(data.strategy);
    const safeHandoverPreference = escapeHtml(data.handoverPreference);
    const safeMessage = escapeHtml(data.message);

    // Email to admin
    const adminEmailHtml = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <style>
            body { font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif; background: #f9f9f9; padding: 40px 20px; margin: 0; }
            .container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
            .header { background: linear-gradient(135deg, #FFA927 0%, #FF7E27 100%); padding: 32px; text-align: center; }
            .header h1 { color: #ffffff; margin: 0; font-size: 24px; font-weight: 600; }
            .content { padding: 32px; }
            .badge { display: inline-block; background: #FFA927; color: #fff; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-bottom: 20px; }
            .field { margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #eee; }
            .field:last-child { border-bottom: none; margin-bottom: 0; }
            .label { font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
            .value { font-size: 16px; color: #111; font-weight: 500; }
            .footer { background: #f5f5f5; padding: 24px; text-align: center; }
            .footer p { color: #888; font-size: 12px; margin: 0; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>New ${isMatchForm ? 'Match Request' : 'Contact Message'}</h1>
            </div>
            <div class="content">
              <span class="badge">${isMatchForm ? 'MATCH FORM' : 'CONTACT FORM'}</span>
              
              ${safeName ? `<div class="field"><div class="label">Name</div><div class="value">${safeName}</div></div>` : ''}
              ${safeEmail ? `<div class="field"><div class="label">Email</div><div class="value">${safeEmail}</div></div>` : ''}
              ${safePhone ? `<div class="field"><div class="label">Phone</div><div class="value">${safePhone}</div></div>` : ''}
              ${safeContactPreference ? `<div class="field"><div class="label">Contact Preference</div><div class="value">${safeContactPreference}</div></div>` : ''}
              ${safeBudget ? `<div class="field"><div class="label">Budget</div><div class="value">${safeBudget}</div></div>` : ''}
              ${safeStrategy ? `<div class="field"><div class="label">Strategy</div><div class="value">${safeStrategy}</div></div>` : ''}
              ${safeHandoverPreference ? `<div class="field"><div class="label">Handover</div><div class="value">${safeHandoverPreference}</div></div>` : ''}
              ${safeMessage ? `<div class="field"><div class="label">Message</div><div class="value">${safeMessage}</div></div>` : ''}
            </div>
            <div class="footer">
              <p>Abriqot Lead Notification</p>
            </div>
          </div>
        </body>
      </html>
    `;

    // Send admin notification
    const adminResponse = await resend.emails.send({
      from: "Abriqot <onboarding@resend.dev>",
      to: [adminEmail],
      subject: `New ${isMatchForm ? 'Match Request' : 'Contact Message'} - Abriqot`,
      html: adminEmailHtml,
    });

    console.log("Admin email sent:", adminResponse);

    // Send confirmation to user if they provided email
    if (data.email) {
      const userEmailHtml = `
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <style>
              body { font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif; background: #f9f9f9; padding: 40px 20px; margin: 0; }
              .container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
              .header { background: linear-gradient(135deg, #FFA927 0%, #FF7E27 100%); padding: 40px 32px; text-align: center; }
              .header h1 { color: #ffffff; margin: 0 0 8px 0; font-size: 28px; font-weight: 600; }
              .header p { color: rgba(255,255,255,0.9); margin: 0; font-size: 16px; }
              .content { padding: 40px 32px; }
              .content h2 { color: #111; font-size: 20px; margin: 0 0 16px 0; }
              .content p { color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0; }
              .highlight { background: #FFA927; background: linear-gradient(135deg, #FFA927 0%, #FF7E27 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 600; }
              .cta { display: inline-block; background: #FFA927; color: #fff; padding: 14px 28px; border-radius: 12px; text-decoration: none; font-weight: 600; margin-top: 8px; }
              .footer { background: #f5f5f5; padding: 24px; text-align: center; }
              .footer p { color: #888; font-size: 12px; margin: 0; }
              .footer a { color: #FFA927; text-decoration: none; }
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h1>We've received your request</h1>
                <p>A specialist will be in touch shortly</p>
              </div>
              <div class="content">
                <h2>What happens next?</h2>
                <p>Thank you for reaching out to Abriqot. ${isMatchForm ? 'Our team is reviewing your investment preferences and will prepare a curated shortlist of opportunities that match your criteria.' : 'Our team will review your message and get back to you.'}</p>
                <p>You can expect to hear from us via your preferred contact method within <span class="highlight">24 hours</span>.</p>
                <p>In the meantime, feel free to explore our investment guides or browse current opportunities.</p>
                <a href="https://abriqot.com/guides" class="cta">Explore Guides</a>
              </div>
              <div class="footer">
                <p>Abriqot | Dubai Real Estate Investment</p>
                <p><a href="https://abriqot.com">abriqot.com</a></p>
              </div>
            </div>
          </body>
        </html>
      `;

      const userResponse = await resend.emails.send({
        from: "Abriqot <onboarding@resend.dev>",
        to: [data.email],
        subject: isMatchForm ? "Your Abriqot Match Request" : "We received your message - Abriqot",
        html: userEmailHtml,
      });

      console.log("User confirmation email sent:", userResponse);
    }

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  } catch (error: any) {
    console.error("Error in send-lead-notification function:", error);
    return new Response(
      JSON.stringify({ error: "An error occurred processing your request" }),
      { status: 500, headers: { "Content-Type": "application/json", ...corsHeaders } }
    );
  }
};

serve(handler);
