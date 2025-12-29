import Layout from '@/components/layout/Layout';

export default function Privacy() {
  return (
    <Layout>
      <section className="pt-32 pb-16 bg-background">
        <div className="container-narrow">
          <h1 className="heading-1 text-foreground mb-6">Privacy Policy</h1>
          <p className="text-muted-foreground mb-8">Last updated: December 2024</p>
          
          <div className="prose prose-lg max-w-none space-y-8">
            <div>
              <h2 className="heading-4 mb-4">Information We Collect</h2>
              <p className="text-muted-foreground">We collect information you provide directly, including name, email, phone number, and investment preferences when you use our matching service or contact us.</p>
            </div>
            <div>
              <h2 className="heading-4 mb-4">How We Use Your Information</h2>
              <p className="text-muted-foreground">We use your information to provide investment matching services, send relevant opportunities, and improve our services. We never sell your data to third parties.</p>
            </div>
            <div>
              <h2 className="heading-4 mb-4">Data Security</h2>
              <p className="text-muted-foreground">We implement industry-standard security measures to protect your personal information from unauthorized access or disclosure.</p>
            </div>
            <div>
              <h2 className="heading-4 mb-4">Contact Us</h2>
              <p className="text-muted-foreground">For privacy-related inquiries, please contact us at privacy@example.com.</p>
            </div>
          </div>
        </div>
      </section>
    </Layout>
  );
}
