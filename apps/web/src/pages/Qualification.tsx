import Layout from '@/components/layout/Layout';
import QualificationChat from '@/components/qualification/QualificationChat';

export default function Qualification() {
  return (
    <Layout>
      <section className="pt-24 pb-16 bg-background">
        <div className="container-narrow">
          <QualificationChat variant="page" />
        </div>
      </section>
    </Layout>
  );
}
