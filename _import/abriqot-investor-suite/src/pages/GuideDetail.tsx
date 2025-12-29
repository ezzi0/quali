import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Clock, ArrowRight, Calendar, User } from 'lucide-react';
import Layout from '@/components/layout/Layout';
import { Helmet } from 'react-helmet-async';

const guideContent: Record<string, {
  title: string;
  excerpt: string;
  readTime: string;
  category: string;
  updated: string;
  content: string[];
  keyTakeaways: string[];
}> = {
  'off-plan-vs-ready': {
    title: 'Off-Plan vs Ready Property: Which is Right for You?',
    excerpt: 'Understand the key differences between off-plan and ready properties in Dubai.',
    readTime: '8 min read',
    category: 'Investment Basics',
    updated: 'December 2024',
    content: [
      'When investing in Dubai real estate, one of the first decisions you\'ll face is whether to purchase off-plan or ready property. Each option has distinct advantages and considerations.',
      'Off-plan properties are purchased directly from developers before construction is complete. The main benefits include lower entry prices (typically 10-20% below market), flexible payment plans spread over construction period, and potential capital appreciation by handover.',
      'Ready properties offer immediate ownership and rental income. You can physically inspect the unit, and there\'s no construction risk. However, you\'ll typically pay market price and need more capital upfront.',
      'For international investors seeking to build a portfolio over time, off-plan often makes sense due to the payment plan flexibility. However, due diligence on the developer\'s track record is essential.',
    ],
    keyTakeaways: [
      'Off-plan offers lower entry prices and payment plans',
      'Ready properties provide immediate rental income',
      'Developer track record is crucial for off-plan',
      'Consider your investment timeline and capital availability',
    ],
  },
  'payment-plans-explained': {
    title: 'Dubai Payment Plans Explained',
    excerpt: 'A complete breakdown of developer payment plans.',
    readTime: '6 min read',
    category: 'Payment Plans',
    updated: 'December 2024',
    content: [
      'Dubai developers offer various payment structures to make off-plan purchases accessible. Understanding these plans is key to matching investments with your cash flow.',
      'The most common structure is the 60/40 plan: 60% during construction and 40% on handover. This provides a good balance between developer security and buyer flexibility.',
      '70/30 and 80/20 plans require more capital during construction but reduce the handover burden. These are often offered for premium projects.',
      'Post-handover payment plans extend payments 2-5 years after completion. While attractive for cash flow, these typically come at a premium price.',
    ],
    keyTakeaways: [
      '60/40 is the most balanced structure',
      'Post-handover plans cost more but ease cash flow',
      'Align payment schedules with your income',
      'Some developers offer customizable plans',
    ],
  },
  'golden-visa-property': {
    title: 'How to Get a Golden Visa Through Property Investment',
    excerpt: 'Step-by-step guide to UAE residency through real estate.',
    readTime: '10 min read',
    category: 'Residency',
    updated: 'December 2024',
    content: [
      'The UAE Golden Visa offers 10-year residency for property investors meeting minimum thresholds. As of 2024, the minimum investment is AED 2 million.',
      'The property must be fully paid (not mortgaged beyond 50%) and can be residential or commercial. Off-plan properties qualify once handover is complete.',
      'The application process involves obtaining a property valuation, submitting documents through ICP (Federal Authority for Identity and Citizenship), and completing biometrics.',
      'Benefits include long-term residency, ability to sponsor family, no minimum stay requirement, and access to UAE banking and business setup.',
    ],
    keyTakeaways: [
      'Minimum AED 2 million property value required',
      'Property must be owned outright or max 50% mortgaged',
      'Off-plan qualifies after handover',
      '10-year renewable visa with family sponsorship',
    ],
  },
  'due-diligence-checklist': {
    title: 'The Complete Due Diligence Checklist',
    excerpt: 'Everything to verify before an off-plan purchase.',
    readTime: '12 min read',
    category: 'Developer Diligence',
    updated: 'December 2024',
    content: [
      'Thorough due diligence protects your investment. Start with the developer: check their track record, completed projects, and any delays on previous developments.',
      'Verify project registration with RERA (Real Estate Regulatory Agency). Every off-plan project must have an escrow account protecting buyer payments.',
      'Review the Sales & Purchase Agreement carefully. Understand cancellation terms, delay compensation, and specification commitments.',
      'Research the location thoroughly: infrastructure plans, nearby developments, and historical price trends in the area.',
    ],
    keyTakeaways: [
      'Verify RERA registration and escrow account',
      'Research developer completion history',
      'Understand SPA terms especially for delays',
      'Assess location infrastructure and growth plans',
    ],
  },
  'rental-yields-dubai': {
    title: 'Understanding Rental Yields in Dubai',
    excerpt: 'Calculate and compare yields across Dubai.',
    readTime: '7 min read',
    category: 'Handover Strategy',
    updated: 'December 2024',
    content: [
      'Dubai offers some of the highest rental yields globally, typically ranging from 5-10% depending on location and property type.',
      'Gross yield is calculated as annual rent divided by purchase price. Net yield deducts service charges, maintenance, and vacancy periods.',
      'Areas like JVC, Sports City, and Dubai South offer higher yields (8-10%) but may have lower capital appreciation. Premium areas like Downtown and Marina offer 5-7% yields with stronger capital growth.',
      'Studio and 1-bedroom apartments typically generate higher yields than larger units due to the rental demand profile.',
    ],
    keyTakeaways: [
      'Dubai yields range from 5-10% depending on area',
      'Always calculate net yield after costs',
      'Smaller units often yield more than larger ones',
      'Balance yield against capital appreciation potential',
    ],
  },
  'buying-remotely': {
    title: 'How to Buy Dubai Property Remotely',
    excerpt: 'Complete purchases without visiting Dubai.',
    readTime: '9 min read',
    category: 'Remote Buying',
    updated: 'December 2024',
    content: [
      'Many international investors complete Dubai property purchases entirely remotely. The legal framework fully supports this through Power of Attorney arrangements.',
      'Start by selecting a reputable agent or advisory service who can conduct viewings, negotiate terms, and coordinate documentation on your behalf.',
      'A POA can be executed at a UAE embassy or through an apostille process. This authorizes your representative to sign on your behalf.',
      'Payments can be made via international wire transfer. Most developers accept transfers from foreign accounts. Title deed registration is completed through Dubai Land Department.',
    ],
    keyTakeaways: [
      'Power of Attorney enables full remote purchase',
      'Work with a trusted local representative',
      'International wire transfers are standard',
      'Title deeds are registered digitally',
    ],
  },
};

const defaultGuide = {
  title: 'Investment Guide',
  excerpt: 'Detailed information about Dubai real estate investment.',
  readTime: '5 min read',
  category: 'General',
  updated: 'December 2024',
  content: [
    'This guide covers essential information for investors considering Dubai real estate.',
    'Dubai offers a unique combination of tax-free income, high yields, and strong capital appreciation potential.',
    'Working with experienced professionals can help navigate the market effectively.',
  ],
  keyTakeaways: [
    'Research thoroughly before investing',
    'Understand the legal framework',
    'Work with reputable partners',
  ],
};

export default function GuideDetail() {
  const { slug } = useParams();
  const guide = slug && guideContent[slug] ? guideContent[slug] : defaultGuide;

  return (
    <Layout>
      <Helmet>
        <title>{guide.title} | Abriqot Guides</title>
        <meta name="description" content={guide.excerpt} />
      </Helmet>

      {/* Hero */}
      <section className="pt-32 pb-8 bg-background">
        <div className="container-narrow">
          <Link to="/guides" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Guides
          </Link>
          
          <span className="inline-block px-3 py-1 bg-primary/10 text-primary text-xs font-medium rounded-full mb-4">
            {guide.category}
          </span>
          
          <h1 className="text-3xl md:text-4xl font-semibold text-foreground mb-4">{guide.title}</h1>
          
          {/* Article microcopy */}
          <div className="flex flex-wrap items-center gap-4 text-muted-foreground text-sm">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              {guide.readTime}
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Updated: {guide.updated}
            </div>
            <div className="flex items-center gap-2">
              <User className="w-4 h-4" />
              Abriqot Editorial
            </div>
          </div>
        </div>
      </section>

      {/* Featured Image */}
      <section className="pb-8">
        <div className="container-narrow">
          <div className="aspect-[21/9] rounded-2xl overflow-hidden">
            <img 
              src="https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1200&h=500&fit=crop"
              alt={guide.title}
              className="w-full h-full object-cover"
            />
          </div>
        </div>
      </section>

      {/* Content */}
      <section className="py-12">
        <div className="container-narrow">
          <div className="space-y-6">
            {guide.content.map((paragraph, index) => (
              <p key={index} className="text-muted-foreground leading-relaxed">{paragraph}</p>
            ))}
          </div>

          {/* Key Takeaways */}
          <div className="mt-10 p-6 bg-muted/50 border border-border rounded-2xl">
            <h2 className="font-semibold text-foreground mb-4">Key Takeaways</h2>
            <ul className="space-y-3">
              {guide.keyTakeaways.map((takeaway, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="w-6 h-6 bg-primary text-primary-foreground text-sm font-medium rounded-full flex items-center justify-center flex-shrink-0">
                    {index + 1}
                  </span>
                  <span className="text-foreground">{takeaway}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* CTA */}
          <div className="mt-12 p-8 bg-card border border-border rounded-2xl text-center">
            <h3 className="text-xl font-semibold text-foreground mb-2">Want a shortlist built around your criteria?</h3>
            <p className="text-muted-foreground mb-6">Start with a brief. We will return with a refined selection.</p>
            <Link to="/match" className="btn-primary inline-flex items-center gap-2">
              Request a Private Shortlist
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
}