import { useEffect, useState } from 'react';
import { Trash2, UserPlus, Shield } from 'lucide-react';
import AdminLayout from '@/components/admin/AdminLayout';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { useAdminSession } from '@/hooks/use-admin-session';

interface AdminUser {
  id: number;
  email: string;
  role: 'admin' | 'agent';
  name: string | null;
  created_at: string;
}

export default function AdminUsers() {
  const { profile } = useAdminSession();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'admin' | 'agent'>('agent');
  const [isInviting, setIsInviting] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (profile?.is_super_admin) {
      fetchUsers();
    }
  }, [profile?.is_super_admin]);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const data = await api.auth.listUsers();
      setUsers(data.users || []);
    } catch (error: any) {
      toast({ title: 'Failed to load users', description: error.message, variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!email.trim()) return;
    setIsInviting(true);
    try {
      await api.auth.inviteUser({ email: email.trim(), role });
      toast({ title: 'Invite sent' });
      setEmail('');
      setRole('agent');
      fetchUsers();
    } catch (error: any) {
      toast({ title: 'Invite failed', description: error.message, variant: 'destructive' });
    } finally {
      setIsInviting(false);
    }
  };

  const handleRoleChange = async (userId: number, nextRole: 'admin' | 'agent') => {
    try {
      await api.auth.updateUserRole(userId, nextRole);
      setUsers((prev) => prev.map((user) => (user.id === userId ? { ...user, role: nextRole } : user)));
      toast({ title: 'Role updated' });
    } catch (error: any) {
      toast({ title: 'Role update failed', description: error.message, variant: 'destructive' });
    }
  };

  const handleDelete = async (userId: number) => {
    if (!confirm('Remove this user?')) return;
    try {
      await api.auth.deleteUser(userId);
      setUsers((prev) => prev.filter((user) => user.id !== userId));
      toast({ title: 'User removed' });
    } catch (error: any) {
      toast({ title: 'Delete failed', description: error.message, variant: 'destructive' });
    }
  };

  if (profile && !profile.is_super_admin) {
    return (
      <AdminLayout title="User management">
        <div className="bg-card border border-border rounded-2xl p-6 text-muted-foreground">
          Only Eli can manage access. Contact the admin if you need changes.
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title="Invite-only access for internal users">
      <div className="space-y-8">
        <section className="bg-card border border-border rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-foreground mb-2">Invite a team member</h2>
          <p className="text-sm text-muted-foreground mb-4">Only abriqot.com emails are allowed.</p>
          <div className="flex flex-col md:flex-row gap-3">
            <input
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@abriqot.com"
              className="flex-1 px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
            />
            <select
              value={role}
              onChange={(event) => setRole(event.target.value as 'admin' | 'agent')}
              className="px-3 py-2 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
            >
              <option value="agent">Agent</option>
              <option value="admin">Admin</option>
            </select>
            <button onClick={handleInvite} className="btn-primary" disabled={isInviting}>
              <UserPlus className="w-4 h-4" />
              {isInviting ? 'Sending...' : 'Send invite'}
            </button>
          </div>
        </section>

        <section className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b border-border flex items-center justify-between">
            <h3 className="text-lg font-semibold text-foreground">Team access</h3>
            <span className="text-sm text-muted-foreground">{users.length} users</span>
          </div>
          {isLoading ? (
            <div className="py-12 text-center text-muted-foreground">Loading users...</div>
          ) : users.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">No users invited yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-muted/30 text-muted-foreground">
                  <tr>
                    <th className="text-left px-6 py-3 font-medium">Email</th>
                    <th className="text-left px-6 py-3 font-medium">Role</th>
                    <th className="text-left px-6 py-3 font-medium">Joined</th>
                    <th className="text-right px-6 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td className="px-6 py-4 text-foreground">
                        <div className="flex items-center gap-2">
                          {user.email === 'eli@abriqot.com' && <Shield className="w-4 h-4 text-primary" />}
                          {user.email}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <select
                          value={user.role}
                          onChange={(event) => handleRoleChange(user.id, event.target.value as 'admin' | 'agent')}
                          className="px-2 py-1 rounded-lg bg-muted/40 border border-border text-sm text-foreground"
                          disabled={user.email === 'eli@abriqot.com'}
                        >
                          <option value="agent">Agent</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {user.email !== 'eli@abriqot.com' && (
                          <button
                            onClick={() => handleDelete(user.id)}
                            className="text-rose-400 hover:text-rose-300"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </AdminLayout>
  );
}
