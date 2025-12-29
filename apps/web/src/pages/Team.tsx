import { Link } from 'react-router-dom';
import { ArrowRight, Linkedin } from 'lucide-react';
import Layout from '@/components/layout/Layout';
import { siteAssets } from '@/data/site-assets';

const team = [
  {
    name: 'Sarah Al-Rashid',
    role: 'Managing Director',
    bio: '15+ years in UAE real estate. Former head of sales at Emaar Properties.',
    image: siteAssets.team[0],
    linkedin: '#',
  },
  {
    name: 'James Chen',
    role: 'Head of International Sales',
    bio: 'Specializes in serving international investors from Asia and Europe.',
    image: siteAssets.team[1],
    linkedin: '#',
  },
  {
    name: 'Fatima Hassan',
    role: 'Senior Investment Advisor',
    bio: 'RERA certified. Expert in off-plan due diligence and market analysis.',
    image: siteAssets.team[2],
    linkedin: '#',
  },
  {
    name: 'Michael Roberts',
    role: 'Client Relations Manager',
    bio: 'Ensures seamless experience for clients from inquiry to handover.',
    image: siteAssets.team[3],
    linkedin: '#',
  },
];

export default function Team() {
  return (
    <Layout>
      {/* Hero */}
      <section className="pt-32 pb-16 bg-background">
        <div className="container-wide">
          <div className="max-w-2xl">
            <h1 className="heading-1 text-foreground mb-6">
              The team behind Abriqot
            </h1>
            <p className="body-large text-muted-foreground mb-8">
              A specialist led team built for international buyers. Languages, time zones, and execution are part of the design.
            </p>
            <Link to="/match" className="btn-primary">
              Request a Private Shortlist
            </Link>
          </div>
        </div>
      </section>

      {/* Team Grid */}
      <section className="section-padding">
        <div className="container-wide">
          <p className="text-sm text-muted-foreground mb-8">Specialists, not generalists.</p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {team.map((member) => (
              <div key={member.name} className="text-center">
                <div className="w-32 h-32 mx-auto mb-4 rounded-full overflow-hidden bg-muted">
                  {member.image ? (
                    <img
                      src={member.image}
                      alt={member.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-muted-foreground text-xs">
                      Image pending
                    </div>
                  )}
                </div>
                <h3 className="font-semibold text-foreground">{member.name}</h3>
                <p className="text-primary text-sm mb-2">{member.role}</p>
                <p className="text-muted-foreground text-sm mb-3">{member.bio}</p>
                <a href={member.linkedin} className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground text-sm">
                  <Linkedin className="w-4 h-4" />
                  Contact this specialist
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="section-padding bg-card border-t border-border">
        <div className="container-narrow text-center">
          <h2 className="heading-3 mb-4">Work with us</h2>
          <p className="text-muted-foreground mb-8">
            Get matched with the right specialist for your investment goals.
          </p>
          <Link to="/match" className="btn-primary inline-flex items-center gap-2">
            Request a Private Shortlist
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </Layout>
  );
}
