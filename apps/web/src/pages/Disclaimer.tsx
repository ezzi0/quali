import Layout from '@/components/layout/Layout';

export default function Disclaimer() {
  return (
    <Layout>
      <section className="pt-32 pb-16 bg-background">
        <div className="container-narrow">
          <h1 className="heading-1 text-foreground mb-6">Disclaimer</h1>
          <p className="text-muted-foreground mb-8">Important information about our services</p>
          
          <div className="prose prose-lg max-w-none space-y-8">
            <div>
              <h2 className="heading-4 mb-4">Investment Risk</h2>
              <p className="text-muted-foreground">Real estate investments involve substantial risk including the possible loss of principal. Past performance is not indicative of future results. Property values and rental income can fluctuate.</p>
            </div>
            <div>
              <h2 className="heading-4 mb-4">Not Financial Advice</h2>
              <p className="text-muted-foreground">Information provided is for general guidance only and should not be considered financial, legal, or tax advice. Consult qualified professionals before making investment decisions.</p>
            </div>
            <div>
              <h2 className="heading-4 mb-4">Forward-Looking Statements</h2>
              <p className="text-muted-foreground">Any projections, forecasts, or estimates are illustrative only and may not reflect actual results. Market conditions can change rapidly.</p>
            </div>
            <div>
              <h2 className="heading-4 mb-4">Third-Party Information</h2>
              <p className="text-muted-foreground">We may reference third-party data which we believe to be reliable but cannot guarantee its accuracy or completeness.</p>
            </div>
          </div>
        </div>
      </section>
    </Layout>
  );
}
