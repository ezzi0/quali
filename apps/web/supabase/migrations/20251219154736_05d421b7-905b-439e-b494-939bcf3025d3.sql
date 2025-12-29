-- Create properties table for the collection
CREATE TABLE public.properties (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  location TEXT NOT NULL,
  developer TEXT NOT NULL,
  price_from INTEGER NOT NULL,
  price_display TEXT NOT NULL,
  handover TEXT NOT NULL,
  handover_year INTEGER NOT NULL,
  payment_plan TEXT NOT NULL,
  roi TEXT,
  property_type TEXT NOT NULL DEFAULT 'Apartment',
  image_url TEXT NOT NULL,
  description TEXT,
  bedrooms TEXT,
  unit_sizes TEXT,
  amenities TEXT[],
  highlights TEXT[],
  is_featured BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.properties ENABLE ROW LEVEL SECURITY;

-- Public can view active properties
CREATE POLICY "Anyone can view active properties"
ON public.properties
FOR SELECT
USING (is_active = true);

-- Admins can do everything
CREATE POLICY "Admins can manage properties"
ON public.properties
FOR ALL
USING (public.has_role(auth.uid(), 'admin'))
WITH CHECK (public.has_role(auth.uid(), 'admin'));

-- Create trigger for updated_at
CREATE TRIGGER update_properties_updated_at
BEFORE UPDATE ON public.properties
FOR EACH ROW
EXECUTE FUNCTION public.update_updated_at_column();