import Layout from '@/components/layout/Layout';
import { Link } from 'react-router-dom';
import { Shield, CheckCircle } from 'lucide-react';

export default function Compliance() {
  return (
    <Layout>
      <section className="section-padding bg-gradient-hero">
        <div className="container-wide">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="w-6 h-6 text-accent" />
            <span className="text-accent font-medium">Transparency</span>
          </div>
          <h1 className="heading-1 mb-6">Compliance and verification</h1>
          <p className="body-large text-muted-foreground max-w-3xl">
            Abriqot operates as a Dubai brokerage. We follow applicable marketing and permitting requirements and encourage clients to verify documentation through official channels.
          </p>
        </div>
      </section>
      
      <section className="section-padding">
        <div className="container-wide space-y-12">
          <p className="text-sm text-muted-foreground">Transparency, quietly handled.</p>
          
          <div className="card-premium p-8">
            <h2 className="heading-4 mb-4">What we verify before presenting opportunities</h2>
            <p className="text-muted-foreground mb-4">We verify project permits and developer credentials before presenting any opportunity. You can independently verify through:</p>
            <ul className="space-y-2">
              <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-accent" /> Dubai Land Department (DLD)</li>
              <li className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-accent" /> Trakheesi permit system</li>
            </ul>
          </div>

          <div className="card-premium p-8">
            <h2 className="heading-4 mb-4">How to verify permits and licenses</h2>
            <p className="text-muted-foreground">All off plan projects in Dubai must be registered with RERA. You can verify any project through the Dubai REST app or the Dubai Land Department website.</p>
          </div>
          
          <div className="card-premium p-8">
            <h2 className="heading-4 mb-4">How we are compensated</h2>
            <p className="text-muted-foreground">In most transactions, commission is paid by the developer. If any other fee applies, we disclose it upfront before you proceed.</p>
          </div>
          
          <div className="card-premium p-8 bg-destructive/5 border-destructive/20">
            <h2 className="heading-4 mb-4">Disclaimers and risk notes</h2>
            <ul className="space-y-2 text-muted-foreground text-sm">
              <li>• Information provided is for general guidance, not financial advice</li>
              <li>• Investing involves risk. Returns are not guaranteed</li>
              <li>• Past performance does not guarantee future results</li>
              <li>• Always conduct independent due diligence</li>
            </ul>
          </div>
        </div>
      </section>
    </Layout>
  );
}