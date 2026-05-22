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
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-background border border-border rounded-lg shadow-lg w-full max-w-md mx-4 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button onClick={onClose} className="p-1 hover:bg-secondary rounded transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              NVIDIA API Key
            </label>
            <p className="text-xs text-muted-foreground mb-2">
              Required for AI coaching features. Your key is stored locally and never sent to our servers.
            </p>
            <div className="relative">
              <input
                ref={inputRef}
                type={showKey ? 'text' : 'password'}
                value={inputValue}
                onChange={(e) => { setInputValue(e.target.value); setSaved(false); }}
                placeholder="nvapi-..."
                className="w-full px-3 py-2 pr-10 text-sm bg-secondary border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary font-mono"
              />
              <button
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-secondary rounded"
              >
                {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {saved && (
            <p className="text-sm text-green-600 dark:text-green-400">API key saved.</p>
          )}

          <div className="flex justify-end space-x-2 pt-2">
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
  );
}
