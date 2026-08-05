'use client';

import type { ReactNode } from 'react';
import { Sparkles } from 'lucide-react';
import { useAuth } from '@/providers';
import { Button } from '@/components/ui/button';

interface PremiumGateProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export function PremiumGate({ children, fallback }: PremiumGateProps) {
  const { user } = useAuth();
  const isPremium = user?.plan === 'premium';

  if (isPremium) return <>{children}</>;
  if (fallback) return <>{fallback}</>;

  return (
    <div
      className="flex h-full flex-col items-center justify-center gap-4 p-6 text-center"
      role="status"
      aria-label="Premium feature"
    >
      <div className="rounded-full bg-primary/10 p-3">
        <Sparkles className="h-6 w-6 text-primary" />
      </div>
      <div>
        <p className="text-sm font-semibold text-foreground/80">
          AI Coach is a Premium feature
        </p>
        <p className="mt-1 text-xs text-muted-foreground/70 leading-relaxed">
          Upgrade to Premium to unlock the AI coaching panel with hints,
          reviews, and debugging help.
        </p>
      </div>
      <Button variant="primary-pill" size="sm" aria-label="Go Premium">
        Go Premium
      </Button>
    </div>
  );
}
