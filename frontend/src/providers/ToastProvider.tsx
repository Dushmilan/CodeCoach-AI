'use client';

import type { ReactNode } from 'react';
import { ToastContainer } from '@/components/ui/Toast';

export function ToastProvider({ children }: { children: ReactNode }) {
  return (
    <>
      {children}
      <ToastContainer />
    </>
  );
}
