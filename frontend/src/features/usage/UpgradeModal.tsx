"use client";

import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UpgradeModalProps {
  open: boolean;
  onClose: () => void;
  limit?: number;
}

export function UpgradeModal({ open, onClose, limit = 20 }: UpgradeModalProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Upgrade to Pro"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md bg-background rounded-2xl border border-white/10 p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold tracking-wide">
              Upgrade to Pro
            </h2>
            <p className="text-xs text-muted-foreground/70 mt-1">
              Unlock unlimited AI coaching and priority support.
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="p-1 hover:bg-white/5 rounded-full"
          >
            <X className="h-4 w-4 text-muted-foreground/60" />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
            <p className="text-xs text-muted-foreground/70">Free</p>
            <p className="text-2xl font-bold mt-1">20</p>
            <p className="text-[11px] text-muted-foreground/60">
              AI messages / day
            </p>
          </div>
          <div className="rounded-xl border border-primary/40 bg-primary/10 p-4">
            <p className="text-xs text-primary">Pro</p>
            <p className="text-2xl font-bold mt-1">Unlimited</p>
            <p className="text-[11px] text-muted-foreground/60">
              Priority support
            </p>
          </div>
        </div>

        <p className="text-xs text-muted-foreground/70 mb-6 leading-relaxed">
          You&apos;ve reached your daily limit of {limit} AI messages. Upgrade to Pro to
          keep getting real-time coding assistance without interruption.
        </p>

        <Button className="w-full" onClick={onClose}>
          Request access
        </Button>
      </div>
    </div>
  );
}