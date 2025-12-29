import { useEffect, useMemo, useState } from 'react';
import { RefreshCw, LayoutGrid, List, Search, Mail, Phone, ClipboardList, X } from 'lucide-react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import AdminLayout from '@/components/admin/AdminLayout';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

const leadStages = [
  'new',
  'contacted',
  'qualified',
  'viewing',
  'offer',
  'nurture',
  'won',
  'lost',
] as const;

type LeadStatus = typeof leadStages[number];

type LeadSummary = {
  id: number;
  source: string;
  persona: string | null;
  status: LeadStatus;
  notes: string | null;
  assigned_to: string | null;
  last_contacted_at: string | null;
  created_at: string;
  contact: {
    name: string | null;
    email: string | null;
    phone: string | null;
  } | null;
  profile: {
    city: string | null;
    areas: string[] | null;
    property_type: string | null;
    beds: number | null;
    budget_min: number | null;
    budget_max: number | null;
    currency: string | null;
    move_in_date: string | null;
  } | null;
};

type LeadDetail = LeadSummary & {
  qualification: {
    score: number;
    qualified: boolean;
    reasons: string[];
    missing_info: string[];
    suggested_next_step: string | null;
    top_matches: any;
    created_at: string;
  } | null;
  timeline: {
    id: number;
    type: string;
    payload: Record<string, any>;
    created_at: string;
  }[];
  tasks: {
    id: number;
    title: string;
    description: string | null;
    status: string;
    due_at: string | null;
    assignee: string | null;
    created_at: string;
  }[];
};

const stageLabels: Record<LeadStatus, string> = {
  new: 'New',
  contacted: 'Contacted',
  qualified: 'Qualified',
  viewing: 'Viewing',
  offer: 'Offer',
  nurture: 'Nurture',
  won: 'Won',
  lost: 'Lost',
};

const stageBorderColors: Record<LeadStatus, string> = {
  new: 'border-t-blue-500',
  contacted: 'border-t-amber-500',
  qualified: 'border-t-violet-500',
  viewing: 'border-t-sky-500',
  offer: 'border-t-fuchsia-500',
  nurture: 'border-t-cyan-500',
  won: 'border-t-emerald-500',
  lost: 'border-t-rose-500',
};

const stageBadgeColors: Record<LeadStatus, string> = {
  new: 'bg-blue-500/10 text-blue-300',
  contacted: 'bg-amber-500/10 text-amber-300',
  qualified: 'bg-violet-500/10 text-violet-300',
  viewing: 'bg-sky-500/10 text-sky-300',
  offer: 'bg-fuchsia-500/10 text-fuchsia-300',
  nurture: 'bg-cyan-500/10 text-cyan-300',
  won: 'bg-emerald-500/10 text-emerald-300',
  lost: 'bg-rose-500/10 text-rose-300',
};

function formatName(lead: LeadSummary) {
  return lead.contact?.name || lead.contact?.email || lead.contact?.phone || 'Unknown';
}

function formatBudget(profile: LeadSummary['profile']) {
  if (!profile) return null;
  const min = profile.budget_min;
  const max = profile.budget_max;
  const currency = profile.currency || 'AED';
  if (min && max) {
    return `${currency} ${min.toLocaleString()} - ${max.toLocaleString()}`;
  }
  if (min) {
    return `${currency} ${min.toLocaleString()}+`;
  }
  if (max) {
    return `Up to ${currency} ${max.toLocaleString()}`;
  }
  return null;
}

export default function AdminDashboard() {
  const [leads, setLeads] = useState<LeadSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'pipeline' | 'list'>('pipeline');
  const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null);
  const [selectedLead, setSelectedLead] = useState<LeadDetail | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<LeadStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [assigneeFilter, setAssigneeFilter] = useState('');
  const { toast } = useToast();

  useEffect(() => {
    fetchLeads();
  }, []);

  useEffect(() => {
    if (selectedLeadId) {
      loadLeadDetail(selectedLeadId);
    }
  }, [selectedLeadId]);

  useEffect(() => {
    if (!selectedLeadId) {
      setSelectedLead(null);
    }
  }, [selectedLeadId]);

  const fetchLeads = async () => {
    setIsLoading(true);
    try {
      const data = await api.leads.list();
      setLeads(data.leads || []);
    } catch (error: any) {
      toast({
        title: 'Failed to load leads',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadLeadDetail = async (leadId: number) => {
    setIsDetailLoading(true);
    try {
      const data = await api.leads.get(leadId);
      setSelectedLead(data as LeadDetail);
    } catch (error: any) {
      toast({
        title: 'Failed to load lead detail',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsDetailLoading(false);
    }
  };

  const updateLead = async (leadId: number, payload: Partial<Pick<LeadSummary, 'status' | 'notes' | 'assigned_to' | 'last_contacted_at'>>) => {
    try {
      await api.leads.update(leadId, payload);
      setLeads((prev) =>
        prev.map((lead) =>
          lead.id === leadId
            ? {
                ...lead,
                ...payload,
              }
            : lead
        )
      );
      if (selectedLead && selectedLead.id === leadId) {
        setSelectedLead({
          ...selectedLead,
          ...payload,
        } as LeadDetail);
      }
      toast({ title: 'Lead updated' });
    } catch (error: any) {
      toast({
        title: 'Update failed',
        description: error.message,
        variant: 'destructive',
      });
    }
  };

  const handleDragEnd = async (result: DropResult) => {
    const { destination, source, draggableId } = result;

    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const newStage = destination.droppableId as LeadStatus;
    const leadId = Number(draggableId);

    setLeads((prev) =>
      prev.map((lead) => (lead.id === leadId ? { ...lead, status: newStage } : lead))
    );

    if (selectedLead?.id === leadId) {
      setSelectedLead({ ...selectedLead, status: newStage });
    }

    await updateLead(leadId, { status: newStage });
  };

  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
      if (statusFilter !== 'all' && lead.status !== statusFilter) {
        return false;
      }
      if (assigneeFilter && (lead.assigned_to || '').toLowerCase() !== assigneeFilter.toLowerCase()) {
        return false;
      }
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const haystack = [
          lead.contact?.name,
          lead.contact?.email,
          lead.contact?.phone,
          lead.profile?.city,
          lead.profile?.areas?.join(' '),
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        if (!haystack.includes(query)) {
          return false;
        }
      }
      return true;
    });
  }, [leads, statusFilter, searchQuery, assigneeFilter]);

  const stats = {
    total: leads.length,
    new: leads.filter((lead) => lead.status === 'new').length,
    inProgress: leads.filter((lead) => ['contacted', 'qualified', 'viewing', 'offer', 'nurture'].includes(lead.status)).length,
    won: leads.filter((lead) => lead.status === 'won').length,
  };

  const stageBuckets = useMemo(() => {
    const buckets: Record<LeadStatus, LeadSummary[]> = {
      new: [],
      contacted: [],
      qualified: [],
      viewing: [],
      offer: [],
      nurture: [],
      won: [],
      lost: [],
    };
    filteredLeads.forEach((lead) => {
      buckets[lead.status]?.push(lead);
    });
    return buckets;
  }, [filteredLeads]);

  return (
    <AdminLayout title="Lead intelligence and pipeline">
      <div className="space-y-8">
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-card border border-border rounded-2xl p-5">
            <p className="text-2xl font-semibold text-foreground">{stats.total}</p>
            <p className="text-sm text-muted-foreground">Total Leads</p>
          </div>
          <div className="bg-card border border-border rounded-2xl p-5">
            <p className="text-2xl font-semibold text-foreground">{stats.new}</p>
            <p className="text-sm text-muted-foreground">New</p>
          </div>
          <div className="bg-card border border-border rounded-2xl p-5">
            <p className="text-2xl font-semibold text-foreground">{stats.inProgress}</p>
            <p className="text-sm text-muted-foreground">In Progress</p>
          </div>
          <div className="bg-card border border-border rounded-2xl p-5">
            <p className="text-2xl font-semibold text-foreground">{stats.won}</p>
            <p className="text-sm text-muted-foreground">Won</p>
          </div>
        </section>

        <section className="bg-card border border-border rounded-2xl p-5">
          <div className="flex flex-wrap gap-3 items-center justify-between">
            <div className="flex flex-wrap gap-3 items-center">
              <div className="relative">
                <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Search by name, email, phone, city"
                  className="pl-9 pr-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                />
              </div>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as LeadStatus | 'all')}
                className="px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
              >
                <option value="all">All stages</option>
                {leadStages.map((stage) => (
                  <option key={stage} value={stage}>
                    {stageLabels[stage]}
                  </option>
                ))}
              </select>
              <input
                value={assigneeFilter}
                onChange={(event) => setAssigneeFilter(event.target.value)}
                placeholder="Filter by assignee"
                className="px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
              />
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center bg-muted/40 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('pipeline')}
                  className={`p-2 rounded-md transition-colors ${
                    viewMode === 'pipeline' ? 'bg-background text-foreground' : 'text-muted-foreground hover:text-foreground'
                  }`}
                  title="Pipeline"
                >
                  <LayoutGrid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-md transition-colors ${
                    viewMode === 'list' ? 'bg-background text-foreground' : 'text-muted-foreground hover:text-foreground'
                  }`}
                  title="List"
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
              <button
                onClick={fetchLeads}
                className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/40"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>
        </section>

        {isLoading ? (
          <div className="text-center text-muted-foreground py-16">Loading leads...</div>
        ) : viewMode === 'pipeline' ? (
          <DragDropContext onDragEnd={handleDragEnd}>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-8 gap-4">
              {leadStages.map((stage) => (
                <div key={stage} className={`bg-card border border-border border-t-4 ${stageBorderColors[stage]} rounded-2xl flex flex-col`}
                >
                  <div className="p-3 border-b border-border flex items-center justify-between">
                    <span className="text-sm font-medium text-foreground">{stageLabels[stage]}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${stageBadgeColors[stage]}`}>
                      {stageBuckets[stage].length}
                    </span>
                  </div>
                  <Droppable droppableId={stage}>
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.droppableProps}
                        className={`p-2 space-y-2 min-h-[140px] max-h-[520px] overflow-y-auto ${
                          snapshot.isDraggingOver ? 'bg-primary/5' : ''
                        }`}
                      >
                        {stageBuckets[stage].map((lead, index) => (
                          <Draggable key={lead.id} draggableId={String(lead.id)} index={index}>
                            {(dragProvided, dragSnapshot) => (
                              <div
                                ref={dragProvided.innerRef}
                                {...dragProvided.draggableProps}
                                {...dragProvided.dragHandleProps}
                                onClick={() => setSelectedLeadId(lead.id)}
                                className={`rounded-xl border border-border bg-background p-3 cursor-pointer transition-all ${
                                  dragSnapshot.isDragging ? 'ring-2 ring-primary' : 'hover:border-primary/40'
                                } ${selectedLeadId === lead.id ? 'border-primary ring-1 ring-primary/50' : ''}`}
                              >
                                <p className="text-sm font-medium text-foreground truncate">{formatName(lead)}</p>
                                {lead.profile?.city && (
                                  <p className="text-xs text-muted-foreground truncate">{lead.profile.city}</p>
                                )}
                                {formatBudget(lead.profile) && (
                                  <p className="text-xs text-muted-foreground mt-1">{formatBudget(lead.profile)}</p>
                                )}
                                <div className="flex items-center gap-2 text-[11px] text-muted-foreground mt-2">
                                  <span>{new Date(lead.created_at).toLocaleDateString()}</span>
                                  {lead.source && (
                                    <span className="px-2 py-0.5 rounded-full bg-muted/50 text-muted-foreground">
                                      {lead.source}
                                    </span>
                                  )}
                                </div>
                              </div>
                            )}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                      </div>
                    )}
                  </Droppable>
                </div>
              ))}
            </div>
          </DragDropContext>
        ) : (
          <div className="grid lg:grid-cols-[2fr_1fr] gap-6">
            <div className="bg-card border border-border rounded-2xl overflow-hidden">
              <div className="px-5 py-4 border-b border-border flex items-center justify-between">
                <h2 className="text-lg font-semibold text-foreground">Lead roster</h2>
                <span className="text-sm text-muted-foreground">{filteredLeads.length} records</span>
              </div>
              {filteredLeads.length === 0 ? (
                <div className="py-16 text-center text-muted-foreground">No leads match the current filters.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-muted/30 text-muted-foreground">
                      <tr>
                        <th className="text-left px-4 py-3 font-medium">Lead</th>
                        <th className="text-left px-4 py-3 font-medium">Stage</th>
                        <th className="text-left px-4 py-3 font-medium">Budget</th>
                        <th className="text-left px-4 py-3 font-medium">Assignee</th>
                        <th className="text-left px-4 py-3 font-medium">Last Contact</th>
                        <th className="text-left px-4 py-3 font-medium">Created</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {filteredLeads.map((lead) => (
                        <tr
                          key={lead.id}
                          onClick={() => setSelectedLeadId(lead.id)}
                          className="cursor-pointer hover:bg-muted/40"
                        >
                          <td className="px-4 py-3">
                            <div className="font-medium text-foreground">{formatName(lead)}</div>
                            <div className="text-xs text-muted-foreground">{lead.contact?.email || lead.contact?.phone}</div>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`text-xs px-2 py-1 rounded-full ${stageBadgeColors[lead.status]}`}>
                              {stageLabels[lead.status]}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">{formatBudget(lead.profile) || '--'}</td>
                          <td className="px-4 py-3 text-muted-foreground">{lead.assigned_to || '--'}</td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {lead.last_contacted_at ? new Date(lead.last_contacted_at).toLocaleDateString() : '--'}
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {new Date(lead.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            <LeadDetailPanel
              lead={selectedLead}
              loading={isDetailLoading}
              onClose={() => setSelectedLeadId(null)}
              onUpdate={updateLead}
              onCreateTask={async (leadId, payload) => {
                await api.leads.createTask(leadId, payload);
                await loadLeadDetail(leadId);
              }}
            />
          </div>
        )}
      </div>

      {viewMode === 'pipeline' && selectedLeadId && (
        <LeadDetailModal
          lead={selectedLead}
          loading={isDetailLoading}
          onClose={() => setSelectedLeadId(null)}
          onUpdate={updateLead}
          onCreateTask={async (leadId, payload) => {
            await api.leads.createTask(leadId, payload);
            await loadLeadDetail(leadId);
          }}
        />
      )}
    </AdminLayout>
  );
}

function LeadDetailPanel({
  lead,
  loading,
  onClose,
  onUpdate,
  onCreateTask,
}: {
  lead: LeadDetail | null;
  loading: boolean;
  onClose: () => void;
  onUpdate: (leadId: number, payload: Partial<Pick<LeadSummary, 'status' | 'notes' | 'assigned_to' | 'last_contacted_at'>>) => Promise<void> | void;
  onCreateTask: (leadId: number, payload: { title: string; description?: string; due_at?: string | null; assignee?: string | null }) => Promise<void>;
}) {
  return (
    <div className="bg-card border border-border rounded-2xl p-5 h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">Lead details</h3>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X className="w-4 h-4" />
        </button>
      </div>
      {loading ? (
        <div className="text-muted-foreground">Loading details...</div>
      ) : lead ? (
        <LeadDetailContent lead={lead} onUpdate={onUpdate} onCreateTask={onCreateTask} />
      ) : (
        <div className="text-muted-foreground">Select a lead to view details.</div>
      )}
    </div>
  );
}

function LeadDetailModal({
  lead,
  loading,
  onClose,
  onUpdate,
  onCreateTask,
}: {
  lead: LeadDetail | null;
  loading: boolean;
  onClose: () => void;
  onUpdate: (leadId: number, payload: Partial<Pick<LeadSummary, 'status' | 'notes' | 'assigned_to' | 'last_contacted_at'>>) => Promise<void> | void;
  onCreateTask: (leadId: number, payload: { title: string; description?: string; due_at?: string | null; assignee?: string | null }) => Promise<void>;
}) {
  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-card border border-border rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto" onClick={(event) => event.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h3 className="text-lg font-semibold text-foreground">Lead details</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-6">
          {loading ? (
            <div className="text-muted-foreground">Loading details...</div>
          ) : lead ? (
            <LeadDetailContent lead={lead} onUpdate={onUpdate} onCreateTask={onCreateTask} />
          ) : (
            <div className="text-muted-foreground">Select a lead to view details.</div>
          )}
        </div>
      </div>
    </div>
  );
}

function LeadDetailContent({
  lead,
  onUpdate,
  onCreateTask,
}: {
  lead: LeadDetail;
  onUpdate: (leadId: number, payload: Partial<Pick<LeadSummary, 'status' | 'notes' | 'assigned_to' | 'last_contacted_at'>>) => Promise<void> | void;
  onCreateTask: (leadId: number, payload: { title: string; description?: string; due_at?: string | null; assignee?: string | null }) => Promise<void>;
}) {
  const [notes, setNotes] = useState(lead.notes || '');
  const [assignedTo, setAssignedTo] = useState(lead.assigned_to || '');
  const [lastContacted, setLastContacted] = useState(lead.last_contacted_at || '');
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [taskDue, setTaskDue] = useState('');
  const [taskAssignee, setTaskAssignee] = useState('');

  useEffect(() => {
    setNotes(lead.notes || '');
    setAssignedTo(lead.assigned_to || '');
    setLastContacted(lead.last_contacted_at || '');
  }, [lead.id, lead.notes, lead.assigned_to, lead.last_contacted_at]);

  const handleTaskSubmit = async () => {
    if (!taskTitle.trim()) return;
    await onCreateTask(lead.id, {
      title: taskTitle.trim(),
      description: taskDescription.trim() || undefined,
      due_at: taskDue || null,
      assignee: taskAssignee.trim() || null,
    });
    setTaskTitle('');
    setTaskDescription('');
    setTaskDue('');
    setTaskAssignee('');
  };

  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground uppercase">Contact</p>
          <p className="text-lg font-semibold text-foreground">{formatName(lead)}</p>
          {lead.contact?.email && (
            <a href={`mailto:${lead.contact.email}`} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary">
              <Mail className="w-4 h-4" />
              {lead.contact.email}
            </a>
          )}
          {lead.contact?.phone && (
            <a href={`tel:${lead.contact.phone}`} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary">
              <Phone className="w-4 h-4" />
              {lead.contact.phone}
            </a>
          )}
        </div>
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground uppercase">Profile</p>
          <div className="text-sm text-muted-foreground space-y-1">
            <div>City: {lead.profile?.city || '--'}</div>
            <div>Areas: {lead.profile?.areas?.join(', ') || '--'}</div>
            <div>Property type: {lead.profile?.property_type || '--'}</div>
            <div>Beds: {lead.profile?.beds || '--'}</div>
            <div>Budget: {formatBudget(lead.profile) || '--'}</div>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <div>
          <label className="text-xs text-muted-foreground uppercase">Stage</label>
          <select
            value={lead.status}
            onChange={(event) => onUpdate(lead.id, { status: event.target.value as LeadStatus })}
            className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
          >
            {leadStages.map((stage) => (
              <option key={stage} value={stage}>
                {stageLabels[stage]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-muted-foreground uppercase">Assigned to</label>
          <input
            value={assignedTo}
            onChange={(event) => setAssignedTo(event.target.value)}
            onBlur={() => onUpdate(lead.id, { assigned_to: assignedTo || null })}
            className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
            placeholder="Owner name"
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground uppercase">Last contacted</label>
          <input
            type="date"
            value={lastContacted ? new Date(lastContacted).toISOString().slice(0, 10) : ''}
            onChange={(event) => {
              const iso = event.target.value ? new Date(event.target.value).toISOString() : '';
              setLastContacted(iso);
              onUpdate(lead.id, { last_contacted_at: iso || null });
            }}
            className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
          />
        </div>
      </div>

      <div>
        <label className="text-xs text-muted-foreground uppercase">Notes</label>
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          onBlur={() => onUpdate(lead.id, { notes })}
          rows={3}
          className="mt-2 w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
          placeholder="Add internal notes"
        />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs text-muted-foreground uppercase">Tasks</p>
            <span className="text-xs text-muted-foreground">{lead.tasks.length}</span>
          </div>
          <div className="space-y-3">
            {lead.tasks.length === 0 ? (
              <div className="text-sm text-muted-foreground">No tasks yet.</div>
            ) : (
              lead.tasks.map((task) => (
                <div key={task.id} className="border border-border rounded-xl p-3">
                  <p className="text-sm font-medium text-foreground">{task.title}</p>
                  {task.description && <p className="text-xs text-muted-foreground">{task.description}</p>}
                  <div className="text-xs text-muted-foreground mt-2">
                    {task.due_at ? `Due ${new Date(task.due_at).toLocaleDateString()}` : 'No due date'}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        <div>
          <p className="text-xs text-muted-foreground uppercase mb-3">Add task</p>
          <div className="space-y-3">
            <input
              value={taskTitle}
              onChange={(event) => setTaskTitle(event.target.value)}
              placeholder="Follow-up call"
              className="w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
            />
            <textarea
              value={taskDescription}
              onChange={(event) => setTaskDescription(event.target.value)}
              placeholder="Notes"
              rows={2}
              className="w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
            />
            <input
              type="date"
              value={taskDue}
              onChange={(event) => setTaskDue(event.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
            />
            <input
              value={taskAssignee}
              onChange={(event) => setTaskAssignee(event.target.value)}
              placeholder="Assignee"
              className="w-full px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
            />
            <button onClick={handleTaskSubmit} className="btn-primary w-full">
              <ClipboardList className="w-4 h-4" />
              Create task
            </button>
          </div>
        </div>
      </div>

      {lead.qualification && (
        <div className="bg-muted/30 border border-border rounded-2xl p-4">
          <p className="text-xs text-muted-foreground uppercase mb-2">Qualification snapshot</p>
          <div className="text-sm text-foreground">Score: {lead.qualification.score}</div>
          <div className="text-sm text-foreground">Qualified: {lead.qualification.qualified ? 'Yes' : 'No'}</div>
          {lead.qualification.reasons?.length ? (
            <div className="text-sm text-muted-foreground mt-2">Reasons: {lead.qualification.reasons.join(', ')}</div>
          ) : null}
        </div>
      )}

      {lead.timeline.length > 0 && (
        <div>
          <p className="text-xs text-muted-foreground uppercase mb-3">Timeline</p>
          <div className="space-y-3">
              {lead.timeline.map((entry) => (
                <div key={entry.id} className="border border-border rounded-xl p-3">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{entry.type}</span>
                    <span>{new Date(entry.created_at).toLocaleString()}</span>
                  </div>
                  {(entry.payload?.message || entry.payload?.note) && (
                    <p className="text-sm text-foreground mt-2">{entry.payload.message || entry.payload.note}</p>
                  )}
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
