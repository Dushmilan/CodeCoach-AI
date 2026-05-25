'use client';

import { useState, useEffect, useRef } from 'react';
import { X, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
  apiKey: string;
  onSave: (key: string) => void;
}

export function SettingsModal({ open, onClose, apiKey, onSave }: SettingsModalProps) {
  const [inputValue, setInputValue] = useState(apiKey);
  const [showKey, setShowKey] = useState(false);
  const [saved, setSaved] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setInputValue(apiKey);
      setSaved(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open, apiKey]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (open) document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  if (!open) return null;

  const handleSave = () => {
    onSave(inputValue.trim());
    setSaved(true);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md mx-4 p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/10">
        <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-semibold tracking-wide text-foreground/80">SETTINGS</h2>
            <button onClick={onClose} className="p-1.5 hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]">
              <X className="h-3.5 w-3.5 text-muted-foreground" strokeWidth={1} />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-foreground/70 mb-1.5 tracking-wide">
                NVIDIA API Key
              </label>
              <p className="text-[10px] text-muted-foreground/50 mb-3 leading-relaxed">
                Required for AI coaching features. Your key is stored locally and never sent to our servers.
            </p>
              <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-0.5">
                <div className="relative rounded-[calc(1rem-0.125rem)]">
              <input
                ref={inputRef}
                type={showKey ? 'text' : 'password'}
                value={inputValue}
                onChange={(e) => { setInputValue(e.target.value); setSaved(false); }}
                placeholder="nvapi-..."
                className="w-full px-3 py-2 pr-10 text-sm bg-transparent text-foreground/80 placeholder:text-muted-foreground/40 focus:outline-none font-mono"
              />
                  <button
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
                  >
                    {showKey ? <EyeOff className="h-3.5 w-3.5 text-muted-foreground/60" strokeWidth={1} /> : <Eye className="h-3.5 w-3.5 text-muted-foreground/60" strokeWidth={1} />}
                  </button>
                </div>
              </div>
            </div>

            {saved && (
              <p className="text-xs text-green-400/80">API key saved.</p>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={onClose}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleSave}>
                Save
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
