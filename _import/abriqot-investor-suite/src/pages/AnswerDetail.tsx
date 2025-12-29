import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Calendar, CheckCircle, AlertTriangle } from 'lucide-react';
import Layout from '@/components/layout/Layout';
import { Helmet } from 'react-helmet-async';

const answerContent: Record<string, {
  question: string;
  category: string;
  updated: string;
  answer: string[];
  whatToVerify: string[];
  commonMistakes: string[];
  relatedQuestions: { slug: string; question: string }[];
}> = {
  'what-is-off-plan': {
    question: 'What is off-plan property?',
    category: 'Getting Started',
    updated: 'December 2024',
    answer: [
      'Off-plan property refers to real estate that is purchased before construction is complete, sometimes even before it begins. You\'re essentially buying based on architectural plans and developer commitments.',
      'In Dubai, off-plan purchases are regulated by RERA (Real Estate Regulatory Agency) and your payments are protected in escrow accounts that developers can only access as construction milestones are met.',
      'The main advantage is price: off-plan units are typically 10-20% below comparable ready properties, and payment plans allow you to spread costs over the construction period.',
    ],
    whatToVerify: [
      'RERA registration number for the project',
      'Developer\'s escrow account details',
      'Construction timeline and milestones',
    ],
    commonMistakes: [
      'Not verifying developer track record',
      'Ignoring escrow account requirements',
      'Overlooking payment plan terms',
    ],
    relatedQuestions: [
      { slug: 'minimum-investment', question: 'What is the minimum investment amount?' },
      { slug: 'what-are-risks', question: 'What are the risks of off-plan investment?' },
    ],
  },
  'minimum-investment': {
    question: 'What is the minimum investment amount?',
    category: 'Getting Started',
    updated: 'December 2024',
    answer: [
      'Entry-level off-plan investments in Dubai start from around AED 500,000 (approximately USD 136,000) for studio apartments in emerging areas like JVC, Dubai South, or Arjan.',
      'For prime locations like Dubai Marina, Downtown, or Palm Jumeirah, expect minimums starting from AED 1.5 million and up.',
      'Payment plans mean you don\'t need the full amount upfront. A typical 60/40 plan requires 10% at booking, with the remaining 50% spread over construction and 40% at handover.',
    ],
    whatToVerify: [
      'Current starting prices for your target area',
      'Payment plan structure and schedule',
      'Any additional fees (DLD, admin, service charges)',
    ],
    commonMistakes: [
      'Not accounting for transfer fees (4% DLD)',
      'Underestimating post-handover costs',
      'Choosing location based on price alone',
    ],
    relatedQuestions: [
      { slug: 'payment-plan-options', question: 'What payment plan options are available?' },
      { slug: 'can-i-get-mortgage', question: 'Can I get a mortgage for off-plan property?' },
    ],
  },
  'payment-plan-options': {
    question: 'What payment plan options are available?',
    category: 'Payment & Financing',
    updated: 'December 2024',
    answer: [
      'Dubai developers offer various payment structures. The most common is 60/40: 60% during construction and 40% on handover. This balances developer needs with buyer flexibility.',
      'Premium projects often offer 70/30 or 80/20 plans, requiring more upfront capital. Post-handover plans extend payments 2-5 years after completion but typically come at a price premium.',
      'Some developers offer customizable plans or 1% monthly structures. Payment flexibility varies by developer and project phase.',
    ],
    whatToVerify: [
      'Exact payment schedule with dates',
      'Penalties for late payments',
      'Options if handover is delayed',
    ],
    commonMistakes: [
      'Not matching payments to income timing',
      'Ignoring post-handover payment obligations',
      'Assuming all plans are negotiable',
    ],
    relatedQuestions: [
      { slug: 'can-i-get-mortgage', question: 'Can I get a mortgage for off-plan property?' },
      { slug: 'what-is-escrow', question: 'What is an escrow account?' },
    ],
  },
  'can-i-get-mortgage': {
    question: 'Can I get a mortgage for off-plan property?',
    category: 'Payment & Financing',
    updated: 'December 2024',
    answer: [
      'Yes, UAE banks offer mortgages for off-plan properties, but with some conditions. Most banks require 50% of construction to be complete before releasing funds.',
      'Non-residents can access mortgages but typically require a larger down payment (30-40%) compared to UAE residents (20-25%).',
      'During construction, you\'ll typically make payments directly to the developer\'s escrow account. The mortgage kicks in closer to handover.',
    ],
    whatToVerify: [
      'Bank\'s construction completion requirements',
      'Interest rates for non-residents',
      'Required documentation for application',
    ],
    commonMistakes: [
      'Assuming mortgage covers booking deposit',
      'Not getting pre-approval before committing',
      'Overlooking currency exchange implications',
    ],
    relatedQuestions: [
      { slug: 'payment-plan-options', question: 'What payment plan options are available?' },
      { slug: 'buying-as-foreigner', question: 'Can foreigners buy property in Dubai?' },
    ],
  },
  'buying-as-foreigner': {
    question: 'Can foreigners buy property in Dubai?',
    category: 'Legal & Process',
    updated: 'December 2024',
    answer: [
      'Yes, foreigners can buy freehold property in designated areas of Dubai. These include most popular investment zones: Dubai Marina, Downtown, Palm Jumeirah, JVC, Business Bay, and many others.',
      'There are no restrictions on nationality, and you don\'t need a UAE visa or residence to purchase. The process is straightforward and regulated by Dubai Land Department.',
      'Property ownership can also qualify you for a UAE residence visa: the Golden Visa requires a minimum AED 2 million property investment.',
    ],
    whatToVerify: [
      'Freehold status of the specific area',
      'Developer\'s authorization to sell to foreigners',
      'Golden Visa eligibility if relevant',
    ],
    commonMistakes: [
      'Confusing freehold with leasehold areas',
      'Not understanding visa requirements',
      'Assuming all areas allow foreign ownership',
    ],
    relatedQuestions: [
      { slug: 'what-is-escrow', question: 'What is an escrow account?' },
      { slug: 'minimum-investment', question: 'What is the minimum investment amount?' },
    ],
  },
  'what-is-escrow': {
    question: 'What is an escrow account?',
    category: 'Legal & Process',
    updated: 'December 2024',
    answer: [
      'An escrow account is a regulated bank account where buyer payments are held during off-plan construction. Developers cannot freely access these funds.',
      'RERA requires all off-plan projects to have an escrow account. Funds are released to developers only as they complete construction milestones verified by independent engineers.',
      'This protects buyers: if a project is cancelled, funds in escrow are returned. It\'s one of Dubai\'s key investor protections.',
    ],
    whatToVerify: [
      'Escrow account number and bank',
      'RERA registration confirming escrow setup',
      'Payment instructions reference escrow',
    ],
    commonMistakes: [
      'Paying directly to developer accounts',
      'Not confirming escrow before payment',
      'Ignoring receipt documentation',
    ],
    relatedQuestions: [
      { slug: 'what-are-risks', question: 'What are the risks of off-plan investment?' },
      { slug: 'buying-as-foreigner', question: 'Can foreigners buy property in Dubai?' },
    ],
  },
  'expected-returns': {
    question: 'What returns can I expect?',
    category: 'Returns & Risk',
    updated: 'December 2024',
    answer: [
      'Dubai rental yields typically range from 5-10% depending on location and property type. Emerging areas like JVC offer higher yields (8-10%), while premium areas like Downtown offer 5-7% with stronger capital appreciation.',
      'Capital gains vary significantly by market cycle and location. Historical data shows Dubai property has delivered 5-15% annual appreciation in strong markets, though this is not guaranteed.',
      'We never promise specific returns. Real estate is a long-term investment with inherent market risk.',
    ],
    whatToVerify: [
      'Current rental rates for comparable units',
      'Historical price trends for the area',
      'Service charges and maintenance costs',
    ],
    commonMistakes: [
      'Relying on developer yield projections',
      'Ignoring vacancy periods in calculations',
      'Not accounting for all ownership costs',
    ],
    relatedQuestions: [
      { slug: 'what-are-risks', question: 'What are the risks of off-plan investment?' },
      { slug: 'minimum-investment', question: 'What is the minimum investment amount?' },
    ],
  },
  'what-are-risks': {
    question: 'What are the risks of off-plan investment?',
    category: 'Returns & Risk',
    updated: 'December 2024',
    answer: [
      'Construction delays are the most common risk. While escrow accounts protect your funds, delayed handover affects your investment timeline and potential rental income.',
      'Market risk exists: property values can decline, affecting both resale value and rental rates. Dubai\'s market has experienced significant cycles historically.',
      'Developer quality varies. Research track record, completed projects, and any history of delays. Established developers with strong portfolios carry less execution risk.',
    ],
    whatToVerify: [
      'Developer\'s delivery history on past projects',
      'SPA terms regarding delay compensation',
      'Current market conditions and trends',
    ],
    commonMistakes: [
      'Assuming all developers are equal',
      'Not reading SPA cancellation terms',
      'Over-leveraging based on projections',
    ],
    relatedQuestions: [
      { slug: 'what-is-escrow', question: 'What is an escrow account?' },
      { slug: 'expected-returns', question: 'What returns can I expect?' },
    ],
  },
};

const defaultAnswer = {
  question: 'Frequently Asked Question',
  category: 'General',
  updated: 'December 2024',
  answer: [
    'This answer provides information about Dubai off-plan investment.',
    'For more detailed guidance, please explore our guides section or contact us directly.',
  ],
  whatToVerify: [],
  commonMistakes: [],
  relatedQuestions: [],
};

export default function AnswerDetail() {
  const { slug } = useParams();
  const answer = slug && answerContent[slug] ? answerContent[slug] : defaultAnswer;

  return (
    <Layout>
      <Helmet>
        <title>{answer.question} | Abriqot Answers</title>
        <meta name="description" content={answer.answer[0]} />
      </Helmet>

      {/* Content */}
      <section className="pt-32 pb-16 bg-background">
        <div className="container-narrow">
          <Link to="/answers" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Answers
          </Link>
          
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <span className="inline-block px-3 py-1 bg-primary/10 text-primary text-xs font-medium rounded-full">
              {answer.category}
            </span>
            <span className="flex items-center gap-1 text-muted-foreground text-xs">
              <Calendar className="w-3 h-3" />
              Updated: {answer.updated}
            </span>
          </div>
          
          <h1 className="text-2xl md:text-3xl font-semibold text-foreground mb-8">{answer.question}</h1>
          
          <div className="prose prose-lg max-w-none">
            {answer.answer.map((paragraph, index) => (
              <p key={index} className="text-muted-foreground mb-6 leading-relaxed">{paragraph}</p>
            ))}
          </div>

          {/* What to Verify */}
          {answer.whatToVerify.length > 0 && (
            <div className="mt-10 p-6 bg-card border border-border rounded-2xl">
              <h2 className="flex items-center gap-2 font-semibold text-foreground mb-4">
                <CheckCircle className="w-5 h-5 text-primary" />
                What to verify
              </h2>
              <ul className="space-y-2">
                {answer.whatToVerify.map((item, index) => (
                  <li key={index} className="flex items-start gap-3 text-muted-foreground">
                    <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Common Mistakes */}
          {answer.commonMistakes.length > 0 && (
            <div className="mt-6 p-6 bg-muted/50 border border-border rounded-2xl">
              <h2 className="flex items-center gap-2 font-semibold text-foreground mb-4">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                Common mistakes
              </h2>
              <ul className="space-y-2">
                {answer.commonMistakes.map((item, index) => (
                  <li key={index} className="flex items-start gap-3 text-muted-foreground">
                    <span className="w-1.5 h-1.5 bg-amber-500 rounded-full mt-2 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Related Questions */}
          {answer.relatedQuestions.length > 0 && (
            <div className="mt-10 p-6 bg-card border border-border rounded-2xl">
              <h2 className="font-semibold text-foreground mb-4">Related Questions</h2>
              <div className="space-y-2">
                {answer.relatedQuestions.map((related) => (
                  <Link
                    key={related.slug}
                    to={`/answers/${related.slug}`}
                    className="block p-4 bg-background border border-border rounded-xl hover:border-primary/50 transition-colors"
                  >
                    <span className="text-foreground">{related.question}</span>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Links */}
          <div className="mt-10 flex flex-wrap gap-4">
            <Link to="/match" className="btn-primary inline-flex items-center gap-2">
              Request a Private Shortlist
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/deal-memos" className="btn-secondary">
              Get the Deal Memo Pack
            </Link>
            <Link to="/compliance" className="text-muted-foreground hover:text-foreground text-sm underline underline-offset-4">
              Compliance and verification
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
}