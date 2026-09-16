'use client';
import { Button } from '@/components/ui/button';
import { FileText, LogOut, Settings2, Sparkles, User, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
interface SettingsModalProps { open: boolean; onClose: () => void; isAuthenticated?: boolean; onLogout?: () => void; }
type Section = 'general' | 'account';
const SECTIONS: { id: Section; label: string; icon: typeof Settings2 }[] = [
  { id: 'general', label: 'General', icon: Settings2 },
  { id: 'account', label: 'Account', icon: User },
];
export function SettingsModal({ open, onClose, isAuthenticated = false, onLogout, }: SettingsModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const tabRefs = useRef<Record<Section, HTMLButtonElement | null>>({ general: null, account: null });
  const [section, setSection] = useState<Section>('general');
  useEffect(() => { if (open) { setTimeout(() => panelRef.current?.focus(), 100); } else { setSection('general'); } }, [open]);
  useEffect(() => { const handleEsc = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); }; if (open) document.addEventListener('keydown', handleEsc); return () => document.removeEventListener('keydown', handleEsc); }, [open, onClose]);
  if (!open) return null;
  const activeIndex = SECTIONS.findIndex((s) => s.id === section);
  const focusSection = (next: Section) => {
    setSection(next);
    tabRefs.current[next]?.focus();
  };
  const handleNavKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
      e.preventDefault();
      focusSection(SECTIONS[(activeIndex + 1) % SECTIONS.length].id);
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
      e.preventDefault();
      focusSection(SECTIONS[(activeIndex - 1 + SECTIONS.length) % SECTIONS.length].id);
    } else if (e.key === 'Home') {
      e.preventDefault();
      focusSection(SECTIONS[0].id);
    } else if (e.key === 'End') {
      e.preventDefault();
      focusSection(SECTIONS[SECTIONS.length - 1].id);
    }
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-2xl mx-4 p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/10">
        <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-6 max-h-[85vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold tracking-wide text-foreground/80">SETTINGS</h2>
            <button aria-label="Close" onClick={onClose} className="p-1.5 hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"><X className="h-3.5 w-3.5 text-muted-foreground" /></button>
          </div>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex sm:flex-col gap-1 sm:w-48 shrink-0 p-1 rounded-2xl sm:rounded-2xl bg-white/[0.04] ring-1 ring-white/5 overflow-x-auto" role="tablist" aria-orientation="vertical" aria-label="Settings sections" onKeyDown={handleNavKeyDown}>
              {SECTIONS.map((s) => {
                const Icon = s.icon;
                const selected = section === s.id;
                return (
                  <button
                    key={s.id}
                    ref={(el) => { tabRefs.current[s.id] = el; }}
                    role="tab"
                    id={`settings-tab-${s.id}-tab`}
                    aria-selected={selected}
                    aria-controls={`settings-panel-${s.id}`}
                    tabIndex={selected ? 0 : -1}
                    data-testid={`settings-tab-${s.id}`}
                    onClick={() => setSection(s.id)}
                    className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium transition-colors whitespace-nowrap ${selected ? 'bg-white text-black' : 'text-muted-foreground hover:text-foreground hover:bg-white/5'}`}
                  >
                    <Icon className="h-3.5 w-3.5" /> {s.label}
                  </button>
                );
              })}
            </div>
            <div ref={panelRef} tabIndex={-1} role="tabpanel" id={`settings-panel-${section}`} aria-labelledby={`settings-tab-${section}-tab`} className="flex-1 min-w-0 space-y-4 outline-none">
              {section === 'general' && (
                <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-4">
                  <div className="flex items-start gap-3"><Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" /><div><p className="text-xs font-medium text-foreground/80">AI coaching powered by Groq</p><p className="text-[10px] text-muted-foreground/60 mt-1 leading-relaxed">Coaching runs on the platform&apos;s Groq API key — no setup required. Usage is capped by a daily limit.</p></div></div>
                </div>
              )}
              {section === 'account' && (
                <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-2">
                  <button onClick={() => { window.location.href = '/privacy'; onClose(); }} className="flex items-center gap-2 w-full px-3 py-2 text-sm text-foreground/60 hover:text-foreground hover:bg-white/5 rounded-xl transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"><FileText className="h-4 w-4" /> Privacy Policy</button>
                  {isAuthenticated && onLogout && (<button onClick={() => { onLogout(); onClose(); }} className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-400/80 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"><LogOut className="h-4 w-4" /> Sign out</button>)}
                </div>
              )}
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-4"><Button variant="outline" size="sm" onClick={onClose}>Cancel</Button><Button size="sm" onClick={onClose}>Done</Button></div>
        </div>
      </div>
    </div>
  );
}
