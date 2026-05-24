'use client';

import { useEffect, useState, useCallback } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

type ToastVariant = 'success' | 'error' | 'info';

interface ToastData {
  id: string;
  message: string;
  variant: ToastVariant;
}

const VARIANT_STYLES: Record<ToastVariant, string> = {
  success: 'bg-green-600 text-white',
  error: 'bg-destructive text-destructive-foreground',
  info: 'bg-primary text-primary-foreground',
};

let toastListeners: Array<(toast: ToastData) => void> = [];
let toastId = 0;

export function showToast(message: string, variant: ToastVariant = 'info') {
  const toast: ToastData = { id: `toast-${++toastId}`, message, variant };
  toastListeners.forEach(fn => fn(toast));
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  useEffect(() => {
    const listener = (toast: ToastData) => {
      setToasts(prev => [...prev, toast]);
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== toast.id));
      }, 4000);
    };
    toastListeners.push(listener);
    return () => {
      toastListeners = toastListeners.filter(fn => fn !== listener);
    };
  }, []);

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={cn(
            'flex items-center gap-2 px-4 py-3 rounded-md shadow-lg text-sm animate-in slide-in-from-right',
            VARIANT_STYLES[toast.variant]
          )}
        >
          <span className="flex-1">{toast.message}</span>
          <button onClick={() => dismiss(toast.id)} className="opacity-70 hover:opacity-100">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}
