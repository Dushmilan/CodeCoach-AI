import React from 'react';

export function LoadingSkeleton() {
  return (
    <main className="flex h-screen bg-background" role="main" aria-label="CodeCoach AI Learning Platform">
      <aside className="w-80 border-r border-border bg-card animate-pulse">
        <div className="p-4 border-b border-border">
          <div className="h-6 bg-secondary rounded w-24" />
        </div>
        <div className="p-4 space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-secondary rounded" />
          ))}
        </div>
      </aside>

      <div className="flex-1 flex flex-col">
        <header className="border-b border-border bg-card p-4">
          <div className="h-8 bg-secondary rounded w-48 animate-pulse" />
        </header>

        <div className="flex-1 flex">
          <section className="flex-1 p-4">
            <div className="space-y-4">
              <div className="h-8 bg-secondary rounded w-64 animate-pulse" />
              <div className="h-4 bg-secondary rounded w-32 animate-pulse" />
              <div className="h-20 bg-secondary rounded animate-pulse" />
            </div>
          </section>

          <aside className="w-96 border-l border-border p-4">
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-16 bg-secondary rounded animate-pulse" />
              ))}
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
}
