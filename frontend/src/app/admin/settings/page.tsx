'use client';
export const dynamic = 'force-dynamic';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/providers';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Settings as SettingsIcon, Save, RotateCcw, Globe, Clock, Cpu, Code } from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuth();
  const [settings, setSettings] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  const fetchSettings = useCallback(async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch('/api/admin/settings', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
      setSettings((await res.json()).settings || {});
    } catch {
      /* */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const saveSettings = async () => {
    setSaving(true);
    setMsg('');
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch('/api/admin/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(settings),
      });
      if (res.ok) setMsg('Settings saved');
      else setMsg('Failed to save');
    } catch {
      setMsg('Error saving');
    } finally {
      setSaving(false);
    }
  };

  const update = (path: string, value: any) => {
    setSettings((prev: any) => {
      const copy = JSON.parse(JSON.stringify(prev));
      const keys = path.split('.');
      let obj = copy;
      for (let i = 0; i < keys.length - 1; i++) {
        if (!obj[keys[i]]) obj[keys[i]] = {};
        obj = obj[keys[i]];
      }
      obj[keys[keys.length - 1]] = value;
      return copy;
    });
  };

  const Field = ({ label, path, type = 'text', icon: Icon, superAdmin = false }: any) => (
    <div className="space-y-1.5">
      <label className="text-xs text-muted-foreground flex items-center gap-1">
        {Icon && <Icon className="h-3 w-3" />}
        {label}
        {superAdmin && (
          <span className="text-[10px] px-1 py-0.5 rounded bg-purple-500/20 text-purple-500">
            super_admin
          </span>
        )}
      </label>
      {type === 'select' ? (
        <input
          className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
          value={String(settings[label.toLowerCase()] ?? '')}
          onChange={(e) => update(path, e.target.value)}
        />
      ) : type === 'number' ? (
        <input
          type="number"
          className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
          value={Number(settings[label.toLowerCase()] ?? 0)}
          onChange={(e) => update(path, Number(e.target.value))}
        />
      ) : (
        <input
          className="w-full text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border outline-none"
          value={String(settings[label.toLowerCase()] ?? '')}
          onChange={(e) => update(path, e.target.value)}
        />
      )}
    </div>
  );

  if (loading)
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-muted-foreground text-sm mt-1">System configuration</p>
        </div>
        <div className="flex items-center gap-2">
          {msg && <span className="text-xs text-green-500">{msg}</span>}
          <Button onClick={saveSettings} disabled={saving}>
            {saving ? (
              <RotateCcw className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-1" />
            )}{' '}
            Save
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Globe className="h-4 w-4" /> Piston API
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Piston URL" path="piston_url" icon={Globe} />
          <Field label="Timeout (ms)" path="piston_timeout" type="number" icon={Clock} />
          <Field
            label="Max Memory (MB)"
            path="piston_memory_limit"
            type="number"
            icon={Cpu}
            superAdmin
          />
          <Field
            label="Max CPU (cores)"
            path="piston_cpu_limit"
            type="number"
            icon={Cpu}
            superAdmin
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Code className="h-4 w-4" /> Enabled Languages
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {['python', 'javascript', 'java', 'cpp', 'c', 'go', 'rust', 'typescript'].map(
              (lang) => {
                const enabled = settings.enabled_languages?.includes(lang);
                return (
                  <button
                    key={lang}
                    onClick={() => {
                      const current: string[] = settings.enabled_languages || [];
                      update(
                        'enabled_languages',
                        enabled ? current.filter((l: string) => l !== lang) : [...current, lang],
                      );
                    }}
                    className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                      enabled
                        ? 'bg-green-500/10 text-green-500 border-green-500/30'
                        : 'bg-muted/30 text-muted-foreground border-border'
                    }`}
                  >
                    {lang}
                  </button>
                );
              },
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
