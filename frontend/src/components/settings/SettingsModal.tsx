"use client";

import { Button } from "@/components/ui/button";
import { showToast } from "@/components/ui/Toast";
import { Eye, EyeOff, FileText, LogOut, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
  apiKey: string;
  onSave: (key: string) => void;
  isAuthenticated?: boolean;
  onLogout?: () => void;
}

export function SettingsModal({
  open,
  onClose,
  apiKey,
  onSave,
  isAuthenticated = false,
  onLogout,
}: SettingsModalProps) {
  const [inputValue, setInputValue] = useState(apiKey);
  const [showKey, setShowKey] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setInputValue(apiKey);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open, apiKey]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (open) document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [open, onClose]);

  if (!open) return null;

  const handleSave = () => {
    onSave(inputValue.trim());
    showToast("API key saved", "success");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative w-full max-w-md mx-4 p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/10">
        <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-semibold tracking-wide text-foreground/80">
              SETTINGS
            </h2>
            <button
              aria-label="Close"
              onClick={onClose}
              className="p-1.5 hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
            >
              <X className="h-3.5 w-3.5 text-muted-foreground" />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-foreground/70 mb-1.5 tracking-wide">
                NVIDIA API Key
              </label>
              <p className="text-[10px] text-muted-foreground/50 mb-3 leading-relaxed">
                Required for AI coaching features. Your key is stored locally
                and never sent to our servers.
              </p>
              <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-0.5">
                <div className="relative rounded-[calc(1rem-0.125rem)]">
                  <input
                    ref={inputRef}
                    type={showKey ? "text" : "password"}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="nvapi-..."
                    className="w-full px-3 py-2 pr-10 text-sm bg-transparent text-foreground/80 placeholder:text-muted-foreground/40 focus:outline-none font-mono"
                  />
                  <button
                    onClick={() => setShowKey(!showKey)}
                    aria-label={showKey ? "Hide password" : "Show password"}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
                  >
                    {showKey ? (
                      <EyeOff className="h-3.5 w-3.5 text-muted-foreground/60" />
                    ) : (
                      <Eye className="h-3.5 w-3.5 text-muted-foreground/60" />
                    )}
                  </button>
                </div>
              </div>
              <div className="text-right mt-1.5">
                <a
                  href="https://build.nvidia.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[10px] text-blue-400/70 hover:text-blue-400 transition-colors"
                >
                  How to get the API key?
                </a>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={onClose}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleSave}>
                Save
              </Button>
            </div>

            <div className="border-t border-white/5 pt-4 mt-2 space-y-1">
              <button
                onClick={() => {
                  window.location.href = "/privacy";
                  onClose();
                }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-foreground/60 hover:text-foreground hover:bg-white/5 rounded-xl transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
              >
                <FileText className="h-4 w-4" />
                Privacy Policy
              </button>
            </div>

            {isAuthenticated && onLogout && (
              <div className="border-t border-white/5 pt-4 mt-2">
                <button
                  onClick={() => {
                    onLogout();
                    onClose();
                  }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-400/80 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
