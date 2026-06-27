'use client';
export const dynamic = 'force-dynamic';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/providers';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Download, Search, AlertTriangle, Info, AlertCircle } from 'lucide-react';

interface LogEntry {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  level: string;
  created_at: string;
  details?: string;
}

export default function AuditLogsPage() {
  const { user } = useAuth();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    user_id: '',
    action: '',
    resource_type: '',
    level: '',
    page: 1,
    per_page: 30,
  });

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const params = new URLSearchParams({
        skip: String((filter.page - 1) * filter.per_page),
        limit: String(filter.per_page),
      });
      if (filter.user_id) params.set('user_id', filter.user_id);
      if (filter.action) params.set('action', filter.action);
      if (filter.resource_type) params.set('resource_type', filter.resource_type);
      if (filter.level) params.set('level', filter.level);
      const res = await fetch(`/api/admin/audit-logs?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setLogs(data.logs || []);
      setTotal(data.total || 0);
    } catch {
      /* */
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const exportCsv = async () => {
    const token = localStorage.getItem('auth_token');
    const res = await fetch('/api/admin/audit-logs/export', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'audit-logs.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const levelIcon = (lvl: string) => {
    const map: Record<string, any> = {
      error: <AlertCircle className="h-3.5 w-3.5 text-red-400" />,
      warn: <AlertTriangle className="h-3.5 w-3.5 text-yellow-400" />,
      info: <Info className="h-3.5 w-3.5 text-blue-400" />,
    };
    return map[lvl] || map.info;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Audit Logs</h1>
          <p className="text-muted-foreground text-sm mt-1">{total} total entries</p>
        </div>
        <Button variant="outline" size="sm" onClick={exportCsv}>
          <Download className="h-4 w-4 mr-1" /> Export CSV
        </Button>
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          className="text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none w-40"
          placeholder="User ID..."
          value={filter.user_id}
          onChange={(e) => setFilter((f) => ({ ...f, user_id: e.target.value, page: 1 }))}
        />
        <input
          className="text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none w-32"
          placeholder="Action..."
          value={filter.action}
          onChange={(e) => setFilter((f) => ({ ...f, action: e.target.value, page: 1 }))}
        />
        <input
          className="text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none w-32"
          placeholder="Resource..."
          value={filter.resource_type}
          onChange={(e) => setFilter((f) => ({ ...f, resource_type: e.target.value, page: 1 }))}
        />
        <select
          value={filter.level}
          onChange={(e) => setFilter((f) => ({ ...f, level: e.target.value, page: 1 }))}
          className="text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
        >
          <option value="">All Levels</option>
          <option value="info">Info</option>
          <option value="warn">Warning</option>
          <option value="error">Error</option>
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : logs.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No audit logs found.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="pt-4">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-muted-foreground text-xs uppercase">
                    <th className="text-left pb-3 font-medium">Level</th>
                    <th className="text-left pb-3 font-medium">User</th>
                    <th className="text-left pb-3 font-medium">Action</th>
                    <th className="text-left pb-3 font-medium">Resource</th>
                    <th className="text-left pb-3 font-medium">Resource ID</th>
                    <th className="text-left pb-3 font-medium">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr
                      key={log.id}
                      className="border-b border-border/50 hover:bg-muted/20 transition-colors"
                    >
                      <td className="py-2">{levelIcon(log.level)}</td>
                      <td className="py-2 text-xs font-mono text-muted-foreground">
                        {log.user_id.slice(0, 8)}...
                      </td>
                      <td className="py-2">
                        <span className="text-xs px-2 py-0.5 rounded-full bg-muted/50">
                          {log.action}
                        </span>
                      </td>
                      <td className="py-2 text-xs text-muted-foreground">{log.resource_type}</td>
                      <td className="py-2 text-xs font-mono text-muted-foreground">
                        {log.resource_id ? log.resource_id.slice(0, 8) + '...' : '-'}
                      </td>
                      <td className="py-2 text-xs text-muted-foreground">
                        {log.created_at ? new Date(log.created_at).toLocaleString() : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {total > filter.per_page && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
                <span className="text-xs text-muted-foreground">
                  Page {filter.page} of {Math.ceil(total / filter.per_page)}
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={filter.page === 1}
                    onClick={() => setFilter((f) => ({ ...f, page: f.page - 1 }))}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={filter.page >= Math.ceil(total / filter.per_page)}
                    onClick={() => setFilter((f) => ({ ...f, page: f.page + 1 }))}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
