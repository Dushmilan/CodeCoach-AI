import React from 'react';

interface MainLayoutContainerProps {
  children: React.ReactNode;
}

export function MainLayoutContainer({ children }: MainLayoutContainerProps) {
  return (
    <main
      className="flex h-[100dvh] bg-background overflow-hidden"
      role="main"
      aria-label="CodeCoach AI Learning Platform"
    >
      <div className="flex w-full gap-0.5 p-2">
        {children}
      </div>
    </main>
  );
}