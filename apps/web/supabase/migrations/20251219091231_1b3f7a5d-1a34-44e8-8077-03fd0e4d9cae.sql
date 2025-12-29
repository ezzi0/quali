-- Create leads table for match form and contact form submissions
CREATE TABLE public.leads (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  
  -- Contact info
  name TEXT,
  email TEXT,
  phone TEXT,
  contact_preference TEXT,
  country_timezone TEXT,
  
  -- Match preferences
  budget TEXT,
  down_payment TEXT,
  installment_preference TEXT,
  handover_preference TEXT,
  strategy TEXT,
  risk_style TEXT,
  exit_preference TEXT,
  
  -- Message (for contact form)
  message TEXT,
  
  -- Source tracking
  source TEXT NOT NULL DEFAULT 'website',
  form_type TEXT NOT NULL, -- 'match' or 'contact'
  
  -- Status tracking
  status TEXT NOT NULL DEFAULT 'new'
);

-- Enable RLS but allow public inserts (leads can be submitted without auth)
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;

-- Policy for public insert (anyone can submit a lead)
CREATE POLICY "Anyone can submit a lead"
ON public.leads
FOR INSERT
WITH CHECK (true);

-- Policy for authenticated users to read leads (for admin purposes later)
CREATE POLICY "Authenticated users can read leads"
ON public.leads
FOR SELECT
TO authenticated
USING (true);