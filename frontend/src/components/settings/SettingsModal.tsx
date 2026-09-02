'use client';
import { Button } from '@/components/ui/button';
import { FileText, LayoutDashboard, LogOut, Sparkles, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
interface SettingsModalProps { open: boolean; onClose: () => void; isAuthenticated?: boolean; onLogout?: () => void; plan?: string; }
type Tab = 'settings' | 'dashboard' | 'skills';
export function SettingsModal({ open, onClose, isAuthenticated = false, onLogout, plan = 'free', }: SettingsModalProps) {
  const inputRef = useRef<HTMLDivElement>(null);
  const [tab, setTab] = useState<Tab>('settings');
  useEffect(() => { if (open) { setTimeout(() => inputRef.current?.focus(), 100); } else { setTab('settings'); } }, [open]);
  useEffect(() => { const handleEsc = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); }; if (open) document.addEventListener('keydown', handleEsc); return () => document.removeEventListener('keydown', handleEsc); }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md mx-4 p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/10">
        <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-6 max-h-[85vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold tracking-wide text-foreground/80">SETTINGS</h2>
            <button aria-label="Close" onClick={onClose} className="p-1.5 hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"><X className="h-3.5 w-3.5 text-muted-foreground" /></button>
          </div>
          <div className="flex items-center gap-1 p-1 rounded-full bg-white/[0.04] ring-1 ring-white/5 mb-4" role="tablist">
            {[
              { id: 'settings' as Tab, label: 'Settings' },
              { id: 'dashboard' as Tab, label: 'Dashboard' },
              { id: 'skills' as Tab, label: 'Skills' },
            ].map((t) => (
              <button key={t.id} role="tab" aria-selected={tab === t.id} data-testid={`settings-tab-${t.id}`} onClick={() => setTab(t.id)} className={`flex-1 rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${tab === t.id ? 'bg-white text-black' : 'text-muted-foreground hover:text-foreground'}`}>{t.label}</button>
            ))}
          </div>
          <div ref={inputRef} tabIndex={-1} className="space-y-4">
            {tab === 'dashboard' && (
              <div className="space-y-3" data-testid="settings-dashboard-tab">
                <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-4">
                  <div className="flex items-center gap-2 mb-1"><LayoutDashboard className="h-4 w-4 text-primary" /><p className="text-xs font-medium text-foreground/80">Dashboard</p></div>
                  <p className="text-[11px] text-muted-foreground/60 leading-relaxed">Your memory graph — what to refresh before you forget. Open the full dashboard for reviews, rescue queue and skill graph.</p>
                  <button onClick={() => { window.location.href = '/dashboard'; onClose(); }} data-testid="settings-dashboard-open" className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-white text-black px-4 py-1.5 text-xs font-medium hover:bg-white/90 transition-colors"><LayoutDashboard className="h-3.5 w-3.5" /> Open Dashboard</button>
                </div>
              </div>
            )}
            {tab === 'skills' && (
              <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-4" data-testid="settings-skills-tab">
                <p className="text-xs font-medium text-foreground/80 mb-1">Your Skill Graph</p>
                <p className="text-[11px] text-muted-foreground/60 leading-relaxed mb-3">Mastery per skill lives in the Dashboard as a graph — open Dashboard to see the full map. This preview is the boilerplate (all 22 skills).</p>
                <button onClick={() => { window.location.href = '/dashboard'; onClose(); }} className="inline-flex items-center gap-1.5 rounded-full bg-primary/90 text-primary-foreground px-4 py-1.5 text-xs font-medium hover:bg-primary transition-colors"><LayoutDashboard className="h-3.5 w-3.5" /> View graph in Dashboard</button>
              </div>
            )}
            {tab === 'settings' && (
              <>
                <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-4">
                  <div className="flex items-start gap-3"><Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" /><div><p className="text-xs font-medium text-foreground/80">AI coaching powered by Groq</p><p className="text-[10px] text-muted-foreground/60 mt-1 leading-relaxed">Coaching runs on the platform&apos;s Groq API key — no setup required. Token usage is metered per account with daily limits.</p></div></div>
                </div>
                <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-4">
                  <div className="flex items-center justify-between gap-3"><div><p className="text-xs font-medium text-foreground/80">Your plan</p><p className="text-[10px] text-muted-foreground/60 mt-1 leading-relaxed">{plan === 'premium' ? 'Premium — AI Coach and all features unlocked.' : 'Free — questions and curriculum included. AI Coach requires Premium.'}</p></div><span className="rounded-full bg-primary/10 px-3 py-1 text-[10px] font-medium uppercase tracking-wide text-primary">{plan === 'premium' ? 'Premium' : 'Free'}</span></div>
                </div>
              </>
            )}
            <div className="flex justify-end gap-2 pt-2"><Button variant="outline" size="sm" onClick={onClose}>Cancel</Button><Button size="sm" onClick={onClose}>Done</Button></div>
            <div className="border-t border-white/5 pt-4 mt-2 space-y-1"><button onClick={() => { window.location.href = '/privacy'; onClose(); }} className="flex items-center gap-2 w-full px-3 py-2 text-sm text-foreground/60 hover:text-foreground hover:bg-white/5 rounded-xl transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"><FileText className="h-4 w-4" /> Privacy Policy</button></div>
            {isAuthenticated && onLogout && (<div className="border-t border-white/5 pt-4 mt-2"><button onClick={() => { onLogout(); onClose(); }} className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-400/80 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"><LogOut className="h-4 w-4" /> Sign out</button></div>)}
          </div>
        </div>
      </div>
    </div>
  );
}
