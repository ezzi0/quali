import AdminLayout from '@/components/admin/AdminLayout';
import QualificationChat from '@/components/qualification/QualificationChat';

export default function AdminChat() {
  return (
    <AdminLayout title="Internal qualification sandbox">
      <div className="grid lg:grid-cols-[1.2fr_1fr] gap-8">
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold text-foreground">Qualification assistant</h2>
          <p className="text-muted-foreground">
            Use this space to test qualification flows. The assistant uses live inventory and saves lead data.
          </p>
          <QualificationChat variant="admin" />
        </div>
        <div className="bg-card border border-border rounded-2xl p-6 space-y-4">
          <h3 className="text-lg font-semibold text-foreground">How to use</h3>
          <ul className="space-y-3 text-sm text-muted-foreground">
            <li>Provide a city, budget, and bedroom count to get started.</li>
            <li>Check tool call badges to confirm inventory lookups.</li>
            <li>Finish the conversation to save a lead and recap.</li>
          </ul>
        </div>
      </div>
    </AdminLayout>
  );
}
