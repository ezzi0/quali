import { Link } from 'react-router-dom';
import { ArrowRight, Quote } from 'lucide-react';
import Layout from '@/components/layout/Layout';

const stories = [
  {
    name: 'David & Emma Thompson',
    location: 'United Kingdom',
    investment: 'Marina Vista Tower, Dubai Marina',
    quote: "We purchased our first Dubai property entirely remotely. The process was transparent from start to finish, and we received our investment brief before speaking to anyone. Now we're looking at our second investment.",
    image: 'https://images.unsplash.com/photo-1522529599102-193c0d76b5b6?w=400&h=400&fit=crop',
  },
  {
    name: 'Zhang Wei',
    location: 'Singapore',
    investment: 'Downtown Residences',
    quote: 'As a busy professional, I appreciated the efficiency. The curated shortlist saved me weeks of research, and the verification checklist gave me confidence to proceed.',
    image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop',
  },
  {
    name: 'Maria Santos',
    location: 'Brazil',
    investment: 'Creek Harbour Vista',
    quote: 'Coming from Brazil, I had many questions about the process. Every step was explained clearly, and I was matched with an advisor who understood my investment goals perfectly.',
    image: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&h=400&fit=crop',
  },
  {
    name: 'Ahmed Al-Farsi',
    location: 'Kuwait',
    investment: 'Business Bay Tower',
    quote: "I've invested in Dubai before, but never with this level of transparency. The investment brief format should be industry standard.",
    image: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&h=400&fit=crop',
  },
];

export default function ClientStories() {
  return (
    <Layout>
      {/* Hero */}
      <section className="pt-32 pb-16 bg-background">
        <div className="container-wide">
          <div className="max-w-2xl">
            <h1 className="heading-1 text-foreground mb-6">
              Client stories
            </h1>
            <p className="body-large text-muted-foreground mb-8">
              A glimpse into how international buyers use a refined shortlist to move faster with more clarity.
            </p>
            <Link to="/match" className="btn-primary">
              Request a Private Shortlist
            </Link>
          </div>
        </div>
      </section>

      {/* Stories Grid */}
      <section className="section-padding">
        <div className="container-wide">
          <p className="text-sm text-muted-foreground mb-8">Real decisions, made cleaner.</p>
          <div className="grid md:grid-cols-2 gap-8">
            {stories.map((story) => (
              <div key={story.name} className="bg-card border border-border rounded-2xl p-8">
                <Quote className="w-10 h-10 text-primary/20 mb-4" />
                <p className="text-foreground mb-6 italic">"{story.quote}"</p>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full overflow-hidden">
                    <img
                      src={story.image}
                      alt={story.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div>
                    <p className="font-semibold text-foreground">{story.name}</p>
                    <p className="text-sm text-muted-foreground">{story.location}</p>
                    <p className="text-sm text-primary">{story.investment}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="section-padding bg-card border-t border-border">
        <div className="container-narrow text-center">
          <h2 className="heading-3 mb-4">Start your investment journey</h2>
          <p className="text-muted-foreground mb-8">
            Get matched to opportunities that fit your goals.
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