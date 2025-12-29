import { useEffect, useState } from 'react';
import { Sparkles, RefreshCw, Wand2, Target, Wallet } from 'lucide-react';
import AdminLayout from '@/components/admin/AdminLayout';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface Persona {
  id: number;
  name: string;
  description: string | null;
  status: string;
  sample_size: number;
  confidence_score: number;
  created_at: string;
}

interface Campaign {
  id: number;
  name: string;
  platform: string;
  objective: string;
  status: string;
  budget_total: number | null;
  budget_daily: number | null;
  spend_total: number | null;
  created_at: string;
}

interface Creative {
  id: number;
  name: string;
  format: string;
  status: string;
  persona_id: number | null;
  headline: string | null;
  risk_flags: Record<string, any> | null;
  created_at: string;
}

export default function AdminMarketing() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [creatives, setCreatives] = useState<Creative[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [discoverLoading, setDiscoverLoading] = useState(false);
  const [creativeLoading, setCreativeLoading] = useState(false);
  const [budgetLoading, setBudgetLoading] = useState(false);
  const [personaId, setPersonaId] = useState<number | ''>('');
  const [creativeFormat, setCreativeFormat] = useState('image');
  const [creativeCount, setCreativeCount] = useState(3);
  const [campaignId, setCampaignId] = useState('');
  const [lookbackDays, setLookbackDays] = useState(7);
  const [volatilityCap, setVolatilityCap] = useState(0.2);
  const [budgetResult, setBudgetResult] = useState<any | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    fetchMarketing();
  }, []);

  const fetchMarketing = async () => {
    setIsLoading(true);
    try {
      const [personaData, campaignData, creativeData] = await Promise.all([
        api.marketing.personas(),
        api.marketing.campaigns(),
        api.marketing.creatives(),
      ]);
      setPersonas(personaData.personas || []);
      setCampaigns(campaignData.campaigns || []);
      setCreatives(creativeData.creatives || []);
    } catch (error: any) {
      toast({ title: 'Failed to load marketing data', description: error.message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDiscover = async () => {
    setDiscoverLoading(true);
    try {
      await api.marketing.discoverPersonas({ min_cluster_size: 25, method: 'hdbscan' });
      toast({ title: 'Persona discovery started' });
      fetchMarketing();
    } catch (error: any) {
      toast({ title: 'Discovery failed', description: error.message, variant: 'destructive' });
    } finally {
      setDiscoverLoading(false);
    }
  };

  const handleGenerateCreatives = async () => {
    if (!personaId) {
      toast({ title: 'Select a persona', variant: 'destructive' });
      return;
    }
    setCreativeLoading(true);
    try {
      await api.marketing.generateCreatives({
        persona_id: personaId,
        format: creativeFormat,
        count: creativeCount,
      });
      toast({ title: 'Creatives generated' });
      fetchMarketing();
    } catch (error: any) {
      toast({ title: 'Creative generation failed', description: error.message, variant: 'destructive' });
    } finally {
      setCreativeLoading(false);
    }
  };

  const handleOptimizeBudget = async () => {
    if (!campaignId) {
      toast({ title: 'Campaign ID required', variant: 'destructive' });
      return;
    }
    setBudgetLoading(true);
    try {
      const data = await api.marketing.optimizeBudget({
        campaign_id: Number(campaignId),
        lookback_days: Number(lookbackDays),
        volatility_cap: Number(volatilityCap),
        auto_apply: false,
      });
      setBudgetResult(data);
      toast({ title: 'Budget recommendations ready' });
    } catch (error: any) {
      toast({ title: 'Budget optimization failed', description: error.message, variant: 'destructive' });
    } finally {
      setBudgetLoading(false);
    }
  };

  return (
    <AdminLayout title="AI-assisted marketing ops">
      <div className="space-y-8">
        <section className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-semibold text-foreground">Marketing studio</h2>
            <p className="text-sm text-muted-foreground">Discover personas, generate creatives, and optimize spend.</p>
          </div>
          <button onClick={fetchMarketing} className="btn-outline">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </section>

        <section className="grid lg:grid-cols-3 gap-6">
          <div className="bg-card border border-border rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-foreground">
              <Sparkles className="w-4 h-4 text-primary" />
              <h3 className="font-semibold">Persona discovery</h3>
            </div>
            <p className="text-sm text-muted-foreground">Cluster qualified leads into repeatable personas.</p>
            <button onClick={handleDiscover} className="btn-primary w-full" disabled={discoverLoading}>
              {discoverLoading ? 'Discovering...' : 'Discover personas'}
            </button>
          </div>

          <div className="bg-card border border-border rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-foreground">
              <Wand2 className="w-4 h-4 text-primary" />
              <h3 className="font-semibold">Creative generator</h3>
            </div>
            <div className="space-y-2">
              <select
                value={personaId}
                onChange={(event) => setPersonaId(event.target.value ? Number(event.target.value) : '')}
                className="w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
              >
                <option value="">Select persona</option>
                {personas.map((persona) => (
                  <option key={persona.id} value={persona.id}>
                    {persona.name}
                  </option>
                ))}
              </select>
              <div className="grid grid-cols-2 gap-2">
                <select
                  value={creativeFormat}
                  onChange={(event) => setCreativeFormat(event.target.value)}
                  className="px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                >
                  <option value="image">Image</option>
                  <option value="video">Video</option>
                  <option value="carousel">Carousel</option>
                  <option value="collection">Collection</option>
                </select>
                <input
                  type="number"
                  min={1}
                  max={8}
                  value={creativeCount}
                  onChange={(event) => setCreativeCount(Number(event.target.value))}
                  className="px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                />
              </div>
            </div>
            <button onClick={handleGenerateCreatives} className="btn-primary w-full" disabled={creativeLoading}>
              {creativeLoading ? 'Generating...' : 'Generate creatives'}
            </button>
          </div>

          <div className="bg-card border border-border rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-foreground">
              <Wallet className="w-4 h-4 text-primary" />
              <h3 className="font-semibold">Budget optimizer</h3>
            </div>
            <div className="space-y-2">
              <input
                value={campaignId}
                onChange={(event) => setCampaignId(event.target.value)}
                placeholder="Campaign ID"
                className="w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
              />
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  min={1}
                  value={lookbackDays}
                  onChange={(event) => setLookbackDays(Number(event.target.value))}
                  className="px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                />
                <input
                  type="number"
                  step="0.05"
                  value={volatilityCap}
                  onChange={(event) => setVolatilityCap(Number(event.target.value))}
                  className="px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                />
              </div>
            </div>
            <button onClick={handleOptimizeBudget} className="btn-primary w-full" disabled={budgetLoading}>
              {budgetLoading ? 'Optimizing...' : 'Optimize budget'}
            </button>
            {budgetResult && (
              <div className="text-xs text-muted-foreground">
                {budgetResult.recommendations?.length || 0} recommendations
              </div>
            )}
          </div>
        </section>

        <section className="grid lg:grid-cols-3 gap-6">
          <div className="bg-card border border-border rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-foreground">
              <Sparkles className="w-4 h-4 text-primary" />
              <h3 className="font-semibold">Personas</h3>
            </div>
            {isLoading ? (
              <div className="text-sm text-muted-foreground">Loading...</div>
            ) : personas.length === 0 ? (
              <div className="text-sm text-muted-foreground">No personas yet.</div>
            ) : (
              <div className="space-y-3">
                {personas.map((persona) => (
                  <div key={persona.id} className="border border-border rounded-xl p-3">
                    <p className="text-sm font-medium text-foreground">{persona.name}</p>
                    <p className="text-xs text-muted-foreground">{persona.sample_size} leads • {persona.confidence_score.toFixed(2)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-card border border-border rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-foreground">
              <Target className="w-4 h-4 text-primary" />
              <h3 className="font-semibold">Campaigns</h3>
            </div>
            {isLoading ? (
              <div className="text-sm text-muted-foreground">Loading...</div>
            ) : campaigns.length === 0 ? (
              <div className="text-sm text-muted-foreground">No campaigns yet.</div>
            ) : (
              <div className="space-y-3">
                {campaigns.map((campaign) => (
                  <div key={campaign.id} className="border border-border rounded-xl p-3">
                    <p className="text-sm font-medium text-foreground">{campaign.name}</p>
                    <p className="text-xs text-muted-foreground">{campaign.platform} • {campaign.status}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-card border border-border rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-foreground">
              <Wand2 className="w-4 h-4 text-primary" />
              <h3 className="font-semibold">Creatives</h3>
            </div>
            {isLoading ? (
              <div className="text-sm text-muted-foreground">Loading...</div>
            ) : creatives.length === 0 ? (
              <div className="text-sm text-muted-foreground">No creatives yet.</div>
            ) : (
              <div className="space-y-3">
                {creatives.map((creative) => (
                  <div key={creative.id} className="border border-border rounded-xl p-3">
                    <p className="text-sm font-medium text-foreground">{creative.name}</p>
                    <p className="text-xs text-muted-foreground">{creative.format} • {creative.status}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {budgetResult && (
          <section className="bg-card border border-border rounded-2xl p-5">
            <h3 className="text-lg font-semibold text-foreground mb-3">Budget recommendations</h3>
            <div className="space-y-3">
              {budgetResult.recommendations?.map((rec: any) => (
                <div key={rec.ad_set_id} className="border border-border rounded-xl p-4">
                  <p className="text-sm font-medium text-foreground">{rec.name}</p>
                  <p className="text-xs text-muted-foreground">Current {rec.current_budget} → Recommended {rec.recommended_budget}</p>
                  <p className="text-xs text-muted-foreground mt-2">{rec.rationale}</p>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </AdminLayout>
  );
}
