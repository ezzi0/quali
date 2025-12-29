import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { 
  Users, TrendingUp, Clock, LogOut, RefreshCw,
  ChevronRight, Mail, Phone, MessageCircle, LayoutGrid, List, X, GripVertical
} from 'lucide-react';
import type { User } from '@supabase/supabase-js';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';

type LeadStage = 'new' | 'contacted' | 'qualified' | 'proposal' | 'negotiation' | 'won' | 'lost';

interface Lead {
  id: string;
  created_at: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  contact_preference: string | null;
  country_timezone: string | null;
  budget: string | null;
  down_payment: string | null;
  installment_preference: string | null;
  handover_preference: string | null;
  strategy: string | null;
  risk_style: string | null;
  exit_preference: string | null;
  message: string | null;
  source: string;
  form_type: string;
  status: string;
  stage: LeadStage;
  notes: string | null;
  assigned_to: string | null;
  last_contacted_at: string | null;
  updated_at: string;
}

const stageColors: Record<LeadStage, string> = {
  new: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  contacted: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  qualified: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  proposal: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
  negotiation: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  won: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  lost: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

const stageBorderColors: Record<LeadStage, string> = {
  new: 'border-t-blue-500',
  contacted: 'border-t-yellow-500',
  qualified: 'border-t-purple-500',
  proposal: 'border-t-indigo-500',
  negotiation: 'border-t-orange-500',
  won: 'border-t-green-500',
  lost: 'border-t-red-500',
};

const stageLabels: Record<LeadStage, string> = {
  new: 'New',
  contacted: 'Contacted',
  qualified: 'Qualified',
  proposal: 'Proposal',
  negotiation: 'Negotiation',
  won: 'Won',
  lost: 'Lost',
};

const stages: LeadStage[] = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost'];
const allKanbanStages: LeadStage[] = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost'];

export default function AdminDashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'pipeline'>('pipeline');
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null);
      if (!session?.user) {
        navigate('/admin/auth');
      }
    });

    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      if (!session?.user) {
        navigate('/admin/auth');
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  useEffect(() => {
    if (user) {
      checkAdminRole();
      fetchLeads();
    }
  }, [user]);

  const checkAdminRole = async () => {
    const { data } = await supabase
      .from('user_roles')
      .select('role')
      .eq('user_id', user?.id)
      .eq('role', 'admin')
      .single();
    
    setIsAdmin(!!data);
    if (!data) {
      toast({
        title: 'Access Denied',
        description: 'You need admin privileges to access this dashboard.',
        variant: 'destructive',
      });
    }
  };

  const fetchLeads = async () => {
    setIsLoading(true);
    const { data, error } = await supabase
      .from('leads')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error fetching leads:', error);
      toast({
        title: 'Error loading leads',
        description: error.message,
        variant: 'destructive',
      });
    } else {
      setLeads(data as Lead[] || []);
    }
    setIsLoading(false);
  };

  const updateLeadStage = async (leadId: string, newStage: LeadStage) => {
    const { error } = await supabase
      .from('leads')
      .update({ stage: newStage })
      .eq('id', leadId);

    if (error) {
      toast({
        title: 'Error updating lead',
        description: error.message,
        variant: 'destructive',
      });
    } else {
      setLeads(leads.map(l => l.id === leadId ? { ...l, stage: newStage } : l));
      if (selectedLead?.id === leadId) {
        setSelectedLead({ ...selectedLead, stage: newStage });
      }
      toast({ title: 'Lead updated' });
    }
  };

  const updateLeadNotes = async (leadId: string, notes: string) => {
    const { error } = await supabase
      .from('leads')
      .update({ notes })
      .eq('id', leadId);

    if (error) {
      toast({
        title: 'Error saving notes',
        description: error.message,
        variant: 'destructive',
      });
    } else {
      setLeads(leads.map(l => l.id === leadId ? { ...l, notes } : l));
      toast({ title: 'Notes saved' });
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate('/admin/auth');
  };

  const getLeadsByStage = (stage: LeadStage) => leads.filter(l => l.stage === stage);

  const handleDragEnd = async (result: DropResult) => {
    const { destination, source, draggableId } = result;

    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const newStage = destination.droppableId as LeadStage;
    const leadId = draggableId;

    // Optimistic update
    setLeads(prevLeads => 
      prevLeads.map(lead => 
        lead.id === leadId ? { ...lead, stage: newStage } : lead
      )
    );

    // Update selected lead if it's the one being moved
    if (selectedLead?.id === leadId) {
      setSelectedLead(prev => prev ? { ...prev, stage: newStage } : null);
    }

    // Persist to database
    const { error } = await supabase
      .from('leads')
      .update({ stage: newStage })
      .eq('id', leadId);

    if (error) {
      // Revert on error
      fetchLeads();
      toast({
        title: 'Error moving lead',
        description: error.message,
        variant: 'destructive',
      });
    } else {
      toast({ title: `Lead moved to ${stageLabels[newStage]}` });
    }
  };
  const stats = {
    total: leads.length,
    new: leads.filter(l => l.stage === 'new').length,
    inProgress: leads.filter(l => ['contacted', 'qualified', 'proposal', 'negotiation'].includes(l.stage)).length,
    won: leads.filter(l => l.stage === 'won').length,
  };

  if (!isAdmin && user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-foreground mb-4">Access Denied</h1>
          <p className="text-muted-foreground mb-6">You need admin privileges to access this dashboard.</p>
          <button onClick={handleLogout} className="btn-primary">
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Header */}
      <header className="bg-background border-b border-border sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-semibold text-foreground">Abriqot Admin</h1>
            <div className="flex items-center gap-2">
              {/* Collection Manager Link */}
              <Link
                to="/admin/collection"
                className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
              >
                Collection
              </Link>
              {/* View Toggle */}
              <div className="flex items-center bg-muted rounded-lg p-1">
                <button
                  onClick={() => setViewMode('pipeline')}
                  className={`p-2 rounded-md transition-colors ${
                    viewMode === 'pipeline' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'
                  }`}
                  title="Pipeline View"
                >
                  <LayoutGrid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-md transition-colors ${
                    viewMode === 'list' ? 'bg-background shadow-sm' : 'text-muted-foreground hover:text-foreground'
                  }`}
                  title="List View"
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
              <button onClick={fetchLeads} className="p-2 text-muted-foreground hover:text-foreground transition-colors">
                <RefreshCw className="w-5 h-5" />
              </button>
              <span className="text-sm text-muted-foreground hidden sm:block">{user?.email}</span>
              <button onClick={handleLogout} className="p-2 text-muted-foreground hover:text-foreground transition-colors">
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                <Users className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-semibold text-foreground">{stats.total}</p>
                <p className="text-sm text-muted-foreground">Total Leads</p>
              </div>
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                <Clock className="w-5 h-5 text-blue-600 dark:text-blue-300" />
              </div>
              <div>
                <p className="text-2xl font-semibold text-foreground">{stats.new}</p>
                <p className="text-sm text-muted-foreground">New</p>
              </div>
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-yellow-100 dark:bg-yellow-900 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-yellow-600 dark:text-yellow-300" />
              </div>
              <div>
                <p className="text-2xl font-semibold text-foreground">{stats.inProgress}</p>
                <p className="text-sm text-muted-foreground">In Progress</p>
              </div>
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-300" />
              </div>
              <div>
                <p className="text-2xl font-semibold text-foreground">{stats.won}</p>
                <p className="text-sm text-muted-foreground">Won</p>
              </div>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-muted-foreground">Loading...</div>
        ) : viewMode === 'pipeline' ? (
          /* Pipeline/Kanban View with Drag & Drop */
          <DragDropContext onDragEnd={handleDragEnd}>
            <div>
              <h2 className="font-semibold text-foreground mb-4">Sales Pipeline</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                {allKanbanStages.map((stage) => {
                  const stageLeads = getLeadsByStage(stage);
                  return (
                    <div key={stage} className={`bg-card border border-border border-t-4 ${stageBorderColors[stage]} rounded-xl overflow-hidden flex flex-col`}>
                      <div className="p-3 border-b border-border">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-foreground text-sm">{stageLabels[stage]}</span>
                          <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${stageColors[stage]}`}>
                            {stageLeads.length}
                          </span>
                        </div>
                      </div>
                      <Droppable droppableId={stage}>
                        {(provided, snapshot) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.droppableProps}
                            className={`p-2 space-y-2 min-h-[200px] max-h-[500px] overflow-y-auto flex-1 transition-colors ${
                              snapshot.isDraggingOver ? 'bg-primary/5' : ''
                            }`}
                          >
                            {stageLeads.length === 0 && !snapshot.isDraggingOver ? (
                              <p className="text-xs text-muted-foreground text-center py-4">Drop leads here</p>
                            ) : (
                              stageLeads.map((lead, index) => (
                                <Draggable key={lead.id} draggableId={lead.id} index={index}>
                                  {(provided, snapshot) => (
                                    <div
                                      ref={provided.innerRef}
                                      {...provided.draggableProps}
                                      onClick={() => setSelectedLead(lead)}
                                      className={`p-3 bg-background border border-border rounded-lg transition-all cursor-pointer ${
                                        snapshot.isDragging ? 'shadow-lg ring-2 ring-primary' : 'hover:border-primary/50'
                                      } ${selectedLead?.id === lead.id ? 'border-primary ring-1 ring-primary' : ''}`}
                                    >
                                      <div className="flex items-start gap-2">
                                        <div {...provided.dragHandleProps} className="mt-0.5 text-muted-foreground hover:text-foreground cursor-grab">
                                          <GripVertical className="w-3 h-3" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                          <p className="font-medium text-foreground text-sm truncate">
                                            {lead.name || lead.email || 'Unknown'}
                                          </p>
                                          {lead.budget && (
                                            <p className="text-xs text-muted-foreground mt-1 truncate">{lead.budget}</p>
                                          )}
                                          <div className="flex items-center gap-1 mt-2 flex-wrap">
                                            <span className="text-xs text-muted-foreground">
                                              {new Date(lead.created_at).toLocaleDateString()}
                                            </span>
                                            {lead.form_type === 'match' && (
                                              <span className="text-xs bg-primary/10 text-primary px-1 py-0.5 rounded">Match</span>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  )}
                                </Draggable>
                              ))
                            )}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>
                  );
                })}
              </div>
            </div>
          </DragDropContext>
        ) : (
          /* List View */
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Leads List */}
            <div className="lg:col-span-2 bg-card border border-border rounded-xl overflow-hidden">
              <div className="p-4 border-b border-border">
                <h2 className="font-semibold text-foreground">All Leads</h2>
              </div>
              {leads.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">No leads yet</div>
              ) : (
                <div className="divide-y divide-border max-h-[600px] overflow-y-auto">
                  {leads.map((lead) => (
                    <button
                      key={lead.id}
                      onClick={() => setSelectedLead(lead)}
                      className={`w-full text-left p-4 hover:bg-muted/50 transition-colors ${
                        selectedLead?.id === lead.id ? 'bg-muted/50' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${stageColors[lead.stage]}`}>
                              {stageLabels[lead.stage]}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {lead.form_type === 'match' ? 'Match' : 'Contact'}
                            </span>
                          </div>
                          <p className="font-medium text-foreground truncate">
                            {lead.name || lead.email || lead.phone || 'Unknown'}
                          </p>
                          <p className="text-sm text-muted-foreground truncate">
                            {lead.budget && `${lead.budget} • `}
                            {new Date(lead.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Lead Detail Sidebar (List View) */}
            <LeadDetailPanel
              lead={selectedLead}
              stages={stages}
              stageLabels={stageLabels}
              stageColors={stageColors}
              onUpdateStage={updateLeadStage}
              onUpdateNotes={updateLeadNotes}
              onClose={() => setSelectedLead(null)}
              onLeadChange={setSelectedLead}
            />
          </div>
        )}
      </main>

      {/* Lead Detail Modal (Pipeline View) */}
      {viewMode === 'pipeline' && selectedLead && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setSelectedLead(null)}>
          <div className="bg-card border border-border rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-4 border-b border-border flex items-center justify-between sticky top-0 bg-card">
              <h2 className="font-semibold text-foreground">Lead Details</h2>
              <button onClick={() => setSelectedLead(null)} className="p-1 text-muted-foreground hover:text-foreground">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4">
              <LeadDetailContent
                lead={selectedLead}
                stages={stages}
                stageLabels={stageLabels}
                stageColors={stageColors}
                onUpdateStage={updateLeadStage}
                onUpdateNotes={updateLeadNotes}
                onLeadChange={setSelectedLead}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Lead Detail Panel for List View
function LeadDetailPanel({
  lead,
  stages,
  stageLabels,
  stageColors,
  onUpdateStage,
  onUpdateNotes,
  onClose,
  onLeadChange,
}: {
  lead: Lead | null;
  stages: LeadStage[];
  stageLabels: Record<LeadStage, string>;
  stageColors: Record<LeadStage, string>;
  onUpdateStage: (id: string, stage: LeadStage) => void;
  onUpdateNotes: (id: string, notes: string) => void;
  onClose: () => void;
  onLeadChange: (lead: Lead) => void;
}) {
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      <div className="p-4 border-b border-border">
        <h2 className="font-semibold text-foreground">Lead Details</h2>
      </div>
      {lead ? (
        <div className="p-4">
          <LeadDetailContent
            lead={lead}
            stages={stages}
            stageLabels={stageLabels}
            stageColors={stageColors}
            onUpdateStage={onUpdateStage}
            onUpdateNotes={onUpdateNotes}
            onLeadChange={onLeadChange}
          />
        </div>
      ) : (
        <div className="p-8 text-center text-muted-foreground">
          Select a lead to view details
        </div>
      )}
    </div>
  );
}

// Shared Lead Detail Content
function LeadDetailContent({
  lead,
  stages,
  stageLabels,
  stageColors,
  onUpdateStage,
  onUpdateNotes,
  onLeadChange,
}: {
  lead: Lead;
  stages: LeadStage[];
  stageLabels: Record<LeadStage, string>;
  stageColors: Record<LeadStage, string>;
  onUpdateStage: (id: string, stage: LeadStage) => void;
  onUpdateNotes: (id: string, notes: string) => void;
  onLeadChange: (lead: Lead) => void;
}) {
  return (
    <div className="space-y-6">
      {/* Contact Info */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">Contact</h3>
        {lead.name && (
          <p className="text-foreground font-medium">{lead.name}</p>
        )}
        {lead.email && (
          <a href={`mailto:${lead.email}`} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary">
            <Mail className="w-4 h-4" />
            {lead.email}
          </a>
        )}
        {lead.phone && (
          <a href={`tel:${lead.phone}`} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary">
            <Phone className="w-4 h-4" />
            {lead.phone}
          </a>
        )}
        {lead.contact_preference && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <MessageCircle className="w-4 h-4" />
            Prefers: {lead.contact_preference}
          </div>
        )}
      </div>

      {/* Investment Preferences */}
      {lead.form_type === 'match' && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">Preferences</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {lead.budget && (
              <div>
                <p className="text-muted-foreground">Budget</p>
                <p className="text-foreground">{lead.budget}</p>
              </div>
            )}
            {lead.down_payment && (
              <div>
                <p className="text-muted-foreground">Down Payment</p>
                <p className="text-foreground">{lead.down_payment}</p>
              </div>
            )}
            {lead.handover_preference && (
              <div>
                <p className="text-muted-foreground">Handover</p>
                <p className="text-foreground">{lead.handover_preference}</p>
              </div>
            )}
            {lead.strategy && (
              <div>
                <p className="text-muted-foreground">Strategy</p>
                <p className="text-foreground">{lead.strategy}</p>
              </div>
            )}
            {lead.risk_style && (
              <div>
                <p className="text-muted-foreground">Risk Style</p>
                <p className="text-foreground">{lead.risk_style}</p>
              </div>
            )}
            {lead.country_timezone && (
              <div>
                <p className="text-muted-foreground">Location</p>
                <p className="text-foreground">{lead.country_timezone}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Message */}
      {lead.message && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">Message</h3>
          <p className="text-sm text-foreground bg-muted/50 p-3 rounded-lg">{lead.message}</p>
        </div>
      )}

      {/* Pipeline Stage */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">Stage</h3>
        <select
          value={lead.stage}
          onChange={(e) => onUpdateStage(lead.id, e.target.value as LeadStage)}
          className="form-input text-sm"
        >
          {stages.map((stage) => (
            <option key={stage} value={stage}>{stageLabels[stage]}</option>
          ))}
        </select>
      </div>

      {/* Notes */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">Notes</h3>
        <textarea
          value={lead.notes || ''}
          onChange={(e) => onLeadChange({ ...lead, notes: e.target.value })}
          onBlur={() => onUpdateNotes(lead.id, lead.notes || '')}
          placeholder="Add notes..."
          className="form-input text-sm"
          rows={3}
        />
      </div>

      {/* Timestamps */}
      <div className="text-xs text-muted-foreground space-y-1 pt-4 border-t border-border">
        <p>Created: {new Date(lead.created_at).toLocaleString()}</p>
        <p>Updated: {new Date(lead.updated_at).toLocaleString()}</p>
      </div>
    </div>
  );
}
