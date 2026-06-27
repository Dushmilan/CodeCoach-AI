'use client';
export const dynamic = 'force-dynamic';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/providers';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Shield, Save, RotateCcw } from 'lucide-react';

interface Flag {
  enabled: boolean;
  rollout_pct: number;
  target_roles?: string[];
  description?: string;
}

export default function FeatureFlagsPage() {
  const { user, token } = useAuth();
  const [flags, setFlags] = useState<Record<string, Flag>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  const fetchFlags = useCallback(async () => {
    try {
      const res = await fetch('/api/admin/feature-flags', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setFlags(data.flags || data);
    } catch {
      /* */
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchFlags();
  }, [fetchFlags]);

  const updateFlag = async (key: string, updates: Partial<Flag>) => {
    setSaving(key);
    try {
      const res = await fetch(`/api/admin/feature-flags/${key}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(updates),
      });
      if (res.ok) await fetchFlags();
    } catch {
      /* */
    } finally {
      setSaving(null);
    }
  };

  if (loading)
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Feature Flags</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Toggle features and control rollout percentages
        </p>
      </div>

      {Object.keys(flags).length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No feature flags configured.
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(flags).map(([key, flag]) => (
            <Card key={key}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Shield
                        className={`h-5 w-5 ${
                          flag.enabled ? 'text-green-500' : 'text-muted-foreground'
                        }`}
                      />
                    </div>
                    <div>
                      <CardTitle className="text-sm capitalize">{key.replace(/_/g, ' ')}</CardTitle>
                      {flag.description && (
                        <p className="text-xs text-muted-foreground mt-0.5">{flag.description}</p>
                      )}
                    </div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={flag.enabled}
                      onChange={(e) => updateFlag(key, { enabled: e.target.checked })}
                    />
                    <div className="w-9 h-5 bg-muted rounded-full peer peer-checked:bg-green-500 after:content-[''] after:absolute after:top-0.5 after:start-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-full" />
                  </label>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">
                    Rollout: {flag.rollout_pct}%
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={flag.rollout_pct}
                    onChange={(e) => updateFlag(key, { rollout_pct: Number(e.target.value) })}
                    className="w-full accent-primary"
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>0%</span>
                    <span>50%</span>
                    <span>100%</span>
                  </div>
                </div>
                {flag.target_roles && (
                  <div className="flex flex-wrap gap-1">
                    {flag.target_roles.map((r) => (
                      <span
                        key={r}
                        className="text-[10px] px-2 py-0.5 rounded-full bg-muted/50 text-muted-foreground capitalize"
                      >
                        {r.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                )}
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  {saving === key ? (
                    <>
                      <RotateCcw className="h-3 w-3 animate-spin" /> Saving...
                    </>
                  ) : (
                    <>
                      <Save className="h-3 w-3" /> Auto-saves on change
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
