import React from 'react';

interface MainLayoutContainerProps {
  children: React.ReactNode;
}

export function MainLayoutContainer({ children }: MainLayoutContainerProps) {
  return (
    <main className="flex h-screen bg-background" role="main" aria-label="CodeCoach AI Learning Platform">
      {children}
    </main>
  );
}