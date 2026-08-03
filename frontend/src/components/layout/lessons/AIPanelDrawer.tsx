'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface AIPanelDrawerProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  label?: string;
}

export function AIPanelDrawer({
  open,
  onClose,
  children,
  label = 'AI Assistant',
}: AIPanelDrawerProps) {
  return (
    <AnimatePresence>
      {open && (
        <div className="absolute inset-0 z-40" role="dialog" aria-label={label}>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={onClose}
            aria-hidden="true"
          />
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.28, ease: [0.32, 0.72, 0, 1] }}
            className="absolute inset-y-0 right-0 w-[min(400px,90vw)] h-full flex flex-col bg-background border-l border-white/[0.06] shadow-2xl"
          >
            {children}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
