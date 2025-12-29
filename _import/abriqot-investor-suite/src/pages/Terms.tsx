import Layout from '@/components/layout/Layout';

export default function Terms() {
  return (
    <Layout>
      <section className="pt-32 pb-16 bg-background">
        <div className="container-narrow">
          <h1 className="heading-1 text-foreground mb-6">Terms of Service</h1>
          <p className="text-muted-foreground mb-8">Last updated: December 2024</p>
          
          <div className="prose prose-lg max-w-none space-y-8">
            <div>
              <h2 className="heading-4 mb-4">Service Description</h2>
              <p className="text-muted-foreground">We provide investment matching and advisory services for Dubai off-plan real estate. We are not licensed financial advisors and do not provide financial advice.</p>
            </div>
            <div>
              <h2 className="heading-4 mb-4">No Guarantees</h2>
              <p className="text-muted-foreground">Real estate investments carry risk. We do not guarantee returns, property values, or rental income. All investment decisions are your responsibility.</p>
            </div>
            <div>
              <h2 className="heading-4 mb-4">User Responsibilities</h2>
              <p className="text-muted-foreground">You agree to provide accurate information and conduct your own due diligence before making investment decisions.</p>
            </div>
            <div>
              <h2 className="heading-4 mb-4">Limitation of Liability</h2>
              <p className="text-muted-foreground">We are not liable for investment losses or decisions made based on information provided through our services.</p>
            </div>
          </div>
        </div>
      </section>
    </Layout>
  );
}
