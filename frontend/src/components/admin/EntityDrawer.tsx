'use client';

import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';

interface EntityDrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  wide?: boolean;
}

export default function EntityDrawer({
  open,
  onClose,
  title,
  subtitle,
  children,
  wide = false,
}: EntityDrawerProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (open) window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Overlay */}
      <div
        ref={overlayRef}
        className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        ref={panelRef}
        className={`relative h-full bg-card border-l border-border shadow-2xl transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] ${
          wide ? 'w-full max-w-2xl' : 'w-full max-w-lg'
        }`}
        style={{
          animation: open ? 'slide-in-right 0.5s cubic-bezier(0.32,0.72,0,1) forwards' : undefined,
        }}
      >
        {/* Glass morphism outer ring effect */}
        <div className="absolute inset-0 rounded-none ring-1 ring-white/5 pointer-events-none" />

        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-border bg-card/80 backdrop-blur-xl">
          <div>
            <h2 className="text-lg font-semibold">{title}</h2>
            {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-muted transition-colors duration-200"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto h-[calc(100vh-65px)]">{children}</div>
      </div>
    </div>
  );
}
